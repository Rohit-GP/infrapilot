"""
Network Agent.

Analyzes network-related evidence (DNS, ping, TCP ports) and produces
structured findings describing network reachability and connectivity.
"""

from __future__ import annotations

from src.graph.nodes._specialist import build_findings
from src.graph.state import NETWORK_PROBES, GraphState


def run(state: GraphState) -> dict:
    evidence = state.get("evidence", [])
    findings = build_findings("network", NETWORK_PROBES, evidence)
    return {"network_findings": findings}
