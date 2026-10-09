'use strict';
(() => {
  let uiLanguage='fr';
  const label=(fr,en)=>uiLanguage==='en'?en:fr;
  // Localize the existing bundled copy control without changing note content.
  const localizeCopyButtons=()=>{
    document.querySelectorAll('.notes-copy-code').forEach(button=>{
      const text=label('Copier','Copy');
      if(button.textContent!==text)button.textContent=text;
      button.setAttribute('aria-label',label('Copier le bloc de code','Copy code block'));
    });
  };
  new MutationObserver(localizeCopyButtons).observe(document.getElementById('editor'), {childList:true,subtree:true});
  let epoch = 0;
  let original = '';
  let baseline = '';
  let muted = false;
  const embeddedAssets = new Map();
  const imageSources = new Map();
  let imageSlots = [];
  const requestedAssets = new Set();
  let insertionSelection = null;
  // Toast UI's Markdown preview accepts data: image URLs, but its WYSIWYG
  // parser drops them when creating ProseMirror image nodes. Use a unique,
  // reserved .invalid URL as the temporary model value; CSP blocks all network
  // loads, then imageResult replaces it with the decrypted data URL.
  const imagePlaceholder = (id) => 'https://notestr-image.invalid/' + id;
  const validImageReference = (reference) => {
    try {
      const url = new URL(reference);
      return url.protocol === 'notestr-image:' && /^[0-9a-f]{64}$/.test(url.hostname)
        && /^https:\/\/[a-z0-9.-]+(?::[0-9]+)?$/i.test(url.searchParams.get('server') || '')
        && url.searchParams.getAll('server').length === 1
        && /^[A-Za-z0-9_-]{43}$/.test(url.searchParams.get('key') || '')
        && url.searchParams.getAll('key').length === 1
        && /^[A-Za-z0-9_-]{16}$/.test(url.searchParams.get('nonce') || '')
        && url.searchParams.getAll('nonce').length === 1
        && url.searchParams.get('mime') === 'image/jpeg' && url.searchParams.getAll('mime').length === 1;
    } catch (_) { return false; }
  };
  // Older notes may have been produced by clients that percent-encode
  // base64url fields differently. Do not silently discard their image while
  // loading the document: let the native decoder validate the key and nonce,
  // and report a useful error if they are actually malformed.
  const imageReferenceCandidate = (reference) => {
    try {
      const url = new URL(reference);
      return url.protocol === 'notestr-image:' && /^[0-9a-f]{64}$/i.test(url.hostname)
        && url.searchParams.getAll('server').length === 1
        && /^https:\/\/[a-z0-9.-]+(?::[0-9]+)?$/i.test(url.searchParams.get('server') || '')
        && url.searchParams.getAll('key').length === 1
        && /^[A-Za-z0-9_=%-]+$/.test(url.searchParams.get('key') || '')
        && url.searchParams.getAll('nonce').length === 1
        && /^[A-Za-z0-9_=%-]+$/.test(url.searchParams.get('nonce') || '')
        && url.searchParams.getAll('mime').length === 1
        && url.searchParams.get('mime') === 'image/jpeg';
    } catch (_) { return false; }
  };
  const resolveImages = () => {
    let sent = 0;
    for (const image of document.querySelectorAll('#editor img')) {
      const reference = imageSources.get(image.getAttribute('src'));
      if (reference && !requestedAssets.has(reference)) { requestedAssets.add(reference); send({type:'loadImage', reference, epoch}); sent++; }
    }
    return sent;
  };
  const restoreWysiwygImageSources = () => {
    const view = editor.wwEditor?.view;
    if (!view || !imageSlots.length) return;
    let slot = 0;
    let transaction = view.state.tr;
    view.state.doc.descendants((node, position) => {
      if (node.type.name !== 'image') return;
      const preview = imageSlots[slot++];
      if (preview && node.attrs.imageUrl !== preview)
        transaction = transaction.setNodeMarkup(position, undefined, {...node.attrs, imageUrl: preview});
    });
    if (transaction.docChanged) view.dispatch(transaction);
  };
  new MutationObserver(resolveImages).observe(document.getElementById('editor'), {childList:true,subtree:true});
  const send = (message) => window.webkit.messageHandlers.notes.postMessage(JSON.stringify(message));
  DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
    if (data.attrName !== 'src') return;
    let custom = false;
    try { const u = new URL(data.attrValue); custom = node.nodeName === 'IMG' && u.protocol === 'notestr-image:' && /^[0-9a-f]{64}$/.test(u.hostname) && /^https:\/\/[a-z0-9.-]+(?::[0-9]+)?$/i.test(u.searchParams.get('server') || '') && /^[A-Za-z0-9_-]+$/.test(u.searchParams.get('key') || '') && /^[A-Za-z0-9_-]+$/.test(u.searchParams.get('nonce') || '') && u.searchParams.get('mime') === 'image/jpeg'; } catch (_) {}
    const inline = node.nodeName === 'IMG' && /^data:image\/(?:jpeg|png);base64,[A-Za-z0-9+/=]+(?:#notestr-[a-z0-9]+)?$/i.test(data.attrValue);
    const localPreview = node.nodeName === 'IMG' && /^https:\/\/notestr-image\.invalid\/notestr-[A-Za-z0-9]+$/.test(data.attrValue);
    data.keepAttr = custom || inline || localPreview;
  });
  let editor;
  function createEditor() {
    const instance = new toastui.Editor({
    el: document.getElementById('editor'),
    height: '100%', initialEditType: 'wysiwyg', initialValue: '',
    hideModeSwitch: true, autofocus: false, language: uiLanguage==='en'?'en-US':'fr-FR',
    usageStatistics: false,
    customHTMLSanitizer: (html) => DOMPurify.sanitize(html, {
      USE_PROFILES: {html: true}, FORBID_TAGS: ['iframe', 'audio', 'video', 'style', 'form', 'canvas'],
      FORBID_ATTR: ['style', 'srcset']
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
  // Keep code-copy controls outside ProseMirror so they never enter the note.
  const copyLayer = document.createElement('div');
  copyLayer.className = 'notes-code-actions';
  document.body.appendChild(copyLayer);
  const copyButtons = new Map();
  const updateCopyButtons = () => {
    const blocks = new Set(document.querySelectorAll('.toastui-editor-ww-container .toastui-editor-ww-code-block'));
    for (const [block, button] of copyButtons) {
      if (!blocks.has(block)) { button.remove(); copyButtons.delete(block); }
    }
    for (const block of blocks) {
      let button = copyButtons.get(block);
      if (!button) {
        button = document.createElement('button');
        button.type = 'button'; button.className = 'notes-copy-code';
        button.addEventListener('pointerdown', event => event.preventDefault());
        button.addEventListener('click', () => {
          const text = Array.from(block.children).map(line => line.textContent).join('\n');
          send({type: 'copyCode', epoch, text});
        });
        copyLayer.appendChild(button); copyButtons.set(block, button);
      }
      button.textContent = label('Copier', 'Copy');
      button.setAttribute('aria-label', label('Copier le contenu du bloc de code', 'Copy code block contents'));
      const rect = block.getBoundingClientRect();
      const container = block.closest('.toastui-editor-ww-container').getBoundingClientRect();
      const top = rect.top + 6, right = Math.min(rect.right, container.right, innerWidth) - 8;
      button.hidden = top < Math.max(container.top, 0) || top + 40 > Math.min(container.bottom, innerHeight) || right < 80;
      button.style.top = `${top}px`; button.style.left = `${right - 76}px`;
    }
  };
  let copyFrame = 0;
  const scheduleCopyButtons = () => {
    if (!copyFrame) copyFrame = requestAnimationFrame(() => { copyFrame = 0; updateCopyButtons(); });
  };
  new MutationObserver(scheduleCopyButtons).observe(document.getElementById('editor'), {subtree: true, childList: true, characterData: true});
  new ResizeObserver(scheduleCopyButtons).observe(document.getElementById('editor'));
  document.addEventListener('scroll', scheduleCopyButtons, true);
  window.addEventListener('resize', scheduleCopyButtons);
  const restoreImageReferences = (value) => {
    for (const [dataUrl, reference] of embeddedAssets) value = value.replaceAll(dataUrl, reference);
    return value;
  };
  function state() {
    const raw = restoreImageReferences(editor.getMarkdown());
    // Si l'utilisateur n'a rien changé (ou a annulé ses changements), restituer
    // exactement le Markdown chargé, pas sa normalisation par TOAST UI.
    if (raw === baseline) return { epoch, markdown: original };
    let value = raw;
    // Paragraphes simples : garder un retour explicite en Markdown après édition.
    const doc = editor.wwEditor?.view?.state?.doc;
    if (doc && doc.childCount > 1) {
      let paragraphs = true;
      doc.forEach(node => { if (node.type.name !== 'paragraph') paragraphs = false; });
      const lines = value.split('\n');
      if (paragraphs && lines.length === doc.childCount) value = lines.join('  \n');
    }
    return { epoch, markdown: value };
  }
  let imageLightbox = null;
  const closeImageLightbox = () => {
    if (!imageLightbox) return;
    imageLightbox.remove(); imageLightbox = null;
    document.removeEventListener('keydown', onImageLightboxKeydown, true);
  };
  const onImageLightboxKeydown = (event) => {
    if (!imageLightbox) return;
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeImageLightbox(); return; }
    const image = imageLightbox.querySelector('img');
    if (!image) return;
    const zoom = Number((image.style.transform.match(/scale\(([^)]+)\)/) || [])[1]) || 1;
    if (event.key === '+' || event.key === '=') { event.preventDefault(); imageLightbox.querySelector('.notes-image-lightbox-zoom-in')?.click(); }
    else if (event.key === '-') { event.preventDefault(); imageLightbox.querySelector('.notes-image-lightbox-zoom-out')?.click(); }
    else if (event.key === 'Home') { event.preventDefault(); imageLightbox.querySelector('.notes-image-lightbox-zoom-reset')?.click(); }
    else if (zoom > 1 && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
      event.preventDefault();
      const match = image.style.transform.match(/translate3d\(([-\d.]+)px,\s*([-\d.]+)px/);
      const maxX = Math.max(0, (image.clientWidth * zoom - (imageLightbox.clientWidth - 48)) / 2);
      const maxY = Math.max(0, (image.clientHeight * zoom - (imageLightbox.clientHeight - 48)) / 2);
      const x = parseFloat(match?.[1] || '0'), y = parseFloat(match?.[2] || '0'), step = event.shiftKey ? 120 : 40;
      image.style.transform = `translate3d(${Math.max(-maxX, Math.min(maxX, x + (event.key === 'ArrowRight' ? step : event.key === 'ArrowLeft' ? -step : 0)))}px,${Math.max(-maxY, Math.min(maxY, y + (event.key === 'ArrowDown' ? step : event.key === 'ArrowUp' ? -step : 0)))}px,0) scale(${zoom})`;
    }
  };
  const showImageLightbox = (image) => {
    const src = image.getAttribute('src') || '';
    if (!/^data:image\/(?:jpeg|png);base64,[A-Za-z0-9+/=]+(?:#notestr-[a-z0-9]+)?$/i.test(src)) return false;
    closeImageLightbox();
    const overlay = document.createElement('div');
    overlay.className = 'notes-image-lightbox'; overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-label', uiLanguage === 'en' ? 'Full-screen image' : 'Image en plein écran');
    const enlarged = document.createElement('img'); enlarged.alt = image.alt || (uiLanguage === 'en' ? 'Enlarged image' : 'Image agrandie'); enlarged.src = src.split('#')[0];
    let zoom = 1, panX = 0, panY = 0, gesture = null, moved = false, suppressBackdropClick = false;
    const pointers = new Map();
    const clampZoom = value => Math.max(1, Math.min(8, value));
    const clampPan = () => {
      const width = Math.max(0, overlay.clientWidth - 48), height = Math.max(0, overlay.clientHeight - 48);
      const maxX = Math.max(0, (enlarged.clientWidth * zoom - width) / 2), maxY = Math.max(0, (enlarged.clientHeight * zoom - height) / 2);
      panX = Math.max(-maxX, Math.min(maxX, panX)); panY = Math.max(-maxY, Math.min(maxY, panY));
    };
    const render = () => { clampPan(); enlarged.style.transform = `translate3d(${panX}px,${panY}px,0) scale(${zoom})`; level.textContent = `${Math.round(zoom * 100)}%`; out.disabled = zoom <= 1; };
    const zoomAt = (next, x = overlay.getBoundingClientRect().left + overlay.clientWidth / 2, y = overlay.getBoundingClientRect().top + overlay.clientHeight / 2) => {
      const rect = overlay.getBoundingClientRect(), px = x - rect.left - overlay.clientWidth / 2, py = y - rect.top - overlay.clientHeight / 2;
      const worldX = (px - panX) / zoom, worldY = (py - panY) / zoom;
      zoom = clampZoom(next); panX = px - worldX * zoom; panY = py - worldY * zoom; render();
    };
    const button = (className, text, aria) => { const item = document.createElement('button'); item.type = 'button'; item.className = className; item.textContent = text; item.setAttribute('aria-label', aria); return item; };
    const controls = document.createElement('div'); controls.className = 'notes-image-lightbox-controls';
    const out = button('notes-image-lightbox-zoom-out', '−', uiLanguage === 'en' ? 'Zoom out' : 'Dézoomer');
    const level = document.createElement('span'); level.className = 'notes-image-lightbox-zoom-level'; level.setAttribute('aria-live', 'polite'); level.textContent = '100%';
    const reset = button('notes-image-lightbox-zoom-reset', '↺', uiLanguage === 'en' ? 'Reset zoom' : 'Réinitialiser le zoom');
    const into = button('notes-image-lightbox-zoom-in', '+', uiLanguage === 'en' ? 'Zoom in' : 'Zoomer');
    out.addEventListener('click', () => zoomAt(zoom / 1.5)); into.addEventListener('click', () => zoomAt(zoom * 1.5));
    reset.addEventListener('click', () => { zoom = 1; panX = 0; panY = 0; render(); }); controls.append(out, level, reset, into);
    const close = document.createElement('button'); close.type = 'button'; close.className = 'notes-image-lightbox-close';
    close.setAttribute('aria-label', uiLanguage === 'en' ? 'Close image' : 'Fermer l’image'); close.textContent = '×';
    overlay.append(enlarged, controls, close);
    overlay.addEventListener('pointerdown', (event) => {
      if (event.target instanceof Element && event.target.closest('button')) return;
      pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
      try { overlay.setPointerCapture(event.pointerId); } catch (_) {}
      if (pointers.size >= 2) {
        const pair = [...pointers.values()].slice(0, 2), midX = (pair[0].x + pair[1].x) / 2, midY = (pair[0].y + pair[1].y) / 2, rect = overlay.getBoundingClientRect();
        gesture = {pinch: true, distance: Math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y) || 1, zoom, worldX: (midX - rect.left - overlay.clientWidth / 2 - panX) / zoom, worldY: (midY - rect.top - overlay.clientHeight / 2 - panY) / zoom};
      } else gesture = {pinch: false, x: event.clientX, y: event.clientY, panX, panY};
      moved = false; if (zoom > 1) event.preventDefault();
    });
    overlay.addEventListener('pointermove', (event) => {
      if (!pointers.has(event.pointerId)) return;
      pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
      if (pointers.size >= 2 && gesture?.pinch) {
        const pair = [...pointers.values()].slice(0, 2), midX = (pair[0].x + pair[1].x) / 2, midY = (pair[0].y + pair[1].y) / 2, rect = overlay.getBoundingClientRect();
        zoom = clampZoom(gesture.zoom * Math.hypot(pair[0].x - pair[1].x, pair[0].y - pair[1].y) / gesture.distance);
        panX = midX - rect.left - overlay.clientWidth / 2 - gesture.worldX * zoom; panY = midY - rect.top - overlay.clientHeight / 2 - gesture.worldY * zoom;
        moved = true; render(); event.preventDefault();
      } else if (gesture && !gesture.pinch) {
        const dx = event.clientX - gesture.x, dy = event.clientY - gesture.y;
        if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
        if (zoom > 1) { panX = gesture.panX + dx; panY = gesture.panY + dy; render(); event.preventDefault(); }
      }
    });
    const endPointer = (event) => {
      if (!pointers.has(event.pointerId)) return; pointers.delete(event.pointerId);
      if (pointers.size === 1) { const point = [...pointers.values()][0]; gesture = {pinch: false, x: point.x, y: point.y, panX, panY}; } else gesture = null;
      if (moved) { suppressBackdropClick = true; setTimeout(() => { suppressBackdropClick = false; }, 350); }
    };
    overlay.addEventListener('pointerup', endPointer); overlay.addEventListener('pointercancel', endPointer);
    overlay.addEventListener('wheel', (event) => { event.preventDefault(); zoomAt(zoom * (event.deltaY < 0 ? 1.15 : 1 / 1.15), event.clientX, event.clientY); }, {passive: false});
    overlay.addEventListener('dblclick', (event) => { event.preventDefault(); zoomAt(zoom > 1 ? 1 : 2, event.clientX, event.clientY); });
    overlay.addEventListener('click', (event) => { if (event.target === overlay && !suppressBackdropClick) closeImageLightbox(); });
    close.addEventListener('click', (e) => { e.preventDefault(); e.stopPropagation(); closeImageLightbox(); });
    document.body.appendChild(overlay); imageLightbox = overlay;
    document.addEventListener('keydown', onImageLightboxKeydown, true); close.focus();
    return true;
  };
  document.addEventListener('click', (event) => {
    if (!(event.target instanceof Element)) return;
    const image = event.target.closest('.toastui-editor-contents img');
    if (image) { if (showImageLightbox(image)) { event.preventDefault(); event.stopImmediatePropagation(); } return; }
    const link = event.target.closest('a');
    if (!link) return;
    event.preventDefault();
    const url = link.getAttribute('href') || '';
    if (event.isTrusted && /^https?:\/\//i.test(url))
      send({type: 'openLink', url, ...state()});
  }, true);
  document.addEventListener('drop', (event) => { event.preventDefault(); event.stopImmediatePropagation(); }, true);
  document.addEventListener('dragover', (event) => event.preventDefault(), true);
  // Le collage ne peut introduire de fichiers ni de HTML actif.
  document.addEventListener('paste', (event) => {
    // Dialog fields (URL, link text, etc.) use native plain-text pasting.
    // Sending these pastes to insertText would modify the underlying note.
    if (event.target instanceof Element && event.target.closest('input, textarea')) return;
    event.preventDefault(); event.stopImmediatePropagation();
    const text = event.clipboardData?.getData('text/plain');
    if (text) editor.insertText(text);
  }, true);
  window.notesEditor = Object.freeze({
    setDocument(markdown, revision, language='fr') {
      uiLanguage=language==='en'?'en':'fr';document.documentElement.lang=uiLanguage;
      if (revision === epoch && markdown === state().markdown) return JSON.stringify(state());
      closeImageLightbox();
      muted = true;
      // Une nouvelle note ne doit jamais hériter de l'historique Annuler d'une autre.
      editor.destroy();
      document.getElementById('editor').replaceChildren();
      editor = createEditor();
      epoch = revision;
      original = markdown;
      embeddedAssets.clear();
      imageSources.clear();
      requestedAssets.clear();
      imageSlots = [];
      insertionSelection = null;
      let serial = 0;
      const displayMarkdown = markdown.replace(/!\[([^\]]*)\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g, (whole, alt, reference) => {
        if (!imageReferenceCandidate(reference)) { imageSlots.push(null); return whole; }
        const preview = imagePlaceholder('notestr-e' + epoch + 'i' + (serial++).toString(36));
        imageSources.set(preview, reference);
        embeddedAssets.set(preview, reference);
        imageSlots.push(preview);
        return whole.replace(reference, preview);
      });
      editor.setMarkdown(displayMarkdown, false);
      restoreWysiwygImageSources();
      baseline = restoreImageReferences(editor.getMarkdown());
      muted = false;
      resolveImages();
      return JSON.stringify(state());
    },
    imageResult(reference, base64) {
      if (typeof reference !== 'string' || typeof base64 !== 'string' || base64.length > 28 * 1024 * 1024) return false;
      let found = false;
      for (const [preview, originalReference] of imageSources) {
        if (originalReference !== reference) continue;
        const marker = '#notestr-' + (preview.split('/').pop() || '').replace(/^notestr-/, '');
        const dataUrl = 'data:image/jpeg;base64,' + base64 + marker;
        embeddedAssets.set(dataUrl, reference);
        for (const image of document.querySelectorAll('#editor img')) {
          if (image.getAttribute('src') === preview) image.setAttribute('src', dataUrl);
        }
        // The WYSIWYG node view may omit src when Toast UI parses a sanitized
        // Markdown image. Its model keeps the safe placeholder URL, so restore
        // the matching visual element directly after the native loader returns.
        const slot = imageSlots.indexOf(preview);
        const editableImages = [...document.querySelectorAll('#editor img')]
          .filter(image => image.closest('[contenteditable]')?.getAttribute('contenteditable') === 'true');
        const target = (slot >= 0 ? editableImages[slot] : null)
          || editableImages.find(image => !image.getAttribute('src') || image.getAttribute('src') === preview);
        if (target && (!target.getAttribute('src') || target.getAttribute('src') === preview))
          target.setAttribute('src', dataUrl);
        imageSources.delete(preview);
        found = true;
      }
      return found;
    },
    rememberInsertionPoint(from, to) {
      try {
        insertionSelection = Number.isInteger(from) && Number.isInteger(to)
          ? [from, to] : editor.getSelection();
        return Array.isArray(insertionSelection) && insertionSelection.length === 2;
      } catch (_) { insertionSelection = null; return false; }
    },
    insertImageReference(reference) {
      const markdown = typeof reference === 'string' && reference.match(/^!\[[^\]]*\]\((notestr-image:\/\/[^)\s]+)\)$/);
      if (markdown) reference = markdown[1];
      if (!validImageReference(reference)) return false;
      try {
        if (insertionSelection) editor.setSelection(...insertionSelection);
        const preview = imagePlaceholder('notestr-e' + epoch + 'i' + Math.random().toString(36).slice(2));
        imageSources.set(preview, reference);
        embeddedAssets.set(preview, reference);
        editor.exec('addImage', {imageUrl: preview, altText: 'Image'});
        insertionSelection = null;
        return true;
      } catch (error) { return String(error); }
    },
    resolveImages(reset = false) { if (reset) requestedAssets.clear(); return resolveImages(); },
    closeImageLightbox,
    snapshot() { return JSON.stringify(state()); }
  });
  send({ type: 'ready' });
})();
