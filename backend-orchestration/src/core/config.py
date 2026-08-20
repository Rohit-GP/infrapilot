"""
Runtime configuration for the FastAPI orchestration backend.

Everything here is environment-driven (see .env.example at the repo root)
so the same code runs unmodified in Docker Compose and locally.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    # --- Database ---
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://infrapilot:infrapilot@localhost:5432/infrapilot",
    )

    # --- JWT auth ---
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

    # --- Diagnostics engine trigger (Phase 3 "probe-trigger" module) ---
    # The diagnostics engine is a separate Python project with its own
    # venv/requirements, so it's invoked as a subprocess (`python -m
    # src.main ...`) rather than imported in-process.
    diagnostics_engine_dir: str = os.getenv(
        "DIAGNOSTICS_ENGINE_DIR",
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "diagnostics-engine"),
    )
    diagnostics_engine_python: str = os.getenv("DIAGNOSTICS_ENGINE_PYTHON", "python3")
    diagnostics_engine_timeout_s: float = float(os.getenv("DIAGNOSTICS_ENGINE_TIMEOUT_S", "60"))

    # --- CORS (React dashboard) ---
    cors_origins: list[str] = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    )


settings = Settings()
