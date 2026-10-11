from pathlib import Path
import io

import pytest
from PIL import Image

from nostr_notes.pdf_export import encrypted_image_references, export_markdown_pdf, markdown_html


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


def test_encrypted_image_references_are_deduplicated_and_remote_images_ignored():
    first = 'notestr-image://' + 'a' * 64 + '?server=https%3A%2F%2Fimages.example&key=' + 'A' * 43 + '&nonce=' + 'A' * 16 + '&mime=image%2Fjpeg'
    second = 'notestr-image://' + 'b' * 64 + '?server=https%3A%2F%2Fimages.example&key=' + 'B' * 43 + '&nonce=' + 'B' * 16 + '&mime=image%2Fjpeg'
    markdown = f'![one]({first})\n\n![external](https://example.org/a.jpg)\n\n![two]({second})\n\n![again]({first})'
    assert encrypted_image_references(markdown) == [first, second]


def test_pdf_embeds_decrypted_notestr_images_and_keeps_remote_images_private(tmp_path):
    first = 'notestr-image://' + 'a' * 64 + '?server=https%3A%2F%2Fimages.example&key=' + 'A' * 43 + '&nonce=' + 'A' * 16 + '&mime=image%2Fjpeg'
    second = 'notestr-image://' + 'b' * 64 + '?server=https%3A%2F%2Fimages.example&key=' + 'B' * 43 + '&nonce=' + 'B' * 16 + '&mime=image%2Fjpeg'
    images = []
    for color in ('navy', 'orange'):
        stream = io.BytesIO()
        Image.new('RGB', (12, 8), color).save(stream, format='JPEG')
        images.append(stream.getvalue())
    markdown = f'# Images\n\n![one]({first})\n\n![two]({second})\n\n![external](https://example.org/private.jpg)'
    image_data = {first: images[0], second: images[1]}
    html = markdown_html(markdown, image_data)
    assert html.count('<img class="note-image"') == 2
    assert 'https://example.org/private.jpg' not in html
    assert 'Image : external' in html
    destination = tmp_path / 'images.pdf'
    export_markdown_pdf(markdown, destination, image_data)
    pdf = destination.read_bytes()
    assert pdf.startswith(b'%PDF-')
    assert pdf.count(b'/Subtype /Image') >= 2


def test_pdf_rejects_non_jpeg_image_data(tmp_path):
    reference = 'notestr-image://' + 'c' * 64 + '?server=https%3A%2F%2Fimages.example&key=' + 'C' * 43 + '&nonce=' + 'C' * 16 + '&mime=image%2Fjpeg'
    with pytest.raises(ValueError, match='Image indisponible'):
        markdown_html(f'![bad]({reference})', {reference: b'not a jpeg'})
