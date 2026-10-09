"""Synthetic settings test: no real account, keyring or network."""
import os,tempfile,time
from unittest.mock import patch
from gi.repository import GLib,Gio,Adw,Gtk
from nostr_notes.app import Application,Window
from nostr_notes.storage import Storage
from nostr_notes.i18n import set_language

def wait(fn):
    end=time.monotonic()+25
    while time.monotonic()<end:
        while GLib.MainContext.default().pending():GLib.MainContext.default().iteration(False)
        if fn():return
        time.sleep(.02)
    raise AssertionError('GTK timeout')
def children(w):
    yield w
    c=w.get_first_child()
    while c:
        yield from children(c);c=c.get_next_sibling()
Adw.init()
with tempfile.TemporaryDirectory(prefix='notestr-relays-test-') as data:
    os.environ['XDG_DATA_HOME']=data
    store=Storage();store.write('config.json',{'relays':['wss://old.example.org'],'pubkey':'1'*64,'synthetic':True})
    app=Application();app.set_application_id('fr.decentralia.NostrNotes.RelaysTest');app.set_flags(Gio.ApplicationFlags.NON_UNIQUE);app.register(None)
    with patch.object(Window,'initial_unlock',return_value=False),patch.object(Window,'retry_pending',return_value=False),patch('nostr_notes.app.save_secret',side_effect=AssertionError('Keyring must not be used')) as secret:
        app.activate();w=app.get_active_window();wait(lambda:w.editor.ready)
        for lang,label in [('fr','Enregistrer les relais'),('en','Save relays')]:
            set_language(lang);w.show_settings()
            d=next(x for x in Gtk.Window.get_toplevels() if x is not w and x.get_transient_for() is w)
            widgets=list(children(d));view=next(x for x in widgets if isinstance(x,Gtk.TextView));save=next(x for x in widgets if isinstance(x,Gtk.Button) and x.get_label()==label)
            assert isinstance(save.get_prev_sibling(),Gtk.ScrolledWindow)
            view.get_buffer().set_text('https://invalid.example.org');before=dict(w.config);save.emit('clicked');assert w.config==before and store.config()==before
            urls=['wss://one.example.org','wss://two.example.org']
            view.get_buffer().set_text('\n'.join(urls));save.emit('clicked');assert w.config['relays']==urls and store.config()['relays']==urls
            assert w.config['pubkey']=='1'*64 and w.config['synthetic'] is True and secret.call_count==0
            view.get_buffer().set_text('wss://not-saved.example.org')
            with patch.object(w.store,'write',side_effect=OSError('Synthetic disk failure')):save.emit('clicked')
            assert w.config['relays']==urls and store.config()['relays']==urls
            d.destroy()
        # Regression for exposure assessment: HTML clipboard never reaches ProseMirror.
        result=[]
        w.editor._evaluate("""JSON.stringify((()=>{let data=new DataTransfer();data.setData('text/plain','Synthetic plain paste');data.setData('text/html','<img src=x onerror=alert(1) data-pm-slice=\"0 0 []\">');let e=new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true});document.querySelector('.toastui-editor-ww-container').dispatchEvent(e);return {prevented:e.defaultPrevented,unsafe:!!document.querySelector('img[onerror]')};})())""",result.append)
        wait(lambda:result)
        assert result[0]['prevented'] and not result[0]['unsafe'],result
        print('PASS: French/English save button, persistent relay-only changes, retained account, invalid URL and disk failure keep old config; HTML paste intercepted',flush=True)
        w.close_clean()
