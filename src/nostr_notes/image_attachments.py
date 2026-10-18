"""Encrypted Blossom attachment primitives shared with the Android wire format."""
import asyncio
import base64
from io import BytesIO
import json
import secrets
import time
from urllib.parse import quote, urlsplit, parse_qs, urlunsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from PIL import Image, ImageOps
from . import __version__

DEFAULT_BLOSSOM_SERVER = "https://blossom.nostr.build"
MAX_SOURCE_BYTES = 30 * 1024 * 1024
MAX_UPLOAD_BYTES = 20 * 1024 * 1024


def normalize_server(value):
    try:
        parsed = urlsplit(value.strip())
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
            return None
        return f"https://{parsed.netloc}"
    except (AttributeError, ValueError):
        return None


def servers_from_profile(event):
    if not isinstance(event, dict) or event.get("kind") != 10063:
        return []
    result = []
    for tag in event.get("tags", []):
        if len(tag) > 1 and tag[0] == "server":
            server = normalize_server(tag[1])
            if server and server not in result:
                result.append(server)
    return result


def prepare_image(data: bytes) -> tuple[bytes, str]:
    if not data or len(data) > MAX_SOURCE_BYTES:
        raise ValueError("Image vide ou supérieure à 30 Mio.")
    try:
        with Image.open(BytesIO(data)) as original:
            if original.width < 1 or original.height < 1 or original.width * original.height > 80_000_000:
                raise ValueError("Image trop grande pour être décodée.")
            original.load()
            image = ImageOps.exif_transpose(original)
            image.thumbnail((2560, 2560), Image.Resampling.LANCZOS)
            # A deterministic JPEG conversion strips EXIF/GPS and avoids active SVG content.
            if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            output = BytesIO()
            image.save(output, format="JPEG", quality=86, optimize=True, exif=b"")
            encoded = output.getvalue()
    except Exception as exc:
        raise ValueError("Format d’image illisible ou non pris en charge.") from exc
    if not encoded or len(encoded) > MAX_UPLOAD_BYTES - 16:
        raise ValueError("Image supérieure à 20 Mio après préparation.")
    return encoded, "image/jpeg"


def encrypt_image(data: bytes, mime: str = "image/jpeg") -> dict:
    key, nonce = secrets.token_bytes(32), secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, data, None)
    import hashlib
    digest = hashlib.sha256(ciphertext).hexdigest()
    return {"ciphertext": ciphertext, "hash": digest, "key": key, "nonce": nonce, "mime": mime}


def decrypt_image(ciphertext: bytes, key: bytes, nonce: bytes, digest: str) -> bytes:
    import hashlib
    if hashlib.sha256(ciphertext).hexdigest() != digest or len(key) != 32 or len(nonce) != 12:
        raise ValueError("Empreinte ou clé d’image invalide.")
    return AESGCM(key).decrypt(nonce, ciphertext, None)


def image_markdown_reference(image: dict, server: str, blob_url: str | None = None) -> str:
    server = normalize_server(server)
    if not server:
        raise ValueError("Serveur Blossom invalide.")
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    host = urlsplit(server).hostname.lower()
    parts = [f"server={quote(server, safe='')}", f"key={enc(image['key'])}",
             f"nonce={enc(image['nonce'])}", "mime=image%2Fjpeg"]
    if blob_url:
        parsed_url = urlsplit(blob_url)
        if (parsed_url.scheme != "https" or not parsed_url.hostname or parsed_url.username or parsed_url.password
                or image["hash"] not in parsed_url.path):
            raise ValueError("URL du blob Blossom invalide.")
        parts.append(f"url={quote(blob_url, safe='')}")
    return f"![Image](notestr-image://{image['hash']}?{'&'.join(parts)})"


def _authorization_tokens(event: dict) -> list[str]:
    encoded_event = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # BUD-11 requires unpadded base64url. Retain a padded standard-base64 fallback
    # for deployed servers that still use a strict legacy decoder.
    tokens = [
        base64.urlsafe_b64encode(encoded_event).decode().rstrip("="),
        base64.b64encode(encoded_event).decode(),
    ]
    return list(dict.fromkeys(tokens))


def upload_blob(server: str, image: dict, identity) -> str | None:
    host = urlsplit(server).hostname.lower()
    auth = identity.signed(24242, [["t", "upload"], ["expiration", str(int(time.time()) + 300)],
                                   ["server", host], ["x", image["hash"]]], "Téléversement d’une image chiffrée Notestr")
    tokens = _authorization_tokens(auth)
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    descriptor = None
    last_error = None
    for index, token in enumerate(tokens):
        request = Request(server + "/upload", data=image["ciphertext"], method="PUT", headers={
            "Content-Type": "application/octet-stream", "Content-Length": str(len(image["ciphertext"])),
            "X-SHA-256": image["hash"], "Authorization": "Nostr " + token,
        })
        try:
            with build_opener(NoRedirect()).open(request, timeout=25) as response:
                descriptor = json.loads(response.read(65536))
                break
        except HTTPError as exc:
            reason = exc.headers.get("X-Reason", "") if exc.headers else ""
            try:
                body = exc.read(2048).decode("utf-8", errors="replace")
            except Exception:
                body = ""
            clean = [" ".join("".join(char if char.isprintable() else " " for char in part).split())
                     for part in (reason, body)]
            detail = " — ".join(dict.fromkeys(part for part in clean if part))[:300]
            failure = RuntimeError(f"HTTP Error {exc.code}: {exc.reason}" + (f": {detail}" if detail else ""))
            legacy_fallback = exc.code in (400, 401) and any(
                marker in detail.lower() for marker in ("invalid auth", "signature mismatch", "invalid nostr event")
            )
            if index + 1 < len(tokens) and legacy_fallback:
                last_error = failure
                continue
            raise failure from exc
    if descriptor is None:
        raise last_error or RuntimeError("Échec de l’envoi Blossom.")
    if descriptor.get("sha256", "").lower() != image["hash"]:
        raise ValueError("Le serveur Blossom a retourné une empreinte différente.")
    blob_url = descriptor.get("url")
    if blob_url is not None:
        if not isinstance(blob_url, str):
            raise ValueError("URL du blob Blossom invalide.")
        parsed_url = urlsplit(blob_url)
        if (parsed_url.scheme != "https" or not parsed_url.hostname or parsed_url.username or parsed_url.password
                or image["hash"] not in parsed_url.path):
            raise ValueError("URL du blob Blossom invalide.")
    return blob_url


async def discover_servers(relays, pubkey, query_profile):
    results = await asyncio.gather(*(query_profile(relay, pubkey) for relay in relays), return_exceptions=True)
    events = [event for result in results if isinstance(result, list) for event in result]
    events.sort(key=lambda event: (-event.get("created_at", 0), event.get("id", "")))
    if events:
        events.sort(key=lambda event: (-event.get("created_at", 0), event.get("id", "")))
        servers = servers_from_profile(events[0])
        if servers:
            return servers
    return [DEFAULT_BLOSSOM_SERVER]


async def upload_encrypted_image(data: bytes, identity, relays, query_profile, cache_dir=None) -> str:
    clean, mime = await asyncio.to_thread(prepare_image, data)
    image = await asyncio.to_thread(encrypt_image, clean, mime)
    servers = await discover_servers(relays, identity.pubkey, query_profile)
    failures = []
    for server in servers:
        try:
            blob_url = await asyncio.to_thread(upload_blob, server, image, identity)
        except Exception as exc:
            failures.append(f"{server}: {exc}")
            continue
        if cache_dir is not None:
            await asyncio.to_thread(_save_encrypted_cache, cache_dir, image["hash"], image["ciphertext"])
        return image_markdown_reference(image, server, blob_url)
    raise ConnectionError("Aucun serveur Blossom n’a accepté l’image. " + " | ".join(failures))


def _save_encrypted_cache(cache_dir, digest: str, ciphertext: bytes) -> None:
    """Atomically cache only the authenticated ciphertext; plaintext/key stay elsewhere."""
    import os
    import tempfile
    from pathlib import Path
    import hashlib
    if (not isinstance(digest, str) or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            or len(ciphertext) < 17 or len(ciphertext) > MAX_UPLOAD_BYTES + 16
            or hashlib.sha256(ciphertext).hexdigest() != digest):
        raise ValueError("Empreinte de l’image chiffrée invalide.")
    path = Path(cache_dir) / f"image-{digest}.bin"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".image-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as output:
            output.write(ciphertext)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_image_reference(reference: str, cache_dir=None, allowed_servers=None) -> bytes:
    """Load encrypted bytes from a local cache or server, then decrypt only in memory."""
    import hashlib
    from pathlib import Path
    import os
    import tempfile
    from urllib.parse import parse_qs
    from urllib.error import HTTPError
    parsed = urlsplit(reference)
    if parsed.scheme != "notestr-image" or not parsed.hostname or len(parsed.hostname) != 64:
        raise ValueError("Référence d’image invalide.")
    digest = parsed.hostname.lower()
    if any(char not in "0123456789abcdef" for char in digest) or parsed.path not in ("", "/"):
        raise ValueError("Référence d’image invalide.")
    values = parse_qs(parsed.query, strict_parsing=True)
    server = values.get("server", [""])[0]
    descriptor_url = values.get("url", [""])[0]
    key_text = values.get("key", [""])[0]
    nonce_text = values.get("nonce", [""])[0]
    mime = values.get("mime", [""])[0]
    if mime != "image/jpeg" or not server or len(values.get("key", [])) != 1 or len(values.get("nonce", [])) != 1:
        raise ValueError("Métadonnées d’image invalides.")
    origin = normalize_server(server)
    if not origin:
        raise ValueError("Serveur Blossom invalide.")
    cached_path = Path(cache_dir) / f"image-{digest}.bin" if cache_dir else None
    ciphertext = None
    if cached_path and cached_path.exists():
        candidate = cached_path.read_bytes()
        if len(candidate) <= MAX_UPLOAD_BYTES + 16 and hashlib.sha256(candidate).hexdigest() == digest:
            ciphertext = candidate
        else:
            cached_path.unlink(missing_ok=True)
    if ciphertext is None:
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None
        blob_urls = []
        if descriptor_url:
            parsed_blob = urlsplit(descriptor_url)
            if (parsed_blob.scheme != "https" or not parsed_blob.hostname or parsed_blob.username or parsed_blob.password
                    or digest not in parsed_blob.path):
                raise ValueError("URL du blob Blossom invalide.")
            blob_urls.append(descriptor_url)
        candidates = [origin]
        if allowed_servers is not None:
            accepted = list(dict.fromkeys(filter(None, (normalize_server(value) for value in allowed_servers))))
            # Prefer the account's current profile servers as mirrors, then
            # fall back to the HTTPS origin embedded in the signed note.
            # Old notes must remain readable after a profile removes a server.
            candidates = accepted + ([origin] if origin not in accepted else [])
        last_error = None
        urls = list(blob_urls)
        for candidate in candidates:
            urls.extend(f"{candidate}/{digest}{suffix}" for suffix in ("", ".jpg", ".jpeg", ".png", ".webp", ".bin"))
            if descriptor_url:
                parsed_blob = urlsplit(descriptor_url)
                urls.append(urlunsplit(("https", candidate.split("://", 1)[1], parsed_blob.path,
                                       parsed_blob.query, "")))
        for download_url in dict.fromkeys(urls):
            try:
                request = Request(download_url, headers={
                    "Accept": "application/octet-stream",
                    # Some Blossom hosts reject Python-urllib's default User-Agent with 403.
                    "User-Agent": f"Notestr/{__version__}",
                })
                with build_opener(NoRedirect()).open(request, timeout=20) as response:
                    candidate_bytes = response.read(MAX_UPLOAD_BYTES + 32)
                if len(candidate_bytes) > MAX_UPLOAD_BYTES + 16 or hashlib.sha256(candidate_bytes).hexdigest() != digest:
                    raise ValueError("Empreinte Blossom incorrecte.")
                ciphertext = candidate_bytes
                break
            except Exception as exc:
                last_error = exc
        if ciphertext is None:
            if last_error:
                raise last_error
            raise ValueError("Serveur d’image absent de la liste Blossom de ce compte.")
        if cached_path:
            _save_encrypted_cache(cached_path.parent, digest, ciphertext)
    decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    return decrypt_image(ciphertext, decode(key_text), decode(nonce_text), digest)


def cached_image_available(reference: str, cache_dir) -> bool:
    """Return true only for a well-formed reference whose encrypted cache hash matches."""
    import hashlib
    from pathlib import Path
    from urllib.parse import parse_qs
    parsed = urlsplit(reference)
    if parsed.scheme != "notestr-image" or not parsed.hostname or len(parsed.hostname) != 64:
        return False
    digest = parsed.hostname.lower()
    if any(char not in "0123456789abcdef" for char in digest) or parsed.path not in ("", "/"):
        return False
    try:
        values = parse_qs(parsed.query, strict_parsing=True)
        if (values.get("mime") != ["image/jpeg"] or len(values.get("server", [])) != 1
                or len(values.get("key", [])) != 1 or len(values.get("nonce", [])) != 1):
            return False
        candidate = (Path(cache_dir) / f"image-{digest}.bin").read_bytes()
    except (OSError, ValueError):
        return False
    return 17 <= len(candidate) <= MAX_UPLOAD_BYTES + 16 and hashlib.sha256(candidate).hexdigest() == digest


def load_image_for_display(reference: str, cache_dir, relays, pubkey, query_profile) -> bytes:
    """Use the reference's server first, then profile mirrors as a fallback."""
    if cached_image_available(reference, cache_dir):
        return load_image_reference(reference, cache_dir, [])
    try:
        # The URL in the attachment is the only location guaranteed to know
        # this blob. Avoid delaying every image on a relay profile query.
        return load_image_reference(reference, cache_dir)
    except Exception as origin_error:
        # A verified ciphertext may have been cached before a decryption error;
        # do not turn that into more network requests to unrelated mirrors.
        if cached_image_available(reference, cache_dir):
            raise
        try:
            servers = asyncio.run(discover_servers(relays, pubkey, query_profile))
            return load_image_reference(reference, cache_dir, servers)
        except Exception as fallback_error:
            raise fallback_error from origin_error
