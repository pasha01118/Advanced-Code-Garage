from app.repositories.audit import AuditRepository


class AuditService:
    def __init__(self, audit: AuditRepository | None = None) -> None:
        self.audit = audit or AuditRepository()

    async def record(self, actor: str, action: str, target: str | None = None, detail: dict | None = None) -> None:
        await self.audit.add(actor=actor, action=action, target=target, detail=detail)