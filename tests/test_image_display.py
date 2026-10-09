import pytest


def test_image_display_tries_reference_origin_before_querying_profile(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module

    monkeypatch.setattr(module, "cached_image_available", lambda *_args: False)
    requests = []
    def load(reference, cache_dir, allowed_servers=None):
        requests.append(allowed_servers)
        return b"decrypted image"
    monkeypatch.setattr(module, "load_image_reference", load)

    async def profile(*_args):
        pytest.fail("Profile lookup should not delay a reachable reference origin")

    result = module.load_image_for_display("synthetic-reference", tmp_path,
                                           ["wss://relay.example"], "pubkey", profile)
    assert result == b"decrypted image"
    assert requests == [None]


def test_image_display_queries_profile_if_reference_origin_fails(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module

    monkeypatch.setattr(module, "cached_image_available", lambda *_args: False)
    requests = []
    def load(reference, cache_dir, allowed_servers=None):
        requests.append(allowed_servers)
        if allowed_servers is None:
            raise OSError("reference server unavailable")
        return b"mirrored image"
    monkeypatch.setattr(module, "load_image_reference", load)

    async def servers(relays, pubkey, query_profile):
        assert relays == ["wss://relay.example"]
        assert pubkey == "synthetic-pubkey"
        return ["https://mirror.example"]
    monkeypatch.setattr(module, "discover_servers", servers)

    result = module.load_image_for_display("synthetic-reference", tmp_path,
                                           ["wss://relay.example"], "synthetic-pubkey", lambda *_: [])
    assert result == b"mirrored image"
    assert requests == [None, ["https://mirror.example"]]
