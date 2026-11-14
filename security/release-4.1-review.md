# Revue de sécurité et confidentialité — Notestr Linux 4.1 — 14 novembre 2026

## Paquet candidat

- AppImage `Notestr-4.1-x86_64.AppImage`, version `4.1`.
- SHA-256 : `605183316b5a08098e4c22bb13105ad8a0908d36fb97d0d09a7486c3137a955f`.
- Le paquet a été reconstruit à partir du runtime AppImage 4.0 déjà examiné, avec le code et les ressources 4.1 ; les caches Python et `direct_url.json` ont été retirés.
- `--version` annonce `Notestr 4.1`. `--check` valide GTK4/libadwaita, WebKitGTK 6.0, les imports Nostr et les opérations synthétiques de chiffrement/déchiffrement/signature.
- Le contrôle graphique GTK n’a pas pu démarrer faute d’affichage dans l’environnement ; `pytest` n’est pas installé. Fontconfig signale aussi l’absence de cache inscriptible dans ce sandbox. Ces limites ne bloquent pas le lancement ni `--check`, mais le test graphique doit être fait par l’utilisateur.

## Dépendances et sécurité

- Dépendances Python du runtime contrôlées : aiohttp `3.14.5`, websockets `17.4`, cryptography `50.0.2`, Pillow `13.0.0`, WeasyPrint `70.0` et leurs dépendances verrouillées dans `packaging/requirements-4.1.txt`. Les versions comprennent les correctifs de sécurité publiés pour ces bibliothèques : notamment aiohttp 3.14.4+, websockets 17.4, Pillow 13.0.0 et WeasyPrint 70.0.
- Le plancher Python est passé à `3.11`, requis par Pillow 13 ; l’AppImage est construit avec Python 3.12. Le README et les métadonnées du projet sont alignés.
- WebKitGTK embarqué : `2.54.0`. Cette version corrige l’avis WSA-2026-0006. La version stable `2.54.2` est sortie ensuite avec des corrections de bugs, sans correctif de sécurité annoncé dans ses notes ; le runtime complet n’a pas été recompilé pour 4.1.
- L’audit en ligne exhaustif des dépendances transitives n’a pas été réalisable dans cet environnement. Les composants natifs/Ubuntu du runtime sont réutilisés depuis le paquet antérieur contrôlé ; ce rapport ne prétend pas qu’ils sont exempts de toute vulnérabilité.

## Sources, paquet et données personnelles

- Scan ciblé de 165 fichiers source et de 3 853 fichiers extraits de l’AppImage : aucun chemin personnel `/home/gerald`, nsec complète, npub fourni, jeton GitHub/Bearer ni métadonnée de construction `direct_url.json` ou bytecode Python restant.
- L’AppImage contient des données de clés de test intégrées en amont dans `libgnutls.so.30` pour les auto-tests cryptographiques GnuTLS. Elles correspondent à des vecteurs synthétiques de test de signature/DH, pas aux clés de l’application ou du propriétaire ; les sources amont les situent dans `lib/crypto-selftests-pk.c`. Des chaînes de format de clé dans libssh et cryptography sont des marqueurs de parseurs, pas des clés complètes.
- Les auteurs/committers de l’historique local sont des identités génériques du projet. Scan ciblé non exhaustif : il ne peut pas garantir l’absence de donnée personnelle inconnue ni remplacer un audit natif complet.

## Publication et vérification publique

- L’utilisateur a autorisé explicitement la publication le 15 novembre 2026.
- GitHub : release [v4.1](https://github.com/gerfondev/notestr-linux/releases/tag/v4.1), commit `949d57a`, tag `v4.1`.
- AppImage et fichier SHA-256 téléchargés depuis les URLs publiques après publication. L’AppImage public est identique au candidat contrôlé : SHA-256 `605183316b5a08098e4c22bb13105ad8a0908d36fb97d0d09a7486c3137a955f`.
- Le contrôle GTK graphique n’était pas disponible dans l’environnement de compilation ; l’utilisateur a autorisé la publication après les versions de test. Le contrôle non graphique `--check` réussit.
- Le commit et le tag ont été ajoutés sans réécriture de l’historique existant.
