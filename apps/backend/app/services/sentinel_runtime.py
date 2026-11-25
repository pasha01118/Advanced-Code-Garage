"""One shared Sentinel instance for the background loop and the admin API.

Keeping the runtime instance in one place makes `running` and `last_run_at`
meaningful in /sentinel/snapshot and prevents concurrent manual runs from
starting a second cycle.
"""

from app.services.notifications import NotificationService
from app.services.sentinel import SentinelService

_sentinel: SentinelService | None = None


def get_sentinel_service() -> SentinelService:
    global _sentinel
    if _sentinel is None:
        _sentinel = SentinelService(notifications=NotificationService())
    return _sentinel


def reset_sentinel_service() -> None:
    """Only used by tests/tools that need a clean runtime instance."""
    global _sentinel
    _sentinel = None
