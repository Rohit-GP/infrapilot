"""
HypothesisEvidence - maps to the class diagram's HypothesisEvidence
association entity, with the composite primary key (hypothesis_id,
evidence_id) called out explicitly in the diagram.

Written by the AI Reasoning Layer alongside Hypothesis rows.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"

    hypothesis_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("hypotheses.hypothesis_id"), primary_key=True
    )
    evidence_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("evidence.evidence_id"), primary_key=True
    )
    relation: Mapped[str] = mapped_column(String(16), nullable=False)  # SUPPORTS | CONTRADICTS

    hypothesis: Mapped["Hypothesis"] = relationship(back_populates="evidence_links")
    evidence: Mapped["Evidence"] = relationship(back_populates="hypothesis_links")

    def supports(self) -> bool:
        return self.relation == "SUPPORTS"

    def contradicts(self) -> bool:
        return self.relation == "CONTRADICTS"
