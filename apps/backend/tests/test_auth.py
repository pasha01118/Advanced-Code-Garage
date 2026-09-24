import base64
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jose import jwt

from app.core.auth import _decode
from app.core.config import get_settings


def _b64url(n: int) -> str:
    return base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()


def _ec_vectors():
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kid": "kid-ec",
                "kty": "EC",
                "crv": "P-256",
                "x": _b64url(pub.x),
                "y": _b64url(pub.y),
                "alg": "ES256",
                "use": "sig",
            }
        ]
    }
    return key, jwks


def _rsa_vectors():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kid": "kid-rsa",
                "kty": "RSA",
                "n": _b64url(pub.n),
                "e": _b64url(pub.e),
                "alg": "RS256",
                "use": "sig",
            }
        ]
    }
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    return pem, jwks


def _decode_claims(token, jwks):
    settings = get_settings()
    old_url = settings.supabase_url
    settings.supabase_url = "https://acg-test.supabase.co"
    try:
        return _decode(token, jwks)
    finally:
        settings.supabase_url = old_url


def test_es256_token_is_verified():
    key, jwks = _ec_vectors()
    token = jwt.encode(
        {
            "iss": "https://acg-test.supabase.co/auth/v1",
            "sub": "user-1",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(time.time()),
        },
        key,
        algorithm="ES256",
        headers={"kid": "kid-ec"},
    )
    claims = _decode_claims(token, jwks)
    assert claims["sub"] == "user-1"
    assert claims["role"] == "authenticated"


def test_rs256_token_is_still_verified():
    pem, jwks = _rsa_vectors()
    token = jwt.encode(
        {
            "iss": "https://acg-test.supabase.co/auth/v1",
            "sub": "user-2",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(time.time()),
        },
        pem,
        algorithm="RS256",
        headers={"kid": "kid-rsa"},
    )
    claims = _decode_claims(token, jwks)
    assert claims["sub"] == "user-2"


def test_wrong_issuer_is_rejected():
    key, jwks = _ec_vectors()
    token = jwt.encode(
        {
            "iss": "https://evil.example.com/auth/v1",
            "sub": "user-3",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": int(time.time()),
        },
        key,
        algorithm="ES256",
        headers={"kid": "kid-ec"},
    )
    with pytest.raises(Exception):
        _decode_claims(token, jwks)