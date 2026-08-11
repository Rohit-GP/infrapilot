"""
InfraPilot LangGraph workflow.

Current implementation:

    START
      |
      v
    Supervisor
      |
      +------> Network --------+
      |                        |
      +------> System ---------+----> Evidence ----> END
      |                        |
      +------> Application ----+

The specialist nodes run in parallel.
"""

from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from .state import DiagnosisState

from .nodes.supervisor_agent import (
    supervisor_agent,
)

from .nodes.network_agent import (
    network_agent,
)

from .nodes.system_agent import (
    system_agent,
)

from .nodes.application_agent import (
    application_agent,
)

from .nodes.evidence_agent import (
    evidence_agent,
)


def build_diagnosis_graph():

    builder = StateGraph(
        DiagnosisState
    )

    # ---------------------------------------------------------
    # Register nodes
    # ---------------------------------------------------------

    builder.add_node(
        "supervisor",
        supervisor_agent,
    )

    builder.add_node(
        "network",
        network_agent,
    )

    builder.add_node(
        "system",
        system_agent,
    )

    builder.add_node(
        "application",
        application_agent,
    )

    builder.add_node(
        "evidence",
        evidence_agent,
    )

    # ---------------------------------------------------------
    # START -> Supervisor
    # ---------------------------------------------------------

    builder.add_edge(
        START,
        "supervisor",
    )

    # ---------------------------------------------------------
    # Supervisor -> all specialist agents
    #
    # All three agents are run in parallel.
    # Each agent only processes evidence relevant to it.
    # ---------------------------------------------------------

    builder.add_edge(
        "supervisor",
        "network",
    )

    builder.add_edge(
        "supervisor",
        "system",
    )

    builder.add_edge(
        "supervisor",
        "application",
    )

    # ---------------------------------------------------------
    # Fan-in
    #
    # Evidence agent waits for all three specialist agents.
    # ---------------------------------------------------------

    builder.add_edge(
        [
            "network",
            "system",
            "application",
        ],
        "evidence",
    )

    # ---------------------------------------------------------
    # Evidence -> END
    # ---------------------------------------------------------

    builder.add_edge(
        "evidence",
        END,
    )

    return builder.compile()