from io import BytesIO

from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter

from finrag.chunking import chunk_document

HTML = """<html><body>
<h1>Estado de resultados</h1>
<p>Resumen del ejercicio 2024.</p>
<table>
  <tr><th>Concepto</th><th>2024</th><th>2023</th></tr>
  <tr><td>Ingresos por intereses</td><td>1,103,976</td><td>1,001,250</td></tr>
  <tr><td>Utilidad neta</td><td>51,272</td><td>45,515</td></tr>
</table>
<h1>Notas</h1>
<p>{long}</p>
<p>{long}</p>
</body></html>"""


def chunks_for(html: str, **kwargs):
    stream = DocumentStream(name="t.html", stream=BytesIO(html.encode()))
    return chunk_document(DocumentConverter().convert(stream).document, **kwargs)


def test_table_is_one_whole_chunk_with_its_section():
    chunks = chunks_for(HTML.format(long="x"))
    tables = [c for c in chunks if c["kind"] == "table"]

    assert len(tables) == 1
    table = tables[0]
    assert table["section"] == "Estado de resultados"
    # Etiqueta y cifra en la misma fila: justo lo que pdftotext rompía.
    assert "| Utilidad neta | 51,272 | 45,515 |" in table["content"]
    assert "Ingresos por intereses" in table["content"]


def test_text_is_grouped_by_section_and_split_at_max_chars():
    chunks = chunks_for(HTML.format(long="a" * 80), max_chars=100)
    texts = [c for c in chunks if c["kind"] == "text"]

    assert texts[0] == {
        "kind": "text",
        "page": None,
        "section": "Estado de resultados",
        "content": "Resumen del ejercicio 2024.",
    }
    notas = [c for c in texts if c["section"] == "Notas"]
    assert len(notas) == 2  # dos párrafos de 80 no caben juntos en 100
