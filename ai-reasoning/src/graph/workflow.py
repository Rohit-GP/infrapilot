"""
InfraPilot LangGraph workflow.

Flow:

    START
      |
      v
    Supervisor
      |
      +------> Network --------+
      |                        |
      +------> System ---------+----> Evidence ----> Final Diagnosis
      |                        |                         |
      +------> Application ----+                         v
                                                         END

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

from .nodes.final_diagnosis_agent import (
    final_diagnosis_agent,
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

    builder.add_node(
        "final_diagnosis",
        final_diagnosis_agent,
    )

    # ---------------------------------------------------------
    # START -> Supervisor
    # ---------------------------------------------------------

    builder.add_edge(
        START,
        "supervisor",
    )

    # ---------------------------------------------------------
    # Supervisor -> Specialist Agents
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
    # Specialist Agents -> Evidence Validation
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
    # Evidence Validation -> Final Diagnosis
    # ---------------------------------------------------------

    builder.add_edge(
        "evidence",
        "final_diagnosis",
    )

    # ---------------------------------------------------------
    # Final Diagnosis -> END
    # ---------------------------------------------------------

    builder.add_edge(
        "final_diagnosis",
        END,
    )

    return builder.compile()