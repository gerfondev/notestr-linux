# AppImage amd64

Construire sur Ubuntu 24.04 / Zorin OS 18 amd64, avec Python 3.12 et les paquets
système du README principal. Installer aussi `squashfs-tools`, `curl` et `python3-packaging`.
Le projet doit disposer d’un `.venv` fonctionnel, avec ses dépendances installées.
Le paquet cible glibc ≥ 2.39 ; les autres distributions doivent être testées avant
d’annoncer leur compatibilité. Les pilotes graphiques, certificats TLS et le
service de trousseau restent fournis par le système hôte.

Depuis la racine du projet :

```bash
curl -fL https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64 -o /tmp/notestr-runtime-x86_64
python3 packaging/build-appimage.py /tmp/notestr-runtime-x86_64 --webkit-install /tmp/notestr-webkit-build/webkit-install --webkit-runtime-root /tmp/ubuntu-build-root
./dist/Notestr-3.9.1-x86_64.AppImage --appimage-extract-and-run --check
```

Le runtime provient du projet officiel [AppImage/type2-runtime](https://github.com/AppImage/type2-runtime).
Pour reproduire une construction, conserver le runtime et son empreinte : la
version `continuous` évolue. Le script vérifie le format et l’architecture du
runtime, mais sa provenance doit être contrôlée avant de lui confier un binaire.

La sortie comprend un `.AppImage` exécutable et son fichier `.sha256` dans `dist/`.
Le script utilise un AppDir temporaire, résout les dépendances natives avec `ldd`
et inclut les bibliothèques chargées via GI, les ressources GTK et les processus
WebKit. Les dépendances Python sont résolues depuis les métadonnées des paquets ;
le venv entier n’est pas copié. Les icônes d’autres applications sont exclues,
et seules les notices de licence des paquets système embarqués sont conservées. Il exclut les caches Python, les chemins d’installation éditable et les
fichiers `direct_url.json`. Il ne copie aucune note, clé, configuration utilisateur
ni sauvegarde. Le bac à sable WebKit reste actif.

Vérification graphique de l’image produite, dans une session Linux :

```bash
python3 packaging/test-appimage.py dist/Notestr-3.9.1-x86_64.AppImage
```

Ce test extrait temporairement l’image et exécute le test GTK/WebKit avec son
Python et ses bibliothèques embarquées. Il utilise une identité de test et un
répertoire de données temporaire, sans publication réseau.

Runtime utilisé pour la construction du 20 septembre 2026 :
`sha256:1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf`.

## Numérotation et historique

La source unique est `nostr_notes.__version__` dans `src/nostr_notes/__init__.py`.
Setuptools et le constructeur AppImage utilisent cette valeur.
`python -m nostr_notes --version` affiche la version sans ouvrir l’interface.
Le test `tests/test_version.py` contrôle aussi les noms de fichiers documentés.

Chaque publication ajoute un nouveau commit et un tag correspondant à la version
(par exemple `v3.5`), sans modifier les commits des versions précédentes et sans
push forcé. Les tags `v3.1` et `v3.4` identifient les publications historiques.
Le fichier AppImage et son SHA-256 doivent correspondre à cette version.

## Reconstruction 3.5.2 et mises à jour natives

Installer les versions Python validées avant la construction (pour 3.6 et 3.7 : `packaging/requirements-3.9.txt`) :

```bash
.venv/bin/python -m pip install -r packaging/requirements-3.5.2.txt
.venv/bin/python -m pip install -e '.[test]' build
mkdir -p build/native-updates
(cd build/native-updates && apt-get download libkrb5-3:amd64 libk5crypto3:amd64 libkrb5support0:amd64 libgssapi-krb5-2:amd64)
python3 packaging/build-appimage.py /tmp/notestr-runtime-x86_64 --native-debs build/native-updates --webkit-install /tmp/notestr-webkit-build/webkit-install --webkit-runtime-root /tmp/ubuntu-build-root
.venv/bin/python packaging/build-python.py
```

N’utiliser pour `--native-debs` que les paquets officiels récupérés avec APT pour
la même distribution et la même architecture. La version 3.5.2 utilise Kerberos
`1.20.1-6ubuntu2.10`. L’option remplace uniquement les fichiers déjà embarqués,
et ajoute les versions à `usr/share/doc/native-versions.json` dans l’image.
Les alias `/lib` et `/usr/lib` sont pris en compte pour retrouver les licences.
Le constructeur Python normalise les propriétaires des archives source afin
de ne pas publier le nom du compte Linux de construction.

Le runtime AppImage du 22 septembre conserve l’empreinte documentée ci-dessus.
Les résultats d’audit et leurs limites sont décrits dans [SECURITY.md](../SECURITY.md).

Les versions disponibles ont été revérifiées le 23 septembre 2026 pour 3.5.2.
Aucune mise à jour supplémentaire n’est disponible dans les dépôts consultés.

## Construction 3.6

Pour la version 3.9, utiliser le verrou `requirements-3.9.txt`. La construction inclut sept mises à jour Ubuntu Noble des bibliothèques natives distribuées : `gir1.2-soup-3.0=3.4.4-5ubuntu0.9`, `libsoup-3.0-0=3.4.4-5ubuntu0.9`, `libfreetype6=2.13.2+dfsg-1ubuntu0.2`, `libpng16-16t64=1.6.43-5ubuntu0.7`, `librsvg2-2=2.58.0+dfsg-1ubuntu0.1`, `librsvg2-common=2.58.0+dfsg-1ubuntu0.1` et `libxml2=2.9.14+dfsg-1.3ubuntu3.10`. Les archives officielles et leurs empreintes figurent dans le rapport de sécurité 3.9. Le constructeur ne modifie pas le système hôte.

## WebKit corrigé pour 3.7

Le moteur Ubuntu 2.52.6 est remplacé par WebKitGTK 2.54.0 compilé depuis l’archive officielle, dont l’empreinte est vérifiée par `build-webkit.py`. Les options correspondent à l’usage local de l’éditeur : GStreamer, vidéo, audio Web, WebGL et synthèse vocale désactivés. L’installation est écrite dans un répertoire DESTDIR, jamais dans le système hôte.

```sh
python3 packaging/build-webkit.py webkitgtk-2.54.0.tar.xz /tmp/notestr-webkit-build
python3 packaging/build-appimage.py /tmp/runtime-x86_64 --webkit-install /tmp/notestr-webkit-build/webkit-install --webkit-runtime-root /tmp/ubuntu-build-root
```

Fournir aussi `--native-debs` avec les mises à jour Ubuntu vérifiées. Le fichier embarqué `webkit-source-build.json` identifie le remplacement source ; `native-versions.json` conserve l’inventaire de la base Ubuntu. Tester l’AppImage final avec `packaging/test-appimage.py` et vérifier toutes les dépendances ELF avant distribution.

Le constructeur applique une garde `ENABLE(VIDEO)` manquante dans `JSHTMLMediaElementCustom.cpp`, cohérente avec son en-tête généré. Ce correctif de compilation exclut uniquement du code vidéo déjà désactivé. Les empreintes avant/après sont dans `webkit-build-patches.json` et dans le manifeste embarqué.

## Construction 3.7.1

Conserver WebKitGTK/JavaScriptCore 2.54.0 et les dépendances Python qualifiées de 3.7. Ajouter au jeu de paquets natifs Ubuntu `libgbm1=25.2.8-0ubuntu0.24.04.4`. Voir SECURITY-REVIEW.md et les rapports 3.7.1 pour les avis natifs non corrigés et leur analyse d’exposition.
