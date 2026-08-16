"""
HTTP Health Probe (Application layer).

Checks config.http_url for reachability, expected status code, expected
body text, and response latency. Skipped (returns DEGRADED, not ERROR)
if http_url isn't set - same "not configured" convention service_probe.py
uses for service_check_url/log_path. ERROR is reserved for the probe
itself failing to complete (timeout, connection error, etc.), so an
unconfigured probe shouldn't count as a failure for exit-code purposes.
"""

from __future__ import annotations

import time

import requests

from src.core.config import ProbeConfig
from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.confidence import calculate_confidence    


def run(config: ProbeConfig, job_id: str) -> Evidence:
    target = config.http_url or f"https://{config.target}"

    start = time.perf_counter()

    try:
        resp = requests.get(
            target,
            timeout=config.http_timeout_s
        )

        latency_ms = (time.perf_counter() - start) * 1000

        raw = {
            "status_code": resp.status_code,
            "response_bytes": len(resp.content),
        }

        # Expected status
        if resp.status_code != config.http_expect_status:
            confidence = calculate_confidence(
                status=ProbeStatus.FAILED,
                latency_ms=latency_ms
            )

            return Evidence(
                probe_type=ProbeType.HTTP,
                target=target,
                status=ProbeStatus.FAILED,
                latency_ms=latency_ms,
                raw=raw,
                job_id=job_id,
                confidence=confidence,
                message=(
                    f"Expected status {config.http_expect_status}, "
                    f"got {resp.status_code}"
                ),
            )

        # Expected body text
        if (
            config.http_expect_text
            and config.http_expect_text not in resp.text
        ):
            confidence = calculate_confidence(
                status=ProbeStatus.FAILED,
                latency_ms=latency_ms
            )

            return Evidence(
                probe_type=ProbeType.HTTP,
                target=target,
                status=ProbeStatus.FAILED,
                latency_ms=latency_ms,
                raw=raw,
                job_id=job_id,
                confidence=confidence,
                message=(
                    f"Expected text '{config.http_expect_text}' "
                    "not found in response body"
                ),
            )

        # Latency
        if latency_ms >= config.http_crit_latency_ms:
            status = ProbeStatus.FAILED
            message = (
                f"Response time {latency_ms:.0f}ms exceeds "
                f"critical threshold {config.http_crit_latency_ms}ms"
            )

        elif latency_ms >= config.http_warn_latency_ms:
            status = ProbeStatus.DEGRADED
            message = (
                f"Response time {latency_ms:.0f}ms exceeds "
                f"warning threshold {config.http_warn_latency_ms}ms"
            )

        else:
            status = ProbeStatus.OK
            message = "Endpoint healthy"

        confidence = calculate_confidence(
            status=status,
            latency_ms=latency_ms
        )

        return Evidence(
            probe_type=ProbeType.HTTP,
            target=target,
            status=status,
            latency_ms=latency_ms,
            raw=raw,
            message=message,
            confidence=confidence,
            job_id=job_id,
        )

    except requests.exceptions.Timeout as exc:
        confidence = calculate_confidence(
            status=ProbeStatus.ERROR
        )
        return Evidence.error_result(
            ProbeType.HTTP,
            target,
            exc,
            confidence=confidence,
            job_id=job_id,
        )

    except requests.exceptions.ConnectionError as exc:
        confidence = calculate_confidence(
            status=ProbeStatus.ERROR
        )
        return Evidence.error_result(
            ProbeType.HTTP,
            target,
            exc,
            confidence=confidence,
            job_id=job_id,
        )

    except Exception as exc:
        confidence = calculate_confidence(
            status=ProbeStatus.ERROR
        )
        return Evidence.error_result(
            ProbeType.HTTP,
            target,
            exc,
            confidence=confidence,
            job_id=job_id,
        )
