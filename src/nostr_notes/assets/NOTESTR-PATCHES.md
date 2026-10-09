# État et reconstruction de l’éditeur

Le dépôt TOAST UI Editor 3.2.2 est archivé. Le bundle a été reconstruit depuis le tag amont `editor@3.2.2` (commit `9b94c04231d4600b42347ff1b99d9813e9becf67`) avec prosemirror-view 1.42.6, model 1.25.12, state 1.4.4, transform 1.12.2, commands 1.7.2, history 1.5.1, inputrules 1.5.1 et keymap 1.2.3. Cette version de prosemirror-view corrige l’avis GHSA-c8x8-7fp4-3x9w / CVE-2026-104847 (versions antérieures à 1.42.3).

DOMPurify 3.4.16 reste séparé et externalisé ; les mentions et licences amont sont conservées. La suite de tests amont archivée n’est pas entièrement compatible avec les versions récentes de ProseMirror/DOMPurify et n’est pas annoncée comme réussie. Les tests d’application et d’intégration du paquet final sont documentés dans `SECURITY-REVIEW.md`. Cette reconstruction ne prouve pas que tout le projet amont archivé est exempt de défauts.

Pour assurer la compatibilité du bundle avec son API, ToastMark a été recompilé depuis le workspace source du même checkout amont. La distribution npm alpha fournit une API incomplète pour l’éditeur (absence de `Renderer`) et n’est donc pas intégrée. Le bundle final inclut l’export `Renderer` et a été contrôlé sur Android et Linux.

ToastMark émet `linebreak` pour les retours Markdown explicites ; TOAST UI Editor 3.2.2 attendait l’ancien type `softbreak`. Le convertisseur reconstruit traite les deux types afin de conserver les retours de paragraphe en mode visuel.
