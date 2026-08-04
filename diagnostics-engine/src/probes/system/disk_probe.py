"""
Disk Probe (System layer).

Checks disk usage across mounted partitions (or a single one, if
config.disk_path is set) of the host this probe executes on. Same
remote-target caveat as cpu_probe.py / memory_probe.py.
"""

from __future__ import annotations

import time

import psutil

from src.core.config import ProbeConfig
from src.core.models import Evidence, ProbeStatus, ProbeType


def run(config: ProbeConfig, job_id: str) -> Evidence:
    start = time.perf_counter()
    try:
        partitions = psutil.disk_partitions(all=False)
        if config.disk_path:
            partitions = [p for p in partitions if p.mountpoint == config.disk_path] or partitions

        usage_by_mount: dict[str, dict] = {}
        worst_pct = 0.0
        worst_mount = None

        for p in partitions:
            try:
                usage = psutil.disk_usage(p.mountpoint)
            except PermissionError:
                continue
            usage_by_mount[p.mountpoint] = {
                "total_gb": round(usage.total / (1024 ** 3), 2),
                "used_gb": round(usage.used / (1024 ** 3), 2),
                "free_gb": round(usage.free / (1024 ** 3), 2),
                "used_percent": usage.percent,
                "filesystem": p.fstype,
            }
            if usage.percent > worst_pct:
                worst_pct = usage.percent
                worst_mount = p.mountpoint

        latency_ms = (time.perf_counter() - start) * 1000
        raw = {
            "partitions": usage_by_mount,
            "worst_mount": worst_mount,
            "worst_used_percent": worst_pct,
        }

        if worst_pct >= config.disk_crit_pct:
            status = ProbeStatus.FAILED
            message = f"{worst_mount} at {worst_pct:.1f}% used >= critical threshold {config.disk_crit_pct}%"
        elif worst_pct >= config.disk_warn_pct:
            status = ProbeStatus.DEGRADED
            message = f"{worst_mount} at {worst_pct:.1f}% used >= warning threshold {config.disk_warn_pct}%"
        else:
            status = ProbeStatus.OK
            message = "All monitored partitions within normal range"

        return Evidence(
            probe_type=ProbeType.DISK, target=config.target, status=status,
            latency_ms=latency_ms, raw=raw, message=message, job_id=job_id,
        )
    except Exception as exc:  # noqa: BLE001
        return Evidence.error_result(ProbeType.DISK, config.target, exc, job_id=job_id)
