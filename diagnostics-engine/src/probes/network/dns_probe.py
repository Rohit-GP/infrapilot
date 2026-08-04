"""
DNS resolution probe.

Uses the stdlib `socket` module for the default (system resolver) case,
and `dnspython` when a specific DNS server needs to be queried directly
(useful for diagnosing "works with 8.8.8.8 but not with our internal
resolver" type incidents).
"""

from __future__ import annotations

import socket
import time

from src.core.models import Evidence, ProbeStatus, ProbeType
from src.core.config import ProbeConfig


def _resolve_via_system(target: str, timeout_s: float) -> tuple[list[str], float]:
    socket.setdefaulttimeout(timeout_s)
    start = time.perf_counter()
    # _, _, ip_list = socket.gethostbyname_ex(target)
    results = socket.getaddrinfo(target, None)
    ip_list = sorted({item[4][0] for item in results})
    elapsed_ms = (time.perf_counter() - start) * 1000
    return ip_list, elapsed_ms


def _resolve_via_custom_server(target: str, dns_server: str, timeout_s: float) -> tuple[list[str], float]:
    import dns.resolver  # dnspython, only imported if a custom server is configured

    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [dns_server]
    resolver.timeout = timeout_s
    resolver.lifetime = timeout_s

    start = time.perf_counter()
    answer = resolver.resolve(target, "A")
    elapsed_ms = (time.perf_counter() - start) * 1000
    return [r.to_text() for r in answer], elapsed_ms


def run(config: ProbeConfig, job_id: str | None = None) -> Evidence:
    target = config.target
    try:
        if config.dns_server:
            ip_list, elapsed_ms = _resolve_via_custom_server(target, config.dns_server, config.dns_timeout_s)
            resolver_used = config.dns_server
        else:
            ip_list, elapsed_ms = _resolve_via_system(target, config.dns_timeout_s)
            resolver_used = "system default"

        return Evidence(
            probe_type=ProbeType.DNS,
            target=target,
            status=ProbeStatus.OK,
            latency_ms=round(elapsed_ms, 2),
            message=f"Resolved to {len(ip_list)} address(es) via {resolver_used}",
            raw={"resolved_ips": ip_list, "resolver": resolver_used},
            job_id=job_id,
        )

    except socket.gaierror as exc:
        return Evidence(
            probe_type=ProbeType.DNS,
            target=target,
            status=ProbeStatus.FAILED,
            message="DNS resolution failed (name does not resolve)",
            error=str(exc),
            job_id=job_id,
        )
    except Exception as exc:  # noqa: BLE001
        return Evidence.error_result(ProbeType.DNS, target, exc, job_id=job_id)
