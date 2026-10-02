from nostr_notes.i18n import set_language, get_language, tr
from nostr_notes.storage import Storage


def test_language_fallback_and_formatted_values_are_not_translated():
    try:
        set_language('en')
        assert tr('Réglages') == 'Settings'
        assert tr('PDF exporté : {0}', 'Réglages.pdf') == 'PDF exported: Réglages.pdf'
        assert tr('https://example.org/Épingler') == 'https://example.org/Épingler'
        set_language('unexpected')
        assert get_language() == 'fr'
        assert tr('Réglages') == 'Réglages'
    finally:
        set_language('fr')


def test_language_preference_is_separate_from_account_and_encrypted_cache(tmp_path):
    store = Storage(tmp_path)
    store.write('config.json', {'relays': ['wss://example.org'], 'pubkey': 'synthetic-public-key'})
    store.write('synthetic-public-key.json', [{'content': 'synthetic-encrypted-event'}])
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    store.write('preferences.json', {'language': 'en'})
    assert Storage(tmp_path).read('preferences.json', {})['language'] == 'en'
    assert all((tmp_path / name).read_bytes() == data for name, data in before.items())
