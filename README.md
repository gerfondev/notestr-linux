# Notes privées Nostr — V3.1 Linux

Documentation mise à jour le 15 septembre 2026. Version du paquet Python : `0.3.1`.

Application Python 3 + GTK4/libadwaita pour lire et éditer des notes Markdown privées
au format des **documents personnels Pages by Formstr**. Interface en français.

## Nouveauté V3 : verrouillage au démarrage

Au premier lancement de la V3, l’application demande de créer un mot de passe d’au
moins huit caractères. Ce mot de passe est ensuite demandé avant le chargement de
la clé Nostr et des notes. Après cinq erreurs, les nouvelles tentatives sont
suspendues pendant trente secondes.

Le mot de passe n’est jamais enregistré. Un sel aléatoire et une empreinte dérivée
avec Argon2id sont conservés dans `~/.local/share/nostr-notes/lock.json`, avec des
permissions limitées au compte Linux. Cette protection bloque l’accès ordinaire
depuis une session déjà ouverte ; elle ne remplace pas le chiffrement du disque ni
le verrouillage de la session Linux. Comme toute application exécutée sous le même
compte, elle ne peut pas résister à une personne capable d’en modifier le code ou
les fichiers locaux.

### Modifier le mot de passe

Ouvrir **Compte et relais**, puis cliquer sur **Modifier le mot de passe**. Saisir
le mot de passe actuel, le nouveau mot de passe et sa confirmation. Le changement
est immédiat et un nouveau sel aléatoire est créé. Une erreur sur le mot de passe
actuel ou un nouveau mot de passe trop court laisse l’ancien verrouillage intact.

## Nouveautés V2 : éditeur visuel

Deux modes sont disponibles au-dessus de la note :

- **Visuel** : mise en forme immédiate, titres, gras, italique, texte barré,
  listes, tâches à cocher, citations, liens, tableaux et blocs de code.
- **Markdown** : modification directe du texte source ; les retours simples du texte deviennent explicites à la publication.

Le mode visuel est sélectionné par défaut lorsque WebKitGTK est disponible.
La barre d’outils et les raccourcis usuels (Ctrl+B, Ctrl+I, Ctrl+Z) permettent la
mise en forme. Le collage insère du texte simple ; les fichiers, images collées
et dépôts de fichiers ne sont pas pris en charge. Les liens sont éditables mais
ne s’ouvrent pas depuis la note ; les images distantes ne sont pas chargées.

Une simple consultation ou un aller-retour Visuel/Markdown **sans modification**
conserve exactement le Markdown original. Une édition visuelle peut normaliser
les marqueurs et les espaces et ne préserve pas nécessairement toutes les syntaxes
spéciales (HTML brut, extensions Markdown, images). Pour ces documents, utiliser
le mode Markdown. À la publication, les simples retours de paragraphe deviennent des sauts Markdown explicites ; le code et la structure Markdown sont préservés.
Le texte courant est récupéré avant publication, changement de
note ou fermeture, y compris les dernières frappes de l’éditeur visuel.

Le contenu envoyé reste du **Markdown chiffré NIP-44**, kind `33457`, avec le même
identifiant `d` lors d’une modification. La clé privée ne passe jamais dans le
composant web. Aucun service web n’est nécessaire pour afficher l’éditeur :
TOAST UI Editor 3.2.2, sa traduction française et DOMPurify 3.4.15 sont embarqués.
Les statistiques d’usage sont désactivées. Une politique CSP interdit les
connexions, cadres et ressources externes ; WebKit utilise une session éphémère,
sans stockage local HTML ni cache de pages. Le moteur visuel accède seulement
aux fichiers explicitement autorisés via un protocole interne.

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

Placer le projet dans un dossier contenant `pyproject.toml`, `src` et
`lancer-notes.sh`. La sauvegarde actuelle s’extrait dans un dossier nommé `notes`.
Les exemples utilisent `/home/user/notestr` comme dossier d’installation.
Remplacer `user` par le nom du compte Linux et adapter le chemin si nécessaire.
Si l’archive crée un dossier `notes`, renommer ce dossier en `notestr` ou déplacer
son contenu dans `/home/user/notestr` avant de suivre les commandes.

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

### Restaurer une sauvegarde ou installer sur un autre PC

Extraire l’archive dans le dossier choisi et adapter le chemin utilisé ci-dessus.
L’archive comprend un `.venv`, mais celui-ci dépend du Python et des chemins du
poste d’origine. **Le recréer après un déplacement ou sur un autre PC.**

Depuis le dossier extrait, conserver l’ancien environnement sous un autre nom
(par exemple `.venv-ancienne`, si ce nom n’existe pas déjà) :

```bash
mv .venv .venv-ancienne
```

Installer les paquets système puis reprendre les étapes 2 et 3. Le nouveau venv
sera construit pour le poste cible.

Les sauvegardes du dossier de l’application ne comprennent ni le cache situé dans
`~/.local/share/nostr-notes`, ni la clé privée du trousseau Linux. Sur un autre PC,
importer la même clé privée dans l’application et configurer les relais pour
récupérer les notes qui y sont encore disponibles. Conserver une sauvegarde
personnelle de la clé privée indépendamment du projet.

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

1. Dans **Compte et relais**, saisir la clé privée du même compte que Pages :
   `nsec1…` ou 64 caractères hexadécimaux. Une `npub` ne permet pas de déchiffrer.
2. Garder `wss://relay.decentralia.fr` ou ajouter plusieurs relais, un par ligne.
   Pour l’interopérabilité, configurer au moins un relais commun dans Pages.
3. Choisir d’enregistrer la clé dans le trousseau Linux, ou seulement en mémoire
   pour cette session. Le compte mémorisé se rouvre au lancement suivant.
4. **Actualiser** charge les notes et les demandes de suppression de l’utilisateur.
   Cliquer une note pour l’ouvrir ; la recherche parcourt tout le Markdown déchiffré.
5. **Nouvelle**, saisir du Markdown, puis **Publier**. La première ligne non vide
   fournit le titre de la liste ; aucun titre séparé n’est envoyé au relais.
6. Modifier puis **Publier** conserve exactement le même tag `d`.
7. **Supprimer** demande confirmation et publie une demande NIP-09.

L’éditeur permet de choisir entre la mise en forme visuelle et le Markdown source. Les changements non publiés
sont signalés dans le titre de fenêtre. Changer de note, actualiser, changer de
compte ou fermer nécessite de confirmer leur abandon. Une publication en échec
conserve le texte dans l’éditeur. Aucun brouillon n’est sauvegardé automatiquement :
un arrêt brutal peut perdre les modifications en mémoire.

La barre inférieure indique combien de relais ont accepté la publication et les
échecs éventuels. **Un succès partiel n’est pas une réplication complète.** Il n’y a
pas de file persistante de retransmission automatique dans cette version. Une publication
sans accusé peut néanmoins avoir atteint un relais : actualiser pour vérifier avant
de réessayer. Après une suppression partielle, sa diffusion vers les relais en échec
nécessite de republier la demande depuis un autre client ou un outil Nostr.

## Format et compatibilité Pages

Le code de référence inspecté est `formstr-hq/nostr-docs`, commit
`57f6d3e2ac8a0c965ded8b2f70ea23c349b2eb2d`.

- [Chiffrement personnel et clés de partage](https://github.com/formstr-hq/nostr-docs/blob/57f6d3e2ac8a0c965ded8b2f70ea23c349b2eb2d/src/utils/encryption.ts)
- [Création et mise à jour des documents](https://github.com/formstr-hq/nostr-docs/blob/57f6d3e2ac8a0c965ded8b2f70ea23c349b2eb2d/src/components/editor/DocEditorController.tsx)
- [Recherche des suppressions avec le tag k](https://github.com/formstr-hq/nostr-docs/blob/57f6d3e2ac8a0c965ded8b2f70ea23c349b2eb2d/src/nostr/fetchDelete.ts)

```json
{
  "kind": 33457,
  "tags": [["d", "a1b2c3"]],
  "content": "<Markdown brut chiffré NIP-44 v2>",
  "created_at": 1789200000
}
```

`monstr==0.1.9` fournit `Keys`, `NIP44Encrypt` et les signatures Schnorr `Event`.
Le chiffrement utilise la clé privée et la clé publique du **même utilisateur**.
Il n’y a pas d’enveloppe JSON autour du Markdown. Les nouveaux identifiants ont
six caractères aléatoires parmi `abcdefghijklmnopqrstuvwxyz0123456789`, obtenus
avec le générateur sécurisé de Python. Les identifiants existants sont conservés,
y compris si leur format diffère. Les autres tags d’un document ne sont pas repris
lors de sa modification : l’application republie le format personnel minimal de Pages.

La suppression signe un événement kind `5`, contenu vide, avec :

```text
["e", "<id de la version courante>"]
["a", "33457:<pubkey>:<d>"]
["k", "33457"]
```

Le tag `a` vise les versions jusqu’à la date de suppression. Une version réellement
plus récente peut réapparaître conformément à [NIP-09](https://github.com/nostr-protocol/nips/blob/master/09.md).
La suppression ne peut garantir l’effacement de copies conservées ailleurs.

Les événements reçus sont vérifiés : auteur, structure, empreinte du contenu et
signature. Parmi les versions, la plus récente gagne ; en cas d’égalité temporelle,
l’id lexicalement le plus petit gagne, conformément à
[NIP-01](https://github.com/nostr-protocol/nips/blob/master/01.md).
L’application refuse de modifier une note dans la même seconde que sa version précédente
pour éviter les égalités ; attendre une seconde. Une horloge locale correcte est nécessaire.

**Périmètre :** documents personnels chiffrés vers soi. Les documents partagés avec
`viewKey`/`editKey`, la collaboration CRDT, les pièces jointes, les commentaires,
les métadonnées kind `34579`, NIP-46 et l’authentification relais NIP-42 ne sont pas
gérés. Les notes indéchiffrables sont comptées et ne sont pas ouvertes pour édition.
Le format a été vérifié dans le code Pages ; une session interactive entre les deux
applications avec un compte réel n’a pas encore été testée.

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

Les actualisations sont manuelles. Il n’y a pas de fusion de modifications simultanées
entre clients : actualiser avant de modifier un document aussi utilisé dans Pages.
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
    core.py       format Pages, chiffrement via monstr, versions et suppressions
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

### Recette manuelle avec Pages

Avec une note jetable et le même compte/relais dans les deux applications :

1. Créer dans Pages `# Test Pages` suivi d’une phrase ; actualiser dans cette application.
2. Modifier ici et publier ; recharger Pages et vérifier le Markdown et le même `d`.
3. Créer ici une deuxième note ; vérifier sa présence dans Pages après actualisation.
4. Supprimer une note ici ; vérifier sa disparition après actualisation dans Pages.
5. Supprimer l’autre dans Pages ; actualiser ici.
6. Tester un relais indisponible : l’erreur doit être visible et un brouillon doit rester éditable.

Ne jamais communiquer la nsec pour cette recette : la saisir uniquement dans les
applications locales de confiance. Aucun événement n’a été publié sur votre relais
pendant la construction de ce projet.

### Test graphique V2 (facultatif)

Dans une session graphique, après avoir installé les dépendances de test :

```bash
python tests/gtk_editor_smoke.py
```

Ce test utilise une clé de test connue et un répertoire de données temporaire.
Il n’ouvre pas votre trousseau et intercepte la publication avant le réseau. Il
vérifie les modes, les allers-retours Markdown, la synchronisation avant chiffrement,
la politique de connexion et le rejet des mises à jour provenant d’une ancienne note.
Une fenêtre temporaire est affichée, puis fermée.

### Retours à la ligne dans la V2.2

Le mode visuel lit les sauts Markdown explicites. À la publication depuis les
deux modes, les simples retours de paragraphe deviennent des sauts explicites
(deux espaces avant le retour). Il n’est pas nécessaire d’ajouter une ligne vide
pour séparer deux phrases. `markdown-it-py` distingue le texte du code et de la
structure Markdown pour effectuer cette transformation.

Les notes stockées ne sont pas modifiées en arrière-plan : ouvrir une ancienne
note puis cliquer **Publier** suffit à enregistrer ses sauts explicites. Une simple
consultation sans publication conserve exactement le texte source existant.
