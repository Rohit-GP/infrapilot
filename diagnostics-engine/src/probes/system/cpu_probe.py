"""
CPU Probe (System layer).

Reads CPU utilization of the host this probe executes on — same caveat
as the design doc's note on DB/infra evidence: for a remote target you
need an agent/exporter on that host, or run this over SSH. As-is, it
reports on wherever the diagnostics engine process itself is running.
"""

from __future__ import annotations

import time

import psutil

from src.core.config import ProbeConfig
from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.confidence import calculate_confidence

SAMPLE_INTERVAL_S = 1.0


def run(config: ProbeConfig, job_id: str) -> Evidence:
    start = time.perf_counter()

    try:
        overall_pct = psutil.cpu_percent(interval=SAMPLE_INTERVAL_S)
        per_core = psutil.cpu_percent(interval=None, percpu=True)

        try:
            load1, load5, load15 = psutil.getloadavg()
        except (AttributeError, OSError):
            load1 = load5 = load15 = None

        latency_ms = (time.perf_counter() - start) * 1000

        raw = {
            "cpu_percent_overall": overall_pct,
            "cpu_percent_per_core": per_core,
            "core_count": psutil.cpu_count(logical=True),
            "load_avg_1m": load1,
            "load_avg_5m": load5,
            "load_avg_15m": load15,
        }

        if overall_pct >= config.cpu_crit_pct:
            status = ProbeStatus.FAILED
            message = (
                f"CPU usage {overall_pct:.1f}% >= critical threshold "
                f"{config.cpu_crit_pct}%"
            )

        elif overall_pct >= config.cpu_warn_pct:
            status = ProbeStatus.DEGRADED
            message = (
                f"CPU usage {overall_pct:.1f}% >= warning threshold "
                f"{config.cpu_warn_pct}%"
            )

        else:
            status = ProbeStatus.OK
            message = f"CPU usage normal ({overall_pct:.1f}%)"

        confidence = calculate_confidence(
            status=status,
        )

        return Evidence(
            probe_type=ProbeType.CPU,
            target=config.target,
            status=status,
            latency_ms=latency_ms,
            raw=raw,
            message=message,
            confidence=confidence,
            job_id=job_id,
        )

    except Exception as exc:  # noqa: BLE001

        confidence = calculate_confidence(
            status=ProbeStatus.ERROR
        )

        return Evidence.error_result(
            ProbeType.CPU,
            config.target,
            exc,
            confidence=confidence,
            job_id=job_id,
        )