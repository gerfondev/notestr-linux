"""Format Pages personnel. Toute la crypto NIP-44/Schnorr appartient à monstr."""
from dataclasses import dataclass
import hashlib
import json
import re
import secrets
import string
import time

from monstr.encrypt import Keys, NIP44Encrypt
from monstr.event.event import Event
from .markdown import explicit_line_breaks

KIND = 33457


def parse_key(value: str) -> Keys:
    value = value.strip()
    try:
        if not (re.fullmatch(r"[0-9a-fA-F]{64}", value) or value.startswith("nsec1")):
            raise ValueError()
        keys = Keys(priv_k=value)
        if not keys.private_key_hex():
            raise ValueError()
        return keys
    except Exception:
        raise ValueError("Clé privée invalide : saisir une nsec ou 64 caractères hexadécimaux.") from None


def tag_values(event, name):
    return [t[1] for t in event["tags"] if len(t) >= 2 and t[0] == name]


def valid_event(data: dict, pubkey: str) -> bool:
    """monstr vérifie la signature de l'id, donc vérifier aussi son lien au contenu."""
    try:
        if data["pubkey"] != pubkey or data["kind"] not in (KIND, 5):
            return False
        if type(data["created_at"]) is not int or data["created_at"] < 0:
            return False
        if not isinstance(data["content"], str) or not isinstance(data["tags"], list):
            return False
        if not all(isinstance(t, list) and t and all(isinstance(v, str) for v in t)
                   for t in data["tags"]):
            return False
        serial = [0, pubkey, data["created_at"], data["kind"], data["tags"], data["content"]]
        digest = hashlib.sha256(json.dumps(serial, ensure_ascii=False,
                                           separators=(",", ":")).encode()).hexdigest()
        return digest == data["id"] and Event.load(data).is_valid()
    except Exception:
        return False


@dataclass(frozen=True)
class Note:
    d: str
    markdown: str
    event: dict

    @property
    def title(self):
        return next((line.lstrip("# ").strip()[:100] for line in self.markdown.splitlines()
                     if line.lstrip("# ").strip()), "Sans titre")


class Identity:
    def __init__(self, secret: str):
        self.keys = parse_key(secret)
        self.pubkey = self.keys.public_key_hex()
        self.cipher = NIP44Encrypt(self.keys)

    def signed(self, kind, tags, content, created_at=None):
        event = Event(kind=kind, tags=tags, content=content, pub_key=self.pubkey,
                      created_at=int(time.time()) if created_at is None else created_at)
        event.sign(self.keys.private_key_hex())
        return event.data()

    def save(self, markdown: str, previous: Note | None = None, d: str | None = None):
        markdown = explicit_line_breaks(markdown)
        size = len(markdown.encode("utf-8"))
        if not 1 <= size <= 65535:
            raise ValueError("Le Markdown doit contenir entre 1 et 65 535 octets UTF-8 (NIP-44 v2).")
        now = int(time.time())
        if previous and previous.event["created_at"] >= now:
            raise ValueError("Attendre la seconde suivante avant de republier cette note ; vérifier l’horloge si nécessaire.")
        identifier = previous.d if previous else d or "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return self.signed(KIND, [["d", identifier]],
                           self.cipher.encrypt(markdown, self.pubkey), now)

    def delete(self, note: Note):
        return self.signed(5, [["e", note.event["id"]],
                               ["a", f"{KIND}:{self.pubkey}:{note.d}"], ["k", str(KIND)]],
                           "", max(int(time.time()), note.event["created_at"]))

    def notes(self, events):
        valid = [e for e in events if valid_event(e, self.pubkey)]
        latest, deleted_ids, deleted_addresses = {}, set(), {}
        for e in valid:
            if e["kind"] == 5:
                deleted_ids.update(tag_values(e, "e"))
                for address in tag_values(e, "a"):
                    deleted_addresses[address] = max(e["created_at"], deleted_addresses.get(address, -1))
            else:
                ds = tag_values(e, "d")
                if not ds:
                    continue
                d = ds[0]  # NIP-01 : première valeur, conserver même les anciens identifiants.
                old = latest.get(d)
                if old is None or (-e["created_at"], e["id"]) < (-old["created_at"], old["id"]):
                    latest[d] = e
        notes, unreadable = [], 0
        for d, event in latest.items():
            if event["id"] in deleted_ids or event["created_at"] <= deleted_addresses.get(
                    f"{KIND}:{self.pubkey}:{d}", -1):
                continue
            try:
                notes.append(Note(d, self.cipher.decrypt(event["content"], self.pubkey), event))
            except Exception:
                unreadable += 1
        return sorted(notes, key=lambda n: (-n.event["created_at"], n.d)), unreadable
