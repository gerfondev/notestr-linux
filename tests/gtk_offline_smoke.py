"""Real GTK editor, isolated storage, synthetic identity and relay stub only."""
import asyncio, os, tempfile, time
from unittest.mock import patch
from nostr_notes.app import Application, Window
from nostr_notes.core import Identity, KIND
from nostr_notes.storage import Storage
from gi.repository import GLib, Gio, Adw, Gtk

def wait(fn):
    end = time.monotonic() + 25
    context = GLib.MainContext.default()
    while time.monotonic() < end:
        while context.pending(): context.iteration(False)
        if fn(): return
        time.sleep(.02)
    raise AssertionError('Offline GTK timeout')

Adw.init()
with tempfile.TemporaryDirectory(prefix='notestr-offline-test-') as data:
    os.environ['XDG_DATA_HOME'] = data
    identity = Identity('0'*63+'1')  # Public synthetic scalar.
    base = identity.signed(KIND, [['d','offline-gui']], identity.cipher.encrypt('# Original', identity.pubkey), 100)
    Storage().save_events(identity.pubkey, [base])
    remote = [base]; online = [False]; sends = []
    async def query(url, pubkey):
        if not online[0]: raise ConnectionError('synthetic offline')
        return list(remote)
    async def publish(url, update, backup=None):
        assert online[0]
        sends.append(update)
        remote.extend([backup, update] if backup else [update])
        return True
    app = Application(); app.set_application_id('fr.decentralia.NostrNotes.OfflineTest')
    app.set_flags(Gio.ApplicationFlags.NON_UNIQUE); app.register(None)
    with patch.object(Window,'initial_unlock',return_value=False), patch.object(Window,'do_refresh'), patch('nostr_notes.app.query_one',query), patch('nostr_notes.app.publish_update',publish):
        app.activate(); w = app.get_active_window(); w.login(identity)
        w.config['relays'] = ['ws://synthetic.invalid']
        wait(lambda:w.editor.ready and not w.editor.pending_document)
        w.display(w.notes[0]); wait(lambda:not w.editor.pending_document)
        w.editor.set_text('# Offline edit'); wait(lambda:not w.editor.pending_document)
        w.changed(None); w.publish_synced()
        wait(lambda:not w.syncing)
        assert w.notes[0].pending and w.pending_label.get_visible()
        assert 'Offline edit' not in (w.store.root / w.outbox.name).read_text()
        assert not sends and not w.dirty
        online[0] = True
        w.retry_pending(); wait(lambda:not w.syncing)
        assert not w.notes[0].pending and len(sends) == 1
        assert w.current.markdown == '# Offline edit'
        online[0] = False
        w.editor.set_text('# Local concurrent edit'); wait(lambda:not w.editor.pending_document)
        w.changed(None); w.publish_synced(); wait(lambda:not w.syncing)
        other = identity.signed(KIND,[['d','offline-gui']],identity.cipher.encrypt('# Other device',identity.pubkey),int(time.time())+2)
        remote.append(other); online[0] = True
        w.retry_pending(); wait(lambda:not w.syncing)
        assert len(w.notes) == 2 and sum(n.conflicted for n in w.notes) == 1
        local = next(n for n in w.notes if n.pending)
        w.display(local); wait(lambda:not w.editor.pending_document)
        assert w.copy_button.get_visible()
        w.publish_synced(as_copy=True); wait(lambda:not w.syncing)
        assert not w.outbox.snapshot() and len(w.notes) == 2
        assert {n.markdown for n in w.notes} == {'# Other device','# Local concurrent edit'}
        print('PASS: encrypted local save, background recovery, conflict keeps both versions, publish copy',flush=True)
        w.close_clean()
