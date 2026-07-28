"""
Shared data model for probe results.

Every probe (ping, dns, port, service) returns an Evidence object.
This is the contract the rest of the system (Redis -> LangGraph agents)
relies on, so keep it stable and probe-agnostic.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


class ProbeStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"   # probe ran, result indicates a partial problem
    FAILED = "failed"       # probe ran, result indicates the check failed
    ERROR = "error"         # probe itself could not complete (timeout, exception)


class ProbeType(str, Enum):
    PING = "ping"
    DNS = "dns"
    PORT = "port"
    SERVICE = "service"


@dataclass
class Evidence:
    """Structured, normalized result of a single probe run."""

    probe_type: ProbeType
    target: str
    status: ProbeStatus
    latency_ms: Optional[float] = None
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    job_id: Optional[str] = None
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["probe_type"] = self.probe_type.value
        d["status"] = self.status.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def error_result(cls, probe_type: ProbeType, target: str, exc: Exception, **kwargs) -> "Evidence":
        """Convenience constructor for when a probe throws instead of completing."""
        return cls(
            probe_type=probe_type,
            target=target,
            status=ProbeStatus.ERROR,
            message=f"{probe_type.value} probe raised an exception",
            error=str(exc),
            **kwargs,
        )
