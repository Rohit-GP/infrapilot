"""
System Agent.

Analyzes system-resource evidence (CPU, memory, disk) and produces
structured findings describing system health and resource conditions.
"""

from __future__ import annotations

from src.graph.nodes._specialist import build_findings
from src.graph.state import SYSTEM_PROBES, GraphState


def run(state: GraphState) -> dict:
    evidence = state.get("evidence", [])
    findings = build_findings("system", SYSTEM_PROBES, evidence)
    return {"system_findings": findings}
