"""Export local et atomique du Markdown vers un PDF A4."""
from html import escape
import os
from pathlib import Path
import tempfile

from markdown_it import MarkdownIt
from weasyprint import HTML


PDF_CSS = """
@page {
  size: A4;
  margin: 17mm 18mm 18mm;
  @bottom-center { content: counter(page) " / " counter(pages); color: #777; font-size: 8.5pt; }
}
html { font-family: sans-serif; color: #202124; font-size: 11pt; line-height: 1.5; }
body { margin: 0; }
h1, h2, h3, h4, h5, h6 { color: #202124; line-height: 1.25; break-after: avoid; }
h1 { font-size: 24pt; border-bottom: 1px solid #999; padding-bottom: 5pt; }
h2 { font-size: 18pt; border-bottom: 1px solid #ddd; padding-bottom: 3pt; }
h3 { font-size: 14pt; }
p, ul, ol, blockquote, pre, table { margin: 0 0 10pt; }
ul, ol { padding-left: 22pt; }
blockquote { border-left: 3px solid #7a43b6; color: #555; padding-left: 10pt; }
pre { background: #f3f5f6; border-radius: 3pt; padding: 10pt; white-space: pre-wrap; break-inside: avoid; }
code { font-family: monospace; font-size: 9.5pt; }
:not(pre) > code { background: #f3f5f6; padding: 1pt 3pt; border-radius: 2pt; }
table { border-collapse: collapse; break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 5pt 8pt; text-align: left; }
th { background: #555; color: white; }
a { color: #4d267f; text-decoration: underline; }
.image-placeholder { color: #777; font-style: italic; }
"""


def _image_as_text(tokens, index, _options, _env):
    token = tokens[index]
    alt = "".join(child.content for child in (token.children or []))
    return f'<span class="image-placeholder">[Image : {escape(alt or "non exportée")}]</span>'


def markdown_html(markdown):
    renderer = MarkdownIt("commonmark", {"html": False}).enable(["table", "strikethrough"])
    renderer.renderer.rules["image"] = _image_as_text
    body = renderer.render(markdown)
    title = next((line.strip().lstrip("#").strip() for line in markdown.splitlines() if line.strip()), "Note Nostr")
    return ("<!doctype html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
            f"<title>{escape(title)}</title><style>{PDF_CSS}</style></head>"
            f"<body>{body}</body></html>")


def export_markdown_pdf(markdown, path):
    """Crée le PDF à côté de sa destination puis le remplace atomiquement."""
    if not markdown.strip():
        raise ValueError("La note est vide.")
    destination = Path(path).expanduser().resolve()
    if not destination.parent.is_dir():
        raise ValueError("Le dossier de destination n’existe pas.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{destination.stem}-", suffix=".pdf",
                                         dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
        HTML(string=markdown_html(markdown)).write_pdf(temporary)
        if temporary.read_bytes()[:5] != b"%PDF-" or temporary.stat().st_size < 500:
            raise RuntimeError("Le fichier PDF généré est invalide.")
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
        temporary = None
        return destination
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
