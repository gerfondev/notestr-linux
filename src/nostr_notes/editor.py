"""Éditeur local hybride : Markdown exact et WYSIWYG WebKitGTK sans réseau."""
from .i18n import tr, get_language
import json
import os
import base64
import re
from pathlib import Path
from urllib.parse import urlsplit

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk

try:
    gi.require_version("WebKit", "6.0")
    from gi.repository import WebKit
except (ImportError, ValueError):
    WebKit = None

ASSETS = Path(__file__).with_name("assets")
EDITOR_URI = "notes-editor://app/index.html"
MIME = {"purify.min.js": "application/javascript", "index.html": "text/html", "editor.js": "application/javascript",
        "toastui-editor.js": "application/javascript", "fr-fr.js": "application/javascript",
        "editor.css": "text/css", "toastui-editor.css": "text/css"}
VISUAL_NOTICE = 'Le mode visuel peut normaliser le Markdown modifié. Pour les syntaxes spéciales ou le HTML, utiliser Markdown.'
SYNC_NOTICE = 'Synchronisation en cours ; réessayer dans un instant.'


def supported_webkit():
    # WSA-2026-0006: older system engines must not render note content.
    return WebKit is not None and (
        WebKit.get_major_version(), WebKit.get_minor_version(), WebKit.get_micro_version()
    ) >= (2, 54, 0)


class MarkdownEditor(Gtk.Box):
    def __init__(self, on_change, on_insert_image=None, on_load_image=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.on_change = on_change
        self.on_insert_image = on_insert_image
        self.on_load_image = on_load_image
        self.markdown = ""
        self.epoch = 0
        self.ready = False
        self.loading_source = False
        self.switching = False
        self.visual_active = False
        self.failed = False
        self.pending_document = False
        self.pending_image_results = {}
        self.image_error_message = None
        self.read_only = False
        self.toolbar = Gtk.Box(spacing=8, margin_start=12, margin_top=6, margin_bottom=6)
        self.visual_button = Gtk.ToggleButton(label=tr('Visuel'))
        self.source_button = Gtk.ToggleButton(label="Markdown")
        self.source_button.set_group(self.visual_button)
        self.visual_button.connect("clicked", lambda _: self.switch_mode(True))
        self.source_button.connect("clicked", lambda _: self.switch_mode(False))
        self.toolbar.append(self.visual_button)
        self.toolbar.append(self.source_button)
        if on_insert_image:
            self.image_button = Gtk.Button(icon_name='insert-image-symbolic')
            self.image_button.set_tooltip_text(tr('Insérer une image'))
            self.image_button.update_property([Gtk.AccessibleProperty.LABEL], [tr('Insérer une image')])
            self.image_button.connect("clicked", self._begin_image_insertion)
            self.image_button.set_visible(False)  # En mode visuel, l’icône est dans la barre WebKit près du tableau.
            self.toolbar.append(self.image_button)
        self.append(self.toolbar)
        self.notice = Gtk.Label(wrap=True, xalign=0, margin_start=12, margin_end=12,
                                margin_bottom=6)
        self.append(self.notice)
        self.stack = Gtk.Stack(vexpand=True, hexpand=True)
        self.append(self.stack)
        self.source = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, monospace=True,
                                  left_margin=20, right_margin=20, top_margin=16, bottom_margin=16)
        self.buffer = self.source.get_buffer()
        self.image_insert_start = None
        self.image_insert_end = None
        self.buffer.connect("changed", self._source_changed)
        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.source)
        self.stack.add_named(scroll, "source")
        self.stack.set_visible_child_name("source")
        self.source_button.set_active(True)
        self.web = None
        if supported_webkit():
            self._build_webview()
            self.notice.set_text(tr('Chargement de l’éditeur visuel local…'))
            self.visual_button.set_sensitive(False)
        else:
            self.visual_button.set_sensitive(False)
            self.notice.set_text(tr('Mode visuel : WebKitGTK 2.54.0 ou ultérieur est requis. Utiliser l’AppImage à jour ou mettre à jour le moteur système. Le mode Markdown reste disponible.'))

    def _build_webview(self):
        self.context = WebKit.WebContext()
        self.context.register_uri_scheme("notes-editor", self._serve_asset)
        manager = self.context.get_security_manager()
        manager.register_uri_scheme_as_secure("notes-editor")
        manager.register_uri_scheme_as_local("notes-editor")
        self.messages = WebKit.UserContentManager()
        self.messages.connect("script-message-received::notes", self._message)
        self.messages.register_script_message_handler("notes", None)
        self.web = WebKit.WebView(web_context=self.context, user_content_manager=self.messages,
                                 network_session=WebKit.NetworkSession.new_ephemeral())
        settings = self.web.get_settings()
        for name in ("enable-html5-local-storage", "enable-page-cache", "enable-dns-prefetching",
                     "enable-developer-extras", "javascript-can-open-windows-automatically",
                     "javascript-can-access-clipboard", "allow-file-access-from-file-urls",
                     "allow-universal-access-from-file-urls", "enable-media-stream", "enable-media", "enable-webgl", "enable-accelerated-2d-canvas"):
            if settings.find_property(name):
                settings.set_property(name, False)
        self.web.connect("decide-policy", self._policy)
        self.web.connect("context-menu", self._context_menu)
        self.web.connect("permission-request", self._deny_permission)
        self.web.connect("web-process-terminated", lambda *_: self._failure(tr('Le moteur visuel s’est arrêté.')))
        self.web.connect("load-failed", lambda *_: self._failure(tr('Chargement visuel impossible.')))
        self.stack.add_named(self.web, "visual")
        self.web.load_uri(EDITOR_URI)
        GLib.timeout_add_seconds(15, self._ready_timeout)

    def _ready_timeout(self):
        if not self.ready and not self.failed:
            self._failure(tr('L’éditeur visuel ne répond pas.'))
        return False

    def _serve_asset(self, request):
        parsed = urlsplit(request.get_uri())
        name = parsed.path.removeprefix("/")
        if parsed.netloc == "app" and not parsed.query and name in MIME:
            data = (ASSETS / name).read_bytes()
            stream = Gio.MemoryInputStream.new_from_bytes(GLib.Bytes.new(data))
            request.finish(stream, len(data), MIME[name])
        else:
            request.finish_error(GLib.Error.new_literal(Gio.io_error_quark(), tr('Ressource interdite'), Gio.IOErrorEnum.PERMISSION_DENIED))

    def _policy(self, _, decision, decision_type):
        if decision_type in (WebKit.PolicyDecisionType.NAVIGATION_ACTION, WebKit.PolicyDecisionType.NEW_WINDOW_ACTION):
            uri = decision.get_navigation_action().get_request().get_uri()
            if uri != EDITOR_URI or decision_type == WebKit.PolicyDecisionType.NEW_WINDOW_ACTION:
                decision.ignore()
                return True
        return False

    def _context_menu(self, _, menu, hit):
        if getattr(hit, 'context_is_image', lambda: False)():
            image = self._image_data_from_uri(hit.get_image_uri())
            if image:
                data, mime = image
                for item in list(menu.get_items()):
                    if item.get_stock_action() in (
                            WebKit.ContextMenuAction.COPY_IMAGE_TO_CLIPBOARD,
                            WebKit.ContextMenuAction.DOWNLOAD_IMAGE_TO_DISK):
                        menu.remove(item)
                copy_action = Gio.SimpleAction.new("copy-note-image", None)
                copy_action.connect("activate", lambda *_: self._copy_context_image(data))
                menu.prepend(WebKit.ContextMenuItem.new_from_gaction(
                    copy_action, tr('Copy Image'), None))
                save_action = Gio.SimpleAction.new("save-note-image", None)
                save_action.connect("activate", lambda *_: self._save_context_image(data, mime))
                menu.prepend(WebKit.ContextMenuItem.new_from_gaction(
                    save_action, tr('Save Image'), None))
                return False
        if not hit.context_is_link():
            return False
        uri = hit.get_link_uri()
        # WebKit's stock actions navigate inside the editor or create a WebView.
        # Replace them with the same external launcher used by a normal click.
        for item in list(menu.get_items()):
            if item.get_stock_action() in (WebKit.ContextMenuAction.OPEN_LINK,
                    WebKit.ContextMenuAction.OPEN_LINK_IN_NEW_WINDOW,
                    WebKit.ContextMenuAction.DOWNLOAD_LINK_TO_DISK):
                menu.remove(item)
        if not self._is_web_link(uri):
            return False
        revision = self.epoch
        action = Gio.SimpleAction.new("open-link-in-browser", None)
        def activate(*_):
            if revision != self.epoch or not self.visual_active:
                return
            # Flush the last edit before leaving the editor; a stale menu must
            # never act on another document loaded in the meantime.
            self.flush(lambda: self._open_link(uri) if revision == self.epoch else None)
        action.connect("activate", activate)
        menu.prepend(WebKit.ContextMenuItem.new_from_gaction(
            action, tr('Ouvrir le lien dans le navigateur'), None))
        return False  # Show the modified native menu, preserving Copy Link etc.

    @staticmethod
    def _image_data_from_uri(uri):
        if not isinstance(uri, str) or len(uri) > 38 * 1024 * 1024:
            return None
        match = re.fullmatch(r"data:(image/(?:jpeg|png));base64,([A-Za-z0-9+/=]+)(?:#notestr-[a-z0-9]+)?", uri, re.I)
        if not match:
            return None
        try:
            data = base64.b64decode(match.group(2), validate=True)
        except (ValueError, base64.binascii.Error):
            return None
        if not data or len(data) > 28 * 1024 * 1024:
            return None
        return data, match.group(1).lower()

    def _copy_context_image(self, data):
        try:
            texture = Gdk.Texture.new_from_bytes(GLib.Bytes.new(data))
            self.web.get_display().get_clipboard().set_texture(texture)
            self.notice.set_text(tr('Image copiée dans le presse-papiers.'))
        except (GLib.Error, TypeError, ValueError):
            self.notice.set_text(tr('Copie de l’image impossible.'))

    def _save_context_image(self, data, mime):
        extension = 'png' if mime == 'image/png' else 'jpg'
        chooser = Gtk.FileDialog(title=tr('Enregistrer l’image'))
        chooser.set_initial_name('Notestr-image.' + extension)

        def selected(dialog, result):
            try:
                file = dialog.save_finish(result)
                file.replace_contents(data, None, False, Gio.FileCreateFlags.REPLACE_DESTINATION, None)
            except GLib.Error as exc:
                if exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.CANCELLED) or \
                        exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    return
                self.notice.set_text(tr('Enregistrement de l’image impossible : {0}', exc.message))
                return
            self.notice.set_text(tr('Image enregistrée.'))

        chooser.save(self.get_root(), None, selected)

    @staticmethod
    def _deny_permission(_, request):
        request.deny()
        return True

    def _failure(self, message):
        self.failed = True
        self.ready = False
        self.visual_active = False
        self.pending_document = False
        self.switching = False
        self.stack.set_sensitive(True)
        self.toolbar.set_sensitive(True)
        self.visual_button.set_sensitive(False)
        self._update_source()
        self.stack.set_visible_child_name("source")
        self.source_button.set_active(True)
        self.notice.set_text(message + tr(' Mode Markdown rétabli avec le dernier texte reçu ; vérifier les dernières frappes.'))
        return True

    def _message(self, _, value):
        try:
            message = json.loads(value.to_string())
            if message.get("type") == "ready":
                if self.failed:
                    return
                self.ready = True
                self.visual_button.set_sensitive(True)
                self.switch_mode(True)
            elif (message.get("type") == "copyCode" and self.visual_active
                  and not self.pending_document and message.get("epoch") == self.epoch
                  and isinstance(message.get("text"), str)):
                self.get_clipboard().set(message["text"])
                self.notice.set_text(tr('Code copié dans le presse-papiers.'))
            elif (message.get("type") == "openLink" and self.visual_active
                  and not self.pending_document and message.get("epoch") == self.epoch):
                self._accept(message)
                self._open_link(message.get("url"))
            elif (message.get("type") == "pickImage" and self.visual_active
                  and not self.pending_document and message.get("epoch") == self.epoch
                  and self.on_insert_image):
                self._begin_image_insertion(None)
            elif (message.get("type") == "loadImage" and self.visual_active
                  and not self.pending_document and message.get("epoch") == self.epoch
                  and isinstance(message.get("reference"), str) and self.on_load_image):
                self.on_load_image(message["reference"], self.epoch)
            elif (message.get("type") == "imageError" and self.visual_active
                  and not self.pending_document and message.get("epoch") == self.epoch
                  and isinstance(message.get("message"), str)):
                self.notice.set_text(tr('Image indisponible : ') + message["message"])
            elif message.get("type") == "change" and self.visual_active and not self.pending_document:
                self._accept(message)
        except (ValueError, TypeError, AttributeError):
            self._failure(tr('Réponse invalide de l’éditeur.'))

    @staticmethod
    def _is_web_link(uri):
        if not isinstance(uri, str) or any(c.isspace() or ord(c) < 32 for c in uri) or "\\" in uri:
            return False
        try:
            parsed = urlsplit(uri)
            return parsed.scheme.lower() in ("http", "https") and bool(parsed.hostname)
        except ValueError:
            return False

    def _open_link(self, uri):
        if not MarkdownEditor._is_web_link(uri):
            return
        def finished(_, result, *args):
            try:
                Gio.AppInfo.launch_default_for_uri_finish(result)
            except GLib.Error:
                self.notice.set_text(tr('Impossible d’ouvrir le navigateur. Vérifier le navigateur par défaut du système.'))
        # Host browsers must not inherit the AppImage's Python/GTK libraries.
        context = Gio.AppLaunchContext()
        if os.environ.get("APPDIR"):
            for name in ("APPDIR", "APPIMAGE", "PYTHONHOME", "PYTHONPATH", "LD_LIBRARY_PATH",
                         "GI_TYPELIB_PATH", "GIO_EXTRA_MODULES", "GSETTINGS_SCHEMA_DIR",
                         "WEBKIT_EXEC_PATH", "WEBKIT_INJECTED_BUNDLE_PATH"):
                context.unsetenv(name)
            paths = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
            bundled = os.environ["APPDIR"].rstrip("/") + "/usr/share"
            context.setenv("XDG_DATA_DIRS", ":".join(p for p in paths if p != bundled))
        Gio.AppInfo.launch_default_for_uri_async(uri, context, None, finished, None)

    def _accept(self, message):
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except (ValueError, TypeError):
                return
        if message.get("epoch") == self.epoch and isinstance(message.get("markdown"), str):
            text = message["markdown"]
            if text != self.markdown:
                self.markdown = text
                self.on_change(self)

    def image_result(self, reference, data):
        if not self.ready or not self.visual_active:
            return
        if self.pending_document:
            # A note can be re-rendered as read-only while its encrypted image
            # is loading. Keep decrypted bytes only in memory until the new
            # document is ready, then let its own image map decide whether the
            # reference is still present.
            self.pending_image_results[reference] = data
            return
        def received(result):
            if result is not True and self.visual_active:
                self.image_error(tr('L’image a été chargée, mais l’éditeur n’a pas pu la placer dans la note.'))
        self._evaluate("window.notesEditor.imageResult(" + json.dumps(reference) + "," + json.dumps(data) + ")", received)

    def image_error(self, message):
        if self.visual_active:
            self.image_error_message = tr('Image indisponible : ') + str(message)
            self.notice.set_text(self.image_error_message)

    def _evaluate(self, script, callback):
        def finished(view, result, _):
            try:
                value = view.evaluate_javascript_finish(result)
                message = json.loads(value.to_string())
            except Exception:
                self._failure(tr('Impossible de synchroniser l’éditeur visuel.'))
                callback(None)
                return
            callback(message)
        self.web.evaluate_javascript(script, -1, None, None, None, finished, None)

    def _source_changed(self, _):
        if not self.loading_source and not self.read_only:
            self.markdown = self.buffer.get_text(self.buffer.get_start_iter(), self.buffer.get_end_iter(), True)
            self.on_change(self)

    def _update_source(self):
        self.loading_source = True
        self.buffer.set_text(self.markdown)
        self.loading_source = False

    def get_text(self):
        return self.markdown

    def _begin_image_insertion(self, _button):
        if self.read_only:
            return
        if self.visual_active and self.ready and not self.pending_document:
            def ready_to_choose(result):
                # The native file chooser steals focus. Open it only after the
                # WebKit editor has captured the actual ProseMirror selection.
                if result is True and self.on_insert_image:
                    self.on_insert_image()
                elif result is not True:
                    self.notice.set_text(tr('Impossible de mémoriser la position du curseur. Réessayez.'))
            self._evaluate("window.notesEditor.rememberInsertionPoint()", ready_to_choose)
            return
        else:
            bounds = self.buffer.get_selection_bounds()
            start, end = bounds if bounds else (self.buffer.get_iter_at_mark(self.buffer.get_insert()),) * 2
            self.image_insert_start = self.buffer.create_mark(None, start, True)
            self.image_insert_end = self.buffer.create_mark(None, end, False)
        if self.on_insert_image:
            self.on_insert_image()

    def insert_image_reference(self, reference):
        if self.read_only:
            return False
        if self.visual_active and self.ready and not self.pending_document:
            def inserted(result):
                if result is not True:
                    self.notice.set_text(tr('Impossible d’insérer l’image à la position choisie.'))
                    return
                # Update the native Markdown copy immediately so switching
                # modes cannot race a queued JavaScript change notification.
                self._evaluate("window.notesEditor.snapshot()", self._accept)
            self._evaluate("window.notesEditor.insertImageReference(" + json.dumps(reference) + ")", inserted)
            return
        buffer = self.buffer
        if self.image_insert_start and self.image_insert_end:
            start = buffer.get_iter_at_mark(self.image_insert_start)
            end = buffer.get_iter_at_mark(self.image_insert_end)
            buffer.delete(start, end)
            buffer.delete_mark(self.image_insert_start)
            buffer.delete_mark(self.image_insert_end)
            self.image_insert_start = self.image_insert_end = None
        else:
            start = buffer.get_iter_at_mark(buffer.get_insert())
        buffer.insert(start, reference)

    def set_text(self, markdown, read_only=False):
        self.epoch += 1
        self.read_only = bool(read_only)
        self.toolbar.set_visible(not self.read_only)
        self.image_error_message = None
        self.markdown = markdown
        self.source.set_editable(not self.read_only)
        self.source.set_cursor_visible(not self.read_only)
        if hasattr(self, "image_button"):
            self.image_button.set_sensitive(not self.read_only)
        self._update_source()
        if self.ready and self.visual_active:
            self._load_visual()

    def _load_visual(self, callback=None):
        revision = self.epoch
        self.pending_document = True
        self.web.set_sensitive(False)
        def loaded(result):
            if revision != self.epoch:
                return
            self.pending_document = False
            self.web.set_sensitive(True)
            pending_images, self.pending_image_results = self.pending_image_results, {}
            for reference, data in pending_images.items():
                self.image_result(reference, data)
            if result is not None and self.visual_active:
                # The initial JS notification can arrive while the native bridge
                # still considers this document pending. Retry after that state
                # transition has reached WebKit's main loop.
                def resolve_images():
                    if revision == self.epoch and self.visual_active and self.ready:
                        self._evaluate("window.notesEditor.resolveImages(true)", lambda _result: None)
                    return False
                GLib.timeout_add(50, resolve_images)
            if result is not None and self.visual_active:
                self.notice.set_text(self.image_error_message or tr(VISUAL_NOTICE))
            if result is not None and callback:
                callback()
        self._evaluate("window.notesEditor.setDocument(" + json.dumps(self.markdown) + "," + str(revision) + "," + json.dumps(get_language()) + "," + json.dumps(self.read_only) + ")", loaded)

    def flush(self, callback):
        """Barrière avant publier/quitter : recevoir les toutes dernières frappes JS."""
        if self.switching or self.pending_document:
            self.notice.set_text(tr(SYNC_NOTICE))
            return
        if not self.visual_active or not self.ready:
            callback()
            return
        self.switching = True
        self.stack.set_sensitive(False)
        self.toolbar.set_sensitive(False)
        revision = self.epoch
        def done(result):
            self.switching = False
            self.stack.set_sensitive(True)
            self.toolbar.set_sensitive(True)
            if result is None or revision != self.epoch:
                return  # Ne pas poursuivre une publication après échec du pont.
            self._accept(result)
            callback()
        self._evaluate("window.notesEditor.snapshot()", done)

    def switch_mode(self, visual):
        if self.switching or self.pending_document:
            (self.visual_button if self.visual_active else self.source_button).set_active(True)
            return
        if visual == self.visual_active or (visual and not self.ready):
            return
        if visual:
            self.visual_active = True
            self.visual_button.set_active(True)
            self.stack.set_visible_child_name("visual")
            self.notice.set_text(tr(VISUAL_NOTICE))
            self._load_visual()
        else:
            def done():
                self.visual_active = False
                self._update_source()
                self.stack.set_visible_child_name("source")
                self.source_button.set_active(True)
                if self.on_insert_image:
                    self.image_button.set_visible(True)
                self.notice.set_text(tr('Markdown : les retours simples seront rendus explicites à la publication. Les blocs de code sont préservés.'))
            self.flush(done)
