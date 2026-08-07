"""
Memory Probe (System layer).

Reads virtual memory and swap usage of the host this probe executes on.
Same remote-target caveat as cpu_probe.py.
"""

from __future__ import annotations

import time

import psutil

from src.core.config import ProbeConfig
from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.confidence import calculate_confidence


def run(config: ProbeConfig, job_id: str) -> Evidence:
    start = time.perf_counter()

    try:
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()
        latency_ms = (time.perf_counter() - start) * 1000

        raw = {
            "total_mb": round(vm.total / (1024 ** 2), 1),
            "used_mb": round(vm.used / (1024 ** 2), 1),
            "available_mb": round(vm.available / (1024 ** 2), 1),
            "used_percent": vm.percent,
            "swap_total_mb": round(swap.total / (1024 ** 2), 1),
            "swap_used_mb": round(swap.used / (1024 ** 2), 1),
            "swap_percent": swap.percent,
        }

        if vm.percent >= config.memory_crit_pct:
            status = ProbeStatus.FAILED
            message = (
                f"Memory usage {vm.percent:.1f}% >= "
                f"critical threshold {config.memory_crit_pct}%"
            )

        elif vm.percent >= config.memory_warn_pct:
            status = ProbeStatus.DEGRADED
            message = (
                f"Memory usage {vm.percent:.1f}% >= "
                f"warning threshold {config.memory_warn_pct}%"
            )

        else:
            status = ProbeStatus.OK
            message = f"Memory usage normal ({vm.percent:.1f}%)"

        confidence = calculate_confidence(
            status=status,
        )

        return Evidence(
            probe_type=ProbeType.MEMORY,
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
            ProbeType.MEMORY,
            config.target,
            exc,
            confidence=confidence,
            job_id=job_id,
        )