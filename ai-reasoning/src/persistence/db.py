"""
Database access for the AI Reasoning Layer's write-back step.

Uses SQLAlchemy Core (not the ORM) with explicit `Table` objects rather
than importing backend-orchestration's ORM models - these are two
independently deployed services with separate dependency sets (see
ai-reasoning/requirements.txt vs backend-orchestration/requirements.txt),
so this module only needs to agree on column names/types with
backend-orchestration/src/models/*.py, not share code with it.

This service only ever writes to three tables: `diagnosis_jobs` (updating
the row the backend already created), `hypotheses`, and
`hypothesis_evidence` (both of which it owns end-to-end). It never writes
to `evidence` - that's populated by the backend from the diagnostics
engine's subprocess output.
"""

from __future__ import annotations

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import sessionmaker

from src.core.config import DatabaseConfig

metadata = MetaData()

diagnosis_jobs = Table(
    "diagnosis_jobs",
    metadata,
    Column("job_id", UUID(as_uuid=False), primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("target_id", Integer, nullable=False),
    Column("status", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True)),
    Column("aggregate_confidence", Float, nullable=True),
    Column("root_cause", Text, nullable=True),
    Column("recommendations", Text, nullable=True),
    Column("error_message", Text, nullable=True),
)

hypotheses = Table(
    "hypotheses",
    metadata,
    Column("hypothesis_id", Integer, primary_key=True, autoincrement=True),
    Column("job_id", UUID(as_uuid=False), ForeignKey("diagnosis_jobs.job_id"), nullable=False),
    Column("rank", Integer, nullable=False),
    Column("description", String(500), nullable=False),
    Column("explanation", Text, nullable=False),
    Column("hypothesis_confidence", Float, nullable=False),
)

hypothesis_evidence = Table(
    "hypothesis_evidence",
    metadata,
    Column("hypothesis_id", Integer, ForeignKey("hypotheses.hypothesis_id"), primary_key=True),
    Column("evidence_id", UUID(as_uuid=False), ForeignKey("evidence.evidence_id"), primary_key=True),
    Column("relation", String(16), nullable=False),
)


def get_engine(config: DatabaseConfig | None = None):
    config = config or DatabaseConfig()
    return create_engine(config.database_url, pool_pre_ping=True, future=True)


def get_session_factory(config: DatabaseConfig | None = None):
    return sessionmaker(bind=get_engine(config), autoflush=False, autocommit=False, future=True)
