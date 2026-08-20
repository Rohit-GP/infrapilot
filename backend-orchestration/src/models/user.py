"""
User - maps to the class diagram's User entity.

`createDiagnosisJob()` and `makeApprovalDecision()` from the class diagram
are business operations, not persisted behavior, so they live as functions
in src/services/job_service.py and src/services/approval_service.py
respectively rather than as methods here.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="USER")  # "ADMIN" | "USER"
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    diagnosis_jobs: Mapped[list["DiagnosisJob"]] = relationship(back_populates="user")
    approval_decisions: Mapped[list["ApprovalDecision"]] = relationship(back_populates="user")
