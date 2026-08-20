from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    job_id: str
    probe_type: str
    observed_result: str
    result_status: str
    latency_ms: float | None
    evidence_confidence: float
    timestamp: datetime
