"""
TCP port / socket-level reachability probe.

This is the purest "socket probing" of the four probes: opens a raw TCP
socket to (host, port) and measures connect time. A closed port refuses
the connection immediately (fast failure); a firewalled port times out
(slow failure) — that distinction itself is useful diagnostic evidence,
so we keep it in the result rather than collapsing both into "failed".
"""

from __future__ import annotations

import socket
import time

from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.config import ProbeConfig


# def _check_port(host: str, port: int, timeout_s: float) -> dict:
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.settimeout(timeout_s)
#     start = time.perf_counter()
#     try:
#         result_code = sock.connect_ex((host, port))
#         elapsed_ms = (time.perf_counter() - start) * 1000
#         if result_code == 0:
#             return {"port": port, "open": True, "latency_ms": round(elapsed_ms, 2), "detail": "connected"}
#         return {"port": port, "open": False, "latency_ms": round(elapsed_ms, 2), "detail": f"refused (errno {result_code})"}
#     except socket.timeout:
#         elapsed_ms = (time.perf_counter() - start) * 1000
#         return {"port": port, "open": False, "latency_ms": round(elapsed_ms, 2), "detail": "timed out (likely firewalled)"}
#     finally:
#         sock.close()

def _check_port(host: str, port: int, timeout_s: float) -> dict:
    start = time.perf_counter()

    infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)

    last_error = None

    for family, socktype, proto, _, sockaddr in infos:
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(timeout_s)

        try:
            result = sock.connect_ex(sockaddr)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if result == 0:
                return {
                    "port": port,
                    "open": True,
                    "latency_ms": round(elapsed_ms, 2),
                    "detail": "connected",
                }

            last_error = result

        finally:
            sock.close()

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "port": port,
        "open": False,
        "latency_ms": round(elapsed_ms, 2),
        "detail": f"connection failed ({last_error})",
    }


def run(config: ProbeConfig, job_id: str | None = None) -> Evidence:
    target = config.target
    try:
        results = [_check_port(target, p, config.port_timeout_s) for p in config.ports]
        open_ports = [r["port"] for r in results if r["open"]]
        closed_ports = [r["port"] for r in results if not r["open"]]
        avg_latency = sum(r["latency_ms"] for r in results) / len(results) if results else None

        if len(open_ports) == len(config.ports):
            status = ProbeStatus.OK
            message = f"All checked ports open: {open_ports}"
        elif open_ports:
            status = ProbeStatus.DEGRADED
            message = f"Partial: open={open_ports} closed/filtered={closed_ports}"
        else:
            status = ProbeStatus.FAILED
            message = f"No checked ports reachable: {closed_ports}"

        return Evidence(
            probe_type=ProbeType.PORT,
            target=target,
            status=status,
            latency_ms=round(avg_latency, 2) if avg_latency is not None else None,
            message=message,
            raw={"ports_checked": config.ports, "results": results},
            job_id=job_id,
        )

    # except Exception as exc:  # noqa: BLE001
    #     return Evidence.error_result(ProbeType.PORT, target, exc, job_id=job_id)
    
    except Exception as exc:
        import traceback

        traceback.print_exc()
        print(f"Port probe exception: {exc!r}")

        return Evidence.error_result(
            ProbeType.PORT,
            target,
            exc,
            job_id=job_id,
        )
