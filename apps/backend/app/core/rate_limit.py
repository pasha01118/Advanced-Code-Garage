"""Small in-process sliding-window limiter for auth-sensitive endpoints.

This is best effort: state is per worker and restarts on deploy. It is meant to
slow down brute-force attempts, not to replace an edge/WAF rate limit.
"""

import asyncio
import ipaddress
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = asyncio.Lock()
_WINDOW_SECONDS = 60.0


@lru_cache(maxsize=32)
def _proxy_networks(raw: str) -> tuple:
    networks = []
    for value in raw.split(","):
        value = value.strip()
        if not value:
            continue
        try:
            networks.append(ipaddress.ip_network(value, strict=False))
        except ValueError:
            continue
    return tuple(networks)


def _parse_ip(value: str):
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def _client_identity(request: Request, trusted_cidrs: str) -> str:
    """Trust X-Forwarded-For only from an explicitly configured proxy peer.

    Walk the chain from the right (the proxy closest to us) and ignore trusted
    proxy hops. Client-controlled leftmost entries therefore cannot rotate a
    rate-limit bucket. Malformed or absent chains fall back to the socket peer.
    """
    peer = request.client.host if request.client else "unknown"
    networks = _proxy_networks(trusted_cidrs)
    peer_ip = _parse_ip(peer)
    if peer_ip is None or not any(peer_ip in net for net in networks):
        return peer

    forwarded = request.headers.get("x-forwarded-for", "")
    if not forwarded:
        return peer
    chain = [value.strip() for value in forwarded.split(",")]
    if not chain or any(_parse_ip(value) is None for value in chain):
        return peer
    for value in reversed(chain):
        address = _parse_ip(value)
        if not any(address in net for net in networks):
            return str(address)
    return peer


async def enforce_rate_limit(scope: str, request: Request) -> None:
    settings = get_settings()
    limit = settings.auth_rate_limit_per_minute
    client = _client_identity(request, getattr(settings, "trusted_proxy_cidrs", ""))
    key = (scope, client)
    now = time.monotonic()
    async with _lock:
        bucket = _hits[key]
        while bucket and now - bucket[0] >= _WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many attempts. Try again shortly.",
            )
        bucket.append(now)
        # Keep the map bounded even for highly distributed client IPs.
        if len(_hits) > 10000:
            stale = [k for k, v in _hits.items() if not v or now - v[-1] >= _WINDOW_SECONDS]
            for stale_key in stale:
                _hits.pop(stale_key, None)
