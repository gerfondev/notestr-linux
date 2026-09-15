"""Interface GTK4/libadwaita. Réseau et crypto hors du thread graphique."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk

from .core import Identity, Note, valid_event
from .editor import MarkdownEditor
from .lock import PasswordLock
from .relay import across, publish_one, query_one
from .storage import Storage, load_secret, save_secret, relays_from_text


def button(label, callback):
    widget = Gtk.Button(label=label)
    widget.connect("clicked", lambda _: callback())
    return widget


class Window(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Notes privées Nostr", default_width=1000, default_height=700)
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.identity = None
        self.events = {}
        self.notes = []
        self.current = None
        self.draft_d = None
        self.dirty = False
        self.loading = False
        self.busy = False
        self.store = Storage()
        self.password_lock = PasswordLock(self.store)
        self.config = self.store.config()
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(root)
        header = Adw.HeaderBar()
        root.append(header)
        self.controls = Gtk.Box(spacing=6)
        header.pack_start(self.controls)
        self.controls.append(button("Nouvelle", self.new_note))
        self.controls.append(button("Actualiser", self.refresh))
        self.controls.append(button("Publier", self.publish))
        self.controls.append(button("Supprimer", self.delete))
        self.controls.set_sensitive(False)
        self.settings_button = button("Compte et relais", self.settings)
        header.pack_end(self.settings_button)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL, position=280, vexpand=True)
        root.append(paned)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, width_request=220)
        self.search = Gtk.SearchEntry(placeholder_text="Rechercher dans les notes")
        self.search.connect("search-changed", lambda _: self.render_list())
        sidebar.append(self.search)
        self.listbox = Gtk.ListBox(selection_mode=Gtk.SelectionMode.NONE)
        self.listbox.connect("row-activated", self.select_row)
        scroll = Gtk.ScrolledWindow(vexpand=True)
        scroll.set_child(self.listbox)
        sidebar.append(scroll)
        paned.set_start_child(sidebar)
        self.editor = MarkdownEditor(self.changed)
        self.editor.set_sensitive(False)
        paned.set_end_child(self.editor)
        self.status = Gtk.Label(label="Importer une clé privée pour commencer.", xalign=0,
                                wrap=True, selectable=True, margin_start=12, margin_end=12,
                                margin_top=8, margin_bottom=8)
        root.append(self.status)
        self.connect("close-request", self.close_requested)
        GLib.idle_add(self.initial_unlock)

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
        return dialog, box

    def close_from_password_window(self, dialog):
        dialog.destroy()
        self.close_clean()

    def show_password_setup(self):
        dialog, box = self.password_window("Créer le mot de passe Notestr")
        box.append(Gtk.Label(
            label="Choisissez le mot de passe demandé à chaque ouverture de Notestr.",
            wrap=True, xalign=0))
        first = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Mot de passe (8 caractères minimum)")
        second = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Confirmer le mot de passe")
        box.append(first)
        box.append(second)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)

        def create():
            try:
                if first.get_text() != second.get_text():
                    raise ValueError("Les deux mots de passe sont différents.")
                self.password_lock.set_password(first.get_text())
                first.set_text("")
                second.set_text("")
                dialog.destroy()
                self.initial_login()
            except Exception as exc:
                info.set_text(str(exc) or type(exc).__name__)

        create_button = button("Créer et ouvrir", create)
        box.append(create_button)
        box.append(button("Quitter", lambda: self.close_from_password_window(dialog)))
        first.connect("activate", lambda _: second.grab_focus())
        second.connect("activate", lambda _: create())
        dialog.connect("close-request", lambda _: self.close_from_password_window(dialog) or True)
        dialog.present()
        first.grab_focus()

    def show_unlock(self):
        dialog, box = self.password_window("Déverrouiller Notestr")
        box.append(Gtk.Label(label="Saisissez le mot de passe de l’application.", wrap=True, xalign=0))
        secret = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Mot de passe")
        box.append(secret)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)
        attempts = {"count": 0}

        def enable_again():
            unlock_button.set_sensitive(True)
            info.set_text("Vous pouvez réessayer.")
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
                info.set_text("Trop de tentatives. Nouvel essai dans 30 secondes.")
                GLib.timeout_add_seconds(30, enable_again)
            else:
                info.set_text("Mot de passe incorrect.")

        unlock_button = button("Déverrouiller", unlock)
        box.append(unlock_button)
        box.append(button("Quitter", lambda: self.close_from_password_window(dialog)))
        secret.connect("activate", lambda _: unlock())
        dialog.connect("close-request", lambda _: self.close_from_password_window(dialog) or True)
        dialog.present()
        secret.grab_focus()

    def show_change_password(self, parent, feedback):
        dialog, box = self.password_window("Modifier le mot de passe", parent)
        box.append(Gtk.Label(
            label="Saisissez le mot de passe actuel, puis choisissez le nouveau.",
            wrap=True, xalign=0))
        current = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Mot de passe actuel")
        new = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Nouveau mot de passe (8 caractères minimum)")
        confirmation = Gtk.PasswordEntry(show_peek_icon=True, placeholder_text="Confirmer le nouveau mot de passe")
        box.append(current)
        box.append(new)
        box.append(confirmation)
        info = Gtk.Label(wrap=True, xalign=0)
        box.append(info)

        def change():
            try:
                if new.get_text() != confirmation.get_text():
                    raise ValueError("Les deux nouveaux mots de passe sont différents.")
                self.password_lock.change_password(current.get_text(), new.get_text())
                current.set_text("")
                new.set_text("")
                confirmation.set_text("")
                dialog.destroy()
                feedback.set_text("Le mot de passe de l’application a été modifié.")
            except Exception as exc:
                current.set_text("")
                info.set_text(str(exc) or type(exc).__name__)
                current.grab_focus()

        box.append(button("Enregistrer le nouveau mot de passe", change))
        box.append(button("Annuler", dialog.destroy))
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

    def work(self, operation, success):
        if self.busy:
            return
        self.busy = True
        self.controls.set_sensitive(False)
        self.settings_button.set_sensitive(False)
        self.editor.set_sensitive(False)
        self.listbox.set_sensitive(False)
        self.status.set_text("Opération en cours…")
        future = self.pool.submit(operation)
        def finish():
            self.busy = False
            self.controls.set_sensitive(self.identity is not None)
            self.settings_button.set_sensitive(True)
            self.editor.set_sensitive(self.identity is not None)
            self.listbox.set_sensitive(True)
            try:
                success(future.result())
            except Exception as exc:
                self.status.set_text(str(exc) or type(exc).__name__)
            return False
        future.add_done_callback(lambda _: GLib.idle_add(finish))

    def text(self):
        return self.editor.get_text()

    def changed(self, _):
        if not self.loading:
            self.dirty = True
            self.set_title("Notes privées Nostr • modifications non publiées")

    def display(self, note=None):
        self.current = note
        self.draft_d = None
        self.loading = True
        self.editor.set_text(note.markdown if note else "")
        self.loading = False
        self.dirty = False
        self.set_title("Notes privées Nostr")

    def confirm(self, text, action, label="Abandonner les modifications"):
        dialog = Gtk.MessageDialog(transient_for=self, modal=True, text=text,
                                   message_type=Gtk.MessageType.WARNING)
        dialog.add_button("Annuler", Gtk.ResponseType.CANCEL)
        dialog.add_button(label, Gtk.ResponseType.ACCEPT)
        dialog.set_default_response(Gtk.ResponseType.CANCEL)
        def response(widget, value):
            widget.destroy()
            if value == Gtk.ResponseType.ACCEPT:
                action()
        dialog.connect("response", response)
        dialog.present()

    def guard(self, action):
        if self.busy:
            return
        def checked():
            if self.dirty:
                self.confirm("Des modifications ne sont pas publiées. Les abandonner ?", action)
            else:
                action()
        self.editor.flush(checked)

    def close_requested(self, _):
        if getattr(self, "closing_clean", False):
            self.pool.shutdown(wait=False)
            return False
        if self.busy:
            self.status.set_text("Attendre la fin de l’opération avant de fermer.")
            return True
        def checked():
            if self.dirty:
                self.confirm("Fermer et perdre les modifications non publiées ?", self.close_clean)
            else:
                self.close_clean()
        self.editor.flush(checked)
        return True

    def close_clean(self):
        self.dirty = False
        self.closing_clean = True
        self.close()

    def new_note(self):
        self.guard(lambda: self.display())

    def select_row(self, _, row):
        self.guard(lambda: self.display(row.note))

    def render_list(self):
        child = self.listbox.get_first_child()
        while child:
            following = child.get_next_sibling()
            self.listbox.remove(child)
            child = following
        query = self.search.get_text().casefold()
        for note in self.notes:
            if query not in note.markdown.casefold():
                continue
            row = Gtk.ListBoxRow()
            row.note = note
            row.set_child(Gtk.Label(label=note.title, xalign=0, ellipsize=3,
                                    margin_start=12, margin_end=12, margin_top=10, margin_bottom=10))
            self.listbox.append(row)

    def login(self, identity):
        self.identity = identity
        self.events = {e["id"]: e for e in self.store.events(identity.pubkey)
                       if valid_event(e, identity.pubkey)}
        self.notes, unreadable = identity.notes(self.events.values())
        self.display()
        self.render_list()
        self.controls.set_sensitive(True)
        self.editor.set_sensitive(True)
        self.status.set_text(f"{len(self.notes)} note(s) en cache · {unreadable} indéchiffrable(s).")
        self.refresh()

    def refresh(self):
        self.guard(self.do_refresh)

    def do_refresh(self):
        def operation():
            good, errors = asyncio.run(across(self.config["relays"], query_one, self.identity.pubkey))
            events = dict(self.events)
            for items in good.values():
                events.update((e["id"], e) for e in items)
            notes, unreadable = self.identity.notes(events.values())
            self.store.save_events(self.identity.pubkey, list(events.values()))
            return events, notes, unreadable, errors
        def success(result):
            events, notes, unreadable, errors = result
            selected = self.current.d if self.current else None
            self.events, self.notes = events, notes
            self.display(next((n for n in notes if n.d == selected), None))
            self.render_list()
            self.status.set_text(f"{len(notes)} note(s) · {unreadable} indéchiffrable(s). " + "\n".join(errors))
        self.work(operation, success)

    def publish(self):
        if not self.identity or self.busy:
            return
        self.editor.flush(self.publish_synced)

    def publish_synced(self):
        try:
            event = self.identity.save(self.text(), self.current, self.draft_d)
            # Conserver le même identifiant après un échec de publication.
            if self.current is None:
                self.draft_d = event["tags"][0][1]
        except Exception as exc:
            self.status.set_text(str(exc))
            return
        self.send(event, deleting=False)

    def delete(self):
        if not self.current:
            self.status.set_text("Sélectionner une note publiée à supprimer.")
            return
        self.confirm("Demander la suppression de cette note sur les relais ? Les éventuelles modifications seront abandonnées. "
                     "Nostr ne garantit pas l’effacement de toutes les copies.",
                     lambda: self.send(self.identity.delete(self.current), deleting=True),
                     "Supprimer")

    def send(self, event, deleting):
        def operation():
            good, errors = asyncio.run(across(self.config["relays"], publish_one, event))
            events = dict(self.events)
            events[event["id"]] = event
            # La publication est déjà effective même si le disque local échoue.
            try:
                self.store.save_events(self.identity.pubkey, list(events.values()))
            except Exception:
                errors.append("Publication acceptée, mais écriture du cache local impossible.")
            notes, _ = self.identity.notes(events.values())
            return events, notes, len(good), errors
        def success(result):
            self.events, self.notes, count, errors = result
            self.display(None if deleting else next(n for n in self.notes if n.event["id"] == event["id"]))
            self.render_list()
            self.status.set_text(f"{'Suppression' if deleting else 'Publication'} acceptée par {count}/{len(self.config['relays'])} relais. "
                                 + "\n".join(errors))
        self.work(operation, success)

    def settings(self):
        self.guard(self.show_settings)

    def show_settings(self):
        dialog = Gtk.Window(title="Compte et relais", transient_for=self, modal=True, default_width=560)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                      margin_start=20, margin_end=20, margin_top=20, margin_bottom=20)
        dialog.set_child(box)
        account = self.identity.keys.public_key_bech32() if self.identity else "Aucun compte ouvert"
        box.append(Gtk.Label(label=account, selectable=True, wrap=True))
        box.append(Gtk.Label(label="Clé privée nsec ou hex (laisser vide pour garder le compte ouvert)", wrap=True))
        secret = Gtk.PasswordEntry(show_peek_icon=True)
        box.append(secret)
        remember = Gtk.CheckButton(label="Enregistrer cette clé dans le trousseau Linux")
        remember.set_active(True)
        box.append(remember)
        box.append(Gtk.Label(label="Relais wss://, un par ligne"))
        relays = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, height_request=100)
        relays.get_buffer().set_text("\n".join(self.config["relays"]))
        box.append(relays)
        info = Gtk.Label(wrap=True)
        box.append(info)
        box.append(button("Modifier le mot de passe", lambda: self.show_change_password(dialog, info)))
        def apply():
            try:
                buf = relays.get_buffer()
                urls = relays_from_text(buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True))
                identity = Identity(secret.get_text()) if secret.get_text().strip() else self.identity
                if identity is None:
                    raise ValueError("Saisir la clé privée du compte Pages.")
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
                info.set_text("Enregistrement impossible. Vérifier la clé et le trousseau, ou décocher l’enregistrement "
                              "pour utiliser la clé uniquement pendant cette session.\n" + str(exc))
        box.append(button("Ouvrir le compte", apply))
        box.append(button("Annuler", dialog.destroy))
        dialog.present()


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="fr.decentralia.NostrNotes")

    def do_activate(self):
        window = self.get_active_window()
        if window is None:
            window = Window(self)
        window.present()
