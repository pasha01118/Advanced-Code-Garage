import asyncio
import time

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwk, jwt

from app.core.config import get_settings

_bearer = HTTPBearer(auto_error=False)
_jwks_cache: dict | None = None
_jwks_at: float = 0.0
_jwks_refresh_at: float = 0.0
_jwks_refresh_lock = asyncio.Lock()
JWKS_TTL_SECONDS = 3600.0
# Cooldown for forced refreshes triggered by an unknown `kid`. It bounds how
# often unknown keys can hit the JWKS endpoint and coalesces concurrent calls.
JWKS_REFRESH_COOLDOWN_SECONDS = 30.0
ALGORITHMS = ["ES256", "RS256"]


async def _get_jwks(*, force: bool = False) -> dict:
    global _jwks_cache, _jwks_at, _jwks_refresh_at
    async with _jwks_refresh_lock:
        now = time.monotonic()
        if not force and _jwks_cache is not None and (now - _jwks_at) < JWKS_TTL_SECONDS:
            return _jwks_cache
        if force and now < _jwks_refresh_at and _jwks_cache is not None:
            # Another request already refreshed during this cooldown.
            return _jwks_cache
        settings = get_settings()
        url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                _jwks_cache = response.json()
                _jwks_at = time.monotonic()
        finally:
            # Even a failed refresh gets a cooldown so bad keys cannot hammer
            # the identity provider; genuine rotation retries after the window.
            _jwks_refresh_at = time.monotonic() + JWKS_REFRESH_COOLDOWN_SECONDS
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
    except JWTError as exc:
        # Only an unknown signing key justifies a refresh; malformed or expired
        # tokens must not let unauthenticated callers hammer the JWKS endpoint.
        if "Unknown signing key" not in str(exc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
        try:
            if time.monotonic() < _jwks_refresh_at:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
            refreshed = await _get_jwks(force=True)
            return _decode(credentials.credentials, refreshed)
        except Exception as refresh_exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from refresh_exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


async def require_authenticated(user: dict = Depends(require_user)) -> dict:
    if user.get("role") not in {"authenticated", "service_role"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return user


ADMIN_ROLE = "admin"


def _is_admin(user: dict) -> bool:
    settings = get_settings()
    allowlisted = {s.strip() for s in settings.admin_user_ids.split(",") if s.strip()}
    if user.get("sub") in allowlisted:
        return True
    app_metadata = user.get("app_metadata") or {}
    if app_metadata.get("role") == ADMIN_ROLE:
        return True
    return user.get("role") == "service_role"


async def require_admin(user: dict = Depends(require_authenticated)) -> dict:
    if not _is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user