"""finrag-ingest: data/raw/*.{pdf,html} -> chunks con embedding en Postgres.

Los archivos se nombran <empresa>_<año>_<tipo>.<ext>, p. ej. davivienda_2024_ef.pdf.
"""

import re
import sys
import time
from io import BytesIO
from pathlib import Path

import torch
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter
from sentence_transformers import SentenceTransformer

from finrag.chunking import chunk_document
from finrag.db import connect

RAW = Path("data/raw")
EMBED_MODEL = "BAAI/bge-m3"


def parse_name(path: Path) -> tuple[str, int]:
    company, year, *_ = path.stem.split("_")
    return company, int(year)


def as_plain_html(html: bytes) -> bytes:
    """Los 20-F de la SEC son Inline XBRL; Docling los leería con su backend XBRL.

    Se quita el bloque oculto de hechos XBRL y se renombra el namespace `ix` de la raíz para
    que Docling lo lea como HTML. Las etiquetas <ix:...> que envuelven cada cifra se quedan:
    el parser HTML conserva su texto. Se trabaja en bytes porque los 20-F guardados desde el
    navegador pueden mezclar codificaciones; Docling detecta la codificación al parsear.
    """
    html = re.sub(rb"<ix:header>.*?</ix:header>", b"", html, flags=re.DOTALL)
    return html.replace(b"xmlns:ix=", b"data-ix=", 1)


def source_for(path: Path) -> Path | DocumentStream:
    if path.suffix != ".html":
        return path
    return DocumentStream(name=path.name, stream=BytesIO(as_plain_html(path.read_bytes())))


def main() -> None:
    files = [Path(p) for p in sys.argv[1:]] or sorted(
        p for p in RAW.iterdir() if p.suffix in {".pdf", ".html"}
    )
    # Falla antes de gastar minutos en Docling si algún nombre no sigue la convención.
    for f in files:
        parse_name(f)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    # fp16 en GPU: la mitad de memoria y prácticamente los mismos vectores.
    model_kwargs = {"torch_dtype": torch.float16} if device == "cuda" else {}
    embedder = SentenceTransformer(EMBED_MODEL, device=device, model_kwargs=model_kwargs)
    converter = DocumentConverter()

    with connect() as conn:
        for f in files:
            company, year = parse_name(f)
            t = time.time()
            chunks = chunk_document(converter.convert(source_for(f)).document)
            # Se embebe "sección + contenido" para que un chunk de solo cifras sepa de qué trata.
            vectors = embedder.encode(
                [f"{c['section']}\n{c['content']}" for c in chunks],
                normalize_embeddings=True,
                batch_size=8,
            )
            with conn.transaction():  # o se reemplaza el documento completo, o no se toca
                conn.execute("DELETE FROM chunks WHERE source = %s", (f.name,))
                with conn.cursor() as cur:
                    cur.executemany(
                        "INSERT INTO chunks (source, company, year, page, section, kind, content,"
                        " embedding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        [
                            (
                                f.name,
                                company,
                                year,
                                c["page"],
                                c["section"],
                                c["kind"],
                                c["content"],
                                v,
                            )
                            for c, v in zip(chunks, vectors, strict=True)
                        ],
                    )
            tables = sum(c["kind"] == "table" for c in chunks)
            print(f"{f.name}: {len(chunks)} chunks ({tables} tablas) en {time.time() - t:.0f}s")
