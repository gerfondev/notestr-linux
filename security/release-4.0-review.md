# Revue sécurité et confidentialité — candidat 4.0 — 3 novembre 2026

## Android

- APK `Notestr-Android-4.0.apk`, versionName `4.0`, versionCode `73`, minSdk 26, target/compileSdk 36.
- SHA-256 : `ea12049c6bc388c5a87f032e33135344daac464fc8e2cee5ff313e7c34306731`.
- Signature APK v2 valide ; certificat de test local identique à celui de la version publique précédente. L’APK n’est pas débogable. Alignement ZIP vérifié. L’APK contient 505 entrées.
- 25 tests unitaires release réussis ; compilation des tests instrumentés réussie. Les tests instrumentés n’ont pas été exécutés sur appareil dans cette vérification.
- Graphe Gradle release résolu localement. Gradle 8.14.6, Kotlin 2.4.21 et correctifs de dépendances transitives des outils déjà intégrés. Les bibliothèques AndroidX/Compose conservent la base compatible SDK 36 ; la mise à niveau majeure candidate requiert une migration de l’outillage et du SDK, sans avis de sécurité pertinent identifié pour les versions actuellement embarquées. Aucun composant Android supplémentaire n’a été monté sans justification de sécurité et de compatibilité.
- Le bundle d’éditeur embarqué conserve ProseMirror 1.42.6 et DOMPurify 3.4.16, au-delà de la version corrigée de l’avis ProseMirror précédemment relevé. Le dépôt TOAST UI intégré reste archivé ; les limites d’entretien amont restent à surveiller.

## Linux

- AppImage `Notestr-4.0-x86_64.AppImage`, WebKitGTK 2.54.0 conservé du paquet précédemment contrôlé ; `websockets` 17.4 et `cryptography` 50.0.2 installés. Pillow 13.0.0 et les composants natifs corrigés qualifiés dans la revue 3.9.5 sont conservés.
- SHA-256 AppImage : `d95e06ae5c1fb2c460908d0f7dadbabeb5706637844ca868f79f0851a837c063`.
- Wheel SHA-256 : `7dc89c55bdde75443a324c1f39d421e6f677edf6935733f2e6db8745fe36ab55`.
- Archive source SHA-256 : `b4f771e49e1b573dd7b249ff8a1e4627bfee2006cbec5ae5e6c4dec13ba94219`.
- 128 tests Python réussis. `--version`, `--check`, imports GTK/WebKit et chiffrement/signature réussis. Le test GTK graphique de l’AppImage n’a pas pu s’exécuter : aucune session graphique/display disponible. L’AppImage signale aussi l’absence de cache Fontconfig accessible dans ce sandbox.
- `pip-audit` n’a pas pu joindre l’API OSV lors de la précédente tentative ; les versions directes/transitives du fichier verrouillé ont été comparées aux versions corrigées et avis officiels disponibles. Cela ne constitue pas un audit en ligne exhaustif.

## Confidentialité et limites

Scans ciblés des sources, du contenu extrait de l’APK et de l’AppImage, du wheel et de l’archive source : chemins personnels connus, identifiant public du compte déjà communiqué, nsec complète, bloc de clé privée PEM et jeton GitHub. Aucun de ces marqueurs n’a été trouvé dans les sources ou l’APK. L’AppImage contient trois marqueurs de début de clé dans des fichiers upstream de bibliothèques (`libssh`, GnuTLS et le module de sérialisation SSH de cryptography) ; aucun bloc PEM complet, chemin personnel, identifiant public connu, nsec complète ou jeton n’a été détecté. Les 13 images sources ont été inspectées ; aucune métadonnée EXIF/auteur/localisation n’a été trouvée.

Le contrôle est ciblé, pas exhaustif ; il ne peut pas détecter toute donnée personnelle inconnue. Les identités auteur existantes de l’historique Git sont conservées et ne sont pas embarquées dans les paquets. Aucun historique distant n’a été réécrit. L’APK, l’AppImage, le wheel et l’archive source sont des candidats locaux ; aucun push, tag, release ou téléversement n’a été effectué.
