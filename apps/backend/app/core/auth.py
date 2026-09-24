import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwk, jwt

from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)
_jwks_cache: dict | None = None
_jwks_at: float = 0.0
JWKS_TTL_SECONDS = 3600.0
ALGORITHMS = ["ES256", "RS256"]


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_at
    now = time.time()
    if _jwks_cache is not None and (now - _jwks_at) < JWKS_TTL_SECONDS:
        return _jwks_cache
    settings = get_settings()
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_at = now
    return _jwks_cache


def _decode(token: str, jwks: dict) -> dict:
    settings = get_settings()
    unverified = jwt.get_unverified_header(token)
    kid = unverified.get("kid")
    keys = {item["kid"]: item for item in jwks.get("keys", []) if "kid" in item}
    if kid not in keys:
        raise JWTError("Unknown signing key")
    rsa_key = jwk.construct(keys[kid])
    return jwt.decode(
        token,
        rsa_key,
        algorithms=ALGORITHMS,
        issuer=f"{settings.supabase_url.rstrip('/')}/auth/v1",
        audience="authenticated",
    )


async def require_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        jwks = await _get_jwks()
        return _decode(credentials.credentials, jwks)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


async def require_authenticated(user: dict = Depends(require_user)) -> dict:
    if user.get("role") not in {"authenticated", "service_role"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user