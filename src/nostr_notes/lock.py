"""Verrouillage local de l'interface avec dérivation Argon2id."""
import base64
import hmac
import secrets

from argon2.low_level import Type, hash_secret_raw


class PasswordLock:
    VERSION = 1
    TIME_COST = 3
    MEMORY_COST = 65536
    PARALLELISM = 1
    HASH_LEN = 32
    SALT_LEN = 16

    def __init__(self, storage, *, time_cost=None, memory_cost=None):
        self.storage = storage
        self.time_cost = time_cost or self.TIME_COST
        self.memory_cost = memory_cost or self.MEMORY_COST

    def exists(self):
        return (self.storage.root / "lock.json").exists()

    def set_password(self, password):
        if len(password) < 8:
            raise ValueError("Le mot de passe doit contenir au moins 8 caractères.")
        salt = secrets.token_bytes(self.SALT_LEN)
        digest = self._derive(password, salt)
        self.storage.write("lock.json", {
            "version": self.VERSION,
            "algorithm": "argon2id",
            "time_cost": self.time_cost,
            "memory_cost": self.memory_cost,
            "parallelism": self.PARALLELISM,
            "salt": base64.b64encode(salt).decode("ascii"),
            "digest": base64.b64encode(digest).decode("ascii"),
        })

    def verify(self, password):
        data = self.storage.read("lock.json", None)
        if data is None:
            return False
        try:
            expected_fields = {
                "version", "algorithm", "time_cost", "memory_cost",
                "parallelism", "salt", "digest"
            }
            if set(data) != expected_fields:
                raise ValueError
            if (data["version"] != self.VERSION or data["algorithm"] != "argon2id"
                    or data["time_cost"] != self.time_cost
                    or data["memory_cost"] != self.memory_cost
                    or data["parallelism"] != self.PARALLELISM):
                raise ValueError
            salt = base64.b64decode(data["salt"], validate=True)
            expected = base64.b64decode(data["digest"], validate=True)
            if len(salt) != self.SALT_LEN or len(expected) != self.HASH_LEN:
                raise ValueError
        except (KeyError, TypeError, ValueError):
            raise ValueError("Configuration du verrouillage local invalide.") from None
        return hmac.compare_digest(self._derive(password, salt), expected)

    def change_password(self, current_password, new_password):
        if not self.verify(current_password):
            raise ValueError("Le mot de passe actuel est incorrect.")
        self.set_password(new_password)

    def _derive(self, password, salt):
        return hash_secret_raw(
            secret=password.encode("utf-8"),
            salt=salt,
            time_cost=self.time_cost,
            memory_cost=self.memory_cost,
            parallelism=self.PARALLELISM,
            hash_len=self.HASH_LEN,
            type=Type.ID,
        )
