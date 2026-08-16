"""
Network reasoning agent.

Handles the network-layer probes produced by diagnostics-engine:

    ping
    dns
    port

No LLM is used here.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


NETWORK_PROBES = {
    "ping",
    "dns",
    "port",
}


def _severity(status: str) -> str:
    if status == "error":
        return "critical"

    if status == "failed":
        return "high"

    if status == "degraded":
        return "medium"

    return "low"


def network_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    evidence = state.get("evidence", [])

    findings: list[dict[str, Any]] = []

    for item in evidence:

        probe_type = str(
            item.get("probe_type", "")
        ).lower()

        if probe_type not in NETWORK_PROBES:
            continue

        status = str(
            item.get("status", "")
        ).lower()

        target = item.get("target", "")
        message = item.get("message", "")
        error = item.get("error")
        latency = item.get("latency_ms")
        evidence_id = item.get("evidence_id")
        job_id = item.get("job_id")

        severity = _severity(status)

        # -------------------------------------------------
        # Ping
        # -------------------------------------------------

        if probe_type == "ping":

            if status == "ok":
                finding = "Host is reachable using ICMP ping."

            elif status == "degraded":
                finding = (
                    "Host is reachable, but ping indicates "
                    "degraded network performance."
                )

            elif status == "failed":
                finding = (
                    "Host did not respond successfully to ICMP ping."
                )

            else:
                finding = (
                    "Ping probe could not complete."
                )

        # -------------------------------------------------
        # DNS
        # -------------------------------------------------

        elif probe_type == "dns":

            if status == "ok":
                finding = (
                    "DNS resolution completed successfully."
                )

            elif status == "degraded":
                finding = (
                    "DNS resolution completed with degraded results."
                )

            elif status == "failed":
                finding = (
                    "DNS resolution failed."
                )

            else:
                finding = (
                    "DNS probe could not complete."
                )

        # -------------------------------------------------
        # TCP port
        # -------------------------------------------------

        elif probe_type == "port":

            if status == "ok":
                finding = (
                    "TCP port is reachable."
                )

            elif status == "degraded":
                finding = (
                    "TCP port is reachable but performance "
                    "or availability is degraded."
                )

            elif status == "failed":
                finding = (
                    "TCP port is not reachable."
                )

            else:
                finding = (
                    "TCP port probe could not complete."
                )

        else:
            continue

        findings.append(
            {
                "agent": "network",
                "probe_type": probe_type,
                "target": target,
                "status": status,
                "severity": severity,
                "finding": finding,
                "message": message,
                "error": error,
                "latency_ms": latency,
                "evidence_id": evidence_id,
                "job_id": job_id,
                "evidence": item,
            }
        )

    return {
        "network_findings": findings
    }