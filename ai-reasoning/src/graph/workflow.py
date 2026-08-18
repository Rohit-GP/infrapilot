"""
LangGraph workflow for the AI Reasoning Layer.

    supervisor_agent
          │
          ├── network_agent ──┐
          ├── system_agent ───┼── evidence_agent ── final_diagnosis_agent
          └── application_agent ┘

The three specialist agents run as independent parallel branches (each one
only writes its own key in GraphState), then fan back in to the Evidence
Agent, which needs all three before it can validate anything.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.graph.nodes import (
    application_agent,
    evidence_agent,
    final_diagnosis_agent,
    network_agent,
    supervisor_agent,
    system_agent,
)
from src.graph.state import GraphState


def build_workflow():
    graph = StateGraph(GraphState)

    graph.add_node("supervisor_agent", supervisor_agent.run)
    graph.add_node("network_agent", network_agent.run)
    graph.add_node("system_agent", system_agent.run)
    graph.add_node("application_agent", application_agent.run)
    graph.add_node("evidence_agent", evidence_agent.run)
    graph.add_node("final_diagnosis_agent", final_diagnosis_agent.run)

    graph.add_edge(START, "supervisor_agent")

    # Fan out: the three specialists run in parallel off the supervisor.
    graph.add_edge("supervisor_agent", "network_agent")
    graph.add_edge("supervisor_agent", "system_agent")
    graph.add_edge("supervisor_agent", "application_agent")

    # Fan in: evidence_agent waits for all three specialist branches.
    graph.add_edge("network_agent", "evidence_agent")
    graph.add_edge("system_agent", "evidence_agent")
    graph.add_edge("application_agent", "evidence_agent")

    graph.add_edge("evidence_agent", "final_diagnosis_agent")
    graph.add_edge("final_diagnosis_agent", END)

    return graph.compile()


# Compiled once at import time - cheap to build and the graph shape is static.
workflow = build_workflow()


def run_workflow(job_id: str, target: str, evidence: list[dict]) -> GraphState:
    """Convenience entry point: run the full reasoning pipeline for one
    completed diagnostics job and return the final graph state."""
    initial_state: GraphState = {
        "job_id": job_id,
        "target": target,
        "evidence": evidence,
    }
    return workflow.invoke(initial_state)
