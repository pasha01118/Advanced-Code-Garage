from app.repositories.modes import ModesRepository
from app.services.audit import AuditService


class ModeService:
    def __init__(self, repo: ModesRepository | None = None, audit: AuditService | None = None) -> None:
        self.repo = repo or ModesRepository()
        self.audit = audit or AuditService()

    async def get(self) -> str:
        return await self.repo.get()

    async def set(self, mode: str, actor: str = "system") -> str:
        previous = await self.repo.get()
        updated = await self.repo.set(mode)
        await self.audit.record(actor=actor, action="mode.set", target="system", detail={"from": previous, "to": updated})
        return updated