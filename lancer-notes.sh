#!/bin/sh
set -eu
# Chemin indépendant du répertoire depuis lequel le script est lancé.
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -x "$APP_DIR/.venv/bin/python" ]; then
    echo "Environnement Python introuvable : $APP_DIR/.venv. Voir README.md." >&2
    exit 1
fi
cd "$APP_DIR"
exec "$APP_DIR/.venv/bin/python" -m nostr_notes "$@"
