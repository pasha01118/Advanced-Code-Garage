from app.repositories.notifications import NotificationsRepository


class NotificationService:
    def __init__(self, repo: NotificationsRepository | None = None) -> None:
        self.repo = repo or NotificationsRepository()

    async def list(self, owner_id: str, *, limit: int = 100, unread_only: bool = False) -> list[dict]:
        return await self.repo.list(owner_id, limit=limit, unread_only=unread_only)

    async def counts(self, owner_id: str) -> dict:
        rows = await self.repo.list(owner_id, limit=1000)
        return {"total": len(rows), "unread": sum(1 for row in rows if not row.get("read_at"))}

    async def notify(
        self,
        owner_id: str | None,
        *,
        title: str,
        body: str = "",
        type: str = "info",
        source: str = "system",
        source_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict | None:
        if not owner_id:
            return None
        if source_id:
            existing = await self.repo.find_source(owner_id, source, source_id)
            if existing:
                return existing
        return await self.repo.create(
            owner_id,
            title=title,
            body=body,
            type=type,
            source=source,
            source_id=source_id,
            metadata=metadata,
        )

    async def from_sentinel_event(self, owner_id: str | None, event: dict) -> dict | None:
        if not owner_id:
            return None
        severity = event.get("severity") or "info"
        notification_type = {
            "error": "error",
            "warn": "warn",
        }.get(severity, "info")
        return await self.notify(
            owner_id,
            title=event.get("title") or "Sentinel finding",
            body=event.get("message") or "",
            type=notification_type,
            source="sentinel",
            source_id=str(event.get("id") or ""),
            metadata={"scope": event.get("scope")},
        )

    async def project_failed(self, owner_id: str | None, project_id: str, message: str) -> dict | None:
        return await self.notify(
            owner_id,
            title="Project pipeline failed",
            body=message,
            type="error",
            source="project",
            source_id=project_id,
        )

    async def project_delivered(self, owner_id: str | None, project_id: str, name: str) -> dict | None:
        return await self.notify(
            owner_id,
            title="Project delivered",
            body=f"{name} completed all pipeline stages.",
            type="success",
            source="project",
            source_id=f"delivered:{project_id}",
        )

    async def mark_read(self, owner_id: str, notification_id: str) -> dict | None:
        return await self.repo.mark_read(owner_id, notification_id)

    async def mark_all_read(self, owner_id: str) -> int:
        return await self.repo.mark_all_read(owner_id)

    async def delete(self, owner_id: str, notification_id: str) -> bool:
        return await self.repo.delete(owner_id, notification_id)

    async def clear(self, owner_id: str) -> int:
        return await self.repo.clear(owner_id)
