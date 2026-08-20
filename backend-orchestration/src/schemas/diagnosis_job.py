from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.evidence import EvidenceResponse
from src.schemas.hypothesis import HypothesisResponse


class DiagnosisJobCreateRequest(BaseModel):
    target_id: int
    # Optional probe overrides - if omitted, the diagnostics engine's
    # defaults are used (all registered probes, ports 80/443, etc).
    probes: list[str] | None = Field(
        default=None, description="Subset of probes to run, e.g. ['dns','ping','http']. Omit to run all."
    )
    ports: list[int] | None = Field(default=None, description="TCP ports to check, e.g. [80, 443]")
    http_url: str | None = Field(default=None, description="Override URL for the HTTP probe")


class DiagnosisJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: str
    user_id: int
    target_id: int
    status: str
    created_at: datetime
    aggregate_confidence: float | None
    root_cause: str | None
    recommendations: list[str] | None  # decoded from the stored JSON text
    error_message: str | None


class DiagnosisJobDetailResponse(DiagnosisJobResponse):
    evidence: list[EvidenceResponse] = []
    hypotheses: list[HypothesisResponse] = []
