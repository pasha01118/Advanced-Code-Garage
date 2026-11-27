from app.repositories.preferences import PreferencesRepository


class PreferencesService:
    def __init__(self, repo: PreferencesRepository | None = None) -> None:
        self.repo = repo or PreferencesRepository()

    async def get(self, owner_id: str) -> dict:
        return await self.repo.get(owner_id)

    async def update(self, owner_id: str, changes: dict) -> dict:
        clean = {key: value for key, value in changes.items() if value is not None}
        return await self.repo.upsert(owner_id, clean)
