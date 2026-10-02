from types import SimpleNamespace
import pytest
pytest.importorskip("gi")
from nostr_notes import editor

@pytest.mark.parametrize("version,expected", [((2, 52, 6), False), ((2, 53, 92), False), ((2, 54, 0), True), ((2, 54, 1), True)])
def test_visual_engine_requires_fixed_release(monkeypatch, version, expected):
    monkeypatch.setattr(editor, "WebKit", SimpleNamespace(get_major_version=lambda: version[0], get_minor_version=lambda: version[1], get_micro_version=lambda: version[2]))
    assert editor.supported_webkit() is expected

def test_missing_engine_keeps_source_mode(monkeypatch):
    monkeypatch.setattr(editor, "WebKit", None)
    assert editor.supported_webkit() is False
