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
python3 packaging/build-appimage.py /tmp/notestr-runtime-x86_64
./dist/Notestr-3.5.2-x86_64.AppImage --appimage-extract-and-run --check
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
python3 packaging/test-appimage.py dist/Notestr-3.5.2-x86_64.AppImage
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

Installer les versions Python validées avant la construction :

```bash
.venv/bin/python -m pip install -r packaging/requirements-3.5.2.txt
.venv/bin/python -m pip install -e '.[test]' build
mkdir -p build/native-updates
(cd build/native-updates && apt-get download libkrb5-3:amd64 libk5crypto3:amd64 libkrb5support0:amd64 libgssapi-krb5-2:amd64)
python3 packaging/build-appimage.py /tmp/notestr-runtime-x86_64 --native-debs build/native-updates
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
