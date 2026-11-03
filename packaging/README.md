# Construction AppImage — Notestr 4.0

La version courante est **4.0**. Les nouveautés sont décrites dans
[la note de version](../RELEASE-NOTES-4.0.md) et les dépendances Python de
construction sont verrouillées dans [`requirements-4.0.txt`](requirements-4.0.txt).

## Prérequis

Construire sur Ubuntu 24.04 / Zorin OS 18 amd64, avec Python 3.12, un venv
installé depuis `requirements-4.0.txt`, `squashfs-tools`, `curl` et
`python3-packaging`. Le paquet cible glibc ≥ 2.39 ; les autres distributions
doivent être testées avant d’annoncer leur compatibilité. Les pilotes, certificats
TLS et le service de trousseau restent fournis par le système hôte.

Depuis la racine du projet, fournir un runtime AppImage type 2 vérifié et une
installation WebKitGTK 2.54.0 validée, puis lancer :

```bash
python3 packaging/build-appimage.py /chemin/vers/runtime-x86_64 \
  --webkit-install /chemin/vers/webkit-install \
  --webkit-runtime-root /chemin/vers/ubuntu-build-root
./dist/Notestr-4.0-x86_64.AppImage --appimage-extract-and-run --check
python3 packaging/test-appimage.py dist/Notestr-4.0-x86_64.AppImage
```

Le constructeur écrit l’AppImage et son SHA-256 dans `dist/`, exclut les caches,
les chemins d’installation éditable, `direct_url.json` et les données utilisateur.
Le test du paquet utilise un compte synthétique et un répertoire temporaire sans
publier sur le réseau.

Pour la publication, vérifier l’empreinte du paquet et suivre le contrôle de
sécurité courant dans [`SECURITY-REVIEW.md`](../SECURITY-REVIEW.md). Ne pas
réutiliser le runtime `continuous` sans vérifier son origine et son empreinte.
