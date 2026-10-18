# Notestr 3.7

Android et Linux conservent le même numéro de version : **3.7**.

## Nouveautés et corrections

- **Cache des notes** : affichage des notes en cache avant la réponse des relais et consultation possible pendant la synchronisation. Le cache disque reste chiffré ; le cache de déchiffrement Android est limité à la session et vidé au verrouillage.
- **Liens ouverts dans le navigateur** : correction des liens HTTP/HTTPS dans l’éditeur Android et Linux. Sous Linux, le clic droit propose également « Ouvrir le lien dans le navigateur ». Curseur main au survol, y compris sur Android avec une souris.
- **Version dans les paramètres** : affichage du numéro exact de l’application installée.
- **Français et anglais** : choix de langue mémorisé dans les paramètres, appliqué immédiatement sur Android et au prochain lancement sur Linux. Le contenu des notes reste inchangé.
- Conservation des brouillons pendant la synchronisation ; refus des publications fondées sur une ancienne version pour limiter les écrasements de modifications.

## Sécurité

- WebKitGTK et JavaScriptCore 2.54.0 embarqués dans l’AppImage, avec les correctifs de WSA-2026-0006.
- Six mises à jour de paquets Ubuntu intégrées depuis 3.6. Contrôles des sources, dépendances et paquets documentés dans SECURITY.md, avec leurs limites et exceptions d’exposition.
- Installation Python avec un ancien WebKit système : mode Markdown disponible, éditeur visuel réservé à WebKit 2.54.0 ou ultérieur.

## Installation

Android : installer l’APK par-dessus la version précédente, sans désinstallation. Certificat conservé, versionCode 26, APK non débogable.

Linux : fermer l’ancienne application avant de lancer l’AppImage 3.7. Pour changer la langue, choisir Français ou English dans Compte et relais, enregistrer puis relancer Notestr.

Les fichiers SHA-256 accompagnent les paquets. Les contrôles de sécurité et de confidentialité sont ciblés et ne constituent pas un audit exhaustif. Les historiques distants et les versions précédentes sont conservés.
