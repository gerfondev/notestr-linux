# Candidat local 3.6.dev23 — 1er octobre 2026

Le cache chiffré reste consultable pendant la synchronisation des relais. Un brouillon ouvert n’est pas remplacé à la fin de l’actualisation. Une publication fondée sur une version devenue obsolète est refusée afin de ne pas écraser la modification distante.

Les clics HTTP/HTTPS dans le mode Visuel sont transmis au navigateur par défaut. Les autres schémas et les clics déclenchés par script sont ignorés ; l’éditeur ne charge aucune page externe. Le lancement du navigateur n’hérite pas des chemins de bibliothèques de l’AppImage.

Le paquet reprend les composants vérifiés de 3.6, avec six mises à jour Ubuntu : gvfs/gvfs-libs 1.54.4-0ubuntu1~24.04.4, heif-gdk-pixbuf/libheif1 1.17.6-1ubuntu4.9, libgbm1 25.2.8-0ubuntu0.24.04.3 et libssl3t64 3.0.13-0ubuntu3.16. Aucun paquet du système hôte n’est modifié.

## Réserve de sécurité ouverte

[WSA-2026-0006](https://webkitgtk.org/security/WSA-2026-0006.html), paru le 29 septembre, recommande WebKitGTK 2.54.0. La branche Ubuntu Noble consultée fournit encore 2.52.6. Le candidat conserve cette bibliothèque avec une exception explicite pour l’essai local : contenu signé et chiffré pour le compte, HTML filtré, CSP restrictive, pages externes exclues, médias/images/canvas et WebGL désactivés. Skia reste utilisé pour le rendu du texte ; ces restrictions ne prouvent pas l’absence de toute exposition. Mettre à niveau le moteur vers une version corrigée et compatible, ou vérifier un correctif rétroporté, avant la prochaine publication. TOAST UI archivé reste également une action de maintenance.

Aucune publication autorisée. Tester l’ouverture après fermeture, avec un relais lent ou indisponible, puis les liens en mode Visuel. Le mode Markdown demeure un champ de saisie.
