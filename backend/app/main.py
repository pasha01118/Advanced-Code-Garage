from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Advanced Code Garage API",
    description="Autonomous Multi-Agent Developer Ecosystem Backend",
    version="1.0.0"
)

# CORS Configuration for Frontend
# Use environment variable for production frontend URL
frontend_url = os.getenv("FRONTEND_URL", "https://advanced-code-garage.vercel.app")
origins = [
    "http://localhost:3000",
    frontend_url,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
