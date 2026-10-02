"""Isolated GTK language/settings regression, no account or network access."""
import os
import tempfile
import time
from unittest.mock import patch
from gi.repository import GLib, Gio, Adw, Gtk
from nostr_notes.app import Application, Window
from nostr_notes import __version__
from nostr_notes.i18n import get_language, set_language
from nostr_notes.storage import Storage


def wait(condition):
    end = time.monotonic() + 20
    context = GLib.MainContext.default()
    while time.monotonic() < end:
        while context.pending():
            context.iteration(False)
        if condition():
            return
        time.sleep(.02)
    raise AssertionError('GTK language test timed out')


def children(widget):
    yield widget
    child = widget.get_first_child()
    while child:
        yield from children(child)
        child = child.get_next_sibling()


def evaluate(editor, script):
    result = []
    editor._evaluate(script, result.append)
    wait(lambda: len(result) > 0)
    return result[0]


Adw.init()
with tempfile.TemporaryDirectory(prefix='notestr-language-test-') as data:
    os.environ['XDG_DATA_HOME'] = data
    store = Storage()
    store.write('preferences.json', {'language': 'en'})
    app = Application()
    app.set_application_id('fr.decentralia.NostrNotes.LanguageTest')
    app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
    app.register(None)
    with patch.object(Window, 'initial_unlock', return_value=False):
        app.activate()
        win = app.get_active_window()
        assert get_language() == 'en'
        assert win.refresh_button.get_tooltip_text() == 'Refresh'
        assert win.settings_button.get_tooltip_text() == 'Account and relays'
        editor = win.editor
        wait(lambda: editor.ready and not editor.pending_document)
        source = '# Réglages\n\n```\nCopier ce texte inchangé\n```\n'
        editor.set_text(source)
        wait(lambda: not editor.pending_document)
        assert evaluate(editor, "JSON.stringify(document.documentElement.lang)") == 'en'
        wait(lambda: evaluate(editor, "JSON.stringify(document.querySelector('.notes-copy-code')?.textContent)") == 'Copy')
        assert evaluate(editor, "JSON.stringify(document.querySelector('button.bold').getAttribute('aria-label'))").startswith('Bold')
        done = []
        editor.flush(lambda: done.append(True))
        wait(lambda: done)
        assert editor.get_text() == source
        win.show_settings()
        dialog = next(w for w in Gtk.Window.get_toplevels() if w is not win and w.get_title() == 'Account and relays')
        widgets = list(children(dialog))
        assert any(isinstance(w, Gtk.Label) and w.get_text() == 'App version : ' + __version__ for w in widgets)
        dropdown = next(w for w in widgets if isinstance(w, Gtk.DropDown))
        dropdown.set_selected(0)
        next(w for w in widgets if isinstance(w, Gtk.Button) and w.get_label() == 'Save language').emit('clicked')
        assert Storage().read('preferences.json', {})['language'] == 'fr'
        assert editor.get_text() == source
        # Saving the preference does not switch or replace an active editor.
        assert get_language() == 'en'
        dialog.destroy()
        win.destroy()
        app.activate()
        restarted = app.get_active_window()
        assert get_language() == 'fr'
        assert restarted.refresh_button.get_tooltip_text() == 'Actualiser'
        restarted.destroy()
set_language('fr')
print('PASS: English settings/version/editor, French preference restored on next activation, note unchanged')
