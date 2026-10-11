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
  let loaded = false;
  let readOnly = false;
  let original = '';
  let baseline = '';
  let muted = false;
  const embeddedAssets = new Map();
  const imageSources = new Map();
  const resolvedImageSources = new Map();
  let imageSlots = [];
  const requestedAssets = new Set();
  let insertionSelection = null;
  // Toast UI's Markdown preview accepts data: image URLs, but its WYSIWYG
  // parser drops them when creating ProseMirror image nodes. Use a unique,
  // reserved .invalid URL as the temporary model value; CSP blocks all network
  // loads, then imageResult replaces it with the decrypted data URL.
  const imagePlaceholder = (id) => 'https://notestr-image.invalid/' + id;
  const parseImageReference = (reference, allowLegacyEncoding = false) => {
    if (typeof reference !== 'string') return null;
    const match = /^notestr-image:\/\/([0-9a-f]{64})\?([^\s#]+)$/i.exec(reference);
    if (!match) return null;
    const params = new URLSearchParams(match[2]);
    const server = params.get('server'), key = params.get('key'), nonce = params.get('nonce'), mime = params.get('mime');
    if (params.getAll('server').length !== 1 || params.getAll('key').length !== 1
        || params.getAll('nonce').length !== 1 || params.getAll('mime').length !== 1
        || !/^https:\/\/[a-z0-9.-]+(?::[0-9]+)?$/i.test(server || '')
        || !(allowLegacyEncoding ? /^[A-Za-z0-9_=%-]+$/ : /^[A-Za-z0-9_-]{43}$/).test(key || '')
        || !(allowLegacyEncoding ? /^[A-Za-z0-9_=%-]+$/ : /^[A-Za-z0-9_-]{16}$/).test(nonce || '')
        || mime !== 'image/jpeg') return null;
    return {hash: match[1], server, key, nonce, mime};
  };
  const validImageReference = (reference) => {
    return !!parseImageReference(reference);
  };
  // Older notes may have been produced by clients that percent-encode
  // base64url fields differently. Do not silently discard their image while
  // loading the document: let the native decoder validate the key and nonce,
  // and report a useful error if they are actually malformed.
  const imageReferenceCandidate = (reference) => {
    return !!parseImageReference(reference, true);
  };
  const resolveImages = () => {
    let sent = 0;
    for (const image of document.querySelectorAll('#editor img')) {
      const reference = imageSources.get(image.getAttribute('src'));
      if (reference && !requestedAssets.has(reference)) { requestedAssets.add(reference); send({type:'loadImage', reference, epoch}); sent++; }
    }
    return sent;
  };
  const imageElementAt = (view, position) => {
    const element = view.nodeDOM(position);
    if (!element) return null;
    if (element.nodeType === Node.ELEMENT_NODE && element.matches('img:not(.ProseMirror-separator)')) return element;
    return element.querySelector?.('img:not(.ProseMirror-separator)') || null;
  };
  const restoreResolvedImageSources = () => {
    const view = editor?.wwEditor?.view;
    if (!view || !resolvedImageSources.size) return;
    view.state.doc.descendants((node, position) => {
      if (node.type.name !== 'image') return;
      const preview = node.attrs.imageUrl;
      const dataUrl = resolvedImageSources.get(preview);
      const image = dataUrl ? imageElementAt(view, position) : null;
      if (image && image.getAttribute('src') !== dataUrl) image.setAttribute('src', dataUrl);
    });
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
  new MutationObserver(() => {
    resolveImages();
    restoreResolvedImageSources();
  }).observe(document.getElementById('editor'), {childList:true,subtree:true});
  const send = (message) => window.webkit.messageHandlers.notes.postMessage(JSON.stringify(message));
  DOMPurify.addHook('uponSanitizeAttribute', (node, data) => {
    if (data.attrName !== 'src') return;
    const custom = node.nodeName === 'IMG' && !!parseImageReference(data.attrValue, true);
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
  function installImageToolbarButton() {
    const toolbar = document.querySelector('.toastui-editor-toolbar');
    const table = toolbar?.querySelector('.toastui-editor-toolbar-icons.table');
    if (!toolbar || !table || readOnly) return;
    let button = toolbar.querySelector('.notes-insert-image');
    if (button) {
      button.setAttribute('aria-label', label('Insérer une image', 'Insert image'));
      button.title = label('Insérer une image', 'Insert image');
      return;
    }
    button = document.createElement('button'); button.type = 'button';
    button.className = 'toastui-editor-toolbar-icons notes-insert-image';
    button.setAttribute('aria-label', label('Insérer une image', 'Insert image'));
    button.title = label('Insérer une image', 'Insert image');
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24'); svg.setAttribute('aria-hidden', 'true');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM19 19H5V5h14v14zM7 17l3.2-4 2.2 2.6 1.6-2 3 3.4H7zm5-6V6m-3 3 3-3 3 3');
    path.setAttribute('fill', 'currentColor'); path.setAttribute('stroke', 'currentColor');
    path.setAttribute('stroke-width', '1.4'); path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('stroke-linejoin', 'round'); svg.appendChild(path); button.appendChild(svg);
    const rememberSelection = () => {
      try {
        const selection = editor.getSelection();
        if (Array.isArray(selection) && selection.length === 2) insertionSelection = selection;
      } catch (_) {}
    };
    button.addEventListener('pointerdown', rememberSelection);
    button.addEventListener('touchstart', rememberSelection, {passive: true});
    let lastActivation = 0;
    const activate = () => {
      const now = Date.now();
      if (now - lastActivation < 250) return;
      lastActivation = now;
      if (readOnly || !loaded) return;
      if (!insertionSelection) rememberSelection();
      if (insertionSelection) send({type: 'pickImage', epoch});
    };
    button.addEventListener('pointerup', activate);
    button.addEventListener('touchend', activate, {passive: true});
    button.addEventListener('click', activate);
    table.closest('button')?.after(button);
  }
  editor = createEditor();
  installImageToolbarButton();
  new MutationObserver(installImageToolbarButton).observe(document.getElementById('editor'), {childList: true, subtree: true});
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
    for (const [dataUrl, reference] of embeddedAssets) value = value.split(dataUrl).join(reference);
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
    if (readOnly && !event.target.closest('a') && event.target.closest('.task-list-item')) {
      event.preventDefault(); event.stopImmediatePropagation(); return;
    }
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
  document.addEventListener('beforeinput', (event) => {
    if (readOnly) { event.preventDefault(); event.stopImmediatePropagation(); }
  }, true);
  // Le collage ne peut introduire de fichiers ni de HTML actif.
  document.addEventListener('paste', (event) => {
    // Dialog fields (URL, link text, etc.) use native plain-text pasting.
    // Sending these pastes to insertText would modify the underlying note.
    if (event.target instanceof Element && event.target.closest('input, textarea')) return;
    event.preventDefault(); event.stopImmediatePropagation();
    if (readOnly) return;
    const text = event.clipboardData?.getData('text/plain');
    if (text) editor.insertText(text);
  }, true);
  function applyReadOnlyState() {
    const host = document.getElementById('editor');
    host.classList.toggle('notes-read-only', readOnly);
    const view = editor?.wwEditor?.view;
    if (view) {
      view.setProps({editable: () => !readOnly});
      if (view.dom) {
        view.dom.setAttribute('contenteditable', readOnly ? 'false' : 'true');
        view.dom.setAttribute('aria-readonly', readOnly ? 'true' : 'false');
      }
    }
    host.querySelectorAll('.ProseMirror').forEach(element => {
      element.setAttribute('contenteditable', readOnly ? 'false' : 'true');
      element.setAttribute('aria-readonly', readOnly ? 'true' : 'false');
    });
  }
  window.notesEditor = Object.freeze({
    setDocument(markdown, revision, language='fr', readonly=false) {
      uiLanguage=language==='en'?'en':'fr';document.documentElement.lang=uiLanguage;
      if (revision === epoch && markdown === state().markdown && readonly === readOnly) return JSON.stringify(state());
      closeImageLightbox();
      readOnly = readonly === true;
      loaded = false;
      muted = true;
      // Une nouvelle note ne doit jamais hériter de l'historique Annuler d'une autre.
      editor.destroy();
      document.getElementById('editor').replaceChildren();
      editor = createEditor();
      epoch = revision;
      original = markdown;
      embeddedAssets.clear();
      imageSources.clear();
      resolvedImageSources.clear();
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
      installImageToolbarButton();
      restoreWysiwygImageSources();
      applyReadOnlyState();
      baseline = restoreImageReferences(editor.getMarkdown());
      loaded = true;
      muted = false;
      // setMarkdown runs while the editor is being reconstructed. Schedule a
      // fresh layout after ProseMirror has committed its WYSIWYG nodes so the
      // floating copy controls are attached to newly loaded code blocks too.
      scheduleCopyButtons();
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
        // Keep the original placeholder in ProseMirror to preserve layout and
        // Markdown serialization. Reapply the decrypted data URL to rebuilt
        // node views, which matters after read-only/locked view updates.
        resolvedImageSources.set(preview, dataUrl);
        // Bind decrypted bytes to the exact ProseMirror image node. The editor
        // also contains hidden views and zero-size separator images; indexing
        // all <img> elements can silently attach the second image to a spacer.
        const view = editor?.wwEditor?.view;
        if (view) {
          view.state.doc.descendants((node, position) => {
            if (node.type.name !== 'image') return;
            if (node.attrs.imageUrl === preview) {
              const target = imageElementAt(view, position);
              if (target) target.setAttribute('src', dataUrl);
            }
          });
        }
        imageSources.delete(preview);
        found = true;
      }
      return found;
    },
    rememberInsertionPoint(from, to) {
      try {
        // The toolbar captures the ProseMirror selection on pointerdown,
        // before the button or native file chooser can steal focus. Keep that
        // range when the native bridge confirms the insertion request.
        if (Number.isInteger(from) && Number.isInteger(to))
          insertionSelection = [from, to];
        else if (!insertionSelection)
          insertionSelection = editor.getSelection();
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
