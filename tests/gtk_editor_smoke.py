"""Test graphique réel. Exécuter dans une session GTK (ou via gtk4-broadwayd)."""
import json
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from nostr_notes.app import Application, Window
from nostr_notes.core import Identity
from gi.repository import GLib, Gtk


def wait_for(condition, timeout=12):
    end = time.monotonic() + timeout
    context = GLib.MainContext.default()
    while time.monotonic() < end:
        while context.pending():
            context.iteration(False)
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError('Délai du test graphique dépassé')


def evaluate(editor, code):
    results = []
    editor._evaluate(code, results.append)
    wait_for(lambda: len(results) > 0)
    assert results[0] is not None
    return results[0]


def flush(editor):
    done = []
    editor.flush(lambda: done.append(True))
    wait_for(lambda: done)


with tempfile.TemporaryDirectory(prefix='notes-v2-test-') as data:
    os.environ['XDG_DATA_HOME'] = data
    app = Application()
    app.register(None)
    with patch.object(Window, 'initial_unlock', return_value=False), patch.object(Window, 'refresh'):
        win = Window(app)
        win.present()
        assert win.header.get_title_widget() is not None
        assert win.header_logo.get_paintable() is not None
        expected_actions = (
            (win.new_button, 'document-new-symbolic', 'Nouvelle note'),
            (win.refresh_button, 'view-refresh-symbolic', 'Actualiser'),
            (win.publish_button, 'mail-send-symbolic', 'Publier'),
            (win.delete_button, 'edit-delete-symbolic', 'Supprimer'),
            (win.pdf_button, 'document-save-as-symbolic', 'Exporter en PDF'),
            (win.settings_button, 'preferences-system-symbolic', 'Compte et relais'),
        )
        for action, icon_name, tooltip in expected_actions:
            assert action.get_icon_name() == icon_name
            assert action.get_tooltip_text() == tooltip
        win.login(Identity('0' * 63 + '1'))
        editor = win.editor
        wait_for(lambda: editor.ready or editor.failed)
        assert editor.ready, editor.notice.get_text()
        wait_for(lambda: not editor.pending_document)
        assert editor.visual_active
        # Un clic pendant le chargement affiche un avertissement temporaire,
        # qui doit disparaître dès que le document visuel est prêt.
        editor.set_text('# Synchronisation temporaire')
        assert editor.pending_document
        editor.flush(lambda: None)
        assert editor.notice.get_text().startswith('Synchronisation en cours')
        wait_for(lambda: not editor.pending_document)
        assert editor.notice.get_text().startswith('Le mode visuel peut normaliser')
        samples = ['# Titre\n\nCafé **gras** et *italique*.\n',
                   'Un lien [local](https://example.org).\n\n- un\n- deux\n',
                   '```python\nprint("bonjour")\n```\n\n> Une citation\n',
                   '<custom>HTML à conserver</custom>\n\n![image](https://example.org/image.png)\n']
        for sample in samples:
            editor.set_text(sample)
            wait_for(lambda: not editor.pending_document)
            flush(editor)
            assert editor.get_text() == sample
            editor.switch_mode(False)
            wait_for(lambda: not editor.visual_active)
            assert editor.get_text() == sample
            editor.switch_mode(True)
            wait_for(lambda: not editor.pending_document)
        editor.set_text('# Format\n\n**Texte gras**')
        wait_for(lambda: not editor.pending_document)
        assert evaluate(editor, "JSON.stringify(!!document.querySelector('.toastui-editor-ww-container h1'))")
        assert evaluate(editor, "JSON.stringify(!!document.querySelector('.toastui-editor-ww-container strong'))")
        editor.set_text('<script>window.noteExecuted = true</script>\n\n<img src="https://example.org/x" onerror="window.noteExecuted=true">')
        wait_for(lambda: not editor.pending_document)
        assert evaluate(editor, 'JSON.stringify(window.noteExecuted === undefined)')
        win.display()
        wait_for(lambda: not editor.pending_document)
        # Saisie native dans le contenteditable avec le bouton Gras activé.
        evaluate(editor, '''(() => {
          const el = document.querySelector('.toastui-editor-ww-container .ProseMirror');
          el.focus();
          document.querySelector('button.bold').click();
          document.execCommand('insertText', false, 'Dernière frappe ☕');
          return window.notesEditor.snapshot();
        })()''')
        flush(editor)
        assert '**Dernière frappe ☕**' in win.text(), repr(win.text())
        assert win.dirty
        assert evaluate(editor, 'JSON.stringify(typeof window.notesEditor)') == 'object'
        # Un fetch est refusé par la CSP avant toute requête réseau.
        evaluate(editor, '''(() => {
            window.blockedFetch = false;
            fetch('https://example.org/private').catch(() => { window.blockedFetch = true; });
            return JSON.stringify(true);
        })()''')
        wait_for(lambda: evaluate(editor, 'JSON.stringify(window.blockedFetch)'))
        assert editor.web.get_network_session().is_ephemeral()
        captured = []
        with patch.object(win, 'send', side_effect=lambda event, deleting: captured.append(event)):
            win.publish()
            wait_for(lambda: captured)
        notes, failures = win.identity.notes(captured)
        assert failures == 0 and 'Dernière frappe ☕' in notes[0].markdown
        # Un message JS tardif d'une autre note ne peut pas remplacer la note courante.
        previous_epoch = editor.epoch
        editor.set_text('Autre note')
        wait_for(lambda: not editor.pending_document)
        editor._accept({'epoch': previous_epoch, 'markdown': 'ancien texte'})
        assert editor.get_text() == 'Autre note'
        evaluate(editor, '''(() => {
          document.querySelector('.toastui-editor-ww-container .ProseMirror').focus();
          document.execCommand('undo');
          return window.notesEditor.snapshot();
        })()''')
        flush(editor)
        assert 'Dernière frappe' not in editor.get_text()
        # Régression : Entrée dans le visuel doit devenir un saut CommonMark explicite.
        win.display()
        wait_for(lambda: not editor.pending_document)
        evaluate(editor, '''(() => {
          document.querySelector('.toastui-editor-ww-container .ProseMirror').focus();
          document.execCommand('insertText', false, 'Gras');
          document.execCommand('insertParagraph');
          document.execCommand('insertText', false, 'Barré');
          document.execCommand('insertParagraph');
          document.execCommand('insertText', false, 'Italique');
          return window.notesEditor.snapshot();
        })()''')
        flush(editor)
        assert editor.get_text() == 'Gras  \nBarré  \nItalique', repr(editor.get_text())
        saved_breaks = editor.get_text()
        editor.switch_mode(False)
        wait_for(lambda: not editor.visual_active)
        editor.switch_mode(True)
        wait_for(lambda: not editor.pending_document)
        flush(editor)
        assert editor.get_text() == saved_breaks
        assert evaluate(editor, "JSON.stringify(document.querySelector('.toastui-editor-ww-container').innerText.includes('Gras'))")
        # Vérifier le rendu géométrique, pas seulement la chaîne source restituée.
        editor.set_text('**Gras**  \n~~Barré~~  \n*Italique*')
        wait_for(lambda: not editor.pending_document)
        positions = evaluate(editor, '''JSON.stringify(
          ['strong', 's, del', 'em'].map(tag =>
            document.querySelector('.toastui-editor-ww-container').querySelector(tag).getBoundingClientRect().y)
        )''')
        assert positions[0] < positions[1] < positions[2], positions
        # Publication directement depuis le mode Markdown, sans ligne vide.
        editor.switch_mode(False)
        wait_for(lambda: not editor.visual_active)
        editor.buffer.set_text('Je suis content\nje suis pas content')
        captured = []
        with patch.object(win, 'send', side_effect=lambda event, deleting: captured.append(event)):
            win.publish()
            wait_for(lambda: captured)
        notes, failures = win.identity.notes(captured)
        from markdown_it import MarkdownIt
        assert 'Je suis content<br' in MarkdownIt().render(notes[0].markdown)
        win.display(notes[0])
        editor.switch_mode(True)
        wait_for(lambda: not editor.pending_document)
        paragraphs = evaluate(editor, '''JSON.stringify(
          Array.from(document.querySelectorAll('.toastui-editor-ww-container p'))
            .map(el => ({text: el.textContent, y: el.getBoundingClientRect().y}))
        )''')
        assert paragraphs[0]['text'] == 'Je suis content', paragraphs
        assert paragraphs[1]['text'] == 'je suis pas content', paragraphs
        assert paragraphs[1]['y'] > paragraphs[0]['y'], paragraphs
        win.close_clean()
        print('GTK/WebKit OK : modes, conservation exacte, frappe, publication chiffrée, CSP et révisions.')
