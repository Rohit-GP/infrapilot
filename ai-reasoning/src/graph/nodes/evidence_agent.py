"""
Evidence validation agent.

Validates findings produced by the specialist agents against
the original Evidence objects.

This agent does not determine the final diagnosis.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


def evidence_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    network = state.get(
        "network_findings",
        [],
    )

    system = state.get(
        "system_findings",
        [],
    )

    application = state.get(
        "application_findings",
        [],
    )

    all_findings = (
        network
        + system
        + application
    )

    # ---------------------------------------------------------
    # Index original evidence by evidence_id
    # ---------------------------------------------------------

    evidence_by_id = {
        item.get("evidence_id"): item
        for item in state.get("evidence", [])
        if item.get("evidence_id")
    }

    validated: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Validate every specialist finding
    # ---------------------------------------------------------

    for finding in all_findings:

        evidence_id = finding.get(
            "evidence_id"
        )

        if not evidence_id:
            continue

        if evidence_id not in evidence_by_id:
            continue

        original_evidence = evidence_by_id[
            evidence_id
        ]

        validated.append(
            {
                **finding,
                "validated": True,
                "source_evidence": original_evidence,
            }
        )

    # ---------------------------------------------------------
    # Return validated findings only
    # ---------------------------------------------------------

    return {
        "validated_findings": validated
    }