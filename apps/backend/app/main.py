import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.services.sentinel import SentinelService

settings = get_settings()

_sentinel_task: asyncio.Task | None = None


async def _sentinel_loop():
    service = SentinelService()
    interval = settings.sentinel_interval_seconds
    while True:
        try:
            await service.run_cycle()
        except Exception:
            pass
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


app = FastAPI(
    title="Advanced Code Garage API",
    description="Autonomous Multi-Agent Developer Ecosystem Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration for Frontend
# Exact origins come from FRONTEND_URLS (comma-separated), with a regex so ANY
# *.vercel.app (including every preview/alias deployment) plus localhost dev
# origins are always allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.frontend_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
from app.routers.agents import router as agents_router
from app.api.v1.logs.route import router as logs_router
from app.api.v1.projects.route import router as projects_router
from app.api.v1.ai.route import router as ai_router
from app.api.v1.auth.route import router as auth_router
from app.api.v1.admin.route import router as admin_router

app.include_router(agents_router)
app.include_router(logs_router, prefix='/api/v1/logs', tags=['logs'])
app.include_router(projects_router, prefix='/api/v1/projects', tags=['projects'])
app.include_router(ai_router, prefix='/api/v1/ai', tags=['ai'])
app.include_router(auth_router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(admin_router, prefix='/api/v1/admin', tags=['admin'])