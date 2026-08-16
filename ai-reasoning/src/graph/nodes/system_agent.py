"""
System reasoning agent.

Handles:

    cpu
    memory
    disk

No LLM is used here.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


SYSTEM_PROBES = {
    "cpu",
    "memory",
    "disk",
}


def _get_percentage(
    raw: dict[str, Any],
    names: tuple[str, ...],
) -> float | None:

    for name in names:

        value = raw.get(name)

        if value is None:
            continue

        try:
            return float(value)
        except (TypeError, ValueError):
            continue

    return None


def system_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    evidence = state.get("evidence", [])

    findings: list[dict[str, Any]] = []

    for item in evidence:

        probe_type = str(
            item.get("probe_type", "")
        ).lower()

        if probe_type not in SYSTEM_PROBES:
            continue

        status = str(
            item.get("status", "")
        ).lower()

        raw = item.get("raw") or {}

        if not isinstance(raw, dict):
            raw = {}

        target = item.get("target", "")
        evidence_id = item.get("evidence_id")
        job_id = item.get("job_id")

        # -------------------------------------------------
        # CPU
        # -------------------------------------------------

        if probe_type == "cpu":

            usage = _get_percentage(
                raw,
                (
                    "cpu_percent_overall",
                    "usage_percent",
                    "cpu_percent",
                    "percent",
                    "usage",
                ),
            )

            if usage is not None:

                if usage >= 90:
                    severity = "critical"
                    finding = (
                        f"CPU utilization is critically high "
                        f"at {usage:.1f}%."
                    )

                elif usage >= 75:
                    severity = "medium"
                    finding = (
                        f"CPU utilization is elevated "
                        f"at {usage:.1f}%."
                    )

                else:
                    severity = "low"
                    finding = (
                        f"CPU utilization is {usage:.1f}%."
                    )

            else:

                severity = (
                    "high"
                    if status in {"failed", "error"}
                    else "low"
                )

                finding = (
                    "CPU probe completed but no utilization "
                    "percentage was available."
                )

        # -------------------------------------------------
        # Memory
        # -------------------------------------------------

        elif probe_type == "memory":

            usage = _get_percentage(
                raw,
                (     
                    "used_percent",
                    "usage_percent",
                    "memory_percent",
                    "percent",
                    "usage",
                ),
            )

            if usage is not None:

                if usage >= 95:
                    severity = "critical"
                    finding = (
                        f"Memory utilization is critically high "
                        f"at {usage:.1f}%."
                    )

                elif usage >= 80:
                    severity = "medium"
                    finding = (
                        f"Memory utilization is elevated "
                        f"at {usage:.1f}%."
                    )

                else:
                    severity = "low"
                    finding = (
                        f"Memory utilization is {usage:.1f}%."
                    )

            else:

                severity = (
                    "high"
                    if status in {"failed", "error"}
                    else "low"
                )

                finding = (
                    "Memory probe completed but no utilization "
                    "percentage was available."
                )

        # -------------------------------------------------
        # Disk
        # -------------------------------------------------

        elif probe_type == "disk":

            usage = _get_percentage(
                raw,
                (
                    "worst_used_percent",
                    "used_percent",
                    "usage_percent",
                    "disk_percent",
                    "percent",
                    "usage",
                ),
            )

            if usage is not None:

                if usage >= 90:
                    severity = "critical"
                    finding = (
                        f"Disk utilization is critically high "
                        f"at {usage:.1f}%."
                    )

                elif usage >= 80:
                    severity = "medium"
                    finding = (
                        f"Disk utilization is elevated "
                        f"at {usage:.1f}%."
                    )

                else:
                    severity = "low"
                    finding = (
                        f"Disk utilization is {usage:.1f}%."
                    )

            else:

                severity = (
                    "high"
                    if status in {"failed", "error"}
                    else "low"
                )

                finding = (
                    "Disk probe completed but no utilization "
                    "percentage was available."
                )

        else:
            continue

        findings.append(
            {
                "agent": "system",
                "probe_type": probe_type,
                "target": target,
                "status": status,
                "severity": severity,
                "finding": finding,
                "evidence_id": evidence_id,
                "job_id": job_id,
                "evidence": item,
            }
        )

    return {
        "system_findings": findings
    }