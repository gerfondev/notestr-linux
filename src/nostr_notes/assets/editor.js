'use strict';
(() => {
  let epoch = 0;
  let original = '';
  let baseline = '';
  let muted = false;
  const send = (message) => window.webkit.messageHandlers.notes.postMessage(JSON.stringify(message));
  let editor;
  function createEditor() {
    const instance = new toastui.Editor({
    el: document.getElementById('editor'),
    height: '100%', initialEditType: 'wysiwyg', initialValue: '',
    hideModeSwitch: true, autofocus: false, language: 'fr-FR',
    usageStatistics: false,
    customHTMLSanitizer: (html) => DOMPurify.sanitize(html, {
      USE_PROFILES: {html: true}, FORBID_TAGS: ['img', 'iframe', 'audio', 'video', 'style', 'form'],
      FORBID_ATTR: ['style', 'src', 'srcset']
    }),
    toolbarItems: [['heading', 'bold', 'italic', 'strike'], ['hr', 'quote'],
      ['ul', 'ol', 'task'], ['table', 'link'], ['code', 'codeblock']],
    hooks: { addImageBlobHook: () => false }
    });
    instance.on('change', () => {
      if (!muted) send({ type: 'change', ...state() });
    });
    return instance;
  }
  document.addEventListener('notes-copy-code', (event) => {
    send({type: 'copyCode', epoch, text: event.detail});
  });
  editor = createEditor();
  function state() {
    const value = editor.getMarkdown();
    // Si l'utilisateur n'a rien changé (ou a annulé ses changements), restituer
    // exactement le Markdown chargé, pas sa normalisation par TOAST UI.
    return { epoch, markdown: value === baseline ? original : value };
  }
  document.addEventListener('click', (event) => {
    if (event.target.closest('a')) event.preventDefault();
  }, true);
  document.addEventListener('drop', (event) => { event.preventDefault(); event.stopImmediatePropagation(); }, true);
  document.addEventListener('dragover', (event) => event.preventDefault(), true);
  // Le collage ne peut introduire de fichiers ni de HTML actif.
  document.addEventListener('paste', (event) => {
    event.preventDefault(); event.stopImmediatePropagation();
    const text = event.clipboardData?.getData('text/plain');
    if (text) editor.insertText(text);
  }, true);
  window.notesEditor = Object.freeze({
    setDocument(markdown, revision) {
      if (revision === epoch && markdown === state().markdown) return JSON.stringify(state());
      muted = true;
      // Une nouvelle note ne doit jamais hériter de l'historique Annuler d'une autre.
      editor.destroy();
      document.getElementById('editor').replaceChildren();
      editor = createEditor();
      epoch = revision;
      original = markdown;
      editor.setMarkdown(markdown, false);
      baseline = editor.getMarkdown();
      muted = false;
      return JSON.stringify(state());
    },
    snapshot() { return JSON.stringify(state()); }
  });
  send({ type: 'ready' });
})();
