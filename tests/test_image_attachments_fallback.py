from nostr_notes.image_attachments import encrypt_image, image_markdown_reference, load_image_reference


def test_removed_profile_server_is_tried_after_current_mirrors_fail(monkeypatch, tmp_path):
    import nostr_notes.image_attachments as module

    attachment = encrypt_image(b"synthetic legacy image")
    markdown = image_markdown_reference(attachment, "https://old-blossom.example")
    reference = markdown[len("![Image]("):-1]
    requests = []

    class Response:
        def __enter__(self): return self
        def __exit__(self, *_args): return None
        def read(self, _limit): return attachment["ciphertext"]

    class Opener:
        def open(self, request, timeout):
            requests.append(request.full_url)
            if request.full_url.startswith("https://current-blossom.example/"):
                raise OSError("mirror does not have this old blob")
            return Response()

    monkeypatch.setattr(module, "build_opener", lambda _handler: Opener())
    decoded = load_image_reference(reference, tmp_path, ["https://current-blossom.example"])

    assert decoded == b"synthetic legacy image"
    assert requests[0].startswith("https://current-blossom.example/")
    assert requests[1].startswith("https://old-blossom.example/")
