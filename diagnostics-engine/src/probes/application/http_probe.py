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


def run(config: ProbeConfig, job_id: str) -> Evidence:
    target = config.http_url or config.target

    if not config.http_url:
        return Evidence(
            probe_type=ProbeType.HTTP, target=target, status=ProbeStatus.DEGRADED,
            message="No http_url configured - probe skipped",
            job_id=job_id,
        )

    start = time.perf_counter()
    try:
        resp = requests.get(config.http_url, timeout=config.http_timeout_s)
        latency_ms = (time.perf_counter() - start) * 1000
        raw = {"status_code": resp.status_code, "response_bytes": len(resp.content)}

        if resp.status_code != config.http_expect_status:
            return Evidence(
                probe_type=ProbeType.HTTP, target=target, status=ProbeStatus.FAILED,
                latency_ms=latency_ms, raw=raw, job_id=job_id,
                message=f"Expected status {config.http_expect_status}, got {resp.status_code}",
            )

        if config.http_expect_text and config.http_expect_text not in resp.text:
            return Evidence(
                probe_type=ProbeType.HTTP, target=target, status=ProbeStatus.FAILED,
                latency_ms=latency_ms, raw=raw, job_id=job_id,
                message=f"Expected text '{config.http_expect_text}' not found in response body",
            )

        if latency_ms >= config.http_crit_latency_ms:
            status = ProbeStatus.FAILED
            message = f"Response time {latency_ms:.0f}ms exceeds critical threshold {config.http_crit_latency_ms}ms"
        elif latency_ms >= config.http_warn_latency_ms:
            status = ProbeStatus.DEGRADED
            message = f"Response time {latency_ms:.0f}ms exceeds warning threshold {config.http_warn_latency_ms}ms"
        else:
            status = ProbeStatus.OK
            message = "Endpoint healthy"

        return Evidence(
            probe_type=ProbeType.HTTP, target=target, status=status,
            latency_ms=latency_ms, raw=raw, message=message, job_id=job_id,
        )

    except requests.exceptions.Timeout as exc:
        return Evidence.error_result(ProbeType.HTTP, target, exc, job_id=job_id)
    except requests.exceptions.ConnectionError as exc:
        return Evidence.error_result(ProbeType.HTTP, target, exc, job_id=job_id)
    except Exception as exc:  # noqa: BLE001
        return Evidence.error_result(ProbeType.HTTP, target, exc, job_id=job_id)
