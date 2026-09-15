import sys


def main():
    if "--check" in sys.argv:
        from .core import Identity, Note, valid_event
        from . import relay, storage
        identity = Identity("0" * 63 + "1")  # Clé publique de test uniquement.
        event = identity.save("# Vérification\n\nBonjour 👋")
        assert valid_event(event, identity.pubkey)
        notes, failures = identity.notes([event])
        assert failures == 0 and notes[0].markdown == "# Vérification\n\nBonjour 👋"
        from .app import Application
        from .editor import WebKit
        print("Éditeur visuel WebKitGTK 6.0 : " + ("disponible" if WebKit else "absent, mode Markdown disponible"))
        print("Imports GTK4/libadwaita et Nostr OK ; chiffrement, déchiffrement et signature OK.")
        return 0
    try:
        from .app import Application
    except (ImportError, ValueError) as exc:
        print(f"GTK4/libadwaita indisponible : {exc}\nVoir les paquets système et le venv --system-site-packages du README.", file=sys.stderr)
        return 1
    return Application().run(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main())
