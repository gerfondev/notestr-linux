import copy
import re
from unittest.mock import patch
import pytest
from nostr_notes.core import Identity, Note, valid_event, parse_key
from nostr_notes.storage import Storage, relays_from_text


@pytest.fixture
def identity():
    return Identity('0' * 63 + '1')


def test_pages_roundtrip(identity):
    markdown = '# Café ☕\n\n**Texte** en français\n'
    event = identity.save(markdown)
    assert event['kind'] == 33457
    assert re.fullmatch('[a-z0-9]{6}', event['tags'][0][1])
    assert len(event['tags']) == 1
    assert markdown not in event['content']
    assert valid_event(event, identity.pubkey)
    notes, failures = identity.notes([event])
    assert failures == 0
    assert notes[0].markdown == markdown
    assert notes[0].title == 'Café ☕'
    assert parse_key(identity.keys.private_key_bech32()).public_key_hex() == identity.pubkey


def test_edit_and_latest(identity):
    with patch('nostr_notes.core.time.time', return_value=100):
        first = identity.save('old')
    original = Note(first['tags'][0][1], 'old', first)
    with patch('nostr_notes.core.time.time', return_value=101):
        second = identity.save('new', original)
    assert first['tags'] == second['tags']
    notes, _ = identity.notes([second, first, second])
    assert len(notes) == 1 and notes[0].markdown == 'new'
    with patch('nostr_notes.core.time.time', return_value=101), pytest.raises(ValueError):
        identity.save('again', notes[0])


def test_tie_lowest_id(identity):
    a = identity.signed(33457, [['d', 'abcdef']], identity.cipher.encrypt('a', identity.pubkey), 10)
    b = identity.signed(33457, [['d', 'abcdef']], identity.cipher.encrypt('b', identity.pubkey), 10)
    notes, _ = identity.notes([a, b])
    assert notes[0].event['id'] == min(a['id'], b['id'])


def test_deletion_and_future_version(identity):
    with patch('nostr_notes.core.time.time', return_value=100):
        e = identity.save('old')
        note = Note(e['tags'][0][1], 'old', e)
        deletion = identity.delete(note)
    assert ['k', '33457'] in deletion['tags']
    assert ['a', f'33457:{identity.pubkey}:{note.d}'] in deletion['tags']
    assert identity.notes([e, deletion])[0] == []
    with patch('nostr_notes.core.time.time', return_value=101):
        newer = identity.save('recreated', note)
    assert identity.notes([deletion, newer, e])[0][0].markdown == 'recreated'


def test_tamper_foreign_author_and_unreadable(identity):
    e = identity.save('secret')
    altered = copy.deepcopy(e)
    altered['content'] = 'forged'
    assert not valid_event(altered, identity.pubkey)
    other = Identity('0' * 63 + '2')
    forged_delete = other.signed(5, [['e', e['id']]], '')
    bad = identity.signed(33457, [['d', 'broken']], 'invalid nip44')
    notes, failures = identity.notes([e, altered, forged_delete, bad])
    assert len(notes) == 1 and failures == 1


def test_single_event_deletion_does_not_restore_old_revision(identity):
    a = identity.signed(33457, [['d', 'abcdef']], identity.cipher.encrypt('old', identity.pubkey), 10)
    b = identity.signed(33457, [['d', 'abcdef']], identity.cipher.encrypt('new', identity.pubkey), 11)
    d = identity.signed(5, [['e', b['id']]], '', 12)
    assert identity.notes([a, b, d])[0] == []


@pytest.mark.parametrize('value', ['', 'npub1abc', '0'*64, 'not a key'])
def test_bad_keys(value):
    with pytest.raises(ValueError):
        parse_key(value)


@pytest.mark.parametrize('body', ['', 'é'*32768])
def test_payload_limits(identity, body):
    with pytest.raises(ValueError):
        identity.save(body)


def test_storage(tmp_path, identity):
    storage = Storage(tmp_path / 'data')
    e = identity.save('not on disk in clear')
    storage.save_events(identity.pubkey, [e])
    path = storage.root / (identity.pubkey + '.json')
    assert 'not on disk in clear' not in path.read_text()
    assert path.stat().st_mode & 0o777 == 0o600
    assert storage.events(identity.pubkey) == [e]
    assert storage.config()['relays'] == ['wss://relay.decentralia.fr']


def test_relay_validation():
    assert relays_from_text('wss://example.org\nwss://example.org') == ['wss://example.org']
    for value in ['', 'http://example.org', 'wss://user:pass@example.org', 'wss://a:bad']:
        with pytest.raises(ValueError):
            relays_from_text(value)
