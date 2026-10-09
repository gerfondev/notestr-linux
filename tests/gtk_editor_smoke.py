"""Test graphique réel. Exécuter dans une session GTK (ou via gtk4-broadwayd)."""
import json
import io
import os
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from nostr_notes.app import Application, Window
from nostr_notes.core import Identity
from gi.repository import GLib, Gtk, Adw, Gio
from PIL import Image


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


def visible_image_loaded(editor, width):
    return evaluate(editor, "JSON.stringify([...document.querySelectorAll('.toastui-editor-ww-container img')].some(i=>{const r=i.getBoundingClientRect();return i.naturalWidth===" + str(width) + "&&r.width>0&&r.height>0&&getComputedStyle(i).display!=='none'}))") is True


Adw.init()
with tempfile.TemporaryDirectory(prefix='notes-v2-test-') as data:
    os.environ['XDG_DATA_HOME'] = data
    app = Application()
    app.set_application_id("fr.decentralia.NostrNotes.Test")
    app.set_flags(Gio.ApplicationFlags.NON_UNIQUE)
    app.register(None)
    with patch.object(Window, 'initial_unlock', return_value=False), patch.object(Window, 'do_refresh'), patch.object(Window, 'retry_pending', return_value=False):
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
        assert editor.image_button.get_icon_name() == 'insert-image-symbolic'
        assert editor.image_button.get_tooltip_text() == 'Insérer une image'
        wait_for(lambda: editor.ready or editor.failed)
        assert editor.ready, editor.notice.get_text()
        wait_for(lambda: not editor.pending_document)
        assert editor.visual_active
        # Encrypted attachment references stay in Markdown while WebKit displays
        # only the host-provided, decrypted in-memory image bytes.
        jpeg = io.BytesIO()
        Image.new('RGB', (3, 2), 'navy').save(jpeg, format='JPEG')
        image_ref = 'notestr-image://' + 'a' * 64 + '?server=https%3A%2F%2Fblossom.yakihonne.com&key=' + 'A' * 43 + '&nonce=' + 'A' * 16 + '&mime=image%2Fjpeg'
        image_markdown = '![Image](' + image_ref + ')'
        image_note = (
            '# 🧑‍💻 Evolution Notestr\n\n'
            '~~\\- ancienne ligne~~  \n'
            '- insertion d\'image\n'
            + image_markdown + '\n'
        )
        with patch('nostr_notes.app.load_image_for_display', return_value=jpeg.getvalue()):
            editor.set_text(image_note)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: visible_image_loaded(editor, 3))
            flush(editor)
            assert editor.get_text() == image_note
            snapshot_before_view = editor.get_text()
            evaluate(editor, "JSON.stringify((() => { const image=[...document.querySelectorAll('.toastui-editor-ww-container img')].find(i=>i.naturalWidth===3); image.click(); return !!document.querySelector('.notes-image-lightbox img'); })())")
            wait_for(lambda: evaluate(editor, "JSON.stringify(!!document.querySelector('.notes-image-lightbox img'))"))
            assert evaluate(editor, "JSON.stringify(document.querySelector('.notes-image-lightbox')?.getAttribute('aria-modal')==='true')")
            evaluate(editor, "JSON.stringify(document.querySelector('.notes-image-lightbox-zoom-in').click() ?? true)")
            wait_for(lambda: evaluate(editor, "JSON.stringify(document.querySelector('.notes-image-lightbox-zoom-level')?.textContent==='150%')"))
            evaluate(editor, """JSON.stringify((() => {
              const overlay=document.querySelector('.notes-image-lightbox'), image=overlay.querySelector('img'), r=image.getBoundingClientRect();
              const common={pointerType:'mouse',bubbles:true,cancelable:true};
              image.dispatchEvent(new PointerEvent('pointerdown',{...common,pointerId:71,clientX:r.left+r.width/2,clientY:r.top+r.height/2}));
              overlay.dispatchEvent(new PointerEvent('pointermove',{...common,pointerId:71,clientX:r.left+r.width/2+50,clientY:r.top+r.height/2}));
              overlay.dispatchEvent(new PointerEvent('pointerup',{...common,pointerId:71,clientX:r.left+r.width/2+50,clientY:r.top+r.height/2}));
              return image.style.transform;
            })())""")
            assert evaluate(editor, "JSON.stringify(/translate3d\\((?!0(?:px)?[, ])[-\\d.]+px/.test(document.querySelector('.notes-image-lightbox img').style.transform))")
            evaluate(editor, "document.querySelector('.notes-image-lightbox-zoom-reset').click(); true")
            wait_for(lambda: evaluate(editor, "JSON.stringify(document.querySelector('.notes-image-lightbox-zoom-level')?.textContent==='100%')"))
            assert editor.get_text() == snapshot_before_view
            evaluate(editor, "JSON.stringify(document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true})))")
            wait_for(lambda: not evaluate(editor, "JSON.stringify(!!document.querySelector('.notes-image-lightbox'))"))
            evaluate(editor, "JSON.stringify((() => { const image=[...document.querySelectorAll('.toastui-editor-ww-container img')].find(i=>i.naturalWidth===3); image.click(); document.querySelector('.notes-image-lightbox').click(); return !document.querySelector('.notes-image-lightbox'); })())")
            assert editor.get_text() == snapshot_before_view
            # A correctly padded base64url key must not be silently dropped
            # by the visual parser before the native decoder can validate it.
            padded_ref = image_ref.replace('&key=' + 'A' * 43 + '&nonce=', '&key=' + 'A' * 43 + '%3D&nonce=')
            padded_markdown = '![Image](' + padded_ref + ')'
            editor.set_text(padded_markdown)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: visible_image_loaded(editor, 3))
            flush(editor)
            assert editor.get_text() == padded_markdown
            # Une image choisie au curseur doit être insérée à cet endroit,
            # et rester visible dans le même document visuel.
            editor.set_text('# Placement\n\navant\n\naprès')
            wait_for(lambda: not editor.pending_document)
            assert evaluate(editor, 'JSON.stringify(window.notesEditor.rememberInsertionPoint(20,20))') is True
            inserted = evaluate(editor, "JSON.stringify(window.notesEditor.insertImageReference(" + json.dumps(image_markdown) + "))")
            assert inserted is True, inserted
            wait_for(lambda: visible_image_loaded(editor, 3))
            flush(editor)
            assert editor.get_text().index(image_markdown) < editor.get_text().index('après'), repr(editor.get_text())
            editor.switch_mode(False)
            wait_for(lambda: not editor.visual_active)
            assert image_ref in editor.get_text()
            editor.switch_mode(True)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: visible_image_loaded(editor, 3))
        editor.switch_mode(False)
        wait_for(lambda: not editor.visual_active)
        editor.buffer.set_text('avant\naprès')
        start = editor.buffer.get_iter_at_offset(len('avant\n'))
        editor.image_insert_start = editor.buffer.create_mark(None, start, True)
        editor.image_insert_end = editor.buffer.create_mark(None, start, False)
        editor.insert_image_reference(image_markdown)
        assert editor.get_text().index(image_markdown) < editor.get_text().index('après'), repr(editor.get_text())
        editor.set_text('')
        editor.switch_mode(True)
        wait_for(lambda: not editor.pending_document)
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
        # Copier doit préserver le texte exact du bloc et le Markdown de la note.
        sample = '```python\nprint("Café ☕")\n  # espaces\n```\n\n```\nsecond bloc\n```\n'
        editor.set_text(sample)
        wait_for(lambda: not editor.pending_document)
        button_count = evaluate(editor, "JSON.stringify(document.querySelectorAll('.notes-copy-code').length)")
        assert button_count == 2
        assert evaluate(editor, "JSON.stringify(document.querySelector('.notes-copy-code').textContent)") == 'Copier'
        for index, expected in enumerate(('print("Café ☕")\n  # espaces', 'second bloc')):
            evaluate(editor, f"JSON.stringify(document.querySelectorAll('.notes-copy-code')[{index}].click() ?? true)")
            copied = []
            clipboard = editor.get_clipboard()
            clipboard.read_text_async(None, lambda cb, result: copied.append(cb.read_text_finish(result)))
            wait_for(lambda: bool(copied))
            assert copied[0] == expected, repr(copied[0])
            flush(editor)
            assert editor.get_text() == sample
        assert evaluate(editor, "JSON.stringify(!document.querySelector('.toastui-editor-ww-code-block-language'))")
        # L’ajout du bouton ne doit pas empêcher l’édition du code.
        evaluate(editor, """(() => {
          const code = document.querySelector('.toastui-editor-ww-code-block code');
          const range = document.createRange();
          range.selectNodeContents(code);
          range.collapse(false);
          const selection = window.getSelection();
          selection.removeAllRanges();
          selection.addRange(range);
          code.closest('.ProseMirror').focus();
          document.execCommand('insertText', false, ' ajouté');
          return window.notesEditor.snapshot();
        })()""")
        flush(editor)
        assert '# espaces ajouté' in editor.get_text()
        assert 'Copier' not in editor.get_text()
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
        with patch.object(win.outbox, 'save', wraps=win.outbox.save) as saved:
            win.publish()
            wait_for(lambda: saved.called)
        captured = [win.current.event]
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
        if not positions[0] < positions[1] < positions[2]: print('Break render diagnostic:', evaluate(editor, "JSON.stringify({html:document.querySelector('.toastui-editor-ww-container .ProseMirror')?.innerHTML,markdown:window.notesEditor.snapshot()})"), flush=True)
        assert positions[0] < positions[1] < positions[2], positions
        # Publication directement depuis le mode Markdown, sans ligne vide.
        editor.switch_mode(False)
        wait_for(lambda: not editor.visual_active)
        editor.buffer.set_text('Je suis content\nje suis pas content')
        with patch.object(win.outbox, 'save', wraps=win.outbox.save) as saved:
            win.publish()
            wait_for(lambda: saved.called)
        captured = [win.current.event]
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
        # Restaurer charge un brouillon sans publier et conserve la note courante.
        with patch('nostr_notes.core.time.time', return_value=100):
            old = win.identity.save('Ancienne version')
        original = win.identity.notes([old])[0][0]
        with patch('nostr_notes.core.time.time', return_value=101):
            updated = win.identity.save('Version actuelle', original)
        backup = win.identity.backup(original, updated)
        current = win.identity.notes([updated])[0][0]
        win.events = {e['id']: e for e in (updated, backup)}
        win.notes = [current]
        win.display(current)
        wait_for(lambda: not editor.pending_document)
        win.restore_previous()
        wait_for(lambda: win.dirty and not editor.pending_document)
        flush(editor)
        assert editor.get_text() == 'Ancienne version'
        assert win.current == current
        with patch.object(win.outbox, 'save', wraps=win.outbox.save) as saved:
            win.publish()
            wait_for(lambda: saved.called)
        row = next(r for r in win.outbox.snapshot() if r['update']['id'] == win.current.event['id'])
        restored, replaced_backup = row['update'], row['backup']
        assert win.identity.notes([restored])[0][0].markdown == 'Ancienne version'
        assert win.identity.previous(current, [replaced_backup]).markdown == 'Version actuelle'
        # Pinning changes the list, but preserves a dirty editor and note timestamp.
        from unittest.mock import AsyncMock
        win.store.write(win.outbox.name, [])
        win.current = current
        win.notes = [current]
        win.changed(None)
        win.update_trash_controls()
        original_text = editor.get_text()
        original_date = current.event['created_at']
        with patch('nostr_notes.app.across', AsyncMock(return_value=({'synthetic': True}, []))):
            win.pin_button.emit('clicked')
            wait_for(lambda: not win.busy)
        assert win.current.pinned and win.current.event['created_at'] == original_date
        assert win.pin_button.get_tooltip_text() == 'Désépingler'
        assert win.pin_button.get_icon_name() == 'notestr-unpin-symbolic'
        assert Gtk.IconTheme.get_for_display(win.get_display()).has_icon('notestr-unpin-symbolic')
        assert win.dirty and editor.get_text() == original_text
        wait_for(lambda: int(time.time()) > max(e['created_at'] for e in win.events.values()))
        with patch('nostr_notes.app.across', AsyncMock(return_value=({'synthetic': True}, []))):
            win.pin_button.emit('clicked')
            wait_for(lambda: not win.busy)
        assert not win.current.pinned and win.dirty
        assert win.pin_button.get_icon_name() == 'notestr-pin-symbolic'
        assert editor.get_text() == original_text
        assert evaluate(editor, "JSON.stringify(DOMPurify.version)") == '3.4.16'
        assert 'onerror' not in evaluate(editor, "JSON.stringify(DOMPurify.sanitize('<img src=x onerror=alert(1)>'))")
        win.close_clean()
        print('GTK/WebKit OK : modes, conservation exacte, frappe, publication chiffrée, CSP et révisions.')
