"""
FastAPI Main Application Entrypoint.
Configures CORS, middleware, static media, and mounts API v1 routes.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from .core.config import settings
from .db.session import engine, Base
from .api.v1 import api_router


def _ensure_schema_columns(sync_conn):
    """Idempotently add newly introduced columns on existing databases."""
    inspector = inspect(sync_conn)
    if "users" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("users")}
        if "daily_goal" not in cols:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN daily_goal INTEGER NOT NULL DEFAULT 50"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure media directory exists
    os.makedirs(settings.MEDIA_DIR, exist_ok=True)
    # Create database tables if they don't exist and apply lightweight column migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_schema_columns)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev and DuckDNS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static media files mounting
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.MEDIA_DIR), name="media")

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker and load balancer probes."""
    return {"status": "healthy", "project": settings.PROJECT_NAME}


@app.get("/")
async def root():
    return {"message": "Welcome to Memora Anki Web Platform API", "docs": "/docs"}
