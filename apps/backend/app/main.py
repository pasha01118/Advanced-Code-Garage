import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.services.ops_state import require_service
from app.services.project import cancel_pipeline_tasks
from app.services.sentinel_runtime import get_sentinel_service

logger = logging.getLogger(__name__)

settings = get_settings()

_sentinel_task: asyncio.Task | None = None


async def _sentinel_loop():
    service = get_sentinel_service()
    interval = settings.sentinel_interval_seconds
    while True:
        try:
            await service.run_cycle()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Sentinel cycle failed")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _sentinel_task
    _sentinel_task = asyncio.create_task(_sentinel_loop())
    yield
    _sentinel_task.cancel()
    try:
        await _sentinel_task
    except asyncio.CancelledError:
        pass
    cancel_pipeline_tasks()


app = FastAPI(
    title="Advanced Code Garage API",
    description="Autonomous Multi-Agent Developer Ecosystem Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# Exact origins come from FRONTEND_URLS; the anchored regex additionally allows
# single-label *.vercel.app preview deployments.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/")
async def root():
    return {
        "system": "Advanced Code Garage",
        "status": "Online",
        "message": "Backend API is running. Agent Swarm ready."
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "agents": "active"}

# Import Routers
from app.routers.agents import router as agents_router  # noqa: E402
from app.api.v1.logs.route import router as logs_router  # noqa: E402
from app.api.v1.projects.route import router as projects_router  # noqa: E402
from app.api.v1.ai.route import router as ai_router  # noqa: E402
from app.api.v1.auth.route import router as auth_router  # noqa: E402
from app.api.v1.admin.route import router as admin_router  # noqa: E402
from app.api.v1.notifications.route import router as notifications_router  # noqa: E402
from app.api.v1.preferences.route import router as preferences_router  # noqa: E402
from app.api.v1.terminal.route import router as terminal_router  # noqa: E402
from app.api.v1.workspace.route import router as workspace_router  # noqa: E402

app.include_router(agents_router)
app.include_router(
    logs_router,
    prefix='/api/v1/logs',
    tags=['logs'],
    dependencies=[Depends(require_service("telemetry"))],
)
app.include_router(projects_router, prefix='/api/v1/projects', tags=['projects'])
app.include_router(
    ai_router,
    prefix='/api/v1/ai',
    tags=['ai'],
    dependencies=[Depends(require_service("ai_routing"))],
)
app.include_router(auth_router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(admin_router, prefix='/api/v1/admin', tags=['admin'])
app.include_router(
    notifications_router,
    prefix='/api/v1/notifications',
    tags=['notifications'],
)
app.include_router(
    preferences_router,
    prefix='/api/v1/preferences',
    tags=['preferences'],
)
app.include_router(
    terminal_router,
    prefix='/api/v1/terminal',
    tags=['terminal'],
    dependencies=[Depends(require_service("telemetry"))],
)
app.include_router(workspace_router, prefix='/api/v1/workspace', tags=['workspace'])
