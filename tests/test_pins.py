"""Only synthetic public scalars 1/2; no user account or public relay."""
from unittest.mock import patch, Mock
from types import SimpleNamespace
import pytest
from nostr_notes.core import Identity, BACKUP_KIND, pin_address, compact_backups

KEY = '0' * 63 + '1'

def make():
    i = Identity(KEY)
    with patch('nostr_notes.core.time.time', return_value=100):
        a = i.save('Ancienne été 漢字', d='legacy-été')
    with patch('nostr_notes.core.time.time', return_value=101):
        b = i.save('Récente', d='recent')
    return i, a, b

def test_pin_unpin_edit_restart_and_backup_isolation():
    i, a, b = make()
    note = i.notes([a])[0][0]
    with patch('nostr_notes.core.time.time', return_value=102):
        pin = i.set_pinned(note, True, [a, b])
    assert pin['kind'] == BACKUP_KIND
    assert pin['tags'] == [['d', pin_address(note.d)]]
    assert pin['content'] not in ('true', 'false')
    events = compact_backups([a, b, pin])
    notes, unreadable = Identity(KEY).notes(events.values())
    assert unreadable == 0
    assert [n.d for n in notes] == [note.d, 'recent']
    assert notes[0].pinned and notes[0].event == a
    assert i.previous(notes[0], events.values()) is None
    with patch('nostr_notes.core.time.time', return_value=103):
        update = i.save('Modifiée', notes[0])
    backup = i.backup(notes[0], update)
    events = compact_backups([*events.values(), update, backup])
    current = i.notes(events.values())[0][0]
    assert current.pinned
    assert i.previous(current, events.values()).markdown == note.markdown
    with patch('nostr_notes.core.time.time', return_value=104):
        unpin = i.set_pinned(current, False, events.values())
    events = compact_backups([*events.values(), unpin, pin])
    assert not i.notes(events.values())[0][0].pinned
    assert len([e for e in events.values() if e['kind'] == BACKUP_KIND]) == 2
    assert i.notes([*events.values(), i.delete(current)])[0][0].d == 'recent'

def test_same_second_conflicts_author_signature_and_malformed():
    i, a, b = make()
    n = i.notes([a])[0][0]
    with patch('nostr_notes.core.time.time', return_value=102):
        pin = i.set_pinned(n, True, [a])
        unpin = i.set_pinned(n, False, [a])
        with pytest.raises(ValueError): i.set_pinned(n, False, [a, pin])
    winner = min([pin, unpin], key=lambda e:e['id'])
    for ordering in ([pin, unpin], [unpin, pin]):
        assert i.notes([a, *ordering])[0][0].pinned == (winner == pin)
    other = Identity('0' * 63 + '2').set_pinned(n, True, [])
    assert not i.notes([a, other])[0][0].pinned
    assert not i.notes([a, dict(pin, content='forged')])[0][0].pinned
    bad = i.signed(BACKUP_KIND, pin['tags'], 'not ciphertext', 103)
    notes, failures = i.notes([a, bad])
    assert len(notes) == 1 and failures == 1

def test_pin_failure_preserves_editor_and_state():
    pytest.importorskip('gi')
    from nostr_notes.app import Window
    i, a, b = make()
    n = i.notes([a])[0][0]
    w = SimpleNamespace(current=n, busy=False, identity=i, events={a['id']:a}, config={'relays':['ws://synthetic']},
        store=Mock(), editor=Mock(), dirty=True, render_list=Mock(), update_pin_button=Mock(), status=Mock())
    def work(operation, success):
        with pytest.raises(ConnectionError): operation()
    w.work = work
    with patch('nostr_notes.app.across', side_effect=ConnectionError('refused')):
        Window.toggle_pin(w)
    assert w.current == n and w.dirty
    w.editor.set_text.assert_not_called()
    w.store.save_events.assert_not_called()
