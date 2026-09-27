# Version 3.6 — contrôle du 27 septembre 2026

Publication GitHub des versions Android et Linux 3.6 explicitement autorisée par l’utilisateur. Android versionCode 22. Numéros publics alignés, historiques conservés.

Dépendances : 699 versions Maven/Cargo/npm/PyPI interrogées via OSV, aucune alerte retournée ; 699 métadonnées officielles consultées sans erreur. Inventaire partagé basé sur les graphes inchangés des candidats testés. Index APT renouvelés et 181 paquets natifs Linux comparés : aucun correctif supplémentaire disponible après intégration de cURL 8.5.0-2ubuntu10.15 et Expat 2.6.1-2ubuntu0.6. Les 41 versions Python verrouillées sont conservées. DOMPurify 3.4.16 et retrait de l’ancien filtre interne inclus sur les deux plateformes. SDK Rust corrigé et JNA nettoyé identiques aux composants Android déjà contrôlés.

Exceptions de maintenance conservées : TOAST UI 3.2.2 archivé, migration nécessaire à terme ; composition JavaScript minifiée reconstruite à partir des dépendances amont, non garantie exhaustive. AGP/AndroidX et Rust de construction conservés pour leur compatibilité, sans prétendre utiliser partout la dernière version. WebKitGTK fourni par la branche Ubuntu corrigée plutôt que par la toute dernière version amont. Les avis Rust Windows/Cygwin ne concernent pas les cibles Linux/Android utilisées ; aucun nouveau binaire Rust compilé pour cette version.

Validation finale : 14 tests JVM, 19 tests instrumentés Android release et 45 tests Python réussis ; essais graphiques de l’AppImage réussis. APK non débogable, signature v2 et certificat des versions précédentes vérifiés. Contrôles ciblés sur 4 159 fichiers des deux paquets décompressés, sans marqueur personnel recherché ; les en-têtes PEM des parseurs de dépendances sont des constantes de format, pas des clés. Aucun téléphone réel ni Amber réel utilisé pour ces tests.

Confidentialité des sources et de l’historique : 1 678 entrées de sources et d’archives inspectées sans correspondance aux marqueurs personnels recherchés. Deux commits Android et un commit Linux déjà publiés portent des métadonnées d’auteur personnelles. Ces données restent dans l’historique existant, qui n’est pas réécrit ; elles ne sont pas reproduites dans les nouveaux fichiers. Aucun marqueur du propriétaire détecté dans les blobs historiques examinés. Les nouveaux commits et tags emploient l’identité neutre du projet.

Les résultats de confidentialité, tests, signatures et empreintes finales sont consignés dans les rapports `security/release-3.6-*.json`. Les sections suivantes conservent l’historique des contrôles, dont les anciens statuts de candidats. L’absence d’avis dans les bases interrogées ne garantit pas l’absence de vulnérabilité inconnue.

---

# Correctif d’icône Linux — 27 septembre 2026

Candidat local 3.5.3.dev2, sans publication. Deux icônes SVG locales sans dépendance supplémentaire ; sélection et changement d’état actualisent le dessin ainsi que l’infobulle et le nom accessible. Sauvegarde des sources avant modification.

Contrôle renouvelé des 699 coordonnées Maven/Cargo/npm/PyPI de l’inventaire partagé : aucune alerte OSV retournée, métadonnées officielles relues sans erreur. Dépendances Linux et correctifs natifs inchangés par rapport au candidat précédent ; comparaison APT des 181 paquets réalisée le 26 septembre, non répétée pour ce changement graphique. Exceptions et limites du contrôle précédent conservées, notamment TOAST UI archivé. Sources et nouvelles ressources contrôlées avec les motifs ciblés de confidentialité. Rapport de dépendances : security/linux-pin-icon-dependencies-2026-09-27.json.

45 tests Python réussis. Tests graphiques et contrôle du paquet final enregistrés dans security/linux-pin-icon-artifact.json. Aucun compte réel ni relais public utilisé.

---

# Candidats locaux avec épinglage — 26 septembre 2026

Aucune publication distante. Sauvegarde des deux projets effectuée avant modification ; archives et SHA-256 conservés séparément des livrables. Android 2.0-test.21 (versionCode 21), Linux 3.5.3.dev1. Format et limites fonctionnelles dans PINNING.md.

Contrôle renouvelé : 699 coordonnées Maven, Cargo, npm et PyPI interrogées via OSV, aucune correspondance retournée ; 699 consultations de métadonnées des registres officiels, sans erreur restante. Les erreurs initiales de décodage de l’index Rust ont été corrigées et toutes ses lignes relues. Inventaires et empreintes dans les rapports pinning-*.json. Graphe Android inchangé depuis 2.0 ; SDK natif et JNA conformes aux AAR vérifiés. Versions stables et avis de l’outillage consultés ; exceptions AGP/AndroidX/JDK/Rust de la revue précédente conservées. Les avis Rust examinés concernent Windows/Cygwin ou des versions antérieures à l’outil utilisé ; pas de reconstruction Rust pour ce changement. L’absence d’avis OSV ne démontre pas l’absence de risque.

Maintenance : TOAST UI 3.2.2 demeure archivé ; son remplacement reste une action à prévoir. Graphe JavaScript interne reconstitué, sans preuve exhaustive de chaque composant minifié. Linux reçoit DOMPurify 3.4.16 et le retrait de l’ancien module 2.3.3 intégré : nettoyage par défaut et personnalisé utilisent le même filtre maintenu. Les adaptations Linux de l’éditeur sont conservées. Pas de nouvelle bibliothèque pour l’épinglage.

Linux : index APT actualisés dans un dossier temporaire ; 181 paquets comparés. Correctifs cURL/GnuTLS 8.5.0-2ubuntu10.15 et Expat 2.6.1-2ubuntu0.6 téléchargés depuis Ubuntu et intégrés à l’AppImage. Correctifs Kerberos précédents conservés. Aucun paquet du système hôte installé/modifié. WebKitGTK 2.52.6 reste la branche de distribution, conforme à WSA-2026-0005 ; 2.54.0 amont non adoptée. Les 41 dépendances Python verrouillées ont été revérifiées avec OSV et PyPI, sans alerte identifiée. Le runtime AppImage conserve l’empreinte déjà contrôlée.

Confidentialité : contrôles ciblés des sources, ressources, images, archives AAR/JAR imbriquées et fichiers décompressés des deux livrables. Les essais utilisent uniquement les scalaires synthétiques publics 1 et 2. Aucun compte utilisateur réel consulté. Les chaînes d’en-tête PEM dans GnuTLS, libssh et cryptography sont des marqueurs de format, pas des clés privées ; un exemple nsec dans la documentation de distribution de monstr est retiré du paquet final, avec mise à jour du RECORD. Les licences et le code de monstr restent inchangés. Ces contrôles ne couvrent pas tous les encodages ni les données personnelles inconnues. Aucun historique Git, journal de test brut, cache utilisateur ou clé de signature n’est livré. Les historiques et la copie de publication ne sont pas modifiés.

Validation : 14 tests JVM, 8 tests instrumentés Android release, 45 tests Linux réussis. Tests GTK/WebKit de l’AppImage avec les correctifs natifs réussis ; épinglage/désépinglage et brouillon inchangé vérifiés. Lecture croisée Android/Linux validée avec événements signés et chiffrés synthétiques. Aucun test sur téléphone réel, Amber réel ou relais public. Limite Android de 2 000 événements par kind conservée.

APK non débogable, signature v2 et certificat de 2.0 conservés. Bibliothèques natives de l’APK identiques aux AAR vérifiés ; alignement de paquet vérifié. Empreintes finales et résultats de confidentialité dans security/pinning-artifacts.json et dans les SHA256SUMS remis avec les fichiers de test. Ces contrôles ne sont pas exhaustifs.

---

# Vérification de la version 3.5.2 — 23 septembre 2026

## Dépendances Python

Les dépendances d’exécution et leurs dépendances indirectes ont été résolues
avec mise à jour complète dans l’environnement de construction. Les versions
exactes des 41 distributions sont enregistrées dans
`packaging/requirements-3.5.2.txt`. Ce fichier décrit la construction Linux
Python 3.12 ; il ne promet pas la compatibilité avec tous les environnements.

`pip-audit` 2.10.1, service PyPI, ne signale aucune vulnérabilité connue pour ces
41 versions, sans exclusion d’avis. Le résultat est conservé dans
`releases/3.5.2-python-audit.json`. Cette vérification ne constitue pas une preuve
d’absence de vulnérabilités inconnues.

Les versions restent identiques à celles de 3.5.1 après résolution complète avec
actualisation des index. Aucun correctif supplémentaire n’est disponible dans
les versions compatibles consultées. Les correctifs déjà intégrés sont conservés.

Principales mises à jour intégrées depuis les versions antérieures à 3.5.1 :

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

L’inventaire `releases/3.5.2-native-versions.json` recense les 181 paquets système
dont des fichiers sont présents dans l’AppImage. Les versions embarquées ont
été comparées aux candidats des index Ubuntu/Zorin actualisés le 23 septembre :
aucune version embarquée n’est antérieure au candidat disponible.

Les quatre bibliothèques Kerberos conservent la mise à jour de `1.20.1-6ubuntu2.8` à
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
restantes ont été examinées : délimiteurs et blocs cryptographiques intégrés aux bibliothèques amont
(notamment GnuTLS, dont le fichier correspond à l’empreinte du paquet système), clé
privée d’exemple déjà publiée dans la documentation amont de monstr, chemins d’exemples ou de construction amont de GTK, monstr et Rust.
Ces éléments proviennent des bibliothèques distribuées, pas du compte utilisateur.
Les mentions légales et les noms de contributeurs dans les licences sont conservés.
Aucune note réelle, clé du trousseau, sauvegarde ni configuration de compte n’est
incluse. Les tests utilisent une identité fictive et ne publient aucune note.

Ce contrôle porte sur les nouveaux livrables et le contenu de la révision publiée.
Il ne réécrit pas l’historique Git et ne prétend pas détecter toute forme possible
de donnée personnelle dans des ressources tierces.
