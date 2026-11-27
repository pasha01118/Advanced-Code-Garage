from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, audit: AuditRepository | None = None) -> None:
        self.audit = audit or AuditRepository()

    async def record(
        self,
        actor: str,
        action: str,
        target: str | None = None,
        detail: dict | None = None,
        owner_id: str | None = None,
    ) -> None:
        await self.audit.add(
            actor=actor,
            action=action,
            target=target,
            detail=detail,
            owner_id=owner_id,
        )

    async def list(
        self,
        owner_id: str | None = None,
        *,
        limit: int = 100,
        action: str | None = None,
        since: str | None = None,
    ) -> list[dict]:
        return await self.audit.list(owner_id, limit=limit, action=action, since=since)
