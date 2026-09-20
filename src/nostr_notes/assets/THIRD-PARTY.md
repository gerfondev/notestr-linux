# Ressources tierces embarquées

Téléchargées le 12 septembre 2026. Aucun téléchargement n’a lieu à l’exécution.

- TOAST UI Editor 3.2.2, NHN Cloud, licence MIT (`LICENSE-toastui.txt`).
  JavaScript autonome : https://uicdn.toast.com/editor/3.2.2/toastui-editor-all.min.js
  CSS et français : https://registry.npmjs.org/@toast-ui/editor/-/editor-3.2.2.tgz
  Source : https://github.com/nhn/tui.editor
  Le bundle inclut notamment ProseMirror et une ancienne copie de DOMPurify ;
  le point d’entrée customHTMLSanitizer utilise la version externe actuelle ci-dessous.
  Les mentions de licence intégrées au bundle ont été conservées.
- DOMPurify 3.4.15, Cure53 et contributeurs, licences Apache-2.0 ou MPL-2.0
  (`LICENSE-dompurify.txt`).
  https://registry.npmjs.org/dompurify/-/dompurify-3.4.15.tgz
  Source : https://github.com/cure53/DOMPurify

`SHA256SUMS` permet de contrôler les fichiers tiers distribués avec cette version.

## Correctif local : sauts de ligne (12 septembre 2026)

Le sérialiseur de paragraphes TOAST UI 3.2.2 est ajusté pour produire deux
espaces avant le retour à la ligne entre deux paragraphes visuels adjacents,
conformément aux sauts de ligne explicites CommonMark. Le traitement des blocs
de code, listes et tableaux reste celui de TOAST UI. Le bundle est donc modifié
localement ; SHA256SUMS correspond à cette version corrigée.

## Correctif local 0.2.2 (13 septembre 2026)

Le convertisseur Markdown vers visuel traitait `softbreak` mais ignorait
`linebreak`. Il traite maintenant les sauts explicites dans les paragraphes
comme des séparations visuelles, y compris dans les citations et listes.
Le test graphique contrôle les positions des textes à l’écran après rechargement.

## Adaptation locale de TOAST UI Editor

Le NodeView des blocs de code crée un bouton « Copier » hors du contenu éditable.
Il émet un événement DOM `notes-copy-code` traité par le pont GTK de l’application.
Les mutations du bouton sont ignorées par le NodeView ; les modifications du code
restent observées. Le sélecteur de langage est masqué par `editor.css` ; les
langages des blocs existants restent conservés dans le Markdown.
`SHA256SUMS` reflète cette adaptation locale du fichier JavaScript.
