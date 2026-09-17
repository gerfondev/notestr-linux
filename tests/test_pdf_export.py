from pathlib import Path

import pytest

from nostr_notes.pdf_export import export_markdown_pdf, markdown_html


SAMPLE = """# Export PDF

Texte **important**.

- premier
- second

| A | B |
|---|---|
| 1 | 2 |

```sh
echo test
```
"""


def test_pdf_export_is_valid_and_replaces_atomically(tmp_path):
    destination = tmp_path / "ma-note.pdf"
    destination.write_text("ancienne version")
    result = export_markdown_pdf(SAMPLE, destination)
    assert result == destination
    assert destination.read_bytes().startswith(b"%PDF-")
    assert destination.stat().st_size > 2_000
    assert destination.stat().st_mode & 0o077 == 0


def test_export_failure_preserves_existing_file(tmp_path):
    destination = tmp_path / "ma-note.pdf"
    destination.write_text("à conserver")
    with pytest.raises(ValueError, match="vide"):
        export_markdown_pdf("   ", destination)
    assert destination.read_text() == "à conserver"


def test_html_blocks_active_html_and_remote_images():
    html = markdown_html('<script>alert(1)</script>\n\n![secret](https://example.org/x.png)')
    assert "<script>" not in html
    assert "https://example.org" not in html
    assert "Image : secret" in html
