"""Transport NIP-01 borné, avec EOSE et accusés OK ; aucun secret envoyé."""
import asyncio
import json
import secrets
from websockets.asyncio.client import connect
from .core import BACKUP_KIND, valid_event

TIMEOUT = 25
PAGE_SIZE = 1000


async def query_one(url, pubkey):
    async def run():
        events = {}
        async with connect(url, open_timeout=10, close_timeout=2, max_size=2**20) as ws:
            # Paginer séparément pour ne pas masquer les anciennes suppressions.
            for kind in (33457, 5, BACKUP_KIND):
                until = None
                for _ in range(100):
                    sub = secrets.token_hex(8)
                    filt = {"kinds": [kind], "authors": [pubkey], "limit": PAGE_SIZE}
                    if until is not None:
                        filt["until"] = until
                    await ws.send(json.dumps(["REQ", sub, filt]))
                    page = []
                    while True:
                        msg = json.loads(await ws.recv())
                        if not isinstance(msg, list) or not msg:
                            continue
                        if msg[0] == "EVENT" and len(msg) == 3 and msg[1] == sub:
                            e = msg[2]
                            if valid_event(e, pubkey) and e["kind"] == kind and (until is None or e["created_at"] <= until):
                                page.append(e)
                                events[e["id"]] = e
                            if len(page) > 10000:
                                raise ValueError("Réponse du relais trop volumineuse.")
                        elif msg[0] == "EOSE" and len(msg) >= 2 and msg[1] == sub:
                            break
                        elif msg[0] == "CLOSED" and len(msg) >= 2 and msg[1] == sub:
                            raise ValueError("Abonnement refusé par le relais.")
                        elif msg[0] == "AUTH":
                            raise ValueError("Ce relais exige NIP-42, non pris en charge en V1.")
                    await ws.send(json.dumps(["CLOSE", sub]))
                    if not page:
                        break
                    oldest = min(e["created_at"] for e in page)
                    # Recouvrir la seconde frontière. Ne jamais sauter silencieusement
                    # des événements si le relais plafonne une seconde entière.
                    if until == oldest:
                        if all(e["created_at"] == oldest for e in page) and len(page) < PAGE_SIZE:
                            until = oldest - 1
                        else:
                            raise ValueError("Pagination saturée sur une même seconde ; récupération incomplète.")
                    else:
                        until = oldest
                else:
                    raise ValueError("Limite de pagination atteinte ; récupération incomplète.")
        return list(events.values())
    return await asyncio.wait_for(run(), TIMEOUT)


async def publish_one(url, event):
    async def run():
        async with connect(url, open_timeout=10, close_timeout=2, max_size=2**20) as ws:
            await ws.send(json.dumps(["EVENT", event]))
            while True:
                msg = json.loads(await ws.recv())
                if isinstance(msg, list) and len(msg) >= 4 and msg[0] == "OK" and msg[1] == event["id"]:
                    if msg[2] is not True:
                        raise ValueError("Publication refusée : " + str(msg[3])[:200])
                    return True
                if isinstance(msg, list) and msg and msg[0] == "AUTH":
                    raise ValueError("Ce relais exige NIP-42, non pris en charge en V1.")
    return await asyncio.wait_for(run(), TIMEOUT)


async def across(relays, operation, *args):
    results = await asyncio.gather(*(operation(url, *args) for url in relays), return_exceptions=True)
    good, errors = {}, []
    for url, result in zip(relays, results):
        if isinstance(result, BaseException):
            reason = "Délai dépassé" if isinstance(result, TimeoutError) else str(result) or type(result).__name__
            errors.append(f"{url} : {reason}")
        else:
            good[url] = result
    if not good:
        raise ConnectionError("\n".join(errors))
    return good, errors


async def publish_update(url, event, backup=None):
    """Each relay must acknowledge the backup before receiving the update."""
    if backup is not None:
        await publish_one(url, backup)
    return await publish_one(url, event)
