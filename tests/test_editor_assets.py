from pathlib import Path
import struct

ASSETS = Path(__file__).parents[1] / 'src/nostr_notes/assets'


def test_assets_shipped_and_offline_policy():
    html = (ASSETS / 'index.html').read_text()
    for name in ('toastui-editor.js', 'toastui-editor.css', 'fr-fr.js', 'editor.js', 'editor.css', 'purify.min.js'):
        assert name in html
        assert (ASSETS / name).is_file()
    assert "connect-src 'none'" in html
    assert "default-src 'none'" in html
    assert "frame-src 'none'" in html
    js = (ASSETS / 'editor.js').read_text()
    assert 'usageStatistics: false' in js
    assert 'DOMPurify.sanitize' in js


def test_application_logo_is_packaged_png():
    logo = ASSETS / 'fr.decentralia.NostrNotes.png'
    data = logo.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', data[16:24])
    assert width == height
    assert width >= 256
    assert data[25] == 6  # PNG true colour with alpha channel
