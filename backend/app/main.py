from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Advanced Code Garage API",
    description="Autonomous Multi-Agent Developer Ecosystem Backend",
    version="1.0.0"
)

# CORS Configuration for Frontend
# Accept comma-separated exact origins via FRONTEND_URLS env var (flexibility),
# PLUS regex so ANY *.vercel.app (including every preview/alias deployment)
# and localhost dev origins are always allowed.
cors_env = os.getenv("FRONTEND_URLS", "")
if cors_env:
    origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://advanced-code-garage.vercel.app",
        "https://advanced-code-garage-rgke.vercel.app",
        "https://www.advanced-code-garage-rgke.vercel.app",
    ]

cors_regex = os.getenv("FRONTEND_ORIGIN_REGEX", r"https://[a-zA-Z0-9-]+\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=cors_regex,
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

app.include_router(agents_router)
app.include_router(logs_router, prefix='/api/v1/logs', tags=['logs'])
app.include_router(projects_router, prefix='/api/v1/projects', tags=['projects'])
