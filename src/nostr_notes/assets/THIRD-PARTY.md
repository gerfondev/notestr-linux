# Ressources tierces embarquées

- TOAST UI Editor 3.2.2, NHN Cloud, licence MIT. Le dépôt amont est archivé. Le bundle distribué a été reconstruit depuis le tag `editor@3.2.2` avec les dépendances ProseMirror actualisées documentées dans `NOTESTR-PATCHES.md`.
- ToastMark (sources du workspace amont correspondant à TOAST UI Editor 3.2.2), MIT ; sa sortie CommonJS est reconstruite pour conserver l’API `Renderer` attendue par l’éditeur.
- DOMPurify 3.4.16, Cure53 et contributeurs, licences Apache-2.0 ou MPL-2.0 (`LICENSE-dompurify.txt`), chargé séparément et externalisé depuis le bundle.
- Les mentions de licence amont sont conservées. Notestr est distribué sous GPLv3 ; les composants tiers gardent leurs licences respectives.

Le convertisseur ToastMark inclut un correctif de compatibilité pour les nœuds `linebreak` du renderer amont. Les ressources sont embarquées ; aucun téléchargement n’a lieu à l’exécution. `SHA256SUMS` contrôle les fichiers de cet éditeur.
