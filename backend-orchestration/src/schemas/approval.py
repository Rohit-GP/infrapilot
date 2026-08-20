from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApprovalDecisionCreateRequest(BaseModel):
    decision: str = Field(pattern="^(APPROVED|REJECTED)$")
    remediation_action: str = Field(min_length=1, max_length=2000)


class ApprovalDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    approval_id: int
    job_id: str
    user_id: int
    decision: str
    remediation_action: str
    timestamp: datetime
