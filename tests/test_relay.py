import asyncio
import json
from unittest.mock import patch
import pytest
from nostr_notes.core import Identity
from nostr_notes.relay import across, publish_one, query_one


class FakeSocket:
    def __init__(self, reject=False):
        self.queue = []
        self.sent = []
        self.reject = reject
        self.event = Identity('0'*63+'1').save('hello')

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def send(self, text):
        msg = json.loads(text)
        self.sent.append(msg)
        if msg[0] == 'EVENT':
            self.queue.extend([['OK', 'unrelated-id', True, ''],
                               ['OK', msg[1]['id'], not self.reject, 'blocked' if self.reject else 'saved']])
        elif msg[0] == 'REQ':
            f = msg[2]
            if f['kinds'] == [33457] and f.get('until', 2**60) >= self.event['created_at']:
                self.queue.append(['EVENT', msg[1], self.event])
            self.queue.append(['EOSE', msg[1]])

    async def recv(self):
        return json.dumps(self.queue.pop(0))


def test_ack_and_rejection():
    ws = FakeSocket()
    with patch('nostr_notes.relay.connect', return_value=ws):
        assert asyncio.run(publish_one('wss://example.org', ws.event))
    ws.reject = True
    with patch('nostr_notes.relay.connect', return_value=ws), pytest.raises(ValueError):
        asyncio.run(publish_one('wss://example.org', ws.event))


def test_query_pagination_and_close():
    ws = FakeSocket()
    with patch('nostr_notes.relay.connect', return_value=ws):
        events = asyncio.run(query_one('wss://example.org', ws.event['pubkey']))
    assert events == [ws.event]
    requests = [m for m in ws.sent if m[0] == 'REQ']
    assert any(m[2]['kinds'] == [5] for m in requests)
    assert len([m for m in ws.sent if m[0] == 'CLOSE']) == len(requests)


def test_partial_and_total_failure():
    async def operation(url):
        if url == 'bad':
            raise ValueError('refused')
        return True
    good, errors = asyncio.run(across(['good', 'bad'], operation))
    assert good == {'good': True} and len(errors) == 1
    with pytest.raises(ConnectionError):
        asyncio.run(across(['bad'], operation))
