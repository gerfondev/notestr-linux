import asyncio
import io

from PIL import Image
import pytest

from nostr_notes.image_attachments import (
    DEFAULT_BLOSSOM_SERVER,
    cached_image_available,
    decrypt_image,
    discover_servers,
    encrypt_image,
    image_markdown_reference,
    normalize_server,
    prepare_image,
    load_image_reference,
    servers_from_profile,
    upload_blob,
    upload_encrypted_image,
)


def test_server_list_uses_ordered_valid_https_servers_and_rejects_unsafe_urls():
    event = {"kind": 10063, "tags": [
        ["server", "https://images.example"], ["server", "http://bad.example"],
        ["server", "https://user:pass@bad.example"], ["server", "https://second.example/"],
        ["server", "https://images.example"],
    ]}
    assert servers_from_profile(event) == ["https://images.example", "https://second.example"]
    assert normalize_server("https://bad.example/path") is None
    assert servers_from_profile({"kind": 10063, "tags": []}) == []


def test_encrypt_decrypt_and_markdown_reference_are_cross_platform_wire_format():
    attachment = encrypt_image(b"synthetic image bytes")
    assert decrypt_image(attachment["ciphertext"], attachment["key"], attachment["nonce"], attachment["hash"]) == b"synthetic image bytes"
    reference = image_markdown_reference(attachment, "https://images.example")
    assert reference.startswith(f"![Image](notestr-image://{attachment['hash']}?server=https%3A%2F%2Fimages.example&key=")
    assert "&nonce=" in reference and "&mime=image%2Fjpeg)" in reference
    with pytest.raises(Exception):
        decrypt_image(attachment["ciphertext"] + b"x", attachment["key"], attachment["nonce"], attachment["hash"])


def test_prepare_image_reencodes_and_strips_metadata():
    image = Image.new("RGB", (8, 4), "red")
    source = io.BytesIO()
    image.save(source, format="JPEG", exif=b"Exif\0\0synthetic-private-metadata")
    clean, mime = prepare_image(source.getvalue())
    assert mime == "image/jpeg"
    with Image.open(io.BytesIO(clean)) as decoded:
        assert decoded.size == (8, 4)
        assert not decoded.getexif()


def test_profile_preference_and_default_fallback():
    async def configured(_relay, _pubkey):
        return [{"kind": 10063, "created_at": 3, "id": "new", "tags": [["server", "https://first.example"]]},
                {"kind": 10063, "created_at": 2, "id": "old", "tags": [["server", "https://old.example"]]}]
    async def absent(_relay, _pubkey):
        return []
    assert asyncio.run(discover_servers(["wss://relay.example"], "pub", configured)) == ["https://first.example"]
    assert asyncio.run(discover_servers(["wss://relay.example"], "pub", absent)) == [DEFAULT_BLOSSOM_SERVER]


def test_cached_encrypted_image_is_available_without_network(tmp_path):
    attachment = encrypt_image(b"offline synthetic JPEG bytes")
    reference = image_markdown_reference(attachment, "https://unreachable.example")
    (tmp_path / f"image-{attachment['hash']}.bin").write_bytes(attachment["ciphertext"])
    assert cached_image_available(reference[len("![Image]("):-1], tmp_path)
    assert load_image_reference(reference[len("![Image]("):-1], tmp_path) == b"offline synthetic JPEG bytes"


def test_download_uses_current_profile_servers_when_original_is_removed(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module
    attachment = encrypt_image(b"mirrored ciphertext bytes")
    reference = image_markdown_reference(attachment, "https://removed.example")
    requests = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def read(self, _limit): return attachment["ciphertext"]

    class Opener:
        def open(self, request, timeout):
            requests.append((request.full_url, timeout))
            return Response()

    monkeypatch.setattr(module, "build_opener", lambda _handler: Opener())
    result = load_image_reference(reference[len("![Image]("):-1], tmp_path, ["https://current.example"])
    assert result == b"mirrored ciphertext bytes"
    assert requests[0][0].startswith("https://current.example/")


def test_download_prefers_exact_blob_url_returned_by_blossom(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module
    attachment = encrypt_image(b"descriptor URL ciphertext")
    blob_url = f"https://cdn.example/blobs/{attachment['hash']}.bin"
    reference = image_markdown_reference(attachment, "https://upload.example", blob_url)
    requests = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def read(self, _limit): return attachment["ciphertext"]

    class Opener:
        def open(self, request, timeout):
            requests.append(request.full_url)
            assert request.get_header("User-agent") == f"Notestr/{module.__version__}"
            return Response()

    monkeypatch.setattr(module, "build_opener", lambda _handler: Opener())
    assert load_image_reference(reference[len("![Image]("):-1], tmp_path) == b"descriptor URL ciphertext"
    assert requests[0] == blob_url


def test_reject_descriptor_url_without_matching_hash():
    attachment = encrypt_image(b"synthetic image")
    with pytest.raises(ValueError, match="URL du blob Blossom invalide"):
        image_markdown_reference(attachment, "https://images.example", "https://cdn.example/other.jpg")


def test_successful_upload_seeds_encrypted_cache_for_immediate_preview(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module
    source = io.BytesIO()
    Image.new("RGB", (3, 2), "blue").save(source, format="JPEG")

    class Identity:
        pubkey = "synthetic"

    async def profile(_relay, _pubkey):
        return [{"kind": 10063, "created_at": 1, "tags": [["server", "https://images.example"]]}]

    uploaded = []
    monkeypatch.setattr(module, "upload_blob", lambda server, image, identity:
                        uploaded.append((server, image["hash"], identity)))
    async def run_inline(function, *args):
        return function(*args)
    monkeypatch.setattr(module.asyncio, "to_thread", run_inline)
    reference = asyncio.run(upload_encrypted_image(source.getvalue(), Identity(), ["wss://relay.example"],
                                                   profile, cache_dir=tmp_path))
    raw_reference = reference[len("![Image]("):-1]
    assert uploaded and cached_image_available(raw_reference, tmp_path)
    assert load_image_reference(raw_reference, tmp_path, [])[:2] == b"\xff\xd8"
    cached = tmp_path / f"image-{uploaded[0][1]}.bin"
    assert cached.stat().st_mode & 0o777 == 0o600


def test_upload_failure_includes_bounded_blossom_reason_and_response_body(monkeypatch):
    import http.client
    import nostr_notes.image_attachments as module
    from urllib.error import HTTPError

    response = HTTPError("https://images.example/upload", 400, "Bad Request",
                         http.client.HTTPMessage(), io.BytesIO(b"invalid encrypted payload\n"))
    response.headers.add_header("X-Reason", "unsupported encrypted blob")

    class Opener:
        def open(self, _request, timeout):
            assert timeout == 25
            raise response

    class Identity:
        def signed(self, *_args):
            return {"synthetic": True}

    monkeypatch.setattr(module, "build_opener", lambda _handler: Opener())
    with pytest.raises(RuntimeError, match="HTTP Error 400: Bad Request") as error:
        module.upload_blob("https://images.example", {"ciphertext": b"ciphertext", "hash": "a" * 64}, Identity())
    assert "unsupported encrypted blob" in str(error.value)
    assert "invalid encrypted payload" in str(error.value)


def test_blossom_auth_token_has_spec_and_legacy_base64_forms():
    import base64
    import json
    from nostr_notes.image_attachments import _authorization_tokens

    event = {"id": "a" * 64, "pubkey": "b" * 64, "created_at": 123, "kind": 24242,
             "tags": [["t", "upload"]], "content": "Téléversement", "sig": "c" * 128}
    urlsafe, legacy = _authorization_tokens(event)
    decoded = json.loads(base64.urlsafe_b64decode(urlsafe + "=" * (-len(urlsafe) % 4)))
    assert decoded == event
    assert "=" not in urlsafe
    assert base64.b64decode(legacy).decode("utf-8") == json.dumps(event, ensure_ascii=False, separators=(",", ":"))


def test_upload_retries_legacy_base64_only_after_auth_encoding_rejection(monkeypatch):
    import http.client
    import json
    from urllib.error import HTTPError
    import nostr_notes.image_attachments as module

    requests = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def read(self, _limit): return json.dumps({"sha256": "a" * 64}).encode()

    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            assert timeout == 25
            if len(requests) == 1:
                raise HTTPError(request.full_url, 400, "Bad Request", http.client.HTTPMessage(),
                                io.BytesIO(b"Invalid auth string"))
            return Response()

    class Identity:
        def signed(self, *_args):
            return {"id": "a" * 64, "pubkey": "b" * 64, "created_at": 123, "kind": 24242,
                    "tags": [["t", "upload"]], "content": "Upload", "sig": "c" * 128}

    monkeypatch.setattr(module, "build_opener", lambda *_args: Opener())
    upload_blob("https://images.example", {"ciphertext": b"encrypted", "hash": "a" * 64}, Identity())
    assert len(requests) == 2
    assert requests[0].get_header("Authorization") != requests[1].get_header("Authorization")
    assert requests[0].data == requests[1].data == b"encrypted"
