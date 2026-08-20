from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class TargetCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    identifier: str = Field(min_length=1, max_length=255, description="Domain, IP, or hostname")
    type: str = Field(pattern="^(SERVER|APPLICATION|NETWORK)$")


class TargetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_id: int
    name: str
    identifier: str
    type: str
