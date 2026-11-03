"""Folder metadata uses synthetic keys and contains only encrypted folder names."""
from unittest.mock import patch
import pytest
from nostr_notes.core import Identity, BACKUP_KIND, FOLDER_ADDRESS, compact_backups

KEY = "0" * 63 + "1"
FOLDER_ID = "0123456789abcdef0123456789abcdef"

def test_folder_state_roundtrip_is_encrypted_and_applies_to_notes():
    identity = Identity(KEY)
    with patch("nostr_notes.core.time.time", return_value=100):
        note = identity.save("# Private note", d="note-a")
    with patch("nostr_notes.core.time.time", return_value=101):
        folders_event = identity.set_folder_state(
            [{"id": FOLDER_ID, "name": "Voyages"}], {"note-a": FOLDER_ID}, [note]
        )
    assert folders_event["kind"] == BACKUP_KIND
    assert folders_event["tags"] == [["d", FOLDER_ADDRESS]]
    assert "Voyages" not in folders_event["content"]
    events = compact_backups([note, folders_event])
    restored = Identity(KEY)
    notes, unreadable = restored.notes(events.values())
    assert unreadable == 0
    assert notes[0].folder_id == FOLDER_ID
    assert restored.folder_state(events.values()) == {
        "version": 1, "folders": [{"id": FOLDER_ID, "name": "Voyages"}],
        "assignments": {"note-a": FOLDER_ID},
    }

def test_delete_folder_keeps_notes_and_unassigns_them():
    identity = Identity(KEY)
    with patch("nostr_notes.core.time.time", return_value=100):
        note = identity.save("# Still here", d="note-b")
    with patch("nostr_notes.core.time.time", return_value=101):
        created = identity.set_folder_state([{"id": FOLDER_ID, "name": "Archive"}], {"note-b": FOLDER_ID}, [note])
    current = [note, created]
    with patch("nostr_notes.core.time.time", return_value=102):
        deleted_folder = identity.set_folder_state([], {}, current)
    events = compact_backups([*current, deleted_folder])
    notes, _ = Identity(KEY).notes(events.values())
    assert len(notes) == 1 and notes[0].markdown == "# Still here" and notes[0].folder_id is None
    assert Identity(KEY).folder_state(events.values())["folders"] == []

def test_folder_validation_rejects_duplicate_names_and_unknown_assignment():
    with pytest.raises(ValueError):
        Identity.validate_folder_state(
            [{"id": FOLDER_ID, "name": "Travel"}, {"id": "abcdef0123456789abcdef0123456789", "name": "Travel"}], {}
        )
    with pytest.raises(ValueError):
        Identity.validate_folder_state(
            [{"id": FOLDER_ID, "name": "Travel"}, {"id": "abcdef0123456789abcdef0123456789", "name": " travel "}], {}
        )
    with pytest.raises(ValueError):
        Identity.validate_folder_state([{"id": FOLDER_ID, "name": "Travel"}], {"note-a": "f" * 32})
