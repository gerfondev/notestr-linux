import asyncio
import json
from dataclasses import replace
from unittest.mock import patch
import pytest
from nostr_notes.core import Identity, Note, KIND, compact_backups
from nostr_notes.offline import Outbox
from nostr_notes.storage import Storage

@pytest.fixture
def data(tmp_path):
    identity = Identity('0' * 63 + '1')  # Public synthetic scalar.
    store = Storage(tmp_path)
    event = identity.signed(KIND, [['d', 'offline-fixture']], identity.cipher.encrypt('# Original', identity.pubkey), 100)
    note = Note('offline-fixture', '# Original', event)
    events = {event['id']: event}
    store.save_events(identity.pubkey, list(events.values()))
    return identity, store, note, events, Outbox(identity, store)


def test_save_restart_and_latest_edit_encrypted(data):
    identity, store, note, events, box = data
    first = box.save('# Private offline text', note)
    second = box.save('# Changed twice', first)
    text = (store.root / box.name).read_text()
    assert 'Private offline text' not in text and 'Changed twice' not in text
    reopened = Outbox(identity, store)
    notes = reopened.overlay(events.values())
    assert len(notes) == 1 and notes[0].markdown == '# Changed twice' and notes[0].pending
    assert reopened.snapshot()[0]['base']['id'] == note.event['id']
    assert reopened.snapshot()[0]['update']['id'] == second.event['id']


def test_sync_ack_and_backup(data):
    identity, store, note, events, box = data
    pending = box.save('# Offline', note)
    sent = []
    async def query(url, pubkey): return list(events.values())
    async def publish(url, update, backup):
        assert backup['content'] == note.event['content']
        sent.append(update)
    merged, errors = asyncio.run(box.synchronize(events, ['local'], query, publish))
    assert len(sent) == 1 and not errors and not box.snapshot()
    assert box.overlay(merged.values())[0].markdown == '# Offline'
    assert not box.overlay(merged.values())[0].pending


def test_offline_or_incomplete_reads_never_publish(data):
    identity, store, note, events, box = data
    box.save('# Offline', note)
    async def query(url, pubkey):
        if url == 'down': raise ConnectionError('synthetic offline')
        return list(events.values())
    async def publish(*args): pytest.fail('Must not publish incomplete snapshot')
    with pytest.raises(ConnectionError): asyncio.run(box.synchronize(events, ['down'], query, publish))
    merged, errors = asyncio.run(box.synchronize(events, ['up', 'down'], query, publish))
    assert errors and box.snapshot()


@pytest.mark.parametrize('remote_action', ['edit', 'trash', 'delete'])
def test_conflict_keeps_local_and_does_not_publish(data, remote_action):
    identity, store, note, events, box = data
    box.save('# Offline', note)
    if remote_action == 'edit':
        remote = identity.signed(KIND, [['d', note.d]], identity.cipher.encrypt('# Other device', identity.pubkey), 200)
    elif remote_action == 'trash':
        remote = identity.set_trashed(note, True, events.values())
    else:
        remote = identity.delete(replace(note, trashed=True))
    async def query(url, pubkey): return [*events.values(), remote]
    async def publish(*args): pytest.fail('Conflict must never auto-publish')
    merged, errors = asyncio.run(box.synchronize(events, ['local'], query, publish))
    local = next(n for n in box.overlay(merged.values()) if n.pending)
    assert local.conflicted and local.markdown == '# Offline'
    assert box.snapshot()
    copy = box.save(local.markdown, local, as_copy=True)
    assert copy.d != note.d and box.snapshot()[0]['base'] is None


def test_ack_lost_then_restart_is_idempotent(data):
    identity, store, note, events, box = data
    saved = box.save('# Offline', note)
    async def query(url, pubkey): return [*events.values(), saved.event]
    async def publish(*args): pytest.fail('Already accepted event must not be duplicated')
    merged, _ = asyncio.run(box.synchronize(events, ['local'], query, publish))
    assert not box.snapshot() and saved.event['id'] in merged


def test_newer_local_edit_during_send_survives(data):
    identity, store, note, events, box = data
    saved = box.save('# First pending', note)
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): box.save('# Latest pending', saved)
    merged, _ = asyncio.run(box.synchronize(events, ['local'], query, publish))
    assert len(box.snapshot()) == 1
    assert next(n for n in box.overlay(merged.values()) if n.pending).markdown == '# Latest pending'


def test_rejection_and_corrupt_file_keep_drafts(data):
    identity, store, note, events, box = data
    box.save('# Offline', note)
    before = (store.root / box.name).read_bytes()
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): raise ConnectionError('synthetic rejection')
    with pytest.raises(ConnectionError): asyncio.run(box.synchronize(events, ['local'], query, publish))
    assert (store.root / box.name).read_bytes() == before
    (store.root / box.name).write_text('broken')
    with pytest.raises(ValueError): box.save('# Never overwrite broken queue', note)
    assert (store.root / box.name).read_text() == 'broken'


def test_forged_base_and_account_isolation(data):
    identity, store, note, events, box = data
    box.save('# Offline', note)
    other = Outbox(Identity('0' * 63 + '2'), store)
    assert not other.snapshot()
    rows = box.snapshot(); rows[0]['base']['id'] = '0' * 64
    store.write(box.name, rows)
    with pytest.raises(ValueError): box.snapshot()


def test_simultaneous_device_edit_recovers_last_acknowledged_copy(data):
    identity, store, note, events, box = data
    local = box.save('# Device A', note)
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): return True
    merged, _ = asyncio.run(box.synchronize(events, ['local'], query, publish))
    # Device B read the same base before A was acknowledged; its later update wins on relays.
    remote = identity.signed(KIND, [['d', note.d], ['notestr-base', note.event['id']]],
        identity.cipher.encrypt('# Device B', identity.pubkey), local.event['created_at']+1)
    merged[remote['id']] = remote
    displayed = Outbox(identity, store).overlay(merged.values())
    assert len(displayed) == 2
    assert next(n for n in displayed if n.pending).markdown == '# Device A'
    assert next(n for n in displayed if n.pending).conflicted
    box.remove(local.d, local.event['id'])
    assert len(box.overlay(merged.values())) == 1


def test_locking_acknowledged_note_does_not_create_duplicate_conflict(data):
    identity, store, note, events, box = data
    accepted = box.save('# Accepted edit', note)
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): return True
    merged, errors = asyncio.run(box.synchronize(events, ['local'], query, publish))
    assert not errors and accepted.event['id'] in merged

    current = identity.notes(merged.values())[0][0]
    with patch('nostr_notes.core.time.time', return_value=accepted.event['created_at'] + 1):
        lock = identity.set_locked(current, True, merged.values())
    merged = compact_backups([*merged.values(), lock])

    displayed = Outbox(identity, store).overlay(merged.values())
    assert len(displayed) == 1
    assert displayed[0].locked
    assert not displayed[0].pending
    assert displayed[0].markdown == '# Accepted edit'


def test_normal_remote_child_is_not_a_conflict(data):
    identity, store, note, events, box = data
    local = box.save('# First', note)
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): return True
    merged, _ = asyncio.run(box.synchronize(events, ['local'], query, publish))
    remote = identity.signed(KIND, [['d', note.d], ['notestr-base', local.event['id']]],
        identity.cipher.encrypt('# Intentional later edit', identity.pubkey), local.event['created_at']+1)
    merged[remote['id']] = remote
    assert all(not n.pending for n in box.overlay(merged.values()))


def test_manual_permanent_deletion_purges_acknowledged_copy(data):
    identity, store, note, events, box = data
    local = box.save('# Accepted then deleted', note)
    async def query(url, pubkey): return list(events.values())
    async def publish(*args): return True
    merged, _ = asyncio.run(box.synchronize(events, ['local'], query, publish))
    deletion = identity.delete(replace(local, pending=False, trashed=True))
    merged[deletion['id']] = deletion
    assert not box.overlay(merged.values())
    assert not box.snapshot(include_sent=True)
