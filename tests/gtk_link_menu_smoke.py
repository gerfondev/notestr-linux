"""Interactive synthetic test: right-click the link then choose the browser action."""
import json,os,time
from pathlib import Path
from unittest.mock import patch
from nostr_notes.editor import MarkdownEditor
import gi
gi.require_version('Adw','1')
from gi.repository import Adw,Gio,GLib
Adw.init()
def wait(condition,seconds=1800):
    stop=time.monotonic()+seconds;ctx=GLib.MainContext.default()
    while time.monotonic()<stop:
        while ctx.pending():ctx.iteration(False)
        if condition():return
        time.sleep(.01)
    raise AssertionError('Interactive test timeout')
app=Adw.Application(application_id='fr.decentralia.NostrNotes.LinkMenuTest',flags=Gio.ApplicationFlags.NON_UNIQUE)
app.register(None)
win=Adw.ApplicationWindow(application=app,title='Test local du menu de lien',default_width=500,default_height=420)
editor=MarkdownEditor(lambda _:None);win.set_content(editor)
source='[**Ouvrir lien test**](https://example.org/menu)\n\nTexte de test conservé.'
editor.set_text(source);win.present()
wait(lambda:editor.ready and not editor.pending_document)
result=[]
editor._evaluate("JSON.stringify(Array.from(document.querySelectorAll('.toastui-editor-ww-container a, .toastui-editor-ww-container a *')).map(e=>getComputedStyle(e).cursor))",result.append)
wait(lambda:result);assert result[0] and all(v=='pointer' for v in result[0]),result
launched=[]
with patch('nostr_notes.editor.Gio.AppInfo.launch_default_for_uri_async',side_effect=lambda *args:launched.append(args[0])):
    print('READY: right-click the link and choose Ouvrir le lien dans le navigateur',flush=True)
    wait(lambda:launched)
    assert launched==['https://example.org/menu'],launched
    assert editor.get_text()==source
    assert editor.web.get_uri()=='notes-editor://app/index.html'
    print('PASS: real context-menu action, external browser dispatch, pointer cursor, unchanged note',flush=True)
    win.close()
