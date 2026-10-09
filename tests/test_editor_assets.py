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
    assert 'imageReferenceCandidate' in js
    assert r'notestr-image\.invalid' in js
    assert 'data.keepAttr = custom || inline || localPreview' in js
    assert 'Older notes may have been produced by clients that percent-encode' in js


def test_application_logo_is_packaged_png():
    logo = ASSETS / 'fr.decentralia.NostrNotes.png'
    data = logo.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    width, height = struct.unpack('>II', data[16:24])
    assert width == height
    assert width >= 256
    assert data[25] == 6  # PNG true colour with alpha channel


def test_both_sanitizers_use_maintained_external_dompurify():
    html = (ASSETS / 'index.html').read_text()
    assert html.index('purify.min.js') < html.index('toastui-editor.js')
    bundle = (ASSETS / 'toastui-editor.js').read_text()
    assert 'DOMPurify 2.3.3' not in bundle
    assert 't(e.DOMPurify)' in bundle
    assert 'require(\"dompurify\")' in bundle
    assert 'DOMPurify 2.3.3' not in bundle
    assert '3.4.16' in (ASSETS / 'purify.min.js').read_text()[:300]


def test_gplv3_license_is_available_in_source_and_asset():
    license_text = (ASSETS.parents[2] / 'LICENSE').read_text()
    bundled = (ASSETS / 'GPL-3.0.txt').read_text()
    assert license_text.lstrip().startswith('GNU GENERAL PUBLIC LICENSE')
    assert bundled.lstrip() == license_text.lstrip()
    assert 'Version 3, 29 June 2007' in license_text
