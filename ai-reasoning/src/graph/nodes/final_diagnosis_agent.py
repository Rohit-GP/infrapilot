"""
Final diagnosis agent.

Consumes validated specialist findings and produces the final
root cause, diagnosis confidence, and recommendations.

No LLM is used yet. The implementation is deterministic and
evidence-backed so that an LLM can later be added.
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
    severity = str(
        finding.get("severity", "")
    ).lower()

    if severity not in {"critical", "high"}:
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


def _evidence_confidence(
    finding: dict[str, Any],
) -> float:

    """
    Convert diagnostics-engine evidence confidence
    from 0-100 into 0.0-1.0.
    """

    value = finding.get("evidence", {}).get(
        "confidence"
    )

    if value is None:
        value = finding.get("confidence")

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.5

    # Support both 0-100 and 0.0-1.0 formats.
    if value > 1:
        value /= 100.0

    return max(
        0.0,
        min(value, 1.0),
    )


def final_diagnosis_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    validated = list(
        state.get(
            "validated_findings",
            [],
        )
    )

    # ---------------------------------------------------------
    # No validated evidence
    # ---------------------------------------------------------

    if not validated:

        return {
            "root_cause": (
                "Insufficient evidence to determine a root cause."
            ),
            "confidence": 0.0,
            "recommendations": [
                "Run diagnostics and collect additional evidence."
            ],
        }

    # ---------------------------------------------------------
    # Separate healthy findings from actual problems.
    #
    # Healthy findings are useful evidence, but should NOT
    # become the root cause.
    # ---------------------------------------------------------

    problematic_findings = [
        finding
        for finding in validated
        if _score(finding) > 0
    ]

    # ---------------------------------------------------------
    # No problem detected
    # ---------------------------------------------------------

    if not problematic_findings:

        evidence_confidences = [
            _evidence_confidence(finding)
            for finding in validated
        ]

        average_confidence = (
            sum(evidence_confidences)
            / len(evidence_confidences)
        )

        # Healthy evidence from multiple probes increases
        # confidence that no significant fault was detected.
        coverage_bonus = min(
            len(validated) * 0.02,
            0.10,
        )

        confidence = min(
            average_confidence + coverage_bonus,
            0.95,
        )

        return {
            "root_cause": (
                "No significant infrastructure fault detected."
            ),
            "confidence": round(
                confidence,
                2,
            ),
            "recommendations": [
                "Continue monitoring the target and collect "
                "additional evidence if the problem persists."
            ],
        }

    # ---------------------------------------------------------
    # Rank actual problems by severity first, then evidence
    # confidence.
    # ---------------------------------------------------------

    problematic_findings.sort(
        key=lambda finding: (
            _score(finding),
            _evidence_confidence(finding),
        ),
        reverse=True,
    )

    strongest = problematic_findings[0]

    strongest_score = _score(
        strongest
    )

    strongest_evidence_confidence = (
        _evidence_confidence(strongest)
    )

    # ---------------------------------------------------------
    # Base diagnosis confidence from severity.
    # ---------------------------------------------------------

    if strongest_score == 3:
        base_confidence = 0.80

    elif strongest_score == 2:
        base_confidence = 0.65

    else:
        base_confidence = 0.45

    # ---------------------------------------------------------
    # Adjust using the confidence of the actual evidence.
    # ---------------------------------------------------------

    confidence = (
        base_confidence
        * strongest_evidence_confidence
    )

    # ---------------------------------------------------------
    # Multiple independent problematic findings provide
    # additional support.
    # ---------------------------------------------------------

    supporting_findings = [
        finding
        for finding in problematic_findings
        if finding.get("probe_type")
        != strongest.get("probe_type")
    ]

    confidence += min(
        len(supporting_findings) * 0.05,
        0.15,
    )

    confidence = min(
        confidence,
        0.95,
    )

    # ---------------------------------------------------------
    # Determine root cause.
    # ---------------------------------------------------------

    root_cause = strongest.get(
        "finding",
        "Infrastructure issue detected.",
    )

    # ---------------------------------------------------------
    # Generate recommendations.
    # ---------------------------------------------------------

    recommendations: list[str] = []

    seen: set[str] = set()

    for finding in problematic_findings:

        recommendation = _recommendation(
            finding
        )

        if (
            recommendation
            and recommendation not in seen
        ):

            recommendations.append(
                recommendation
            )

            seen.add(
                recommendation
            )

    if not recommendations:

        recommendations.append(
            "Continue monitoring the target and collect "
            "additional evidence if the problem persists."
        )

    return {
        "root_cause": root_cause,
        "confidence": round(
            confidence,
            2,
        ),
        "recommendations": recommendations,
    }