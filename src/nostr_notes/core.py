"""Format Pages personnel. Toute la crypto NIP-44/Schnorr appartient à monstr."""
from .i18n import tr
from dataclasses import dataclass, replace
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
BACKUP_KIND = 30078
BACKUP_PREFIX = "notestr/previous/"
TRASH_PREFIX = "notestr/trash/"
LOCK_PREFIX = "notestr/lock/"

def trash_address(d):
    return TRASH_PREFIX + hashlib.sha256(d.encode()).hexdigest()


def lock_address(d):
    return LOCK_PREFIX + hashlib.sha256(d.encode()).hexdigest()


PIN_PREFIX = "notestr/pin/"

def pin_address(d):
    return PIN_PREFIX + hashlib.sha256(d.encode()).hexdigest()


def backup_address(d):
    return BACKUP_PREFIX + hashlib.sha256(d.encode()).hexdigest()


def compact_backups(events):
    """Keep just the current encrypted backup per address in the local cache."""
    events = list(events)
    tombstones = {(e["pubkey"], a) for e in events if e["kind"] == 5
                  and valid_event(e, e["pubkey"]) for a in tag_values(e, "a")}
    result, latest = {}, {}
    for event in events:
        ds = tag_values(event, "d")
        if event["kind"] != 5 and ds and (event["pubkey"], f"{event['kind']}:{event['pubkey']}:{ds[0]}") in tombstones:
            continue
        if event["kind"] != BACKUP_KIND:
            result[event["id"]] = event
            continue
        ds = tag_values(event, "d")
        if not ds or not ds[0].startswith((BACKUP_PREFIX, PIN_PREFIX, TRASH_PREFIX, LOCK_PREFIX)):
            continue
        old = latest.get(ds[0])
        if old is None or (-event["created_at"], event["id"]) < (-old["created_at"], old["id"]):
            latest[ds[0]] = event
    result.update((event["id"], event) for event in latest.values())
    return result


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
        raise ValueError(tr('Clé privée invalide : saisir une nsec ou 64 caractères hexadécimaux.')) from None


def tag_values(event, name):
    return [t[1] for t in event["tags"] if len(t) >= 2 and t[0] == name]


def valid_event(data: dict, pubkey: str) -> bool:
    """monstr vérifie la signature de l'id, donc vérifier aussi son lien au contenu."""
    try:
        if data["pubkey"] != pubkey or data["kind"] not in (KIND, BACKUP_KIND, 5, 10063):
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
    pinned: bool = False
    trashed: bool = False
    pending: bool = False
    conflicted: bool = False
    locked: bool = False

    @property
    def title(self):
        return next((line.lstrip("# ").strip()[:100] for line in self.markdown.splitlines()
                     if line.lstrip("# ").strip()), tr('Sans titre'))


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
        if previous and previous.trashed:
            raise ValueError(tr("Restaurez la note depuis la corbeille avant de la modifier."))
        if previous and previous.locked:
            raise ValueError(tr("Déverrouillez cette note avant de la modifier."))
        markdown = explicit_line_breaks(markdown)
        size = len(markdown.encode("utf-8"))
        if not 1 <= size <= 65535:
            raise ValueError(tr('Le Markdown doit contenir entre 1 et 65 535 octets UTF-8 (NIP-44 v2).'))
        now = int(time.time())
        if previous and previous.event["created_at"] >= now:
            raise ValueError(tr('Attendre la seconde suivante avant de republier cette note ; vérifier l’horloge si nécessaire.'))
        identifier = previous.d if previous else d or "".join(
            secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
        return self.signed(KIND, [["d", identifier]],
                           self.cipher.encrypt(markdown, self.pubkey), now)

    def backup(self, note: Note, update):
        """Reuse the already encrypted previous content; never publish plaintext."""
        return self.signed(BACKUP_KIND,
                           [["d", backup_address(note.d)], ["e", note.event["id"]]],
                           note.event["content"], update["created_at"])

    def set_pinned(self, note, pinned, events):
        address = pin_address(note.d)
        metadata, _ = self.notes(events, kind=BACKUP_KIND)
        old = next((item for item in metadata if item.d == address), None)
        now = int(time.time())
        if old and old.event["created_at"] >= now:
            raise ValueError(tr('Attendre la seconde suivante avant de changer l’épinglage ; vérifier l’horloge si nécessaire.'))
        return self.signed(BACKUP_KIND, [["d", address]],
                           self.cipher.encrypt("true" if pinned else "false", self.pubkey), now)

    def set_locked(self, note, locked, events):
        events = list(events)
        current = next((n for n in self.notes(events)[0] if n.d == note.d), None)
        if current is None or current.event["id"] != note.event["id"] or current.locked != note.locked:
            raise ValueError(tr("La note a changé. Actualisez et ouvrez sa dernière version."))
        if note.pending:
            raise ValueError(tr("Publiez d’abord cette note avant de la verrouiller."))
        address = lock_address(note.d)
        metadata, _ = self.notes(events, kind=BACKUP_KIND)
        old = next((item for item in metadata if item.d == address), None)
        now = int(time.time())
        if old and old.event["created_at"] >= now:
            raise ValueError(tr("Attendre la seconde suivante avant de changer le verrouillage."))
        return self.signed(BACKUP_KIND, [["d", address]],
                           self.cipher.encrypt("true" if locked else "false", self.pubkey), now)

    def set_trashed(self, note, trashed, events):
        events = list(events)
        current = next((n for n in self.notes(events)[0] if n.d == note.d), None)
        if current is None or current.event["id"] != note.event["id"] or current.trashed != note.trashed or current.locked != note.locked:
            raise ValueError(tr("La note a changé. Actualisez et ouvrez sa dernière version."))
        if trashed and current.locked:
            raise ValueError(tr("Déverrouillez cette note avant de la déplacer vers la corbeille."))
        metadata, _ = self.notes(events, kind=BACKUP_KIND)
        old = next((n for n in metadata if n.d == trash_address(note.d)), None)
        now = int(time.time())
        if old and old.event["created_at"] >= now:
            raise ValueError(tr("Attendre la seconde suivante avant de modifier la corbeille."))
        return self.signed(BACKUP_KIND, [["d", trash_address(note.d)]],
                           self.cipher.encrypt("true" if trashed else "false", self.pubkey), now)

    def previous(self, note, events):
        backups, _ = self.notes(events, kind=BACKUP_KIND)
        return next((backup for backup in backups if backup.d == backup_address(note.d)), None)

    def delete(self, note: Note, events=None):
        if note.locked:
            raise ValueError(tr("Déverrouillez cette note avant de la supprimer définitivement."))
        if events is not None:
            current = next((n for n in self.notes(events)[0] if n.d == note.d), None)
            if current is None or current.event["id"] != note.event["id"] or current.locked:
                raise ValueError(tr("La note a changé ou est verrouillée. Actualisez avant de la supprimer."))
        if not note.trashed:
            raise ValueError(tr("Déplacez d’abord la note dans la corbeille."))
        return self.signed(5, [["e", note.event["id"]],
                               ["a", f"{KIND}:{self.pubkey}:{note.d}"], ["k", str(KIND)],
                               ["a", f"{BACKUP_KIND}:{self.pubkey}:{backup_address(note.d)}"],
                               ["a", f"{BACKUP_KIND}:{self.pubkey}:{pin_address(note.d)}"],
                               ["a", f"{BACKUP_KIND}:{self.pubkey}:{trash_address(note.d)}"],
                               ["a", f"{BACKUP_KIND}:{self.pubkey}:{lock_address(note.d)}"],
                               ["k", str(BACKUP_KIND)]],
                           "", max(int(time.time()), note.event["created_at"]))

    def notes(self, events, kind=KIND):
        events = list(events)
        valid = [e for e in events if valid_event(e, self.pubkey) and e["kind"] in (kind, 5)]
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
                    f"{kind}:{self.pubkey}:{d}", -1):
                continue
            try:
                notes.append(Note(d, self.cipher.decrypt(event["content"], self.pubkey), event))
            except Exception:
                unreadable += 1
        if kind == KIND:
            metadata, failed = self.notes(events, kind=BACKUP_KIND)
            pins = {n.d for n in metadata if n.d.startswith(PIN_PREFIX) and n.markdown == "true"}
            trash = {n.d: n.markdown for n in metadata if n.d.startswith(TRASH_PREFIX)}
            locks = {n.d: n.markdown for n in metadata if n.d.startswith(LOCK_PREFIX)}
            lock_addresses = {tag_values(e, "d")[0] for e in events
                              if valid_event(e, self.pubkey) and e["kind"] == BACKUP_KIND
                              and tag_values(e, "d") and tag_values(e, "d")[0].startswith(LOCK_PREFIX)}
            # An address deletion is terminal for this identifier on new clients.
            destroyed = {a for e in valid if e["kind"] == 5 for a in tag_values(e, "a")}
            trash_addresses = {tag_values(e, "d")[0] for e in events
                               if valid_event(e, self.pubkey) and e["kind"] == BACKUP_KIND
                               and tag_values(e, "d") and tag_values(e, "d")[0].startswith(TRASH_PREFIX)}
            notes = [replace(n, pinned=pin_address(n.d) in pins,
                             trashed=trash.get(trash_address(n.d)) == "true",
                             locked=(lock_address(n.d) in lock_addresses and locks.get(lock_address(n.d)) != "false")) for n in notes
                     if f"{KIND}:{self.pubkey}:{n.d}" not in destroyed
                     and (trash_address(n.d) not in trash_addresses or
                          trash.get(trash_address(n.d)) in ("true", "false"))]
            unreadable += failed
        return sorted(notes, key=lambda n: (not n.pinned, -n.event["created_at"], n.d)), unreadable
