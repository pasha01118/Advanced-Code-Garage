"""Versioned envelope encryption for repository-scoped secrets.

A unique data key encrypts each value. The data key is wrapped by a versioned
key-encryption key (KEK), so rotating the KEK never requires re-encrypting every
stored secret immediately: old ciphertext names its KEK version and stays
readable while the previous KEK remains configured.
"""

import base64
import hashlib
import hmac
import json

from cryptography.fernet import Fernet

from app.core.config import get_settings

_FORMAT_VERSION = 1


def _derive(secret: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())


def _current_kek_secret() -> str:
    settings = get_settings()
    secret = settings.user_key_encryption_key or settings.secret_key
    if settings.is_production:
        lowered = secret.strip().lower()
        if not secret or lowered.startswith("your-") or "change-me" in lowered or len(secret) < 32:
            raise RuntimeError(
                "A strong USER_KEY_ENCRYPTION_KEY (32+ chars, not a placeholder) is "
                "required in production before storing repository secrets."
            )
    return secret


def _kek_secret(version: str) -> str:
    settings = get_settings()
    if version == settings.vault_kek_version:
        return _current_kek_secret()
    for item in settings.vault_previous_keks.split(","):
        name, separator, secret = item.partition(":")
        if separator and name.strip() == version and secret.strip():
            return secret.strip()
    raise ValueError(f"No vault key configured for version '{version}'")


def encrypt_value(plaintext: str) -> str:
    settings = get_settings()
    version = settings.vault_kek_version
    dek = Fernet.generate_key()
    wrapped_dek = Fernet(_derive(_kek_secret(version))).encrypt(dek).decode("utf-8")
    ciphertext = Fernet(dek).encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return json.dumps(
        {
            "format": _FORMAT_VERSION,
            "kek": version,
            "dek": wrapped_dek,
            "value": ciphertext,
        },
        separators=(",", ":"),
        sort_keys=True,
    )


def decrypt_value(ciphertext: str) -> str:
    payload = json.loads(ciphertext)
    if payload.get("format") != _FORMAT_VERSION:
        raise ValueError("Unsupported secret ciphertext format")
    dek = Fernet(_derive(_kek_secret(str(payload["kek"])))).decrypt(
        str(payload["dek"]).encode("utf-8")
    )
    return Fernet(dek).decrypt(str(payload["value"]).encode("utf-8")).decode("utf-8")


def fingerprint(plaintext: str) -> str:
    """Stable non-reversible identifier for displaying a secret safely."""
    key = _derive(_kek_secret(get_settings().vault_kek_version))
    return hmac.new(key, plaintext.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
