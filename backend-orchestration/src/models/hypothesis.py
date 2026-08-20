"""
Hypothesis - maps to the class diagram's Hypothesis entity.

Written by the AI Reasoning Layer (ai-reasoning/src/persistence), not by
this backend - the Final Diagnosis Agent produces ranked hypotheses (see
ai-reasoning/src/graph/nodes/final_diagnosis_agent.py), which get persisted
here once the LangGraph workflow finishes for a job. This backend only
*reads* hypotheses (GET endpoints).

`addEvidence()/calculateConfidence()/getSupportingEvidence()/
getContradictingEvidence()` from the class diagram are implemented as
functions in ai-reasoning's persistence layer and this backend's
services/hypothesis query helpers, not as methods here.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    hypothesis_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("diagnosis_jobs.job_id"), nullable=False)

    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 = highest
    description: Mapped[str] = mapped_column(String(500), nullable=False)  # brief statement of hypothesis
    explanation: Mapped[str] = mapped_column(Text, nullable=False)         # detailed explanation
    hypothesis_confidence: Mapped[float] = mapped_column(nullable=False)   # confidence in this hypothesis being true

    job: Mapped["DiagnosisJob"] = relationship(back_populates="hypotheses")
    evidence_links: Mapped[list["HypothesisEvidence"]] = relationship(back_populates="hypothesis", cascade="all, delete-orphan")
