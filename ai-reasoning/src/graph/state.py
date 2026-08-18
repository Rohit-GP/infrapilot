"""
Shared graph state for the LangGraph reasoning workflow.

Every node reads/writes a subset of this TypedDict. Keeping the shape in one
place is what lets Network/System/Application agents run as independent
parallel branches: each one only ever writes its own key
(`network_findings` / `system_findings` / `application_findings`), so
LangGraph doesn't need a custom reducer to merge concurrent branch output.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict


class GraphState(TypedDict, total=False):
    # --- input (populated by the Redis consumer before the graph runs) ---
    job_id: str
    target: str
    evidence: list[dict[str, Any]]          # raw Evidence.to_dict() payloads for the job

    # --- supervisor output ---
    required_agents: list[str]              # which specialist agents actually have evidence to look at

    # --- specialist agent output (one list of findings each) ---
    network_findings: list[dict[str, Any]]
    system_findings: list[dict[str, Any]]
    application_findings: list[dict[str, Any]]

    # --- evidence agent output ---
    validated_findings: list[dict[str, Any]]

    # --- final diagnosis agent output ---
    diagnosis: dict[str, Any]

    # --- standardized payload for the (not-yet-implemented) Cloud LLM ---
    llm_input: dict[str, Any]


# --- Domain routing -----------------------------------------------------
# Which specialist agent is responsible for each ProbeType (see
# diagnostics-engine/src/core/models.py::ProbeType). Kept here, not
# scattered across the node files, so the mapping stays a single source of
# truth for both routing and for the "required_agents" field.
NETWORK_PROBES = {"ping", "dns", "port"}
SYSTEM_PROBES = {"cpu", "memory", "disk"}
APPLICATION_PROBES = {"http", "ssl", "service"}

AGENT_PROBE_MAP: dict[str, set[str]] = {
    "network": NETWORK_PROBES,
    "system": SYSTEM_PROBES,
    "application": APPLICATION_PROBES,
}

# --- Severity -------------------------------------------------------------
# Findings are derived deterministically from ProbeStatus - no judgement
# call happens at the LLM layer for this part, it's all evidence-backed.
STATUS_TO_SEVERITY = {
    "ok": "low",
    "degraded": "medium",
    "failed": "high",
    "error": "medium",   # the probe itself couldn't complete: worth flagging, but not proof of a real fault
}

SEVERITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def severity_for_status(status: str) -> str:
    return STATUS_TO_SEVERITY.get(status, "medium")
