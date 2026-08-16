"""
InfraPilot LangGraph workflow.

<<<<<<< HEAD
Flow:
=======
Current implementation:
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904

    START
      |
      v
    Supervisor
      |
      +------> Network --------+
      |                        |
<<<<<<< HEAD
      +------> System ---------+----> Evidence ----> Final Diagnosis
      |                        |                         |
      +------> Application ----+                         v
                                                         END
=======
      +------> System ---------+----> Evidence ----> END
      |                        |
      +------> Application ----+
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904

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

<<<<<<< HEAD
from .nodes.final_diagnosis_agent import (
    final_diagnosis_agent,
)

=======
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904

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

<<<<<<< HEAD
    builder.add_node(
        "final_diagnosis",
        final_diagnosis_agent,
    )

=======
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904
    # ---------------------------------------------------------
    # START -> Supervisor
    # ---------------------------------------------------------

    builder.add_edge(
        START,
        "supervisor",
    )

    # ---------------------------------------------------------
<<<<<<< HEAD
    # Supervisor -> Specialist Agents
=======
    # Supervisor -> all specialist agents
    #
    # All three agents are run in parallel.
    # Each agent only processes evidence relevant to it.
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904
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
<<<<<<< HEAD
    # Specialist Agents -> Evidence Validation
=======
    # Fan-in
    #
    # Evidence agent waits for all three specialist agents.
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904
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
<<<<<<< HEAD
    # Evidence Validation -> Final Diagnosis
=======
    # Evidence -> END
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904
    # ---------------------------------------------------------

    builder.add_edge(
        "evidence",
<<<<<<< HEAD
        "final_diagnosis",
    )

    # ---------------------------------------------------------
    # Final Diagnosis -> END
    # ---------------------------------------------------------

    builder.add_edge(
        "final_diagnosis",
=======
>>>>>>> 3abd7385429267f861b24ad5986b496c491b3904
        END,
    )

    return builder.compile()