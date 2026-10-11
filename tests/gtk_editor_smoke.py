"""Test graphique réel. Exécuter dans une session GTK (ou via gtk4-broadwayd)."""
import json
import io
import os
from pathlib import Path
import tempfile
import threading
import time
from unittest.mock import patch
from dataclasses import replace

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
        assert not editor.image_button.get_visible()
        assert evaluate(editor, "JSON.stringify((() => { const button=document.querySelector('.notes-insert-image'); const table=document.querySelector('.toastui-editor-toolbar-icons.table')?.closest('button'); return !!button && button.previousElementSibling===table && button.getAttribute('aria-label')==='Insérer une image'; })())")
        image_picker_calls=[]
        editor.on_insert_image=lambda: image_picker_calls.append(True)
        assert evaluate(editor, "window.notesEditor.rememberInsertionPoint()")
        evaluate(editor, "document.querySelector('.notes-insert-image').click(); true")
        wait_for(lambda: bool(image_picker_calls))
        editor.on_insert_image=win.insert_image
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
            # The native bridge calls rememberInsertionPoint() a second time
            # after opening the file chooser. That confirmation must preserve
            # the range captured before focus was lost.
            assert evaluate(editor, 'JSON.stringify(window.notesEditor.rememberInsertionPoint(20,20))') is True
            assert evaluate(editor, 'JSON.stringify(window.notesEditor.rememberInsertionPoint())') is True
            with patch('nostr_notes.app.load_image_for_display', return_value=jpeg.getvalue()):
                inserted = evaluate(editor, "JSON.stringify(window.notesEditor.insertImageReference(" + json.dumps(image_markdown) + "))")
                assert inserted is True, inserted
                wait_for(lambda: visible_image_loaded(editor, 3))
            flush(editor)
            placed_text = editor.get_text()
            assert placed_text.index('avant') < placed_text.index(image_markdown) < placed_text.index('après'), repr(placed_text)
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
        try:
            wait_for(lambda: evaluate(editor, "JSON.stringify(document.querySelectorAll('.notes-copy-code').length)") == 2)
        except AssertionError:
            print('CODE-BUTTON-DIAG', evaluate(editor, "JSON.stringify({buttons:document.querySelectorAll('.notes-copy-code').length,blocks:document.querySelectorAll('.toastui-editor-ww-container .toastui-editor-ww-code-block').length,editable:[...document.querySelectorAll('[contenteditable]')].map(e=>e.getAttribute('contenteditable')),text:document.querySelector('.toastui-editor-ww-container')?.innerText})"))
            raise
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
        # A locked note remains scrollable in visual and Markdown read-only modes.
        long_markdown = ('# Note verrouillée\n\n' + '\n\n'.join(f'Paragraphe {n} — contenu de test.' for n in range(80))
                         + '\n\n- [ ] Tâche protégée\n\n' + image_markdown)
        locked_note = replace(current, markdown=long_markdown, locked=True)
        win.current = locked_note
        win.notes = [locked_note]
        with patch('nostr_notes.app.load_image_for_display', return_value=jpeg.getvalue()):
            win.display(locked_note)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: visible_image_loaded(editor, 3))
            locked_image = evaluate(editor, '''JSON.stringify((() => {
              const image=[...document.querySelectorAll('.toastui-editor-ww-container img:not(.ProseMirror-separator)')]
                .find(item=>item.naturalWidth===3);
              return image && image.getAttribute('src').startsWith('data:image/jpeg;base64,')
                && getComputedStyle(image).maxWidth==='100%';
            })())''')
            assert locked_image is True
        # Regression for notes with multiple encrypted images. The original
        # user report has two images interleaved with text; a one-image test
        # missed that the second image could disappear in locked mode.
        second_jpeg = io.BytesIO()
        Image.new('RGB', (5, 3), 'orange').save(second_jpeg, format='JPEG')
        second_image_ref = image_ref.replace('a' * 64, 'b' * 64).replace('key=' + 'A' * 43, 'key=' + 'B' * 43).replace('nonce=' + 'A' * 16, 'nonce=' + 'B' * 16)
        second_image_markdown = '![Image](' + second_image_ref + ')'
        multi_image_markdown = (
            '# Test\n\n' + image_markdown + '\n\nOk\n\nTest verrouillage\n\n'
            'Ok\n\nTest 1\n\nTest 2\n\nTest 3\n\n' + second_image_markdown + '\n\nTest 4\n\nTest 5'
        )
        multi_locked_note = replace(current, markdown=multi_image_markdown, locked=True)
        win.current = multi_locked_note
        win.notes = [multi_locked_note]
        def multi_image_load(reference, *_args):
            return second_jpeg.getvalue() if reference == second_image_ref else jpeg.getvalue()
        with patch('nostr_notes.app.load_image_for_display', side_effect=multi_image_load):
            win.display(multi_locked_note)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: evaluate(editor, '''JSON.stringify((() => {
              const images=[...document.querySelectorAll('.toastui-editor-ww-container img:not(.ProseMirror-separator)')];
              return images.some(i=>i.naturalWidth===3) && images.some(i=>i.naturalWidth===5);
            })())'''))
            locked_images = evaluate(editor, '''JSON.stringify((() => {
              const images=[...document.querySelectorAll('.toastui-editor-ww-container img:not(.ProseMirror-separator)')]
                .filter(i=>i.getBoundingClientRect().width>0 && i.getBoundingClientRect().height>0);
              return images.map(i=>({width:i.naturalWidth, visible:true,
                src:i.getAttribute('src')?.startsWith('data:image/jpeg;base64,')}));
            })())''')
            assert locked_images == [
                {'width': 3, 'visible': True, 'src': True},
                {'width': 5, 'visible': True, 'src': True},
            ], locked_images
            assert editor.get_text() == multi_image_markdown
        # Simulate the exact race reported: the image decryption starts for an
        # editable note, then its locked view replaces the editor before the
        # decrypting worker returns. The result must reach the locked view.
        load_started = threading.Event()
        allow_load_to_finish = threading.Event()
        def delayed_image_load(*_args):
            load_started.set()
            assert allow_load_to_finish.wait(5)
            return jpeg.getvalue()
        race_markdown = '# Image en cours\n\n' + image_markdown
        old_epoch = editor.epoch
        with patch('nostr_notes.app.load_image_for_display', side_effect=delayed_image_load):
            editor.set_text(race_markdown, read_only=False)
            wait_for(load_started.is_set)
            editor.set_text(race_markdown, read_only=True)
            wait_for(lambda: not editor.pending_document)
            allow_load_to_finish.set()
            wait_for(lambda: visible_image_loaded(editor, 3))
        assert editor.epoch != old_epoch
        with patch('nostr_notes.app.load_image_for_display', return_value=jpeg.getvalue()):
            win.display(locked_note)
            wait_for(lambda: not editor.pending_document)
            wait_for(lambda: visible_image_loaded(editor, 3))
        win.update_trash_controls()
        assert not editor.toolbar.get_visible()
        assert win.editor.get_sensitive() and editor.web.get_sensitive()
        readonly_ui = evaluate(editor, '''JSON.stringify((() => {
          const toolbar=document.querySelector('.toastui-editor-toolbar');
          const content=document.querySelector('.ProseMirror');
          return {toolbarHidden:!toolbar || getComputedStyle(toolbar).display==='none',
            editable:content?.getAttribute('contenteditable'),hostClass:document.getElementById('editor').classList.contains('notes-read-only')};
        })())''')
        assert readonly_ui == {'toolbarHidden': True, 'editable': 'false', 'hostClass': True}, readonly_ui
        evaluate(editor, "document.querySelector('.task-list-item')?.click(); true")
        locked_snapshot = evaluate(editor, "JSON.stringify(JSON.parse(window.notesEditor.snapshot()).markdown)")
        assert locked_snapshot == long_markdown, repr(locked_snapshot)
        assert editor.get_text() == long_markdown
        evaluate(editor, "document.body.dispatchEvent(new ClipboardEvent('paste',{bubbles:true,cancelable:true})); true")
        assert editor.get_text() == long_markdown
        visual_scroll = evaluate(editor, '''JSON.stringify((() => {
          const boxes=[document.documentElement,document.body,...document.querySelectorAll('*')]
            .filter(e=>e.getBoundingClientRect().height>0 && e.scrollHeight>e.clientHeight+2)
            .map(e=>({tag:e.tagName,cls:typeof e.className==='string'?e.className:'',id:e.id,
              before:e.scrollTop,max:e.scrollHeight-e.clientHeight,overflow:getComputedStyle(e).overflowY}));
          const box=boxes.find(e=>/auto|scroll/.test(e.overflow)) || boxes[0];
          if(!box)return {boxes};
          const node=box.id?document.getElementById(box.id):[document.documentElement,document.body,...document.querySelectorAll('*')]
            .find(e=>e.tagName===box.tag && (typeof e.className==='string'?e.className:'')===box.cls && e.scrollHeight-e.clientHeight===box.max);
          node.scrollTop=node.scrollHeight;
          return {before:box.before,after:node.scrollTop,max:box.max,cls:box.cls,overflow:box.overflow,boxes};
        })())''')
        assert visual_scroll['max'] > 0 and visual_scroll['after'] > visual_scroll['before'], visual_scroll
        editor.switch_mode(False)
        wait_for(lambda: not editor.visual_active)
        assert not editor.source.get_editable()
        scroll_box = editor.stack.get_child_by_name('source')
        adjustment = scroll_box.get_vadjustment()
        assert adjustment.get_upper() > adjustment.get_page_size()
        old_scroll = adjustment.get_value()
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        while GLib.MainContext.default().pending(): GLib.MainContext.default().iteration(False)
        assert adjustment.get_value() > old_scroll
        assert editor.get_text() == long_markdown
        editor.switch_mode(True)
        wait_for(lambda: editor.visual_active and not editor.pending_document)
        unlocked_note = replace(current, locked=False)
        win.current = unlocked_note
        win.notes = [unlocked_note]
        win.display(unlocked_note)
        wait_for(lambda: editor.toolbar.get_visible() and not editor.pending_document)
        assert editor.toolbar.get_visible()
        editable_ui = evaluate(editor, '''JSON.stringify((() => ({
          toolbarVisible:getComputedStyle(document.querySelector('.toastui-editor-toolbar')).display!=='none',
          editable:document.querySelector('.ProseMirror')?.getAttribute('contenteditable'),
          hostReadOnly:document.getElementById('editor').classList.contains('notes-read-only')
        }))())''')
        assert editable_ui == {'toolbarVisible': True, 'editable': 'true', 'hostReadOnly': False}, editable_ui
        win.close_clean()
        print('GTK/WebKit OK : barre d’édition masquée sur note verrouillée et rétablie au déverrouillage, défilement, conservation, frappe, publication, CSP et révisions.')
