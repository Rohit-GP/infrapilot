"""
FastAPI application entry point.

Usage:
    uvicorn src.main:app --reload
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import approvals, auth, diagnosis_jobs, targets
from src.core.config import settings
from src.core.database import Base, engine
from src.websocket import job_status

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="InfraPilot Backend Orchestration",
    description="Owns the diagnostic job lifecycle, REST API, JWT auth, and the human-in-the-loop approval gate.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(targets.router)
app.include_router(diagnosis_jobs.router)
app.include_router(approvals.router)
app.include_router(job_status.router)


@app.on_event("startup")
def on_startup() -> None:
    # Prototype-grade schema bootstrap - see docs/backend.md for why this
    # is create_all() rather than Alembic migrations at this stage.
    Base.metadata.create_all(bind=engine)
    job_status.set_main_loop(asyncio.get_event_loop())


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
