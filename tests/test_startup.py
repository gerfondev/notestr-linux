"""Régressions du chargement initial, sans fenêtre ni accès au compte réel."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("gi")
from nostr_notes.app import Window
from nostr_notes.editor import MarkdownEditor


@pytest.mark.parametrize("visual_ready", [False, True])
def test_login_refreshes_even_while_visual_document_is_loading(visual_ready):
    editor = SimpleNamespace(
        pending_document=False, switching=False, ready=visual_ready,
        visual_active=visual_ready, notice=Mock(),
    )

    def set_text(text):
        editor.pending_document = visual_ready

    editor.set_text = set_text
    editor.set_sensitive = Mock()
    editor.flush = lambda callback: MarkdownEditor.flush(editor, callback)
    identity = SimpleNamespace(pubkey="test-account", notes=Mock(return_value=([], 0)))
    window = SimpleNamespace(
        store=SimpleNamespace(events=Mock(return_value=[])),
        editor=editor, controls=Mock(), status=Mock(), set_title=Mock(),
        render_list=Mock(), do_refresh=Mock(), busy=False, confirm=Mock(),
    )
    window.display = lambda: Window.display(window)
    window.guard = lambda action: Window.guard(window, action)
    window.refresh = lambda: Window.refresh(window)

    Window.login(window, identity)

    assert editor.pending_document == visual_ready
    assert window.dirty is False
    window.do_refresh.assert_called_once_with()
    window.confirm.assert_not_called()


def test_manual_refresh_still_protects_unpublished_changes():
    window = SimpleNamespace(
        busy=False, dirty=True, do_refresh=Mock(), confirm=Mock(),
        editor=SimpleNamespace(flush=lambda callback: callback()),
    )
    window.guard = lambda action: Window.guard(window, action)

    Window.refresh(window)

    window.do_refresh.assert_not_called()
    window.confirm.assert_called_once()
    assert window.confirm.call_args.args[1] == window.do_refresh
