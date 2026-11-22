# Revue de sécurité et confidentialité — Notestr Linux 4.1.1 — 22 novembre 2026

## Paquet candidat

- AppImage : `Notestr-4.1.1-x86_64.AppImage`.
- SHA-256 : `985811ecd9ee00da480220769da4c2e1bdc0b46ba0fc06fbf82dfb87f823ca45`.
- `--version` affiche `Notestr 4.1.1`. `--check` confirme GTK4/libadwaita, WebKitGTK 6.0, imports Nostr, chiffrement, déchiffrement et signature.
- Contrôle de dépendances ELF intégré au build réussi. L’utilisateur confirme avoir testé les candidats Android et Linux 4.1.1 ; les scénarios précis ne sont pas consignés.

## Moteur web et dépendances

- WebKitGTK/JavaScriptCore embarqués : `2.54.3`, en remplacement de `2.54.0`, afin de corriger [WSA-2026-0007](https://webkitgtk.org/security/WSA-2026-0007.html).
- Archive officielle `webkitgtk-2.54.3.tar.xz`, SHA-256 `2779c1b46f88762e8400650271ba14452dc4e30b37059981552d8b562b7d0862`.
- Correctif local documenté : copie du pointeur d’image avant appel de redimensionnement, pour rendre compilable le chemin du curseur WebKitGTK 2.54.3. Le patch attend une occurrence exacte dans le fichier source ; le rapport d’overlay est embarqué dans l’AppImage.
- Dépendances Python épinglées issues de la 4.1 contrôlée. L’audit en ligne exhaustif des bibliothèques natives transitives reste incomplet ; aucune absence générale de vulnérabilité n’est revendiquée.

## Sources et confidentialité

- Scan ciblé final de 168 fichiers source et 3 722 fichiers du contenu décompressé de l’AppImage : aucun chemin personnel du propriétaire, jeton d’accès ou npub connu détecté. Trois détections `nsec` correspondent à un même symbole C++ WebKit, présent sous trois noms de bibliothèque ; aucun secret Nostr n’a été identifié. Le contrôle reste ciblé et ne constitue pas une garantie exhaustive.
- Aucun `direct_url.json` ni bytecode Python n’est embarqué. Le scan est ciblé et ne constitue pas une garantie exhaustive.

## Publication

L’utilisateur a confirmé le 22 novembre 2026 avoir testé les candidats Android et Linux 4.1.1. Aucun push, tag distant, release ni téléversement n’a encore été effectué au moment de cette revue.
