# Vérification de la version 3.5.1 — 22 septembre 2026

## Dépendances Python

Les dépendances d’exécution et leurs dépendances indirectes ont été résolues
avec mise à jour complète dans l’environnement de construction. Les versions
exactes des 41 distributions sont enregistrées dans
`packaging/requirements-3.5.1.txt`. Ce fichier décrit la construction Linux
Python 3.12 ; il ne promet pas la compatibilité avec tous les environnements.

`pip-audit` 2.10.1, service PyPI, ne signale aucune vulnérabilité connue pour ces
41 versions, sans exclusion d’avis. Le résultat est conservé dans
`releases/3.5.1-python-audit.json`. Cette vérification ne constitue pas une preuve
d’absence de vulnérabilités inconnues.

Principales mises à jour par rapport à l’environnement précédent :

| Bibliothèque | Avant | Version embarquée |
| --- | --- | --- |
| cryptography | 41.0.7 | 50.0.1 |
| Pillow | 10.2.0 | 12.3.0 |
| markdown-it-py | 3.0.0 | 4.2.0 |
| cachetools | 5.3.0 | 7.2.0 |
| multidict | 6.8.0 | 6.9.1 |
| propcache | 0.5.2 | 0.5.4 |
| yarl | 1.24.5 | 1.25.1 |

## Bibliothèques natives et JavaScript

L’inventaire `releases/3.5.1-native-versions.json` recense les 181 paquets système
dont des fichiers sont présents dans l’AppImage. Les versions embarquées ont
été comparées aux candidats des index Ubuntu/Zorin actualisés le 22 septembre :
aucune version embarquée n’est antérieure au candidat disponible.

Les quatre bibliothèques Kerberos passent de `1.20.1-6ubuntu2.8` à
`1.20.1-6ubuntu2.10`. Les paquets officiels sont téléchargés par APT, extraits
localement et appliqués aux seuls fichiers déjà sélectionnés pour l’image.
Les licences correspondantes sont incluses. Les autres applications du système
hôte ne sont pas mises à jour par cette construction.

WebKitGTK et JavaScriptCore restent à `2.52.6-0ubuntu0.24.04.1`, version corrigée
pour les problèmes de l’avis officiel
[WSA-2026-0005](https://webkitgtk.org/security/WSA-2026-0005.html).
La version amont 2.54.0 existe, mais n’est pas proposée par ces dépôts ; la
construction conserve la branche prise en charge par la distribution.

DOMPurify 3.4.15 et TOAST UI Editor 3.2.2 correspondent aux versions stables
publiées dans le registre npm lors du contrôle. L’application utilise DOMPurify
3.4.15 via `customHTMLSanitizer`. Le bundle TOAST UI contient toujours une
ancienne copie interne de DOMPurify : elle n’est pas mise à niveau séparément,
et le point d’entrée de nettoyage de l’application utilise la version externe.
Ce contrôle de versions ne remplace pas un audit complet des dépendances internes
minifiées de TOAST UI. Voir les
[avis DOMPurify](https://github.com/cure53/DOMPurify/security/advisories).

## Confidentialité des livrables

Contrôles sur les fichiers sources candidats à la publication, les fichiers de
l’AppImage extraite, les membres du wheel et de l’archive source, et les sommes
de contrôle : chemins du compte local, chemins encodés, clés Nostr privées,
jetons GitHub, marqueurs de clés privées et fichiers de configuration utilisateur.
Les métadonnées de propriétaire de l’archive source sont normalisées à `root`,
UID/GID 0 ; le système de fichiers AppImage est également construit avec
`-all-root -no-xattrs`.

Aucune donnée personnelle du compte utilisateur n’a été détectée. Les alertes
restantes ont été examinées : délimiteurs de formats cryptographiques, clé
privée d’exemple déjà publiée dans la documentation amont de monstr, chemins d’exemples ou de construction amont de GTK, monstr et Rust.
Ces éléments proviennent des bibliothèques distribuées, pas du compte utilisateur.
Les mentions légales et les noms de contributeurs dans les licences sont conservés.
Aucune note réelle, clé du trousseau, sauvegarde ni configuration de compte n’est
incluse. Les tests utilisent une identité fictive et ne publient aucune note.

Ce contrôle porte sur les nouveaux livrables et le contenu de la révision publiée.
Il ne réécrit pas l’historique Git et ne prétend pas détecter toute forme possible
de donnée personnelle dans des ressources tierces.
