"""Synthetic key scalar 1, public test-only events. No personal account or relay."""
from dataclasses import replace
import pytest
from nostr_notes.core import Identity, Note, KIND, BACKUP_KIND, trash_address, compact_backups

KEY = "0" * 63 + "1"

def initial():
    i = Identity(KEY)
    e = i.signed(KIND, [["d", "trash-été"]], i.cipher.encrypt("# Note fictive\n\nTexte", i.pubkey), 100)
    return i, e, i.notes([e])[0][0]

def test_trash_restore_preserves_content_pin_and_backup(monkeypatch):
    i, e, n = initial()
    monkeypatch.setattr("nostr_notes.core.time.time", lambda: 101)
    pin = i.set_pinned(n, True, [e])
    monkeypatch.setattr("nostr_notes.core.time.time", lambda: 102)
    trash = i.set_trashed(n, True, [e, pin])
    notes, failed = i.notes([e, pin, trash])
    assert failed == 0 and notes[0].trashed and notes[0].pinned
    assert notes[0].markdown == n.markdown and notes[0].event == e
    assert trash["content"] not in ("true", "false")
    monkeypatch.setattr("nostr_notes.core.time.time", lambda: 103)
    restore = i.set_trashed(notes[0], False, [e, pin, trash])
    notes, _ = i.notes([restore, trash, pin, e])
    assert not notes[0].trashed and notes[0].pinned
    assert notes[0].markdown == n.markdown
    assert sum(x["kind"] == BACKUP_KIND for x in compact_backups([e,pin,trash,restore]).values()) == 2

def test_permanent_delete_is_manual_and_terminal(monkeypatch):
    i, e, n = initial()
    with pytest.raises(ValueError): i.delete(n)
    monkeypatch.setattr("nostr_notes.core.time.time", lambda: 102)
    t = i.set_trashed(n, True, [e])
    n = i.notes([e,t])[0][0]
    d = i.delete(n)
    assert i.notes([e,t,d])[0] == []
    # Late stale-client content must not resurrect a permanently deleted address.
    later = i.signed(KIND, [["d", n.d]], e["content"], 200)
    assert i.notes([later,t,d])[0] == []
    with pytest.raises(ValueError): i.set_trashed(n, False, [e,t,d])

def test_stale_trash_action_rejected_and_bad_state_not_shown(monkeypatch):
    i,e,n=initial()
    monkeypatch.setattr("nostr_notes.core.time.time", lambda: 102)
    t=i.set_trashed(n, True, [e])
    with pytest.raises(ValueError):i.set_trashed(n,False,[e,t])
    bad=i.signed(BACKUP_KIND,[["d",trash_address(n.d)]],i.cipher.encrypt("invalid",i.pubkey),103)
    assert i.notes([e,t,bad])[0] == []

def test_same_second_tie_and_signature(monkeypatch):
    i,e,n=initial()
    a=i.signed(BACKUP_KIND,[["d",trash_address(n.d)]],i.cipher.encrypt("true",i.pubkey),102)
    b=i.signed(BACKUP_KIND,[["d",trash_address(n.d)]],i.cipher.encrypt("false",i.pubkey),102)
    expected=min([a,b],key=lambda x:x["id"])
    assert i.notes([e,a,b])[0][0].trashed == (i.cipher.decrypt(expected["content"],i.pubkey)=="true")
    assert i.notes([e,a,b]) == i.notes([b,a,e])
    forged=dict(a,content="bad")
    assert not i.notes([e,forged])[0][0].trashed
