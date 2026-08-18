"""
Supervisor Agent.

Runs first, before the specialist agents. It doesn't diagnose anything -
it just looks at which probe types actually reported evidence for this job
and records which specialist agents have something to say
(`required_agents`). The specialist agents still run unconditionally (they
just produce an empty finding list when their domain has no evidence), but
`required_agents` is threaded through to the Final Diagnosis Agent and the
LLM input so the reasoning trail is explicit about which domains were
actually in scope for a given job, matching the diagnostics engine's
`--probes` subset.
"""

from __future__ import annotations

from src.graph.state import AGENT_PROBE_MAP, GraphState


def run(state: GraphState) -> dict:
    evidence = state.get("evidence", [])
    probe_types_present = {ev.get("probe_type") for ev in evidence}

    required_agents = sorted(
        agent
        for agent, probe_types in AGENT_PROBE_MAP.items()
        if probe_types & probe_types_present
    )

    return {"required_agents": required_agents}
