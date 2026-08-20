"""Target - maps to the class diagram's Target entity (the thing being diagnosed)."""

from __future__ import annotations

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Target(Base):
    __tablename__ = "targets"

    target_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)  # domain, IP, hostname
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # SERVER | APPLICATION | NETWORK

    diagnosis_jobs: Mapped[list["DiagnosisJob"]] = relationship(back_populates="target")

    def get_identifier(self) -> str:
        return self.identifier

    def get_type(self) -> str:
        return self.type
