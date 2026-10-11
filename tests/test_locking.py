from dataclasses import replace
from unittest.mock import patch
from types import SimpleNamespace
import pytest
from nostr_notes.core import Identity, BACKUP_KIND, KIND, lock_address, compact_backups

KEY = '0' * 63 + '1'  # Scalar 1 is synthetic; no user key or relay is used.

def test_lock_sync_blocks_edit_trash_and_permanent_delete_until_unlocked():
    identity = Identity(KEY)
    with patch('nostr_notes.core.time.time', return_value=100):
        event = identity.save('# Synthetic shared note', d='lock-test')
    note = identity.notes([event])[0][0]
    address = lock_address(note.d)
    with patch('nostr_notes.core.time.time', return_value=101):
        lock = identity.set_locked(note, True, [event])
    assert lock['kind'] == BACKUP_KIND
    assert lock['tags'] == [['d', address]]
    assert lock['content'] not in ('true', 'false')
    events = compact_backups([event, lock])
    locked = Identity(KEY).notes(events.values())[0][0]
    assert locked.locked and locked.event == event
    with pytest.raises(ValueError): identity.save('# changed', locked)
    with pytest.raises(ValueError): identity.set_trashed(locked, True, events.values())
    with patch('nostr_notes.core.time.time', return_value=102):
        unlock = identity.set_locked(locked, False, events.values())
    events = compact_backups([*events.values(), unlock, lock])
    unlocked = Identity(KEY).notes(events.values())[0][0]
    assert not unlocked.locked
    with patch('nostr_notes.core.time.time', return_value=103):
        trash = identity.set_trashed(unlocked, True, events.values())
    events = compact_backups([*events.values(), trash])
    trashed = Identity(KEY).notes(events.values())[0][0]
    with patch('nostr_notes.core.time.time', return_value=104):
        lock_in_trash = identity.set_locked(trashed, True, events.values())
    events = compact_backups([*events.values(), lock_in_trash])
    protected = Identity(KEY).notes(events.values())[0][0]
    assert protected.trashed and protected.locked
    with pytest.raises(ValueError): identity.delete(protected, events.values())
    with patch('nostr_notes.core.time.time', return_value=105):
        unlock_in_trash = identity.set_locked(protected, False, events.values())
    events = compact_backups([*events.values(), unlock_in_trash])
    restored_lock = Identity(KEY).notes(events.values())[0][0]
    with patch('nostr_notes.core.time.time', return_value=106):
        deletion = identity.delete(restored_lock, events.values())
    assert Identity(KEY).notes([*events.values(), deletion])[0] == []


def test_unreadable_lock_state_fails_closed():
    identity = Identity(KEY)
    with patch('nostr_notes.core.time.time', return_value=100):
        event = identity.save('# Synthetic note', d='bad-lock')
    note = identity.notes([event])[0][0]
    bad = identity.signed(BACKUP_KIND, [['d', lock_address(note.d)]], 'malformed', 101)
    visible = identity.notes([event, bad])[0][0]
    assert visible.locked
    with pytest.raises(ValueError): identity.set_trashed(visible, True, [event, bad])

def test_lock_button_icon_reflects_current_note_state():
    from nostr_notes.app import Window

    class Button:
        def set_icon_name(self, value): self.icon = value
        def set_tooltip_text(self, value): self.tooltip = value
        def update_property(self, *_): pass
        def set_sensitive(self, value): self.sensitive = value

    button = Button()
    window = SimpleNamespace(current=SimpleNamespace(locked=True, pending=False),
                             note_lock_button=button, syncing=False, busy=False)
    Window.update_note_lock_button(window)
    assert button.icon == 'object-locked-symbolic'
    assert button.tooltip == 'Déverrouiller la note'
    window.current.locked = False
    Window.update_note_lock_button(window)
    assert button.icon == 'object-unlocked-symbolic'
    assert button.tooltip == 'Verrouiller la note'

def test_locked_note_disables_previous_version_restore():
    from nostr_notes.app import Window

    class Widget:
        def set_sensitive(self, value): self.sensitive = value
        def set_visible(self, value): pass
        def set_text(self, value): pass
        def set_tooltip_text(self, value): pass
        def update_property(self, *_): pass

    locked = SimpleNamespace(locked=True, trashed=False, pending=False, conflicted=False)
    window = SimpleNamespace(
        current=locked, busy=False, syncing=False, refreshing=False, identity=object(),
        editor=Widget(), pending_label=Widget(), pending_actions=Widget(), copy_button=Widget(),
        publish_button=Widget(), delete_button=Widget(), restore_button=Widget(), pin_button=Widget(),
        update_note_lock_button=lambda: None,
    )
    Window.update_trash_controls(window)
    assert window.restore_button.sensitive is False
    assert window.publish_button.sensitive is False
    assert window.editor.sensitive is True  # Keep pointer/scroll events enabled in the read-only viewer.

    locked.locked = False
    Window.update_trash_controls(window)
    assert window.restore_button.sensitive is True

    locked.trashed = True
    locked.locked = True
    Window.update_trash_controls(window)
    assert window.restore_button.sensitive is True  # Returning a trashed note to the list remains possible.

def test_restore_previous_returns_without_loading_for_locked_note():
    from nostr_notes.app import Window

    class Status:
        message = None
        def set_text(self, value): self.message = value

    window = SimpleNamespace(current=SimpleNamespace(locked=True, trashed=False, pending=False),
                             syncing=False, status=Status())
    Window.restore_previous(window)
    assert window.status.message == 'Déverrouillez la note avant de charger une version précédente.'

def test_lock_toggle_reloads_editor_in_unlocked_mode():
    from nostr_notes.app import Window
    from unittest.mock import AsyncMock

    identity = Identity(KEY)
    with patch('nostr_notes.core.time.time', return_value=200):
        event = identity.save('# Synthetic note', d='toggle-lock-test')
    note = identity.notes([event])[0][0]
    displays = []
    class Status:
        def set_text(self, value): pass
    window = SimpleNamespace(
        current=note, events={event['id']: event}, notes=[note], identity=identity,
        config={'relays': []}, outbox=SimpleNamespace(overlay=lambda events: identity.notes(list(events))[0]),
        store=SimpleNamespace(save_events=lambda *_: None), status=Status(), busy=False, syncing=False,
        display=lambda shown: displays.append(shown), render_list=lambda: None,
        guard=lambda action: action(), work=lambda operation, success: success(operation()),
    )
    with patch('nostr_notes.app.across', AsyncMock(return_value=({'synthetic': True}, []))), \
         patch('nostr_notes.core.time.time', side_effect=[201, 202]):
        Window.toggle_note_lock(window)
        assert displays[-1].locked
        Window.toggle_note_lock(window)
        assert not displays[-1].locked
