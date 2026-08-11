"""
Application reasoning agent.

Handles:

    http
    ssl
    service

No LLM is used here.
"""

from __future__ import annotations

from typing import Any

from ..state import DiagnosisState


APPLICATION_PROBES = {
    "http",
    "ssl",
    "service",
}


def _severity_from_status(
    status: str,
) -> str:

    if status == "error":
        return "critical"

    if status == "failed":
        return "high"

    if status == "degraded":
        return "medium"

    return "low"


def _get_number(
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


def application_agent(
    state: DiagnosisState,
) -> dict[str, Any]:

    evidence = state.get("evidence", [])

    findings: list[dict[str, Any]] = []

    for item in evidence:

        probe_type = str(
            item.get("probe_type", "")
        ).lower()

        if probe_type not in APPLICATION_PROBES:
            continue

        status = str(
            item.get("status", "")
        ).lower()

        raw = item.get("raw") or {}

        if not isinstance(raw, dict):
            raw = {}

        target = item.get("target", "")
        message = item.get("message", "")
        error = item.get("error")
        latency = item.get("latency_ms")
        evidence_id = item.get("evidence_id")
        job_id = item.get("job_id")

        # -------------------------------------------------
        # HTTP
        # -------------------------------------------------

        if probe_type == "http":

            status_code = _get_number(
                raw,
                (
                    "status_code",
                    "http_status",
                    "response_status",
                ),
            )

            if status_code is not None:

                status_code_int = int(status_code)

                if status_code_int >= 500:

                    severity = "critical"

                    finding = (
                        f"Application returned server error "
                        f"HTTP {status_code_int}."
                    )

                elif status_code_int >= 400:

                    severity = "high"

                    finding = (
                        f"Application returned client error "
                        f"HTTP {status_code_int}."
                    )

                elif status_code_int >= 300:

                    severity = "medium"

                    finding = (
                        f"Application returned redirect "
                        f"HTTP {status_code_int}."
                    )

                else:

                    severity = (
                        "low"
                        if status == "ok"
                        else _severity_from_status(status)
                    )

                    finding = (
                        f"Application returned HTTP "
                        f"{status_code_int}."
                    )

            elif status == "failed":

                severity = "high"

                finding = (
                    "HTTP application probe failed."
                )

            elif status == "error":

                severity = "critical"

                finding = (
                    "HTTP application probe could not complete."
                )

            else:

                severity = "low"

                finding = (
                    "HTTP application endpoint is responding normally."
                )

            # Latency is additional evidence.
            if latency is not None:

                try:
                    latency_value = float(latency)

                    if latency_value >= 3000:

                        severity = max(
                            severity,
                            "high",
                            key=lambda x: {
                                "low": 0,
                                "medium": 1,
                                "high": 2,
                                "critical": 3,
                            }[x],
                        )

                        finding += (
                            f" Response latency is high "
                            f"at {latency_value:.1f} ms."
                        )

                    elif latency_value >= 1000:

                        if severity == "low":
                            severity = "medium"

                        finding += (
                            f" Response latency is elevated "
                            f"at {latency_value:.1f} ms."
                        )

                except (TypeError, ValueError):
                    pass

        # -------------------------------------------------
        # SSL
        # -------------------------------------------------

        elif probe_type == "ssl":

            days_remaining = _get_number(
                raw,
                (
                    "days_remaining",
                    "days_to_expiry",
                    "certificate_days_remaining",
                ),
            )

            if status in {"failed", "error"}:

                severity = (
                    "critical"
                    if status == "error"
                    else "high"
                )

                finding = (
                    "SSL/TLS certificate check failed."
                )

            elif days_remaining is not None:

                if days_remaining <= 7:

                    severity = "critical"

                    finding = (
                        f"SSL/TLS certificate expires in "
                        f"{days_remaining:.0f} days."
                    )

                elif days_remaining <= 30:

                    severity = "medium"

                    finding = (
                        f"SSL/TLS certificate expires in "
                        f"{days_remaining:.0f} days."
                    )

                else:

                    severity = "low"

                    finding = (
                        f"SSL/TLS certificate has "
                        f"{days_remaining:.0f} days remaining."
                    )

            else:

                severity = _severity_from_status(status)

                finding = (
                    "SSL/TLS certificate check completed."
                )

        # -------------------------------------------------
        # Service
        # -------------------------------------------------

        elif probe_type == "service":

            if status == "ok":

                severity = "low"

                finding = (
                    "Configured service health check succeeded."
                )

            elif status == "degraded":

                severity = "medium"

                finding = (
                    "Configured service health check is degraded."
                )

            elif status == "failed":

                severity = "high"

                finding = (
                    "Configured service health check failed."
                )

            else:

                severity = "critical"

                finding = (
                    "Configured service health check "
                    "could not complete."
                )

        else:
            continue

        findings.append(
            {
                "agent": "application",
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
        "application_findings": findings
    }