import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.api.v1.ai.route import get_ai_service
from app.api.v1.notifications.route import get_notification_service
from app.api.v1.preferences.route import get_preferences_service
from app.api.v1.projects.route import get_project_service
from app.api.v1.terminal.route import get_terminal_service
from app.api.v1.workspace.route import get_audit_service, get_workspace_service
from app.core.auth import require_authenticated
from app.main import app
from app.repositories.audit import AuditRepository
from app.routers.agents import get_mode_service
from app.services.ai_integration import AIIntegrationService, SessionModelCache
from app.services.audit import AuditService
from app.services.mode import ModeService
from app.services.notifications import NotificationService
from app.services.ops_state import OpsStateService, get_ops_service as get_global_ops_service
from app.services.preferences import PreferencesService
from app.services.project import ProjectService
from app.services.terminal import TerminalService
from app.services.workspace import WorkspaceService

from tests.fakes import (
    FakeAdminRepository,
    FakeAIKeysRepository,
    FakeAuditRepository,
    FakeLogsRepository,
    FakeHistoryRepository,
    FakeModesRepository,
    FakeNotificationsRepository,
    FakePreferencesRepository,
    FakeProjectsRepository,
    FakeSnippetsRepository,
    FakeTemplatesRepository,
)


pytest_plugins = ("pytest_asyncio",)


@pytest.fixture()
def fakes():
    return {
        "modes": FakeModesRepository(),
        "projects": FakeProjectsRepository(),
        "audit": FakeAuditRepository(),
        "logs": FakeLogsRepository(),
        "ai_keys": FakeAIKeysRepository(),
        "admin": FakeAdminRepository(),
        "preferences": FakePreferencesRepository(),
        "snippets": FakeSnippetsRepository(),
        "history": FakeHistoryRepository(),
        "notifications": FakeNotificationsRepository(),
        "templates": FakeTemplatesRepository(),
    }


def _authed_user():
    return {"sub": "test-user", "role": "authenticated", "email": "tester@example.com"}


@pytest.fixture()
def client(fakes):
    def override_mode_service() -> ModeService:
        return ModeService(repo=fakes["modes"], audit=AuditService(audit=fakes["audit"]))

    def override_project_service() -> ProjectService:
        return ProjectService(
            projects=fakes["projects"],
            logs=fakes["logs"],
            audit=AuditService(audit=fakes["audit"]),
            templates=fakes["templates"],
            notifications=NotificationService(repo=fakes["notifications"]),
        )

    def override_ai_service() -> AIIntegrationService:
        return AIIntegrationService(repo=fakes["ai_keys"])

    def override_global_ops_service() -> OpsStateService:
        return OpsStateService(repo=fakes["admin"])

    def override_notifications_service() -> NotificationService:
        return NotificationService(repo=fakes["notifications"])

    def override_preferences_service() -> PreferencesService:
        return PreferencesService(repo=fakes["preferences"])

    def override_terminal_service() -> TerminalService:
        return TerminalService(
            snippets=fakes["snippets"],
            history=fakes["history"],
            projects=fakes["projects"],
            logs=fakes["logs"],
            audit=AuditService(audit=fakes["audit"]),
        )

    def override_workspace_service() -> WorkspaceService:
        return WorkspaceService(
            projects=fakes["projects"],
            templates=fakes["templates"],
            logs=fakes["logs"],
            ai_keys=fakes["ai_keys"],
            notifications=NotificationService(repo=fakes["notifications"]),
            ops=OpsStateService(repo=fakes["admin"]),
            admin=fakes["admin"],
            modes=ModeService(repo=fakes["modes"], audit=AuditService(audit=fakes["audit"])),
        )

    app.dependency_overrides[get_mode_service] = override_mode_service
    app.dependency_overrides[get_project_service] = override_project_service
    app.dependency_overrides[get_ai_service] = override_ai_service
    app.dependency_overrides[get_global_ops_service] = override_global_ops_service
    app.dependency_overrides[get_notification_service] = override_notifications_service
    app.dependency_overrides[get_preferences_service] = override_preferences_service
    app.dependency_overrides[get_terminal_service] = override_terminal_service
    app.dependency_overrides[get_workspace_service] = override_workspace_service
    app.dependency_overrides[get_audit_service] = lambda: AuditService(audit=fakes["audit"])
    app.dependency_overrides[require_authenticated] = _authed_user
    SessionModelCache.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


class _UnauthenticatedClient:
    """Proxy that issues requests without the `client` fixture's auth override."""

    def __init__(self, wrapped: TestClient) -> None:
        self._wrapped = wrapped

    def _request(self, method: str, *args, **kwargs):
        auth_override = app.dependency_overrides.pop(require_authenticated, None)
        try:
            return getattr(self._wrapped, method)(*args, **kwargs)
        finally:
            if auth_override is not None:
                app.dependency_overrides[require_authenticated] = auth_override

    def get(self, *args, **kwargs):
        return self._request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request("put", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self._request("patch", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request("delete", *args, **kwargs)


@pytest.fixture()
def bare_client(fakes):
    app.dependency_overrides[get_global_ops_service] = lambda: OpsStateService(repo=fakes["admin"])
    yield _UnauthenticatedClient(TestClient(app))
    app.dependency_overrides.clear()