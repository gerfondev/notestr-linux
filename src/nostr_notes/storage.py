"""Configuration publique et cache d'événements chiffrés ; jamais de Markdown clair."""
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

DEFAULT_RELAY = "wss://relay.decentralia.fr"


def relays_from_text(text):
    values = list(dict.fromkeys(text.replace(",", " ").split()))
    if not values:
        raise ValueError("Indiquer au moins un relais wss://.")
    for value in values:
        url = urlsplit(value)
        if url.scheme != "wss" or not url.hostname or url.username or url.password or url.fragment:
            raise ValueError("Chaque relais doit être une URL wss:// valide sans identifiants ni fragment.")
        try:
            _ = url.port
        except ValueError:
            raise ValueError("Port du relais invalide.") from None
    return values


class Storage:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "nostr-notes"
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root.chmod(0o700)

    def read(self, name, default):
        path = self.root / name
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text())
        except (ValueError, OSError):
            raise ValueError(f"Fichier local illisible : {path}. Le sauvegarder puis le retirer pour repartir.") from None

    def write(self, name, data):
        fd, path = tempfile.mkstemp(dir=self.root, prefix=".write-")
        try:
            with os.fdopen(fd, "w") as out:
                json.dump(data, out, ensure_ascii=False)
                out.flush()
                os.fsync(out.fileno())
            os.replace(path, self.root / name)
        finally:
            if os.path.exists(path):
                os.unlink(path)

    def config(self):
        data = self.read("config.json", {"relays": [DEFAULT_RELAY]})
        data["relays"] = relays_from_text("\n".join(data["relays"]))
        return data

    def events(self, pubkey):
        return self.read(f"{pubkey}.json", [])

    def save_events(self, pubkey, events):
        self.write(f"{pubkey}.json", events)


def secret_backend():
    # Sélection explicite : aucun repli possible vers un backend texte en clair.
    from keyring.backends.SecretService import Keyring
    return Keyring()


def load_secret(pubkey):
    return secret_backend().get_password("nostr-notes", pubkey)


def save_secret(identity):
    secret_backend().set_password("nostr-notes", identity.pubkey, identity.keys.private_key_hex())
