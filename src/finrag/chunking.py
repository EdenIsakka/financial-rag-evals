"""Convierte un DoclingDocument en chunks: texto agrupado por sección y cada tabla entera."""

import re

from docling_core.types.doc import DoclingDocument, SectionHeaderItem, TableItem, TitleItem

# shortcut: límite en caracteres (~400 tokens), no en tokens; medir con el tokenizer si molesta.
MAX_CHARS = 1500


def chunk_document(doc: DoclingDocument, max_chars: int = MAX_CHARS) -> list[dict]:
    chunks: list[dict] = []
    section = ""
    buf: list[str] = []
    buf_page: int | None = None

    def flush() -> None:
        nonlocal buf
        if buf:
            # page = página donde empieza el chunk (puede continuar en la siguiente).
            chunks.append(
                {"kind": "text", "page": buf_page, "section": section, "content": "\n".join(buf)}
            )
            buf = []

    for item, _level in doc.iterate_items():
        page = item.prov[0].page_no if item.prov else None  # el HTML no tiene páginas

        if isinstance(item, SectionHeaderItem | TitleItem):
            flush()
            section = item.text
        elif isinstance(item, TableItem):
            flush()
            # Docling rellena las celdas con espacios para alinear; no aportan nada al embedding.
            md = re.sub(r" {2,}", " ", item.export_to_markdown(doc))
            chunks.append({"kind": "table", "page": page, "section": section, "content": md})
        elif text := getattr(item, "text", "").strip():
            if buf and sum(map(len, buf)) + len(text) > max_chars:
                flush()
            if not buf:
                buf_page = page
            buf.append(text)

    flush()
    return chunks
