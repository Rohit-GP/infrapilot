"""
Service / log-level probe.

Two independent checks, either or both may run depending on config:
1. HTTP health check (config.service_check_url) - is the app-level service
   actually answering, not just the port.
2. Log scan (config.log_path) - tail the last N lines of a local log file
   and flag common error/crash signatures.

This is intentionally the least "socket-y" probe of the four - it's the
one Section 9 of the design doc flags as needing to be extended with real
DB/infra checks later. For now it demonstrates the pattern with an HTTP
check + a log grep.
"""

from __future__ import annotations

import time
import urllib.request
import urllib.error

from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.config import ProbeConfig

ERROR_PATTERNS = ("ERROR", "FATAL", "Exception", "Traceback", "panic:", "OOM", "refused")


def _http_health_check(url: str, timeout_s: float) -> dict:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return {"reachable": True, "status_code": resp.status, "latency_ms": round(elapsed_ms, 2)}
    except urllib.error.HTTPError as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"reachable": True, "status_code": e.code, "latency_ms": round(elapsed_ms, 2)}
    except Exception as e:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"reachable": False, "status_code": None, "latency_ms": round(elapsed_ms, 2), "error": str(e)}


def _scan_log(path: str, tail_lines: int = 200) -> dict:
    try:
        with open(path, "r", errors="ignore") as f:
            lines = f.readlines()[-tail_lines:]
        hits = [ln.strip() for ln in lines if any(p in ln for p in ERROR_PATTERNS)]
        return {"scanned_lines": len(lines), "error_lines_found": len(hits), "sample": hits[:5]}
    except FileNotFoundError as e:
        return {"error": str(e)}


def run(config: ProbeConfig, job_id: str | None = None) -> Evidence:
    target = config.target
    raw: dict = {}
    problems = []

    try:
        if config.service_check_url:
            http_result = _http_health_check(config.service_check_url, config.port_timeout_s)
            raw["http_health"] = http_result
            if not http_result["reachable"] or (http_result.get("status_code") or 0) >= 500:
                problems.append("service HTTP health check failing")

        if config.log_path:
            log_result = _scan_log(config.log_path)
            raw["log_scan"] = log_result
            if log_result.get("error_lines_found", 0) > 0:
                problems.append(f"{log_result['error_lines_found']} error-pattern lines in log")

        if not config.service_check_url and not config.log_path:
            return Evidence(
                probe_type=ProbeType.SERVICE,
                target=target,
                status=ProbeStatus.DEGRADED,
                message="No service_check_url or log_path configured - probe skipped",
                job_id=job_id,
            )

        status = ProbeStatus.FAILED if problems else ProbeStatus.OK
        message = "; ".join(problems) if problems else "Service/log checks passed"

        return Evidence(
            probe_type=ProbeType.SERVICE,
            target=target,
            status=status,
            message=message,
            raw=raw,
            job_id=job_id,
        )

    except Exception as exc:  # noqa: BLE001
        return Evidence.error_result(ProbeType.SERVICE, target, exc, job_id=job_id)
