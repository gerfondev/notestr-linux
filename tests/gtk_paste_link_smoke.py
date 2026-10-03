import time,json
from nostr_notes.editor import MarkdownEditor
from gi.repository import Adw,GLib,Gio
Adw.init()
def wait(condition):
 end=time.monotonic()+20;ctx=GLib.MainContext.default()
 while time.monotonic()<end:
  while ctx.pending():ctx.iteration(False)
  if condition():return
  time.sleep(.02)
 raise AssertionError('Timeout')
def js(code):
 parts=code.rsplit(';',1); body=(parts[0]+';return '+parts[1]) if len(parts)==2 else ('return '+code)
 result=[];editor._evaluate('JSON.stringify((()=>{'+body+'})())',result.append);wait(lambda:result);return result[0]
app=Adw.Application(application_id='fr.decentralia.NostrNotes.PasteTest',flags=Gio.ApplicationFlags.NON_UNIQUE);app.register(None)
win=Adw.ApplicationWindow(application=app,default_width=900,default_height=650)
editor=MarkdownEditor(lambda _:None);win.set_content(editor);win.present()
source='# Note fictive\n\nUn paragraphe **important**.\n\n- Premier élément\n- Second élément\n'
editor.set_text(source);wait(lambda:editor.ready and not editor.pending_document)
js("document.querySelector('button.link').click(); true")
print(js("JSON.stringify(Array.from(document.querySelectorAll('.toastui-editor-popup input')).map(x=>({id:x.id,type:x.type,placeholder:x.placeholder})))"),flush=True)
url='https://example.org/notes?lang=fr&test=1'
editor.web.grab_focus()
js("document.querySelector('.toastui-editor-popup input').focus(); true")
editor.get_clipboard().set(url);editor.web.execute_editing_command('Paste')
wait(lambda:js("document.querySelector('.toastui-editor-popup input').value")==url)
assert editor.get_text()==source
js("document.querySelector('.toastui-editor-popup input').select(); true")
editor.get_clipboard().set('https://example.org/remplacement');editor.web.execute_editing_command('Paste')
wait(lambda:js("document.querySelector('.toastui-editor-popup input').value")=='https://example.org/remplacement')
assert editor.get_text()==source
js("document.querySelector('.toastui-editor-popup .toastui-editor-close-button').click(); true")
assert editor.get_text()==source
# Validate insertion as well, with the two popup fields using native pasting.
js("document.querySelector('button.link').click(); true")
editor.web.grab_focus()
js("document.querySelector('#toastuiLinkUrlInput').focus(); true")
editor.get_clipboard().set(url);editor.web.execute_editing_command('Paste')
wait(lambda:js("document.querySelector('#toastuiLinkUrlInput').value")==url)
js("document.querySelector('#toastuiLinkTextInput').focus(); true")
editor.get_clipboard().set('Lien de démonstration');editor.web.execute_editing_command('Paste')
wait(lambda:js("document.querySelector('#toastuiLinkTextInput').value")=='Lien de démonstration')
assert editor.get_text()==source
js("document.querySelector('.toastui-editor-popup .toastui-editor-ok-button').click(); true")
wait(lambda: '[Lien de démonstration]('+url+')' in json.loads(js("window.notesEditor.snapshot()"))['markdown'])
assert js("document.querySelector('.toastui-editor-ww-container h1').textContent")=='Note fictive'
assert js("Array.from(document.querySelectorAll('.toastui-editor-ww-container li')).every((e,i)=>e.textContent.startsWith(['Premier élément','Second élément'][i]))")
print('PASS: native clipboard paste into URL, replace selected URL, cancel without changing Markdown; confirmed link inserted, heading/list preserved',flush=True)
win.close()
