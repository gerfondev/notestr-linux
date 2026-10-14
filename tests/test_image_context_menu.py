from types import SimpleNamespace

import gi
gi.require_version("WebKit", "6.0")
from gi.repository import WebKit

import nostr_notes.editor as editor_module
from nostr_notes.editor import MarkdownEditor


def test_context_image_uri_extracts_only_supported_inline_image_data():
    result = MarkdownEditor._image_data_from_uri(
        "data:image/jpeg;base64,aGVsbG8=#notestr-e1i0"
    )
    assert result == (b"hello", "image/jpeg")


def test_context_image_uri_supports_png():
    assert MarkdownEditor._image_data_from_uri(
        "data:image/png;base64,YWJj"
    ) == (b"abc", "image/png")


def test_context_image_uri_rejects_remote_and_malformed_sources():
    assert MarkdownEditor._image_data_from_uri("https://example.test/image.jpg") is None
    assert MarkdownEditor._image_data_from_uri("data:image/svg+xml;base64,PHN2Zz4=") is None
    assert MarkdownEditor._image_data_from_uri("data:image/jpeg;base64,%%%") is None


def test_image_context_menu_replaces_inert_webkit_stock_actions():
    menu = WebKit.ContextMenu.new()
    menu.append(WebKit.ContextMenuItem.new_from_stock_action(
        WebKit.ContextMenuAction.COPY_IMAGE_TO_CLIPBOARD))
    menu.append(WebKit.ContextMenuItem.new_from_stock_action(
        WebKit.ContextMenuAction.DOWNLOAD_IMAGE_TO_DISK))
    hit = SimpleNamespace(
        context_is_image=lambda: True,
        get_image_uri=lambda: "data:image/jpeg;base64,aGVsbG8=#notestr-e1i0",
    )
    editor = SimpleNamespace(
        _image_data_from_uri=MarkdownEditor._image_data_from_uri,
        _copy_context_image=lambda _data: None,
        _save_context_image=lambda _data, _mime: None,
    )

    assert MarkdownEditor._context_menu(editor, None, menu, hit) is False
    actions = [item.get_gaction().get_name() for item in menu.get_items()]
    assert "copy-note-image" in actions
    assert "save-note-image" in actions
    assert not any(item.get_stock_action() in (
        WebKit.ContextMenuAction.COPY_IMAGE_TO_CLIPBOARD,
        WebKit.ContextMenuAction.DOWNLOAD_IMAGE_TO_DISK,
    ) for item in menu.get_items())


def test_copy_context_image_sends_decoded_image_to_clipboard(monkeypatch):
    copied = []
    clipboard = SimpleNamespace(set_texture=copied.append)
    monkeypatch.setattr(editor_module, "Gdk", SimpleNamespace(
        Texture=SimpleNamespace(new_from_bytes=lambda _data: "texture")))
    monkeypatch.setattr(editor_module, "GLib", SimpleNamespace(
        Bytes=SimpleNamespace(new=lambda data: data)))
    editor = SimpleNamespace(
        web=SimpleNamespace(get_display=lambda: SimpleNamespace(get_clipboard=lambda: clipboard)),
        notice=SimpleNamespace(set_text=lambda _text: None),
    )

    MarkdownEditor._copy_context_image(editor, b"image bytes")

    assert copied == ["texture"]


def test_save_context_image_writes_selected_file(monkeypatch):
    saved = {}
    dialogs = []

    class File:
        def replace_contents(self, data, *_args):
            saved["data"] = data

    file = File()
    class Dialog:
        def __init__(self, **kwargs):
            assert kwargs == {"title": "Enregistrer l’image"}
            dialogs.append(self)
        def set_initial_name(self, name):
            saved["name"] = name
        def save(self, _parent, _cancellable, callback):
            self.callback = callback
        def save_finish(self, _result):
            return file

    fake_gtk = SimpleNamespace(FileDialog=Dialog)
    monkeypatch.setattr(editor_module, "Gtk", fake_gtk)
    editor = SimpleNamespace(get_root=lambda: "window", notice=SimpleNamespace(set_text=lambda text: saved.update(notice=text)))

    MarkdownEditor._save_context_image(editor, b"image bytes", "image/jpeg")
    chooser = dialogs[-1]
    chooser.callback(chooser, object())

    assert saved["data"] == b"image bytes"
    assert saved["notice"] == "Image enregistrée."
