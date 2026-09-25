import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.api.v1.ai.route import get_ai_service
from app.api.v1.projects.route import get_project_service
from app.core.auth import require_authenticated
from app.main import app
from app.repositories.audit import AuditRepository
from app.routers.agents import get_mode_service
from app.services.ai_integration import AIIntegrationService, SessionModelCache
from app.services.audit import AuditService
from app.services.mode import ModeService
from app.services.project import ProjectService

from tests.fakes import (
    FakeAIKeysRepository,
    FakeAuditRepository,
    FakeLogsRepository,
    FakeModesRepository,
    FakeProjectsRepository,
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
        )

    def override_ai_service() -> AIIntegrationService:
        return AIIntegrationService(repo=fakes["ai_keys"])

    app.dependency_overrides[get_mode_service] = override_mode_service
    app.dependency_overrides[get_project_service] = override_project_service
    app.dependency_overrides[get_ai_service] = override_ai_service
    app.dependency_overrides[require_authenticated] = _authed_user
    SessionModelCache.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def bare_client():
    yield TestClient(app)