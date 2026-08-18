"""
Shared logic for the domain specialist agents (Network / System / Application).

Each specialist agent does the same kind of work - pick the evidence that
belongs to its domain and turn it into a structured finding - so the shape
of a "finding" is defined once here rather than three times.

A finding is the standardized, LLM-ready unit the rest of the pipeline
passes around:

    {
        "agent": "network" | "system" | "application",
        "probe": "<probe_type>",
        "status": "<ok|degraded|failed|error>",
        "severity": "<low|medium|high|critical>",
        "finding": "<human-readable description>",
        "confidence": <0-100>,
        "evidence_id": "<uuid of the source Evidence>",
    }
"""

from __future__ import annotations

from typing import Any

from src.graph.state import severity_for_status


def build_findings(agent_name: str, probe_types: set[str], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    for ev in evidence:
        if ev.get("probe_type") not in probe_types:
            continue

        status = ev.get("status", "error")
        findings.append(
            {
                "agent": agent_name,
                "probe": ev.get("probe_type"),
                "status": status,
                "severity": severity_for_status(status),
                "finding": ev.get("message") or f"{ev.get('probe_type')} probe returned no message.",
                "confidence": ev.get("confidence", 0),
                "evidence_id": ev.get("evidence_id"),
            }
        )

    # Deterministic ordering makes downstream ranking/printing reproducible.
    findings.sort(key=lambda f: f["probe"] or "")
    return findings
