# Notes privées Nostr — Version 4.0 Linux

Version du paquet Python : `4.0`.

Application Python 3 + GTK4/libadwaita pour lire et éditer des notes Markdown privées compatible avec la version Notestr Android. Langues disponibles : français, anglais.

## Version 4.0

- Ajout de dossiers nommés, création, renommage et suppression sécurisée sans effacer les notes.
- Notes épinglées visibles en tête de liste et dans leur dossier ; « Sans dossier » en fin de liste.
- Mises à jour de sécurité Python : Pillow 13.0.0, cryptography 50.0.2 et websockets 17.4.
- Version Linux alignée sur Android : 4.0. [Notes de version](RELEASE-NOTES-4.0.md).
- Les notes des versions précédentes sont conservées dans [`release-notes/`](release-notes/).

Télécharger [Notestr Linux 4.0 — AppImage x86_64](https://github.com/gerfondev/notestr-linux/releases/latest/download/Notestr-4.0-x86_64.AppImage) ou consulter [la release GitHub](https://github.com/gerfondev/notestr-linux/releases/latest). Les empreintes des fichiers sont dans `SHA256SUMS-4.0-Linux.txt`.

## Installation Debian, Ubuntu et Zorin

L’application nécessite Python ≥ 3.10, GTK4 et libadwaita. Le mode visuel utilise
**WebKitGTK 6.0 (GTK4)**, différent de WebKit2 4.0/4.1 (GTK3).
La version actuelle a été vérifiée sous Zorin OS 18.1. Le paquet WebKitGTK requis
est également proposé pour [Ubuntu 24.04](https://packages.ubuntu.com/noble/gir1.2-webkit-6.0)
et [Debian 12](https://packages.debian.org/bookworm/gir1.2-webkit-6.0).
Les autres versions de distribution n’ont pas toutes été testées.

### 1. Installer les paquets système

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip python3-gi \
  gir1.2-gtk-4.0 gir1.2-adw-1 gir1.2-webkit-6.0 \
  gnome-keyring libsecret-1-0 \
  build-essential pkg-config python3-dev libffi-dev libssl-dev libsecp256k1-dev
```

Si votre distribution ne propose pas `gir1.2-webkit-6.0`, vous pouvez installer
les autres paquets et utiliser le mode Markdown seul. Le mode visuel nécessite
une distribution fournissant cette bibliothèque.

### 2. Installer le projet Python

Extraire l’archive source 4.0 dans le dossier choisi. Elle crée le dossier
`nostr-private-notes-4.0`, qui contient `pyproject.toml`, `src` et
`lancer-notes.sh`. Les exemples ci-dessous utilisent `/home/user/notestr` ;
adapter ce chemin au dossier réellement extrait.

```bash
cd /home/user/notestr
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
chmod +x lancer-notes.sh
./lancer-notes.sh --check
```

Ces commandes supposent une installation neuve, sans ancien `.venv`. Si le dossier
provient d’une sauvegarde ou d’un autre PC, suivre d’abord la section restauration
ci-dessous. Sur le même poste avec un venv fonctionnel, suivre la section mise à jour.

`--system-site-packages` permet au venv de trouver les bindings GTK installés par
apt. Utiliser **/usr/bin/python3**, fourni par la distribution. PyGObject est fourni
par apt et n’est pas reconstruit par pip.

`pip install -e .` installe les dépendances déclarées dans `pyproject.toml`, dont
`monstr`, `websockets`, `keyring`, **`argon2-cffi`** pour le verrouillage et
**`markdown-it-py`** pour les retours à la ligne.
Les ressources de l’éditeur visuel sont déjà embarquées : aucune installation de
Node.js ni compilation JavaScript n’est nécessaire.

### 3. Lancer l’application

Depuis le dossier du projet :

```bash
./lancer-notes.sh
```

Ou depuis n’importe quel répertoire (en adaptant `user`) :

```bash
/home/user/notestr/lancer-notes.sh
```

Le lanceur trouve son propre dossier et utilise directement `.venv/bin/python`.
Il n’est pas nécessaire d’activer le venv, de réinstaller le projet ou d’exécuter
`--check` à chaque lancement. Ne pas lancer l’application avec sudo ; utiliser
une session graphique Linux. Le trousseau Secret Service doit être disponible
et déverrouillé pour mémoriser la clé.

### Mise à jour d’une installation existante

Fermer l’application, mettre en place les nouveaux fichiers du projet, puis :

```bash
cd /home/user/notestr
.venv/bin/python -m pip install -e .
./lancer-notes.sh --check
./lancer-notes.sh
```

Si le mode visuel est ajouté pour la première fois, installer aussi
`gir1.2-webkit-6.0` avec apt. La configuration, le cache et le trousseau existants
sont réutilisés ; aucune migration des notes n’est nécessaire pour cette version.

### Recréer l’environnement Python

L’archive source ne transporte pas de venv lié à une machine particulière. Après
extraction ou déplacement du projet, créer un environnement adapté au système :

```bash
cd /home/user/notestr
/usr/bin/python3 -m venv --system-site-packages .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
```

Les notes chiffrées en cache et la clé du trousseau ne sont pas incluses dans
l’archive source. Pour récupérer ses notes sur un autre ordinateur, connecter le
même compte et configurer au moins un relais commun.

### Dépannage rapide

- **`gi` introuvable** : recréer le venv avec `/usr/bin/python3` et
  `--system-site-packages`, puis réinstaller le projet.
- **Mode visuel indisponible** : installer `gir1.2-webkit-6.0`, puis relancer.
- **Module Python manquant, notamment `markdown_it`** : relancer
  `.venv/bin/python -m pip install -e .` depuis le dossier du projet.
- **Trousseau inaccessible** : le déverrouiller dans « Mots de passe et clés »,
  ou décocher son utilisation pour garder la clé uniquement pendant la session.
- **Ancien script de lancement en échec** : utiliser `lancer-notes.sh`.
  Un fichier `activate` se charge avec `. .venv/bin/activate` ; il ne s’exécute
  pas directement. Le lanceur fourni évite cette étape.

## Première utilisation

1. Dans **Compte et relais**, saisir la clé privée du compte Nostr utilisé pour les notes :
   `nsec1…` ou 64 caractères hexadécimaux. Une `npub` ne permet pas de déchiffrer.
2. Garder `wss://relay.decentralia.fr` ou ajouter plusieurs relais, un par ligne.
   Pour synchroniser les notes entre Notestr Android et Linux, configurer au moins un relais commun.
3. Choisir d’enregistrer la clé dans le trousseau Linux, ou seulement en mémoire
   pour cette session. Le compte mémorisé se rouvre au lancement suivant.
4. **Actualiser** charge les notes et les demandes de suppression de l’utilisateur.
   Cliquer une note pour l’ouvrir ; la recherche parcourt tout le Markdown déchiffré.
5. **Nouvelle**, saisir du Markdown, puis **Publier**. La première ligne non vide
   fournit le titre de la liste ; aucun titre séparé n’est envoyé au relais.
6. Modifier puis **Publier** conserve exactement le même tag `d`.
7. **Supprimer** demande confirmation et publie une demande NIP-09.
8. **Exporter PDF** choisit un emplacement local et crée une copie PDF de la note
   actuellement affichée, sans la publier ni modifier son contenu.

L’éditeur permet de choisir entre la mise en forme visuelle et le Markdown source. Les changements non publiés
sont signalés dans le titre de fenêtre. Changer de note, actualiser, changer de
compte ou fermer nécessite de confirmer leur abandon. Une publication en échec
conserve le texte dans l’éditeur. Aucun brouillon n’est sauvegardé automatiquement :
un arrêt brutal peut perdre les modifications en mémoire.

La barre inférieure indique combien de relais ont accepté la publication et les
échecs éventuels. **Un succès partiel n’est pas une réplication complète.** Il n’y a
les erreurs et états en attente sont affichés. Une publication sans accusé peut néanmoins avoir atteint un relais : actualiser pour vérifier avant de réessayer.

## Format des notes

Chaque note utilise un événement Nostr `kind 33457`. Son Markdown est chiffré NIP-44 v2 avec la clé privée et la clé publique du même compte. Les métadonnées de dossiers, d’épinglage, de verrouillage et de corbeille sont publiées chiffrées dans des événements de sauvegarde dédiés.

La suppression publie un événement NIP-09 (`kind 5`) qui référence la version courante et l’adresse de la note. Elle ne peut pas garantir l’effacement des copies conservées par des relais ou d’autres clients. Les notes indéchiffrables sont comptées et ne sont pas ouvertes pour édition.

Les événements reçus sont vérifiés : auteur, structure, empreinte du contenu et signature. La version la plus récente est retenue ; en cas d’égalité temporelle, l’identifiant lexicalement le plus petit gagne. L’application refuse de modifier une note dans la même seconde que sa version précédente pour éviter les égalités.

**Périmètre :** notes personnelles chiffrées vers soi. Les notes indéchiffrables ne sont pas ouvertes pour édition. Le format des événements est documenté et implémenté dans ce dépôt.

## Stockage local

- Clé privée : Secret Service / GNOME Keyring, service `nostr-notes`, compte = pubkey.
  Aucun backend de stockage en clair n’est utilisé en repli.
- Sans mémorisation : clé uniquement en mémoire, à ressaisir au lancement suivant.
  Décocher la mémorisation ne supprime pas une ancienne entrée du trousseau ; utiliser
  « Mots de passe et clés » pour la retirer si nécessaire.
- Configuration et cache : `$XDG_DATA_HOME/nostr-notes`, par défaut
  `~/.local/share/nostr-notes`. Répertoire `0700`, fichiers `0600`, écritures atomiques.
- `config.json` contient les relais et éventuellement la pubkey du compte mémorisé.
- `<pubkey>.json` contient uniquement les événements signés, avec Markdown chiffré,
  ainsi que les demandes de suppression. Les dates, tags et identifiants sont publics.
- Aucun titre ni contenu Markdown déchiffré n’est écrit dans le cache. Le texte et la
  clé sont présents dans la mémoire du processus ; Python ne garantit pas leur effacement.

Le cache garde les versions reçues et les demandes de suppression. Une note supprimée
reste donc éventuellement présente sous forme chiffrée dans ce cache ; aucune purge
historique n’est implémentée. Le cache permet de consulter les notes connues si le
réseau échoue. Il ne constitue pas une sauvegarde des brouillons non publiés.

## Réseau et limites

Les opérations passent par un worker pour garder l’interface réactive. Les relais
sont interrogés en parallèle. Chaque opération attend au plus 25 secondes par relais,
avec pages de 1 000 événements et borne de 100 pages par kind. Les requêtes récupèrent
séparément `33457` et `5`, recouvrent la seconde frontière, puis dédupliquent. Les
saturations détectées sont signalées ; un relais peut néanmoins omettre des données.
La récupération n’est donc pas une garantie d’exhaustivité globale.

Les notes sont actualisées automatiquement à l’ouverture du compte. Ensuite, les actualisations sont manuelles. Les modifications hors connexion restent chiffrées dans la file locale et sont proposées à la synchronisation lorsque la connexion revient. Il n’y a pas de fusion de modifications simultanées entre clients : actualiser avant de modifier une note utilisée sur un autre appareil.
Le dernier événement retenu par le relais fait foi. Les relais doivent autoriser
`33457` et `5`, accepter les connexions sans NIP-42 et les tailles de messages utilisées.
L’application limite le Markdown à 1–65 535 octets UTF-8, le format historique NIP-44 v2
supporté ici. Elle n’accepte que les URL `wss://` avec vérification TLS normale.

## Structure

```text
pyproject.toml
README.md
lancer-notes.sh
src/nostr_notes/
    __main__.py   lancement et vérification --check
    app.py        fenêtres GTK4/libadwaita
    editor.py     modes Visuel/Markdown et pont WebKit sécurisé
    assets/       éditeur web local, traduction, styles et licences
    markdown.py   sauts de ligne explicites avant chiffrement
    core.py       notes Nostr, chiffrement, dossiers, versions et suppressions
    relay.py      requêtes WebSocket, pagination, EOSE et OK
    storage.py    configuration, cache et trousseau
tests/
    test_core.py
    test_relay.py
    test_editor_assets.py
    test_markdown.py
    gtk_editor_smoke.py
```

## Vérifications

```bash
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m compileall -q src tests
python -m pytest -q
nostr-notes --check
```

`--check` utilise une clé de test connue, uniquement en mémoire, ne contacte aucun
relais et ne crée aucun compte. Il importe aussi GTK4/libadwaita sans ouvrir de fenêtre.

Les tests vérifient notamment : chiffrement/déchiffrement Unicode, signature et
contenu altéré, identifiant `d`, mise à jour, égalité d’horodatage, suppressions par
adresse et événement, faux auteur, limites de taille, permissions du cache,
pagination, accusés `OK`, refus et pannes partielles. Le transport y est simulé. Le bilan de cette exécution figure dans [VALIDATION.md](VALIDATION.md).

### Test graphique (facultatif)

Dans une session graphique, après avoir installé les dépendances de test :

```bash
python tests/gtk_editor_smoke.py
```

Ce test utilise une clé de test connue et un répertoire de données temporaire.
Il n’ouvre pas votre trousseau et intercepte la publication avant le réseau. Il
vérifie les modes, les allers-retours Markdown, la synchronisation avant chiffrement,
la politique de connexion et le rejet des mises à jour provenant d’une ancienne note.
Une fenêtre temporaire est affichée, puis fermée.

### Retours à la ligne

Le mode visuel lit les sauts Markdown explicites. À la publication depuis les
deux modes, les simples retours de paragraphe deviennent des sauts explicites
(deux espaces avant le retour). Il n’est pas nécessaire d’ajouter une ligne vide
pour séparer deux phrases. `markdown-it-py` distingue le texte du code et de la
structure Markdown pour effectuer cette transformation.

Les notes stockées ne sont pas modifiées en arrière-plan : ouvrir une ancienne
note puis cliquer **Publier** suffit à enregistrer ses sauts explicites. Une simple
consultation sans publication conserve exactement le texte source existant.

### Moteur visuel et sécurité

Les installations depuis le wheel ou les sources nécessitent WebKitGTK 2.54.0 ou ultérieur pour le mode Visuel. Un moteur plus ancien conserve uniquement le mode Markdown. Utiliser l’AppImage pour bénéficier du moteur corrigé embarqué.

## Modifications hors connexion

Le bouton Publier enregistre une modification chiffrée sur cet appareil avant de tenter sa synchronisation. Les modifications en attente persistent au redémarrage. La reprise nécessite une application ouverte et déverrouillée ; les conflits conservent les deux versions. Voir [OFFLINE.md](OFFLINE.md) pour le fonctionnement, les limites et le protocole de test.
