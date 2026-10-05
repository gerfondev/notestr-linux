"""Isolated GTK trash workflow with synthetic identity and in-process relay stub."""
import os,tempfile,time
from unittest.mock import patch
from nostr_notes.app import Application,Window
from nostr_notes.core import Identity,KIND
from nostr_notes.storage import Storage
from gi.repository import GLib,Gio,Adw,Gtk

def wait(fn):
    end=time.monotonic()+20;c=GLib.MainContext.default()
    while time.monotonic()<end:
        while c.pending():c.iteration(False)
        if fn():return
        time.sleep(.02)
    raise AssertionError('Trash GTK timeout')

def dialog(answer):
    d=next(w for w in Gtk.Window.get_toplevels() if isinstance(w,Gtk.MessageDialog))
    d.response(answer)

async def accepted(*args):return {'wss://relay.invalid':True},[]
async def rejected(*args):raise ConnectionError('Synthetic offline relay')

Adw.init()
with tempfile.TemporaryDirectory(prefix='notestr-trash-test-') as data:
    os.environ['XDG_DATA_HOME']=data
    i=Identity('0'*63+'1') # Public synthetic scalar, never use as an account.
    e=i.signed(KIND,[['d','trash-demo']],i.cipher.encrypt('# Note fictive\n\nTexte',i.pubkey),100)
    Storage().save_events(i.pubkey,[e])
    app=Application();app.set_application_id('fr.decentralia.NostrNotes.TrashTest');app.set_flags(Gio.ApplicationFlags.NON_UNIQUE);app.register(None)
    with patch.object(Window,'initial_unlock',return_value=False),patch.object(Window,'do_refresh'),patch('nostr_notes.app.across',accepted):
        app.activate();w=app.get_active_window();w.login(i)
        wait(lambda:w.editor.ready and not w.editor.pending_document)
        w.display(w.notes[0]);wait(lambda:not w.editor.pending_document)
        w.delete();dialog(Gtk.ResponseType.CANCEL)
        assert not w.notes[0].trashed
        with patch('nostr_notes.core.time.time',return_value=1000):
            w.delete();dialog(Gtk.ResponseType.ACCEPT);wait(lambda:not w.busy and not w.editor.pending_document)
        assert w.notes[0].trashed and w.listbox.get_first_child() is None
        assert not any(x['kind']==5 for x in w.events.values())
        w.toggle_trash_view();wait(lambda:w.showing_trash)
        w.display(w.notes[0]);wait(lambda:not w.editor.pending_document)
        assert not w.editor.get_sensitive() and not w.publish_button.get_sensitive()
        assert w.restore_button.get_tooltip_text()=='Restaurer la note'
        with patch('nostr_notes.core.time.time',return_value=1001):
            w.restore_previous();wait(lambda:not w.busy and not w.editor.pending_document)
        assert not w.notes[0].trashed and w.listbox.get_first_child() is None
        with patch('nostr_notes.app.across',rejected),patch('nostr_notes.core.time.time',return_value=1002):
            w.set_trashed(w.notes[0],True);wait(lambda:not w.busy and not w.editor.pending_document)
        assert not w.notes[0].trashed
        with patch('nostr_notes.core.time.time',return_value=1003):
            w.set_trashed(w.notes[0],True);wait(lambda:not w.busy and not w.editor.pending_document)
        w.display(w.notes[0]);wait(lambda:not w.editor.pending_document)
        w.delete();dialog(Gtk.ResponseType.CANCEL);assert len(w.notes)==1
        with patch('nostr_notes.core.time.time',return_value=1004):
            w.delete();dialog(Gtk.ResponseType.ACCEPT);wait(lambda:not w.busy and not w.editor.pending_document)
        assert not w.notes and all(x['kind']==5 for x in w.events.values())
        assert all(x['kind']==5 for x in w.store.events(i.pubkey))
        print('PASS: manual move, cancel, restore, offline rejection, permanent delete, read-only trash and encrypted cache cleanup',flush=True)
        w.close_clean()
