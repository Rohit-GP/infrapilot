"""
Supervisor agent.

Determines which reasoning domains are relevant to the evidence.

Current domains:

    network
    system
    application

The supervisor does not use an LLM yet.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


NETWORK_PROBES = {
    "ping",
    "dns",
    "port",
}

SYSTEM_PROBES = {
    "cpu",
    "memory",
    "disk",
}

APPLICATION_PROBES = {
    "http",
    "ssl",
    "service",
}


def supervisor_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    evidence = state.get("evidence", [])

    required: set[str] = set()

    for item in evidence:

        probe_type = str(
            item.get("probe_type", "")
        ).lower()

        if probe_type in NETWORK_PROBES:
            required.add("network")

        if probe_type in SYSTEM_PROBES:
            required.add("system")

        if probe_type in APPLICATION_PROBES:
            required.add("application")

    return {
        "required_agents": sorted(required)
    }