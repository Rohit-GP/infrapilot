"""
DiagnosisJob - maps to the class diagram's DiagnosisJob entity.

Deviation from the diagram: `job_id` is a UUID (string), not a Long.
This is deliberate - the job_id has to be generated *before* any Postgres
row exists (it's threaded through Redis Streams evidence and the LangGraph
reasoning state across three independently-running services: this backend,
the diagnostics engine, and the AI reasoning layer), so it can't be a
DB-assigned auto-increment integer. The diagnostics engine already
generates a UUID job_id per run (see diagnostics-engine/src/core/runner.py)
- this backend reuses that same UUID as the primary key so evidence
published to Redis lines up with the DiagnosisJob row without translation.

`start()/complete()/fail()/addEvidence()/addHypothesis()/
calculateAggregateConfidence()` from the class diagram are implemented as
functions in src/services/job_service.py, operating on this model, rather
than as methods on it - keeps persistence and business logic separately
testable.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class JobStatus(str, Enum):
    QUEUED = "QUEUED"                      # row created, probes not started yet
    RUNNING = "RUNNING"                    # diagnostics engine is executing probes
    AWAITING_DIAGNOSIS = "AWAITING_DIAGNOSIS"  # evidence collected + published, waiting on AI agents
    COMPLETED = "COMPLETED"                # AI reasoning layer wrote a final diagnosis
    FAILED = "FAILED"                      # probes or reasoning failed


class DiagnosisJob(Base):
    __tablename__ = "diagnosis_jobs"

    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("targets.target_id"), nullable=False)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default=JobStatus.QUEUED.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    aggregate_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # final confidence of diagnosis
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)                # final root cause determined
    recommendations: Mapped[str | None] = mapped_column(Text, nullable=True)           # JSON-encoded list of strings

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)  # populated when status == FAILED

    user: Mapped["User"] = relationship(back_populates="diagnosis_jobs")
    target: Mapped["Target"] = relationship(back_populates="diagnosis_jobs")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    hypotheses: Mapped[list["Hypothesis"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    approval_decisions: Mapped[list["ApprovalDecision"]] = relationship(back_populates="job", cascade="all, delete-orphan")
