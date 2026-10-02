"""Native menu actions remain external, revision-bound, and preserve Copy Link."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
pytest.importorskip('gi')
from nostr_notes.editor import MarkdownEditor, WebKit


def menu_case(uri='https://example.org/test'):
    menu=WebKit.ContextMenu.new()
    for action in (WebKit.ContextMenuAction.OPEN_LINK,WebKit.ContextMenuAction.OPEN_LINK_IN_NEW_WINDOW,WebKit.ContextMenuAction.DOWNLOAD_LINK_TO_DISK,WebKit.ContextMenuAction.COPY_LINK_TO_CLIPBOARD):
        menu.append(WebKit.ContextMenuItem.new_from_stock_action(action))
    hit=SimpleNamespace(context_is_link=lambda:True,get_link_uri=lambda:uri)
    editor=SimpleNamespace(epoch=7,visual_active=True,_is_web_link=MarkdownEditor._is_web_link,_open_link=Mock(),flush=Mock(side_effect=lambda done:done()))
    assert MarkdownEditor._context_menu(editor,None,menu,hit) is False
    return editor,menu


def test_context_open_dispatches_browser_after_flush_and_keeps_copy():
    editor,menu=menu_case()
    assert menu.get_n_items()==2
    assert menu.last().get_stock_action()==WebKit.ContextMenuAction.COPY_LINK_TO_CLIPBOARD
    menu.first().get_gaction().activate(None)
    editor.flush.assert_called_once()
    editor._open_link.assert_called_once_with('https://example.org/test')


def test_menu_from_previous_document_cannot_open_link():
    editor,menu=menu_case();editor.epoch+=1
    menu.first().get_gaction().activate(None)
    editor.flush.assert_not_called();editor._open_link.assert_not_called()


def test_document_changed_during_flush_cannot_open_link():
    editor,menu=menu_case()
    def flush(done):editor.epoch+=1;done()
    editor.flush=flush;menu.first().get_gaction().activate(None)
    editor._open_link.assert_not_called()


@pytest.mark.parametrize('uri',['javascript:alert(1)','file:///etc/passwd','https:','data:text/html,test'])
def test_menu_never_opens_non_web_url(uri):
    editor,menu=menu_case(uri)
    assert menu.get_n_items()==1
    assert menu.first().get_stock_action()==WebKit.ContextMenuAction.COPY_LINK_TO_CLIPBOARD
    editor._open_link.assert_not_called()
