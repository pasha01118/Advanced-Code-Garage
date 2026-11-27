"""Regression tests for trusted-proxy-aware auth rate limiting."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import rate_limit
from app.core.rate_limit import _client_identity, enforce_rate_limit

TRUSTED = "10.0.0.0/8"


def _request(peer: str, forwarded: str | None = None):
    headers = {} if forwarded is None else {"x-forwarded-for": forwarded}
    return SimpleNamespace(client=SimpleNamespace(host=peer), headers=headers)


def test_untrusted_peer_ignores_forwarded_values():
    request = _request("203.0.113.9", "1.2.3.4, 5.6.7.8")
    assert _client_identity(request, TRUSTED) == "203.0.113.9"


def test_malformed_forwarded_chain_falls_back_to_peer():
    request = _request("10.0.0.5", "1.2.3.4, not-an-ip")
    assert _client_identity(request, TRUSTED) == "10.0.0.5"


@pytest.mark.asyncio
async def test_rotating_forwarded_values_share_one_bucket(monkeypatch):
    monkeypatch.setattr(
        rate_limit,
        "get_settings",
        lambda: SimpleNamespace(trusted_proxy_cidrs=TRUSTED, auth_rate_limit_per_minute=2),
    )
    rate_limit._hits.clear()

    # The proxy peer is trusted and the rightmost entry is the client it saw.
    # Rotating the client-controlled leftmost entries must not rotate the bucket.
    for rotating in ("1.1.1.1", "2.2.2.2"):
        await enforce_rate_limit("test-rotation", _request("10.0.0.5", f"{rotating}, 203.0.113.9"))

    with pytest.raises(HTTPException) as exc:
        await enforce_rate_limit("test-rotation", _request("10.0.0.5", "3.3.3.3, 203.0.113.9"))
    assert exc.value.status_code == 429
    rate_limit._hits.clear()
