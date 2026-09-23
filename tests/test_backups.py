import asyncio
from unittest.mock import AsyncMock, patch
import pytest
from nostr_notes.core import Identity, BACKUP_KIND, compact_backups, valid_event
from nostr_notes.relay import across, publish_update


def test_rotation_restore_delete():
    identity = Identity('0' * 63 + '1')
    with patch('nostr_notes.core.time.time', return_value=100):
        first = identity.save('version one')
    original = identity.notes([first])[0][0]
    assert identity.previous(original, [first]) is None
    with patch('nostr_notes.core.time.time', return_value=101):
        second = identity.save('version two', original)
    backup1 = identity.backup(original, second)
    current = identity.notes([second, backup1])[0][0]
    assert current.markdown == 'version two'
    assert valid_event(backup1, identity.pubkey)
    assert 'version one' not in str(backup1)
    assert identity.previous(current, [backup1]).markdown == 'version one'
    with patch('nostr_notes.core.time.time', return_value=102):
        third = identity.save('version three', current)
    backup2 = identity.backup(current, third)
    events = compact_backups([first, second, third, backup1, backup2])
    assert len([e for e in events.values() if e['kind'] == BACKUP_KIND]) == 1
    current = identity.notes(events.values())[0][0]
    assert identity.previous(current, events.values()).markdown == 'version two'
    with patch('nostr_notes.core.time.time', return_value=103):
        restored = identity.save(identity.previous(current, events.values()).markdown, current)
    backup3 = identity.backup(current, restored)
    current = identity.notes([restored])[0][0]
    assert current.markdown == 'version two'
    assert identity.previous(current, [backup3]).markdown == 'version three'
    deletion = identity.delete(current)
    assert identity.notes([restored, deletion])[0] == []
    assert identity.previous(current, [backup3, deletion]) is None


def test_scoped_to_note_and_owner():
    identity = Identity('0' * 63 + '1')
    first = identity.notes([identity.save('first', d='first')])[0][0]
    other = identity.notes([identity.save('other', d='other')])[0][0]
    backup = identity.backup(first, first.event)
    assert identity.previous(other, [backup]) is None
    assert Identity('0' * 63 + '2').previous(first, [backup]) is None


def test_backup_ack_required():
    backup, update = {'id': 'backup'}, {'id': 'update'}
    sender = AsyncMock(return_value=True)
    with patch('nostr_notes.relay.publish_one', sender):
        asyncio.run(publish_update('relay', update, backup))
    assert [call.args for call in sender.call_args_list] == [('relay', backup), ('relay', update)]
    sender = AsyncMock(side_effect=ValueError('backup rejected'))
    with patch('nostr_notes.relay.publish_one', sender), pytest.raises(ValueError):
        asyncio.run(publish_update('relay', update, backup))
    assert sender.call_count == 1


def test_partial_failure_and_new_note():
    calls = []
    async def sender(url, event):
        calls.append((url, event))
        if url == 'bad':
            raise ValueError('rejected')
        return True
    with patch('nostr_notes.relay.publish_one', sender):
        good, errors = asyncio.run(across(['good', 'bad'], publish_update, 'update', 'backup'))
        assert list(good) == ['good'] and len(errors) == 1
        assert ('bad', 'update') not in calls
        calls.clear()
        asyncio.run(publish_update('good', 'new'))
        assert calls == [('good', 'new')]
