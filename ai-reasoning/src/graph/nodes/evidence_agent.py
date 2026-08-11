"""
Evidence validation and final diagnosis agent.

This is the final reasoning stage before the result is returned.

No LLM is used yet. The implementation is deterministic and
evidence-backed so that an LLM can later be added on top of it.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


SEVERITY_SCORE = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def _score(finding: dict[str, Any]) -> int:

    severity = str(
        finding.get("severity", "low")
    ).lower()

    return SEVERITY_SCORE.get(
        severity,
        0,
    )


def _recommendation(
    finding: dict[str, Any],
) -> str | None:

    probe = finding.get("probe_type")
    severity = finding.get("severity")

    if severity not in {
        "critical",
        "high",
    }:
        return None

    recommendations = {

        "ping": (
            "Investigate host reachability, routing, "
            "firewall rules, and packet loss."
        ),

        "dns": (
            "Investigate DNS resolution, DNS server "
            "availability, records, and resolver configuration."
        ),

        "port": (
            "Investigate firewall rules, listening services, "
            "network ACLs, and TCP connectivity."
        ),

        "http": (
            "Inspect application health, server errors, "
            "upstream dependencies, and HTTP response latency."
        ),

        "ssl": (
            "Inspect the TLS certificate, certificate chain, "
            "expiry date, and server TLS configuration."
        ),

        "service": (
            "Inspect the service health, process state, "
            "dependencies, and recent service logs."
        ),

        "cpu": (
            "Identify CPU-intensive processes and investigate "
            "unexpected workload or resource saturation."
        ),

        "memory": (
            "Inspect memory-consuming processes, memory pressure, "
            "and possible memory leaks."
        ),

        "disk": (
            "Free disk capacity and investigate processes or "
            "logs consuming excessive storage."
        ),
    }

    return recommendations.get(probe)


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

    validated: list[dict[str, Any]] = []

    # ---------------------------------------------------------
    # Validate every finding against an actual Evidence object
    # ---------------------------------------------------------

    evidence_by_id = {
        item.get("evidence_id"): item
        for item in state.get("evidence", [])
        if item.get("evidence_id")
    }

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
    # No evidence
    # ---------------------------------------------------------

    if not validated:

        return {
            "validated_findings": [],
            "root_cause": (
                "Insufficient evidence to determine a root cause."
            ),
            "confidence": 0.0,
            "recommendations": [
                "Run diagnostics and collect additional evidence."
            ],
        }

    # ---------------------------------------------------------
    # Sort by severity
    # ---------------------------------------------------------

    validated.sort(
        key=_score,
        reverse=True,
    )

    strongest = validated[0]

    strongest_score = _score(
        strongest
    )

    # ---------------------------------------------------------
    # Count supporting findings
    # ---------------------------------------------------------

    high_or_critical = [
        finding
        for finding in validated
        if _score(finding) >= 2
    ]

    # ---------------------------------------------------------
    # Determine confidence
    # ---------------------------------------------------------

    if strongest_score == 3:

        confidence = 0.80

    elif strongest_score == 2:

        confidence = 0.65

    elif strongest_score == 1:

        confidence = 0.45

    else:

        confidence = 0.30

    # Multiple independent findings increase confidence.
    confidence += min(
        len(high_or_critical) * 0.05,
        0.15,
    )

    confidence = min(
        confidence,
        0.95,
    )

    # ---------------------------------------------------------
    # Root cause
    # ---------------------------------------------------------

    root_cause = strongest.get(
        "finding",
        "Infrastructure issue detected.",
    )

    # ---------------------------------------------------------
    # Recommendations
    # ---------------------------------------------------------

    recommendations: list[str] = []

    seen_recommendations: set[str] = set()

    for finding in validated:

        recommendation = _recommendation(
            finding
        )

        if (
            recommendation
            and recommendation
            not in seen_recommendations
        ):

            recommendations.append(
                recommendation
            )

            seen_recommendations.add(
                recommendation
            )

    if not recommendations:

        recommendations.append(
            "Continue monitoring the target and collect "
            "additional evidence if the problem persists."
        )

    return {
        "validated_findings": validated,
        "root_cause": root_cause,
        "confidence": round(
            confidence,
            2,
        ),
        "recommendations": recommendations,
    }