"""Synthetic cache and browser regressions. No real account/browser access."""
from concurrent.futures import Future
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
pytest.importorskip('gi')
from nostr_notes.app import Window
from nostr_notes.editor import MarkdownEditor


def test_cache_accessible_during_delayed_refresh():
    future=Future()
    window=SimpleNamespace(busy=False,refreshing=False,identity=object(),controls=Mock(),settings_button=Mock(),editor=Mock(),listbox=Mock(),status=Mock(),pool=SimpleNamespace(submit=lambda _:future))
    success=Mock()
    with patch('nostr_notes.app.GLib.idle_add',side_effect=lambda f:f()):
        Window.work(window,lambda:None,success,readable=True)
        assert window.busy and window.refreshing
        window.editor.set_sensitive.assert_called_with(True)
        window.listbox.set_sensitive.assert_called_with(True)
        window.controls.set_sensitive.assert_called_with(False)
        assert not success.called
        future.set_result('updated')
    assert not window.busy and not window.refreshing
    success.assert_called_once_with('updated')


def test_refresh_preserves_open_draft():
    original=object()
    window=SimpleNamespace(current=original,dirty=True,notes=[original],display=Mock(),render_list=Mock(),status=Mock())
    def work(operation,success,readable=False):
        assert readable
        success(({'new':'event'},['updated'],0,[]))
    window.work=work
    Window.do_refresh(window)
    assert window.current is original and window.dirty
    window.display.assert_not_called()
    assert window.notes==['updated']


@pytest.mark.parametrize('uri',['https://example.org/path?q=test#anchor','http://example.org'])
def test_links_launch_browser(uri):
    with patch('nostr_notes.editor.Gio.AppInfo.launch_default_for_uri_async') as launch:
        MarkdownEditor._open_link(SimpleNamespace(notice=Mock()),uri)
    assert launch.call_args.args[0]==uri


@pytest.mark.parametrize('uri',['javascript:alert(1)','file:///etc/passwd','data:text/html,test','https:','https:///path','//example.org','https://exa\nmple.org','https://example.org\\file',None])
def test_unsafe_links_never_launch(uri):
    with patch('nostr_notes.editor.Gio.AppInfo.launch_default_for_uri_async') as launch:
        MarkdownEditor._open_link(SimpleNamespace(notice=Mock()),uri)
    launch.assert_not_called()


def test_failed_refresh_preserves_cache():
    future=Future()
    window=SimpleNamespace(busy=False,refreshing=False,identity=object(),notes=['cached'],controls=Mock(),settings_button=Mock(),editor=Mock(),listbox=Mock(),status=Mock(),pool=SimpleNamespace(submit=lambda _:future))
    with patch('nostr_notes.app.GLib.idle_add',side_effect=lambda f:f()):
        Window.work(window,lambda:None,Mock(),readable=True)
        future.set_exception(ConnectionError('Relais indisponible'))
    assert window.notes==['cached'] and not window.busy
    window.editor.set_sensitive.assert_called_with(True)


def test_stale_draft_cannot_overwrite_remote_update():
    window=SimpleNamespace(current=SimpleNamespace(d='synthetic',event={'id':'old'}),notes=[SimpleNamespace(d='synthetic',event={'id':'new'})],identity=Mock(),status=Mock(),send=Mock())
    Window.publish_synced(window)
    window.identity.save.assert_not_called()
    window.send.assert_not_called()


def test_host_browser_does_not_inherit_bundle_library_paths():
    with patch.dict('os.environ',{'APPDIR':'/synthetic/AppDir','LD_LIBRARY_PATH':'/synthetic/AppDir/lib','XDG_DATA_DIRS':'/synthetic/AppDir/usr/share:/usr/share'}),patch('nostr_notes.editor.Gio.AppInfo.launch_default_for_uri_async') as launch:
        MarkdownEditor._open_link(SimpleNamespace(notice=Mock()),'https://example.org')
        env=launch.call_args.args[1].get_environment()
    assert not any(v.startswith(('APPDIR=','LD_LIBRARY_PATH=')) for v in env)
    assert 'XDG_DATA_DIRS=/usr/share' in env
