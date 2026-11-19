from pathlib import Path

from docling.utils.xbrl_utils import is_ixbrl

from finrag.ingest import as_plain_html, parse_name

IXBRL = (
    b'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">'
    b'<body><div style="display:none"><ix:header><ix:hidden>hecho oculto</ix:hidden></ix:header>'
    # \x92 es un apóstrofo en Windows-1252: aparece en 20-F guardados desde el navegador.
    b"</div><p>Bancolombia\x92s net income was Ps <ix:nonFraction>6,300</ix:nonFraction>.</p>"
    b"</body></html>"
)


def test_ixbrl_becomes_plain_html_and_keeps_visible_figures():
    html = as_plain_html(IXBRL)

    assert is_ixbrl(IXBRL)
    assert not is_ixbrl(html)
    assert b"hecho oculto" not in html
    assert b"<ix:nonFraction>6,300</ix:nonFraction>" in html


def test_parse_name():
    assert parse_name(Path("data/raw/bancolombia_2024_20f.html")) == ("bancolombia", 2024)
