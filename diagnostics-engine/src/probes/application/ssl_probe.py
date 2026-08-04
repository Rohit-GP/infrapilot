"""
SSL/TLS Certificate Probe (Application layer).

Connects to config.target:config.ssl_port over TLS and checks certificate
validity/expiry. A verification failure or expiring cert is a FAILED
result (real signal about the target); a connection-level problem
(timeout, refused, DNS) is an ERROR (the probe itself couldn't complete).
"""

from __future__ import annotations

import socket
import ssl
import time
from datetime import datetime, timezone

from src.core.config import ProbeConfig
from src.core.models import Evidence, ProbeStatus, ProbeType


def run(config: ProbeConfig, job_id: str) -> Evidence:
    target = f"{config.target}:{config.ssl_port}"
    context = ssl.create_default_context()

    try:
        start = time.perf_counter()
        with socket.create_connection((config.target, config.ssl_port), timeout=config.ssl_timeout_s) as sock:
            with context.wrap_socket(sock, server_hostname=config.target) as ssock:
                cert = ssock.getpeercert()
                protocol = ssock.version()
                cipher = ssock.cipher()
        latency_ms = (time.perf_counter() - start) * 1000

        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days_remaining = (not_after - datetime.now(timezone.utc)).days

        issuer = dict(x[0] for x in cert.get("issuer", []))
        raw = {
            "days_remaining": days_remaining,
            "not_after": cert["notAfter"],
            "issuer": issuer.get("organizationName", issuer.get("commonName", "unknown")),
            "protocol": protocol,
            "cipher": cipher[0] if cipher else None,
        }

        if days_remaining < 0:
            status, message = ProbeStatus.FAILED, "Certificate has expired"
        elif days_remaining <= config.ssl_crit_days:
            status, message = ProbeStatus.FAILED, f"Certificate expires in {days_remaining} days"
        elif days_remaining <= config.ssl_warn_days:
            status, message = ProbeStatus.DEGRADED, f"Certificate expires in {days_remaining} days"
        else:
            status, message = ProbeStatus.OK, f"Certificate valid, {days_remaining} days remaining"

        return Evidence(
            probe_type=ProbeType.SSL, target=target, status=status,
            latency_ms=latency_ms, raw=raw, message=message, job_id=job_id,
        )

    except ssl.SSLCertVerificationError as exc:
        return Evidence(
            probe_type=ProbeType.SSL, target=target, status=ProbeStatus.FAILED,
            message="Certificate verification failed", error=str(exc), job_id=job_id,
        )
    except (socket.timeout, ConnectionRefusedError, socket.gaierror) as exc:
        return Evidence.error_result(ProbeType.SSL, target, exc, job_id=job_id)
    except Exception as exc:  # noqa: BLE001
        return Evidence.error_result(ProbeType.SSL, target, exc, job_id=job_id)
