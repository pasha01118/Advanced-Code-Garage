"""Small in-process sliding-window limiter for auth-sensitive endpoints.

This is best effort: state is per worker and restarts on deploy. It is meant to
slow down brute-force attempts, not to replace an edge/WAF rate limit.
"""

import asyncio
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = asyncio.Lock()
_WINDOW_SECONDS = 60.0


async def enforce_rate_limit(scope: str, request: Request) -> None:
    settings = get_settings()
    limit = settings.auth_rate_limit_per_minute
    # Behind Vercel/Render the socket peer is the proxy; its X-Forwarded-For
    # header carries the real client as the leftmost entry.
    forwarded = request.headers.get("x-forwarded-for", "")
    client = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "unknown"
    )
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
