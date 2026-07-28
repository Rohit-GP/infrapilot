"""
Ping / reachability probe.

Note: raw ICMP sockets require root/CAP_NET_RAW on most OSes, so this
shells out to the system `ping` binary (works unprivileged everywhere)
and parses its output. This keeps the probe portable across Linux/macOS/
Windows without needing elevated permissions.
"""

from __future__ import annotations

import platform
import re
import subprocess

from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.config import ProbeConfig


def _build_command(target: str, count: int, timeout_s: float) -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return ["ping", "-n", str(count), "-w", str(int(timeout_s * 1000)), target]
    # Linux / macOS
    return ["ping", "-c", str(count), "-W", str(int(timeout_s)), target]


def _parse_loss_and_latency(output: str) -> tuple[float | None, float | None]:
    """Returns (packet_loss_pct, avg_latency_ms) best-effort across platforms."""
    loss_match = re.search(r"(\d+(?:\.\d+)?)%\s*(?:packet)?\s*loss", output)
    loss_pct = float(loss_match.group(1)) if loss_match else None

    # Linux/macOS: "min/avg/max/... = 12.1/15.3/20.0/..."
    avg_match = re.search(r"=\s*[\d.]+/([\d.]+)/", output)
    if not avg_match:
        # Windows: "Average = 15ms"
        avg_match = re.search(r"Average\s*=\s*(\d+)ms", output)
    avg_latency = float(avg_match.group(1)) if avg_match else None

    return loss_pct, avg_latency


def run(config: ProbeConfig, job_id: str | None = None) -> Evidence:
    target = config.target
    try:
        cmd = _build_command(target, config.ping_count, config.ping_timeout_s)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.ping_timeout_s * config.ping_count + 5,
        )
        output = result.stdout + result.stderr
        loss_pct, avg_latency = _parse_loss_and_latency(output)

        if result.returncode == 0 and (loss_pct is None or loss_pct < 100):
            status = ProbeStatus.DEGRADED if (loss_pct and loss_pct > 0) else ProbeStatus.OK
            message = (
                f"Host reachable, {loss_pct or 0:.0f}% packet loss"
                if loss_pct else "Host reachable"
            )
        else:
            status = ProbeStatus.FAILED
            message = "Host unreachable (100% packet loss or ping failed)"

        return Evidence(
            probe_type=ProbeType.PING,
            target=target,
            status=status,
            latency_ms=avg_latency,
            message=message,
            raw={"stdout": output, "returncode": result.returncode, "packet_loss_pct": loss_pct},
            job_id=job_id,
        )

    except subprocess.TimeoutExpired as exc:
        return Evidence.error_result(ProbeType.PING, target, exc, job_id=job_id)
    except Exception as exc:  # noqa: BLE001 - probes must never raise, always return Evidence
        return Evidence.error_result(ProbeType.PING, target, exc, job_id=job_id)
