from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="Advanced Code Garage API",
    description="Autonomous Multi-Agent Developer Ecosystem Backend",
    version="1.0.0"
)

# CORS Configuration for Frontend
origins = [
    "http://localhost:3000",
    "https://advanced-code-garage.vercel.app", # Update when deployed
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

app.include_router(agents_router)
