"""Two shared roles for a local demo; these are not enterprise identities."""
import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Literal

from utils.errors import AppError


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise AppError("Use a password of at least 12 characters.")
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000)
    return f"pbkdf2_sha256$600000${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(iterations) <= 1_000_000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt),
                                    int(iterations)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class Principal:
    role: Literal["admin", "user"]

    def require_admin(self):
        if self.role != "admin":
            raise AppError("Only an administrator can manage documents.")


class AuthService:
    def __init__(self, settings):
        self.hashes = {"admin": settings.admin_password_hash.get_secret_value(),
                       "user": settings.user_password_hash.get_secret_value()}
        self.failures: dict[str, tuple[int, float]] = {}
        self.lock = threading.Lock()

    def login(self, role: str, password: str) -> Principal:
        with self.lock:
            count, until = self.failures.get(role, (0, 0))
            if time.monotonic() < until:
                raise AppError("Too many sign-in attempts. Please wait one minute.")
            if role not in self.hashes or not verify_password(password, self.hashes[role]):
                count += 1
                self.failures[role] = (count, time.monotonic() + 60 if count >= 5 else 0)
                raise AppError("The role or password is incorrect.")
            self.failures.pop(role, None)
            return Principal(role)
