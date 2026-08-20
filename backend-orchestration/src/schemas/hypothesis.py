from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HypothesisEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    evidence_id: str
    relation: str  # SUPPORTS | CONTRADICTS


class HypothesisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hypothesis_id: int
    job_id: str
    rank: int
    description: str
    explanation: str
    hypothesis_confidence: float
    evidence_links: list[HypothesisEvidenceResponse] = []
