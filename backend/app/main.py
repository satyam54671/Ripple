"""FastAPI entrypoint for RIPPLE Travel Disruption Recovery System."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.services.trip_service import seed_initial_trips_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_initial_trips_if_empty(db)
    finally:
        db.close()
    yield


settings = get_settings()

app = FastAPI(
    title="RIPPLE — AI-Powered Travel Disruption Recovery API",
    description=(
        "Cross-provider travel disruption recovery engine powered by LangGraph, "
        "MCP tool interfaces, Trip Dependency Graphs, and Google OR-Tools."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "RIPPLE API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
