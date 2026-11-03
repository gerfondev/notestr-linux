# Revue de sécurité — candidat Notestr Linux 4.0 — 3 novembre 2026

Rapport courant : [`security/release-4.0-review.md`](security/release-4.0-review.md). AppImage SHA-256 `d95e06ae5c1fb2c460908d0f7dadbabeb5706637844ca868f79f0851a837c063`; wheel et archive source empreintes et versions détaillées dans le rapport et `SHA256SUMS-4.0-Linux.txt`. 128 tests Python réussis, contrôles AppImage de version, imports et chiffrement réussis. Le test GTK graphique n’a pas pu s’exécuter sans affichage. La revue de dépendances, les scans ciblés et leurs limites sont consignés ; candidat local seulement, sans publication.

# Revue de sécurité et confidentialité — Notestr 3.9.5 — 31 octobre 2026

## Linux

Pillow 12.3.0 a été remplacé par Pillow 13.0.0. Les avis amont de sécurité publiés le 17 octobre indiquent que 12.3.0 est affectée et que 13.0.0 corrige ces défauts ([avis Pillow](https://github.com/python-pillow/Pillow/security/advisories/GHSA-v9pv-5gc8-w2m6), [notes 13.0.0](https://pillow.readthedocs.io/en/stable/releasenotes/13.0.0.html)). L’AppImage embarque aussi les versions Ubuntu Noble actualisées : GLib 2.80.0-6ubuntu3.10, Brotli 1.1.0-2ubuntu0.1, liblzma 5.6.1+really5.4.5-1ubuntu0.4, zlib 1:1.3.dfsg-3.1ubuntu2.3 et typelib GLib 2.80.0-6ubuntu3.10. Les avis Ubuntu Brotli et XZ documentent les versions corrigées [Brotli](https://ubuntu.com/security/notices/USN-8956-1) et [XZ](https://ubuntu.com/security/notices/USN-8945-1).

Le runtime AppImage réutilise le WebKitGTK 2.54.0 construit précédemment depuis les sources et contrôlé pour la réserve WSA-2026-0006. Cinq paquets système ont été extraits des paquets Ubuntu obtenus après rafraîchissement des index signés. `--appimage-extract-and-run --version` affiche 3.9.5 ; `--check` confirme GTK4/libadwaita, WebKitGTK 6.0, Nostr et les fonctions cryptographiques. FUSE n’est pas disponible dans l’environnement, donc le montage direct n’a pas pu être vérifié.

Limite : `pip-audit` n’a pas pu joindre `api.osv.dev` (échec de résolution DNS). L’audit en ligne complet des dépendances Python n’est donc pas confirmé et nous ne déclarons pas le paquet exempt de vulnérabilités. Les réserves natives documentées dans la revue antérieure restent applicables.

## Android

APK versionName 3.9.5, versionCode 71, non débogable, signature v2 et certificat habituel vérifiés, alignement 16 Kio confirmé. `clean testReleaseUnitTest assembleRelease` a réussi avec 22 tests JVM. SHA-256 APK : `e1b1fce8bdfb313822677c19301a3f636249e240f61c3dae2e7d09fbfee8ac3e`.

Gradle 8.14.6 et Kotlin 2.4.21 sont les versions stables examinées ; Gradle 8.14.6 corrige trois vulnérabilités à sévérité élevée ([notes Gradle 8.14.6](https://docs.gradle.org/8.14.6/release-notes.html)). Compose BOM 2026.06.00, Lifecycle 2.10.0, AGP 8.13.2 et SDK 36 sont conservés. Les versions AndroidX plus récentes et les changements d’outillage nécessaires n’ont pas été intégrés sans migration ni validation de compatibilité. Les limites précédemment documentées sur AndroidX, TOAST UI et FFI restent ouvertes. L’audit Maven/OSV n’a pas pu être rafraîchi faute d’accès réseau ; il n’est pas déclaré complet. L’utilisateur a confirmé avoir testé le candidat Android nommé dev ; son empreinte APK est identique à la copie de livraison 3.9.5. La confirmation de test et l’autorisation de publication sont reçues.

## Confidentialité — périmètre et limites

Scans ciblés des sources Android/Linux, du contenu décompressé de l’APK, de l’AppImage, du wheel et de l’archive source : chemins personnels connus, identifiant public connu, nsec complète, bloc PEM de clé privée et jetons GitHub. Aucune donnée personnelle recherchée détectée dans les périmètres inspectés. L’AppImage contient cinq clés privées de test publiques intégrées à GnuTLS pour ses autotests cryptographiques, identifiées par leur présence dans le code amont `crypto-selftests-pk.c` ; elles ne sont pas des clés du propriétaire. Les marqueurs PEM de libssh/cryptography ne forment pas de bloc complet. Ce contrôle n’est pas exhaustif et ne permet pas d’exclure d’autres formes ou données inconnues. Les anciens commits distants conservent les identités auteur déjà présentes ; l’historique n’a pas été réécrit. Les rapports JSON dans les arbres sources donnent les versions, empreintes et limites par plateforme.

## État

Publication effectuée le 31 octobre 2026 : release Linux [3.9.5](https://github.com/gerfondev/notestr-linux/releases/tag/v3.9.5), tag `v3.9.5`, commit `f298e64`. AppImage, wheel, archive source, notes et checksum téléchargés anonymement depuis GitHub ; les sommes des trois paquets sont identiques aux artefacts contrôlés. SHA-256 AppImage : `37c42105f8d092d84d27f2eebb0aea3fd39e63253a876cf4e5d8ade0c8ba12d2`. Les limites d’audit et de confidentialité décrites ci-dessus restent applicables.
