"""Interface GTK4/libadwaita. Réseau et crypto hors du thread graphique."""
from .i18n import tr, set_language, get_language
from . import __version__
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk

from .offline import Outbox
from .core import Identity, Note, valid_event, compact_backups
from .editor import MarkdownEditor
from .lock import PasswordLock
from .pdf_export import export_markdown_pdf
from .relay import across, publish_update, query_one, query_server_profile
from .image_attachments import upload_encrypted_image, load_image_for_display
from .storage import Storage, load_secret, save_secret, relays_from_text


ASSETS = Path(__file__).with_name("assets")
APP_ICON_NAME = "fr.decentralia.NostrNotes"
LOGO = ASSETS / f"{APP_ICON_NAME}.png"


def logo_picture(size):
    """Create a consistently scaled Notestr logo without altering its aspect ratio."""
    picture = Gtk.Picture.new_for_filename(str(LOGO))
    picture.set_content_fit(Gtk.ContentFit.CONTAIN)
    picture.set_can_shrink(True)
    picture.set_keep_aspect_ratio(True)
    picture.set_size_request(size, size)
    picture.set_alternative_text(tr('Logo Notestr'))
    return picture


def button(label, callback, icon_name=None):
    widget = Gtk.Button(icon_name=icon_name) if icon_name else Gtk.Button(label=label)
    if icon_name:
        widget.set_tooltip_text(label)
        widget.update_property([Gtk.AccessibleProperty.LABEL], [label])
    widget.connect("clicked", lambda _: callback())
    return widget


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=tr('Notes privées Nostr'), default_width=1000, default_height=700)
        Gtk.IconTheme.get_for_display(self.get_display()).add_search_path(str(ASSETS))
        self.set_icon_name(APP_ICON_NAME)
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.sync_pool = ThreadPoolExecutor(max_workers=1)
        self.image_pool = ThreadPoolExecutor(max_workers=2)
        self.pending_image_loads = set()
        self.syncing = False
        self.sync_loop = None
        self.sync_async_task = None
        self.outbox = None
        self.identity = None
        self.events = {}
        self.notes = []
        self.showing_trash = False
        self.current = None
        self.draft_d = None
        self.dirty = False
        self.loading = False
        self.busy = False
        self.refreshing = False
        self.store = Storage()
        self.password_lock = PasswordLock(self.store)
        self.config = self.store.config()
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)
        self.header = Adw.HeaderBar()
        root.append(self.header)
        title = Gtk.Box(spacing=8, valign=Gtk.Align.CENTER)
        self.header_logo = logo_picture(30)
        title.append(self.header_logo)
        title_label = Gtk.Label(label=tr('Notes privées Nostr'))
        title_label.add_css_class("title")
        title.append(title_label)
        self.header.set_title_widget(title)
        self.controls = Gtk.Box(spacing=6)
        self.header.pack_start(self.controls)
        self.new_button = button(tr('Nouvelle note'), self.new_note, "document-new-symbolic")
        self.refresh_button = button(tr('Actualiser'), self.refresh, "view-refresh-symbolic")
        self.publish_button = button(tr('Publier'), self.publish, "mail-send-symbolic")
        self.delete_button = button(tr('Supprimer'), self.delete, "edit-delete-symbolic")
        self.restore_button = button(tr('Version précédente'), self.restore_previous, "edit-undo-symbolic")
        self.pin_button = button(tr('Épingler'), self.toggle_pin, "notestr-pin-symbolic")
        self.pdf_button = button(tr('Exporter en PDF'), self.export_pdf, "document-save-as-symbolic")
        for action in (self.new_button, self.refresh_button, self.publish_button,
                       self.delete_button, self.restore_button, self.pin_button, self.pdf_button):
            self.controls.append(action)
        self.controls.set_sensitive(False)
        self.settings_button = button(tr('Compte et relais'), self.settings, "preferences-system-symbolic")
        self.header.pack_end(self.settings_button)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=280, vexpand=True)
        root.append(paned)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, width_request=220)
        self.search = Gtk.SearchEntry(placeholder_text=tr('Rechercher dans les notes'))
        self.search.connect("search-changed", lambda _: self.render_list())
        self.trash_button = Gtk.ToggleButton(label=tr("Corbeille"))
        self.trash_button.connect("clicked", lambda _: self.toggle_trash_view())
        self.trash_toolbar = Gtk.Box(spacing=8, margin_start=12, margin_end=12,
                                     margin_top=6, margin_bottom=6)
        self.trash_toolbar.append(self.trash_button)
        sidebar.append(self.trash_toolbar)
        sidebar.append(self.search)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.listbox.connect("row-activated", self.select_row)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.listbox)
        sidebar.append(scroll)
        paned.set_start_child(sidebar)
        self.editor = MarkdownEditor(self.changed, self.insert_image, self.load_image)
        self.editor.set_sensitive(False)
        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.pending_label = Gtk.Label(wrap=True, xalign=0, margin_start=8, margin_end=8)
        self.pending_actions = Gtk.Box(spacing=8)
        self.copy_button = button(tr('Publier comme nouvelle note'), lambda: self.editor.flush(lambda: self.publish_synced(as_copy=True)))
        self.discard_button = button(tr('Abandonner les modifications locales'), self.discard_pending)
        self.pending_actions.append(self.copy_button)
        self.pending_actions.append(self.discard_button)
        # Keep navigation aligned even when a pending-sync notice is shown.
        self.navigation_size_group = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.VERTICAL)
        self.navigation_size_group.add_widget(self.trash_toolbar)
        self.navigation_size_group.add_widget(self.editor.toolbar)
        self.editor.insert_child_after(self.pending_label, self.editor.toolbar)
        self.editor.insert_child_after(self.pending_actions, self.pending_label)
        editor_box.append(self.editor)
        self.editor.set_vexpand(True)
        paned.set_end_child(editor_box)
        self.status = Gtk.Label(label=tr('Importer une clé privée pour commencer.'), xalign=0,
                                wrap=True, selectable=True, margin_start=12, margin_end=12,
                                margin_top=8, margin_bottom=8)
        root.append(self.status)
        self.connect("close-request", self.close_requested)
        GLib.idle_add(self.initial_unlock)
        self.retry_source = GLib.timeout_add_seconds(30, self.retry_pending)
        self.network_monitor = Gio.NetworkMonitor.get_default()
        self.network_handler = self.network_monitor.connect("network-changed", lambda _m, available: self.retry_pending() if available else None)

    def initial_unlock(self):
        if self.password_lock.exists():
            self.show_unlock()
        else:
            self.show_password_setup()
        return False

    def password_window(self, title, parent=None):
        dialog = Gtk.Window(title=title, transient_for=parent or self, modal=True,
                            default_width=440, resizable=False)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_start=24, margin_end=24, margin_top=24, margin_bottom=24)
        dialog.set_child(box)
        logo = logo_picture(80)
        logo.set_halign(Gtk.Align.CENTER)
        box.append(logo)
        return dialog, box

    def close_from_password_window(self, dialog):
        dialog.destroy()
        self.close_clean()

    def show_password_setup(self):
        dialog, box = self.password_window(tr('Créer le mot de passe Notestr'))
        box.append(Gtk.Label(
            label=tr('Choisissez le mot de passe demandé à chaque ouverture de Notestr.'),
            wrap=True, xalign=0))
        first = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Mot de passe (8 caractères minimum)'))
        second = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Confirmer le mot de passe'))
        box.append(first)
        box.append(second)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)

        def create():
            try:
                if first.get_text() != second.get_text():
                    raise ValueError(tr('Les deux mots de passe sont différents.'))
                self.password_lock.set_password(first.get_text())
                first.set_text("")
                second.set_text("")
                dialog.destroy()
                self.initial_login()
            except Exception as exc:
                info.set_text(str(exc) or type(exc).__name__)

        create_button = button(tr('Créer et ouvrir'), create)
        box.append(create_button)
        box.append(button(tr("Quitter"), lambda: self.close_from_password_window(dialog)))
        first.connect("activate", lambda _: second.grab_focus())
        second.connect("activate", lambda _: create())
        dialog.connect("close-request", lambda _: self.close_from_password_window(dialog) or True)
        dialog.present()
        first.grab_focus()

    def show_unlock(self):
        dialog, box = self.password_window(tr('Déverrouiller Notestr'))
        box.append(Gtk.Label(label=tr('Saisissez le mot de passe de l’application.'), wrap=True, xalign=0))
        secret = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Mot de passe'))
        box.append(secret)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)
        attempts = {"count": 0}

        def enable_again():
            unlock_button.set_sensitive(True)
            info.set_text(tr('Vous pouvez réessayer.'))
            secret.grab_focus()
            return False

        def unlock():
            try:
                valid = self.password_lock.verify(secret.get_text())
            except Exception as exc:
                info.set_text(str(exc) or type(exc).__name__)
                return
            secret.set_text("")
            if valid:
                dialog.destroy()
                self.initial_login()
                return
            attempts["count"] += 1
            if attempts["count"] >= 5:
                attempts["count"] = 0
                unlock_button.set_sensitive(False)
                info.set_text(tr('Trop de tentatives. Nouvel essai dans 30 secondes.'))
                GLib.timeout_add_seconds(30, enable_again)
            else:
                info.set_text(tr('Mot de passe incorrect.'))

        unlock_button = button(tr('Déverrouiller'), unlock)
        box.append(unlock_button)
        box.append(button(tr("Quitter"), lambda: self.close_from_password_window(dialog)))
        secret.connect("activate", lambda _: unlock())
        dialog.connect("close-request", lambda _: self.close_from_password_window(dialog) or True)
        dialog.present()
        secret.grab_focus()

    def show_change_password(self, parent, feedback):
        dialog, box = self.password_window(tr('Modifier le mot de passe'), parent)
        box.append(Gtk.Label(
            label=tr('Saisissez le mot de passe actuel, puis choisissez le nouveau.'),
            wrap=True, xalign=0))
        current = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Mot de passe actuel'))
        new = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Nouveau mot de passe (8 caractères minimum)'))
        confirmation = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text=tr('Confirmer le nouveau mot de passe'))
        box.append(current)
        box.append(new)
        box.append(confirmation)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)

        def change():
            try:
                if new.get_text() != confirmation.get_text():
                    raise ValueError(tr('Les deux nouveaux mots de passe sont différents.'))
                self.password_lock.change_password(current.get_text(), new.get_text())
                current.set_text("")
                new.set_text("")
                confirmation.set_text("")
                dialog.destroy()
                feedback.set_text(tr('Le mot de passe de l’application a été modifié.'))
            except Exception as exc:
                current.set_text("")
                info.set_text(str(exc) or type(exc).__name__)
                current.grab_focus()

        box.append(button(tr('Enregistrer le nouveau mot de passe'), change))
        box.append(button(tr('Annuler'), dialog.destroy))
        current.connect("activate", lambda _: new.grab_focus())
        new.connect("activate", lambda _: confirmation.grab_focus())
        confirmation.connect("activate", lambda _: change())
        dialog.present()
        current.grab_focus()

    def initial_login(self):
        pubkey = self.config.get("pubkey")
        if pubkey:
            self.work(lambda: load_secret(pubkey), self.restored)
        else:
            self.settings()
        return False

    def restored(self, secret):
        if secret:
            self.login(Identity(secret))
        else:
            self.settings()

    def work(self, operation, success, readable=False):
        if self.busy:
            return
        self.busy = True
        self.controls.set_sensitive(readable)
        self.settings_button.set_sensitive(False)
        self.refreshing = readable
        self.editor.set_sensitive(readable)
        self.update_trash_controls()
        self.listbox.set_sensitive(readable)
        self.status.set_text(tr('Notes en cache disponibles · synchronisation des relais…') if readable else tr('Opération en cours…'))
        future = self.pool.submit(operation)
        def finish():
            self.busy = False
            self.refreshing = False
            self.controls.set_sensitive(self.identity is not None)
            self.settings_button.set_sensitive(True)
            self.editor.set_sensitive(self.identity is not None)
            self.listbox.set_sensitive(True)
            try:
                success(future.result())
            except Exception as exc:
                self.status.set_text(str(exc) or type(exc).__name__)
            self.update_trash_controls()
            return False
        future.add_done_callback(lambda _: GLib.idle_add(finish))

    def text(self):
        return self.editor.get_text()

    def changed(self, _):
        if not self.loading:
            self.dirty = True
            self.set_title(tr('Notes privées Nostr • modifications non publiées'))

    def display(self, note=None):
        self.current = note
        self.update_pin_button()
        self.draft_d = None
        self.loading = True
        self.editor.set_text(note.markdown if note else "")
        self.loading = False
        self.dirty = False
        self.set_title(tr('Notes privées Nostr'))
        self.update_trash_controls()

    def confirm(self, text, action, label=None):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, text=text,
                                   message_type=Gtk.MessageType.WARNING)
        dialog.add_button(tr('Annuler'), Gtk.ResponseType.CANCEL)
        dialog.add_button(label or tr("Abandonner les modifications"), Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        def response(widget, value):
            widget.destroy()
            if value == Gtk.ResponseType.ACCEPT:
                action()
        dialog.connect("response", response)
        dialog.present()

    def guard(self, action, allow_read=False):
        if self.busy and not (allow_read and self.refreshing):
            return
        def checked():
            if self.dirty:
                self.confirm(tr('Des modifications ne sont pas publiées. Les abandonner ?'), action)
            else:
                action()
        self.editor.flush(checked)

    def close_requested(self, _):
        if getattr(self, "closing_clean", False):
            self.stop_sync()
            GLib.source_remove(self.retry_source)
            self.network_monitor.disconnect(self.network_handler)
            self.pool.shutdown(wait=False)
            self.sync_pool.shutdown(wait=False)
            return False
        if self.busy:
            self.status.set_text(tr('Attendre la fin de l’opération avant de fermer.'))
            return True
        def checked():
            if self.dirty:
                self.confirm(tr('Fermer et perdre les modifications non publiées ?'), self.close_clean)
            else:
                self.close_clean()
        self.editor.flush(checked)
        return True

    def close_clean(self):
        self.dirty = False
        self.closing_clean = True
        self.close()

    def new_note(self):
        def create():
            self.showing_trash = False
            self.trash_button.set_active(False)
            self.render_list()
            self.display()
        self.guard(create, allow_read=True)

    def toggle_trash_view(self):
        # Restore button state until draft confirmation has been accepted.
        self.trash_button.set_active(self.showing_trash)
        def change():
            self.showing_trash = not self.showing_trash
            self.trash_button.set_active(self.showing_trash)
            self.display()
            self.render_list()
        self.guard(change, allow_read=True)

    def update_trash_controls(self):
        trashed = bool(self.current and self.current.trashed)
        self.editor.set_sensitive(self.identity is not None and not trashed and (not self.busy or self.refreshing))
        pending = bool(self.current and self.current.pending)
        self.pending_label.set_visible(pending)
        self.pending_actions.set_visible(pending)
        self.pending_actions.set_sensitive(not self.busy and not self.syncing)
        self.copy_button.set_visible(bool(pending and self.current.conflicted))
        self.pending_label.set_text(tr('Conflit — la version distante est conservée dans la liste.' if pending and self.current.conflicted else 'Modifications enregistrées localement, en attente de synchronisation.'))
        self.publish_button.set_sensitive(not trashed)
        self.delete_button.set_sensitive(not pending and not self.syncing and not self.busy)
        self.restore_button.set_sensitive(not pending and not self.syncing and not self.busy)
        self.pin_button.set_sensitive(self.current is not None and not trashed and not pending and not self.syncing and not self.busy)
        label = tr('Restaurer la note') if trashed else tr('Version précédente')
        self.restore_button.set_tooltip_text(label)
        self.restore_button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        label = tr('Supprimer définitivement') if trashed else tr('Supprimer')
        self.delete_button.set_tooltip_text(label)
        self.delete_button.update_property([Gtk.AccessibleProperty.LABEL], [label])

    def set_trashed(self, note, trashed):
        def operation():
            event = self.identity.set_trashed(note, trashed, self.events.values())
            good, errors = asyncio.run(across(self.config['relays'], publish_update, event, None))
            events = compact_backups([*self.events.values(), event])
            try:
                self.store.save_events(self.identity.pubkey, list(events.values()))
            except Exception:
                errors.append(tr('Corbeille synchronisée, mais écriture du cache local impossible. Actualisez avant de fermer.'))
            return events, self.identity.notes(events.values())[0], errors
        def success(result):
            self.events, self.notes, errors = result
            self.notes = self.outbox.overlay(self.events.values())
            self.display()
            self.render_list()
            self.status.set_text(tr('Note déplacée dans la corbeille.' if trashed else 'Note restaurée.') + '\n'.join(errors))
        self.work(operation, success)

    def select_row(self, _, row):
        self.guard(lambda: self.display(row.note), allow_read=True)

    def render_list(self):
        child = self.listbox.get_first_child()
        while child:
            following = child.get_next_sibling()
            self.listbox.remove(child)
            child = following
        query = self.search.get_text().casefold()
        for note in self.notes:
            if note.trashed != self.showing_trash or query not in note.markdown.casefold():
                continue
            row = Gtk.ListBoxRow()
            row.note = note
            row.set_child(Gtk.Label(label=((tr("Conflit — version locale") + " · ") if note.conflicted else (tr("En attente de synchronisation") + " · ") if note.pending else "") + ("📌 " if note.pinned else "") + note.title, xalign=0, ellipsize=3,
                                    margin_start=12, margin_end=12, margin_top=10, margin_bottom=10))
            self.listbox.append(row)

    def login(self, identity):
        self.stop_sync()
        self.identity = identity
        self.outbox = Outbox(identity, self.store)
        self.events = {e["id"]: e for e in self.store.events(identity.pubkey)
                       if valid_event(e, identity.pubkey)}
        self.notes, unreadable = identity.notes(self.events.values())
        self.notes = self.outbox.overlay(self.events.values())
        self.display()
        self.render_list()
        self.controls.set_sensitive(True)
        self.editor.set_sensitive(True)
        self.status.set_text(tr('{0} note(s) en cache · {1} indéchiffrable(s).', len(self.notes), unreadable))
        # display() vient de réinitialiser le document : aucune saisie à protéger.
        # Le chargement asynchrone de l’éditeur ne doit pas bloquer la connexion.
        self.do_refresh()

    def refresh(self):
        if self.syncing:
            return
        self.guard(self.do_refresh)

    def do_refresh(self):
        def operation():
            good, errors = asyncio.run(across(self.config["relays"], query_one, self.identity.pubkey))
            events = dict(self.events)
            for items in good.values():
                events.update((e["id"], e) for e in items)
            events = compact_backups(events.values())
            notes, unreadable = self.identity.notes(events.values())
            self.store.save_events(self.identity.pubkey, list(events.values()))
            return events, notes, unreadable, errors
        def success(result):
            events, notes, unreadable, errors = result
            self.events = events
            self.notes = self.outbox.overlay(events.values())
            # Never replace an editor draft while a background refresh finishes.
            # Keep the opened version so publish can detect a conflicting update.
            self.render_list()
            self.status.set_text(tr('{0} note(s) · {1} indéchiffrable(s). ', len(notes), unreadable) + "\n".join(errors))
            GLib.idle_add(lambda: (self.retry_pending(), False)[1])
        self.work(operation, success, readable=True)

    def load_image(self, reference, epoch):
        if reference in self.pending_image_loads or self.identity is None:
            return
        self.pending_image_loads.add(reference)
        identity = self.identity
        relays = list(self.config['relays'])
        def operation():
            return load_image_for_display(reference, self.store.root, relays,
                                          identity.pubkey, query_server_profile)
        future = self.image_pool.submit(operation)
        def finish():
            self.pending_image_loads.discard(reference)
            if self.identity is None or epoch != self.editor.epoch:
                return False
            try:
                import base64
                payload = base64.b64encode(future.result()).decode('ascii')
                self.editor.image_result(reference, payload)
            except Exception as exc:
                self.status.set_text(tr('Image indisponible : ') + str(exc))
                self.editor.image_error(str(exc))
            return False
        future.add_done_callback(lambda _future: GLib.idle_add(finish))

    def insert_image(self):
        if self.identity is None or self.busy or (self.current and self.current.trashed):
            return
        def choose():
            chooser = Gtk.FileDialog(title=tr('Insérer une image'))
            filters = Gio.ListStore.new(Gtk.FileFilter)
            images = Gtk.FileFilter(name=tr('Images'))
            for mime in ('image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/heic'):
                images.add_mime_type(mime)
            filters.append(images)
            chooser.set_filters(filters)
            def selected(dialog, result):
                try:
                    file = dialog.open_finish(result)
                except GLib.Error as exc:
                    if exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.CANCELLED):
                        return
                    self.status.set_text(tr('Sélection de l’image impossible : ') + exc.message)
                    return
                path = file.get_path()
                if not path:
                    self.status.set_text(tr('Choisir une image locale.'))
                    return
                identity = self.identity
                relays = list(self.config['relays'])
                def operation():
                    data = Path(path).read_bytes()
                    return asyncio.run(upload_encrypted_image(data, identity, relays, query_server_profile,
                                                              cache_dir=self.store.root))
                def success(reference):
                    self.editor.insert_image_reference(reference)
                    self.status.set_text(tr('Image chiffrée et ajoutée à la note.'))
                self.work(operation, success)
            chooser.open(self, None, selected)
        # The editor toolbar waits for its caret capture before calling us.
        # A flush here adds another WebKit round trip after focus has changed.
        choose()

    def publish(self):
        if not self.identity or (self.busy and not self.refreshing):
            return
        self.editor.flush(self.publish_synced)

    def export_pdf(self):
        if not self.identity or self.busy:
            return
        self.editor.flush(self.choose_pdf_destination)

    def choose_pdf_destination(self):
        first = next((line.strip().lstrip("#").strip() for line in self.text().splitlines()
                      if line.strip()), tr('Note Nostr'))
        basename = re.sub(r"[^\w .-]+", "_", first, flags=re.UNICODE).strip(" ._")[:80]
        chooser = Gtk.FileDialog(title=tr('Exporter la note en PDF'))
        chooser.set_initial_name((basename or tr('Note Nostr')) + ".pdf")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        pdf_filter = Gtk.FileFilter(name=tr('Document PDF'))
        pdf_filter.add_mime_type("application/pdf")
        pdf_filter.add_pattern("*.pdf")
        filters.append(pdf_filter)
        chooser.set_filters(filters)

        def selected(dialog, result):
            try:
                file = dialog.save_finish(result)
            except GLib.Error as exc:
                if exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.CANCELLED) or \
                        exc.matches(Gtk.dialog_error_quark(), Gtk.DialogError.DISMISSED):
                    return
                self.status.set_text(tr('Export PDF impossible : {0}', exc.message))
                return
            path = file.get_path()
            if not path:
                self.status.set_text(tr('Choisir un emplacement local pour le fichier PDF.'))
                return
            destination = Path(path)
            if destination.suffix.lower() != ".pdf":
                destination = destination.with_suffix(".pdf")
            markdown = self.text()
            self.work(lambda: export_markdown_pdf(markdown, destination),
                      lambda exported: self.status.set_text(tr('PDF exporté : {0}', exported)))

        chooser.save(self, None, selected)

    def publish_synced(self, as_copy=False):
        try:
            note = self.outbox.save(self.text(), self.current, as_copy)
            self.notes = self.outbox.overlay(self.events.values())
            self.display(next(n for n in self.notes if n.pending and n.d == note.d))
            self.render_list()
            self.status.set_text(tr('Modifications enregistrées sur cet appareil, en attente de synchronisation.'))
            GLib.idle_add(lambda: (self.retry_pending(), False)[1])
        except Exception as exc:
            self.status.set_text(str(exc))

    def discard_pending(self):
        note = self.current
        if not note or not note.pending:
            return
        def discard():
            self.outbox.remove(note.d, note.event['id'])
            self.notes = self.outbox.overlay(self.events.values())
            self.display()
            self.render_list()
        self.confirm(tr('La version des relais sera conservée. Le texte local en attente sera supprimé de cet appareil.'), discard, tr('Abandonner'))

    def stop_sync(self):
        if self.sync_loop and self.sync_async_task:
            try:
                self.sync_loop.call_soon_threadsafe(self.sync_async_task.cancel)
            except RuntimeError:
                pass

    def retry_pending(self):
        if getattr(self, 'closing_clean', False):
            return False
        if self.identity is None or self.busy or self.syncing or not self.outbox or not any(n.pending and not n.conflicted for n in self.notes):
            return True
        if not self.network_monitor.get_network_available():
            return True
        self.syncing = True
        identity, outbox, events, relays = self.identity, self.outbox, dict(self.events), list(self.config['relays'])
        self.update_trash_controls()
        self.status.set_text(tr('Synchronisation des modifications en attente…'))
        def operation():
            async def run():
                self.sync_loop = asyncio.get_running_loop()
                self.sync_async_task = asyncio.current_task()
                try:
                    return await outbox.synchronize(events, relays, query_one, publish_update)
                finally:
                    self.sync_loop = self.sync_async_task = None
            return asyncio.run(run())
        future = self.sync_pool.submit(operation)
        def finish():
            self.syncing = False
            if self.identity is not identity or getattr(self, 'closing_clean', False):
                return False
            try:
                received, errors = future.result()
                self.events = compact_backups([*self.events.values(), *received.values()])
                self.store.save_events(identity.pubkey, list(self.events.values()))
                self.status.set_text(tr('Modifications synchronisées.') if not outbox.snapshot() else tr('En attente de synchronisation'))
            except BaseException as exc:
                if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                    raise
                self.status.set_text(tr('Modifications enregistrées localement, en attente de synchronisation.'))
                # A relay may have acknowledged before a later relay or disk failure.
                self.events = compact_backups([*self.events.values(), *self.store.events(identity.pubkey)])
            self.notes = outbox.overlay(self.events.values())
            self.render_list()
            # Refresh status for a saved note, never replace unsaved editor text.
            if self.current and not self.dirty:
                current = next((n for n in self.notes if n.d == self.current.d and n.pending == self.current.pending), None)
                if current is None:
                    current = next((n for n in self.notes if n.d == self.current.d), None)
                if current:
                    self.current = current
            self.update_trash_controls()
            return False
        future.add_done_callback(lambda _: GLib.idle_add(finish))
        return True

    def restore_previous(self):
        if self.current and self.current.pending or self.syncing:
            return
        if self.current and self.current.trashed:
            self.set_trashed(self.current, False)
            return
        def restore():
            if not self.current:
                self.status.set_text(tr('Sélectionner une note publiée.'))
                return
            previous = self.identity.previous(self.current, self.events.values())
            if previous is None:
                self.status.set_text(tr('Aucune version précédente disponible pour cette note.'))
                return
            self.loading = True
            self.editor.set_text(previous.markdown)
            self.loading = False
            self.changed(None)
            self.status.set_text(tr('Version précédente chargée. Vérifier puis cliquer sur Publier pour la restaurer.'))
        self.guard(restore)

    def update_pin_button(self):
        label = tr('Désépingler') if self.current and self.current.pinned else tr('Épingler')
        self.pin_button.set_icon_name("notestr-unpin-symbolic" if self.current and self.current.pinned else "notestr-pin-symbolic")
        self.pin_button.set_tooltip_text(label)
        self.pin_button.update_property([Gtk.AccessibleProperty.LABEL], [label])
        self.pin_button.set_sensitive(self.current is not None)

    def toggle_pin(self):
        if not self.current or self.current.trashed or self.current.pending or self.busy or self.syncing:
            return
        # Preserve the current editor and any unpublished changes.
        note = self.current
        def operation():
            event = self.identity.set_pinned(note, not note.pinned, self.events.values())
            good, errors = asyncio.run(across(self.config["relays"], publish_update, event, None))
            events = compact_backups([*self.events.values(), event])
            try:
                self.store.save_events(self.identity.pubkey, list(events.values()))
            except Exception:
                errors.append(tr('Épinglage accepté, mais écriture du cache local impossible.'))
            notes, _ = self.identity.notes(events.values())
            return events, notes, errors
        def success(result):
            self.events, self.notes, errors = result
            self.notes = self.outbox.overlay(self.events.values())
            self.current = next(n for n in self.notes if n.d == note.d)
            self.update_pin_button()
            self.render_list()
            self.status.set_text((tr('Note épinglée.') if self.current.pinned else tr('Note désépinglée.')) + "\n" + "\n".join(errors))
        self.work(operation, success)

    def delete(self):
        note = self.current
        if not note or note.pending or self.busy or self.syncing:
            return
        if not note.trashed:
            self.confirm(tr('La note publiée sera conservée dans la corbeille commune. Les modifications non publiées seront abandonnées.'),
                         lambda: self.set_trashed(note, True), tr('Déplacer'))
        else:
            self.confirm(tr('Une demande de suppression définitive sera envoyée aux relais. L’effacement de toutes les copies n’est pas garanti.'),
                         lambda: self.send(self.identity.delete(note), deleting=True), tr('Supprimer définitivement'))

    def send(self, event, deleting, backup=None):
        def operation():
            good, errors = asyncio.run(across(self.config["relays"], publish_update, event, backup))
            events = dict(self.events)
            events[event["id"]] = event
            if backup is not None:
                events[backup["id"]] = backup
            events = compact_backups(events.values())
            # La publication est déjà effective même si le disque local échoue.
            try:
                self.store.save_events(self.identity.pubkey, list(events.values()))
            except Exception:
                errors.append(tr('Publication acceptée, mais écriture du cache local impossible.'))
            notes, _ = self.identity.notes(events.values())
            return events, notes, len(good), errors
        def success(result):
            self.events, self.notes, count, errors = result
            self.notes = self.outbox.overlay(self.events.values())
            self.display(None if deleting else next(n for n in self.notes if n.event["id"] == event["id"]))
            self.render_list()
            self.status.set_text(tr('{0} acceptée par {1}/{2} relais. ', tr('Suppression') if deleting else tr('Publication'), count, len(self.config['relays']))
                                 + "\n".join(errors))
        self.work(operation, success)

    def show_license(self):
        dialog = Gtk.Window(title=tr("Licence GPLv3"), transient_for=self, modal=True,
                            default_width=720, default_height=640)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_start=16, margin_end=16, margin_top=16, margin_bottom=16)
        intro = Gtk.Label(label=tr("La licence GPLv3 garantit que les versions modifiées distribuées restent sous GPLv3. Aucune garantie n’est fournie."), wrap=True, xalign=0)
        box.append(intro)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        license_label = Gtk.Label(label=(ASSETS / "GPL-3.0.txt").read_text(encoding="utf-8"),
                                   selectable=True, xalign=0, yalign=0, wrap=True, wrap_mode=Gtk.WrapMode.WORD_CHAR)
        scroll.set_child(license_label)
        box.append(scroll)
        close = Gtk.Button(label=tr("Fermer"), halign=Gtk.Align.END)
        close.connect("clicked", lambda *_: dialog.close())
        box.append(close)
        dialog.set_child(box)
        dialog.present()

    def settings(self):
        self.guard(self.show_settings)

    def show_settings(self):
        dialog = Gtk.Window(title=tr('Compte et relais'), transient_for=self, modal=True, default_width=560, default_height=650)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_start=20, margin_end=20, margin_top=20, margin_bottom=20)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(box)
        dialog.set_child(scroll)
        box.append(Gtk.Label(label=tr("Version de l’application") + " : " + __version__, selectable=True))
        box.append(button(tr("Licence GPLv3"), self.show_license))
        box.append(Gtk.Label(label=tr("Langue"), xalign=0))
        language = Gtk.DropDown.new_from_strings(["Français", "English"])
        saved_language = self.store.read("preferences.json", {}).get("language", "fr")
        language.set_selected(1 if saved_language == "en" else 0)
        box.append(language)
        language_info = Gtk.Label(label=tr("La langue sera appliquée au prochain lancement."), wrap=True)
        box.append(language_info)
        def save_language():
            preferences = self.store.read("preferences.json", {})
            preferences["language"] = "en" if language.get_selected() == 1 else "fr"
            try:
                self.store.write("preferences.json", preferences)
                language_info.set_text(tr("Langue enregistrée. Relancez Notestr pour l’appliquer."))
            except (OSError, ValueError) as exc:
                language_info.set_text(str(exc))
        box.append(button(tr("Enregistrer la langue"), save_language))
        account = self.identity.keys.public_key_bech32() if self.identity else tr('Aucun compte ouvert')
        box.append(Gtk.Label(label=account, selectable=True, wrap=True))
        box.append(Gtk.Label(label=tr('Clé privée nsec ou hex (laisser vide pour garder le compte ouvert)'), wrap=True))
        secret = Gtk.PasswordEntry(show_peek_icon=True)
        box.append(secret)
        remember = Gtk.CheckButton(label=tr('Enregistrer cette clé dans le trousseau Linux'))
        remember.set_active(True)
        box.append(remember)
        box.append(Gtk.Label(label=tr('Relais wss://, un par ligne')))
        relays = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, height_request=100)
        relays.get_buffer().set_text("\n".join(self.config["relays"]))
        relay_scroll = Gtk.ScrolledWindow(min_content_height=100, max_content_height=160,
                                          propagate_natural_height=True)
        relay_scroll.set_child(relays)
        box.append(relay_scroll)
        info = Gtk.Label(wrap=True)
        def save_relays():
            try:
                buf = relays.get_buffer()
                urls = relays_from_text(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True))
                config = dict(self.config)
                config["relays"] = urls
                self.store.write("config.json", config)
                self.config = config
                info.set_text(tr("Relais enregistrés. Ils seront utilisés lors des prochaines synchronisations."))
            except (OSError, ValueError) as exc:
                info.set_text(tr("Impossible d’enregistrer les relais : ") + str(exc))
        box.append(button(tr("Enregistrer les relais"), save_relays))
        box.append(info)
        box.append(button(tr('Modifier le mot de passe'), lambda: self.show_change_password(dialog, info)))
        def apply():
            try:
                buf = relays.get_buffer()
                urls = relays_from_text(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True))
                identity = Identity(secret.get_text()) if secret.get_text().strip() else self.identity
                if identity is None:
                    raise ValueError(tr('Saisir la clé privée du compte Pages.'))
                if remember.get_active():
                    save_secret(identity)
                config = {"relays": urls}
                if remember.get_active():
                    config["pubkey"] = identity.pubkey
                self.store.write("config.json", config)
                self.config = config
                secret.set_text("")
                dialog.destroy()
                self.login(identity)
            except Exception as exc:
                info.set_text(tr('Enregistrement impossible. Vérifier la clé et le trousseau, ou décocher l’enregistrement pour utiliser la clé uniquement pendant cette session.\n') + str(exc))
        box.append(button(tr('Ouvrir le compte'), apply))
        box.append(button(tr('Annuler'), dialog.destroy))
        dialog.present()


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="fr.decentralia.NostrNotes")

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            set_language(Storage().read("preferences.json", {}).get("language", "fr"))
            window = Window(self)
        window.present()
