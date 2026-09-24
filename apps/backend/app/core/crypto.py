"""Symmetric encryption for user-supplied provider API keys (Fernet).

The encryption key is derived from USER_KEY_ENCRYPTION_KEY (or the legacy
SECRET_KEY) via SHA-256, so any stable secret yields a stable Fernet key.
"""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def get_fernet() -> Fernet:
    settings = get_settings()
    secret = settings.user_key_encryption_key or settings.secret_key or "change-me"
    return Fernet(_derive_fernet_key(secret))


def encrypt_secret(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(ciphertext: str) -> str:
    return get_fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")