"""Durable signed NIP-44 edits. No plaintext, no network at save time."""
from dataclasses import replace
import secrets
import threading
import time
from .core import (KIND, BACKUP_KIND, Note, valid_event, tag_values,
                   compact_backups, backup_address)
from .markdown import explicit_line_breaks
from .i18n import tr


def require(condition):
    if not condition:
        raise ValueError(tr('Fichier de modifications locales invalide.'))


class Outbox:
    def __init__(self, identity, store):
        self.identity, self.store = identity, store
        self.lock = threading.RLock()
        self.name = f"pending-{identity.pubkey}.json"

    def _load(self):
        rows = self.store.read(self.name, [])
        seen = set()
        for row in rows:
            update, base, backup = row['update'], row['base'], row['backup']
            require(valid_event(update, self.identity.pubkey) and update['kind'] == KIND)
            d = tag_values(update, 'd')[0]
            require(d not in seen)
            seen.add(d)
            require(tag_values(update, 'notestr-base') == [base['id'] if base else ''])
            if base:
                require(valid_event(base, self.identity.pubkey) and base['kind'] == KIND)
                require(tag_values(base, 'd') == [d])
                require(backup and valid_event(backup, self.identity.pubkey) and backup['kind'] == BACKUP_KIND)
                require(tag_values(backup, 'd') == [backup_address(d)] and tag_values(backup, 'e') == [base['id']])
                require(backup['content'] == base['content'] and backup['created_at'] == update['created_at'])
            else:
                require(backup is None)
        return rows

    def snapshot(self, include_sent=False):
        with self.lock:
            return [r for r in self._load() if include_sent or not r.get("sent", False)]

    def save(self, markdown, previous=None, as_copy=False):
        with self.lock:
            rows = self._load()
            old = next((r for r in rows if tag_values(r['update'], 'd')[0] == previous.d), None) if previous else None
            if previous and previous.trashed:
                raise ValueError(tr('Restaurez la note depuis la corbeille avant de la modifier.'))
            if old and not old.get("sent", False) and (not previous.pending or previous.event['id'] != old['update']['id']):
                raise ValueError(tr('La note a changé. Actualisez et ouvrez sa dernière version.'))
            base = None if as_copy else old['base'] if old and previous.pending else previous.event if previous else None
            markdown = explicit_line_breaks(markdown)
            if not markdown.strip() or not 1 <= len(markdown.encode('utf-8')) <= 65535:
                raise ValueError(tr('Le Markdown doit contenir entre 1 et 65 535 octets UTF-8 (NIP-44 v2).'))
            d = secrets.token_hex(8) if as_copy or previous is None else previous.d
            when = max(int(time.time()), base['created_at'] + 1 if base else 0)
            update = self.identity.signed(KIND, [['d', d], ['notestr-base', base['id'] if base else '']],
                self.identity.cipher.encrypt(markdown, self.identity.pubkey), when)
            backup = self.identity.backup(Note(d, '', base), update) if base else None
            if previous:
                rows = [r for r in rows if tag_values(r['update'], 'd')[0] != previous.d]
            rows.append(dict(update=update, base=base, backup=backup))
            self.store.write(self.name, rows)
            return Note(d, markdown, update, pinned=previous.pinned if previous else False, pending=True)

    def remove(self, identifier, event_id):
        with self.lock:
            rows = self._load()
            # A newer save during network IO must never be removed by an older acknowledgement.
            remaining = [r for r in rows if not (tag_values(r['update'], 'd')[0] == identifier and r['update']['id'] == event_id)]
            self.store.write(self.name, remaining)

    def purge_sent(self, identifier):
        with self.lock:
            rows = self._load()
            kept = [r for r in rows if not (r.get('sent', False) and tag_values(r['update'], 'd')[0] == identifier)]
            if len(kept) != len(rows):
                self.store.write(self.name, kept)

    def acknowledge(self, identifier, event_id):
        with self.lock:
            rows = self._load()
            for row in rows:
                if tag_values(row['update'], 'd')[0] == identifier and row['update']['id'] == event_id:
                    row['sent'] = True
            self.store.write(self.name, rows)

    def conflict(self, row, current, events):
        d = tag_values(row['update'], 'd')[0]
        address = f'{KIND}:{self.identity.pubkey}:{d}'
        if any(e['kind'] == 5 and valid_event(e, self.identity.pubkey) and
               address in tag_values(e, 'a') for e in events):
            return True
        if current and current.trashed:
            return True
        if current and current.event['id'] == row['update']['id']:
            return False
        return (current.event['id'] if current else None) != (row['base']['id'] if row['base'] else None)

    def overlay(self, events):
        events = list(events)
        remote, _ = self.identity.notes(events)
        result = list(remote)
        for row in self.snapshot(include_sent=True):
            d = tag_values(row['update'], 'd')[0]
            current = next((n for n in remote if n.d == d), None)
            conflict = self.conflict(row, current, events)
            if row.get('sent', False):
                address = f'{KIND}:{self.identity.pubkey}:{d}'
                if any(e['kind'] == 5 and valid_event(e, self.identity.pubkey) and address in tag_values(e, 'a') for e in events):
                    self.purge_sent(d)
                    continue
                if not conflict or current is None or current.trashed:
                    continue
                parent = tag_values(current.event, 'notestr-base')
                if parent and parent != [row['base']['id'] if row['base'] else '']:
                    continue
            if not conflict:
                result = [n for n in result if n.d != d]
            result.append(Note(d, self.identity.cipher.decrypt(row['update']['content'], self.identity.pubkey), row['update'],
                               pinned=current.pinned if current else False, pending=True, conflicted=conflict))
        return sorted(result, key=lambda n: (not n.pinned, -n.event['created_at'], n.d, n.pending))

    async def synchronize(self, events, relays, query, publish):
        from .relay import across
        rows = self.snapshot()
        if not rows:
            return dict(events), []
        good, errors = await across(relays, query, self.identity.pubkey)
        merged = compact_backups([*events.values(), *(e for batch in good.values() for e in batch)])
        self.store.save_events(self.identity.pubkey, list(merged.values()))
        if errors or len(good) != len(relays):
            return merged, errors  # all configured relays must complete before automatic sends
        for row in rows:
            current = next((n for n in self.identity.notes(merged.values())[0] if n.d == tag_values(row['update'], 'd')[0]), None)
            if self.conflict(row, current, merged.values()):
                continue
            # Skip a snapshot that was superseded by a local save during relay reads.
            if not any(r['update']['id'] == row['update']['id'] for r in self.snapshot()):
                continue
            if not current or current.event['id'] != row['update']['id']:
                accepted, failures = await across(relays, publish, row['update'], row['backup'])
                errors.extend(failures)
                merged = compact_backups([*merged.values(), row['update'], *([row['backup']] if row['backup'] else [])])
                self.store.save_events(self.identity.pubkey, list(merged.values()))
            self.acknowledge(tag_values(row['update'], 'd')[0], row['update']['id'])
        return merged, errors
