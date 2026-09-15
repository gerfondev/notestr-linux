from pathlib import Path

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
