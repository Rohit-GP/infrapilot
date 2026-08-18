"""
Application Agent.

Analyzes application and service evidence (HTTP, SSL/TLS, service/log
health) and produces structured findings describing application-layer
health.
"""

from __future__ import annotations

from src.graph.nodes._specialist import build_findings
from src.graph.state import APPLICATION_PROBES, GraphState


def run(state: GraphState) -> dict:
    evidence = state.get("evidence", [])
    findings = build_findings("application", APPLICATION_PROBES, evidence)
    return {"application_findings": findings}
