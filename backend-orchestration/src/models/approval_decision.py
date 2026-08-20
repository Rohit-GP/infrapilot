"""
ApprovalDecision - maps to the class diagram's ApprovalDecision entity.

This is the human-in-the-loop safety gate: an admin user reviews a
DiagnosisJob's recommendations and approves or rejects the suggested
remediation action before anything destructive is (hypothetically) carried
out. `approve()/reject()/isApproved()` from the class diagram are
implemented as functions in src/services/approval_service.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ApprovalDecision(Base):
    __tablename__ = "approval_decisions"

    approval_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("diagnosis_jobs.job_id"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)

    decision: Mapped[str] = mapped_column(String(16), nullable=False)  # APPROVED | REJECTED
    remediation_action: Mapped[str] = mapped_column(Text, nullable=False)  # action to be taken
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job: Mapped["DiagnosisJob"] = relationship(back_populates="approval_decisions")
    user: Mapped["User"] = relationship(back_populates="approval_decisions")

    def is_approved(self) -> bool:
        return self.decision == "APPROVED"
