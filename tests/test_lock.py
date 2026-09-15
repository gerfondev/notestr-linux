import json

import pytest

from nostr_notes.lock import PasswordLock
from nostr_notes.storage import Storage


@pytest.fixture
def password_lock(tmp_path):
    return PasswordLock(Storage(tmp_path / "data"), time_cost=1, memory_cost=1024)


def test_create_and_verify_password(password_lock):
    assert not password_lock.exists()
    password_lock.set_password("correct cheval")
    assert password_lock.exists()
    assert password_lock.verify("correct cheval")
    assert not password_lock.verify("mauvais cheval")


def test_password_is_not_stored_and_file_is_private(password_lock):
    password_lock.set_password("phrase secrète")
    path = password_lock.storage.root / "lock.json"
    assert "phrase secrète" not in path.read_text()
    assert json.loads(path.read_text())["algorithm"] == "argon2id"
    assert path.stat().st_mode & 0o777 == 0o600


def test_short_password_is_rejected(password_lock):
    with pytest.raises(ValueError, match="8 caractères"):
        password_lock.set_password("court")


def test_invalid_lock_file_is_rejected(password_lock):
    password_lock.storage.write("lock.json", {"algorithm": "inconnu"})
    with pytest.raises(ValueError, match="invalide"):
        password_lock.verify("mot de passe")


def test_change_password_requires_current_password(password_lock):
    password_lock.set_password("ancien mot de passe")
    before = (password_lock.storage.root / "lock.json").read_text()
    with pytest.raises(ValueError, match="actuel est incorrect"):
        password_lock.change_password("erreur", "nouveau mot de passe")
    assert (password_lock.storage.root / "lock.json").read_text() == before
    assert password_lock.verify("ancien mot de passe")


def test_change_password_replaces_digest_and_salt(password_lock):
    password_lock.set_password("ancien mot de passe")
    path = password_lock.storage.root / "lock.json"
    before = json.loads(path.read_text())
    password_lock.change_password("ancien mot de passe", "nouveau mot de passe")
    after = json.loads(path.read_text())
    assert before["salt"] != after["salt"]
    assert before["digest"] != after["digest"]
    assert not password_lock.verify("ancien mot de passe")
    assert password_lock.verify("nouveau mot de passe")


def test_change_password_rejects_short_new_password(password_lock):
    password_lock.set_password("ancien mot de passe")
    with pytest.raises(ValueError, match="8 caractères"):
        password_lock.change_password("ancien mot de passe", "court")
    assert password_lock.verify("ancien mot de passe")
