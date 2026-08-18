"""
Evidence Agent.

Validates the specialist agents' findings against the underlying
diagnostic evidence and ensures every finding remains connected to the
evidence that produced it. Concretely this means:

* every finding must reference a real `evidence_id` from this job's raw
  evidence (guards against a specialist agent hallucinating or
  mis-attributing a finding),
* the finding's status/severity must still agree with the evidence it
  points to (guards against stale/inconsistent state),
* duplicate findings for the same evidence_id are collapsed.

Findings that fail validation are dropped rather than passed downstream -
the Final Diagnosis Agent only ever sees findings that are provably backed
by evidence.
"""

from __future__ import annotations

from typing import Any

from src.graph.state import GraphState, severity_for_status


def _collect_candidate_findings(state: GraphState) -> list[dict[str, Any]]:
    return [
        *state.get("network_findings", []),
        *state.get("system_findings", []),
        *state.get("application_findings", []),
    ]


def run(state: GraphState) -> dict:
    evidence_by_id = {ev.get("evidence_id"): ev for ev in state.get("evidence", [])}

    validated: list[dict[str, Any]] = []
    seen_evidence_ids: set[str] = set()

    for finding in _collect_candidate_findings(state):
        evidence_id = finding.get("evidence_id")
        source = evidence_by_id.get(evidence_id)

        if source is None:
            # No matching evidence for this job - can't validate, so drop it.
            continue

        if evidence_id in seen_evidence_ids:
            # Same piece of evidence already validated (shouldn't normally
            # happen since each specialist owns disjoint probe types, but
            # guards against a routing bug producing duplicates).
            continue

        # Re-derive status/severity from the source evidence rather than
        # trusting the specialist's copy, so a stale finding can't slip
        # through with a mismatched severity.
        status = source.get("status", finding.get("status", "error"))
        validated.append(
            {
                **finding,
                "status": status,
                "severity": severity_for_status(status),
                "confidence": source.get("confidence", finding.get("confidence", 0)),
            }
        )
        seen_evidence_ids.add(evidence_id)

    return {"validated_findings": validated}
