"""Runtime configuration for the diagnostics engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class ProbeConfig:
    target: str
    ports: list[int] = field(default_factory=lambda: [80, 443])
    dns_server: str | None = None          # None = use system resolver
    ping_count: int = 4
    ping_timeout_s: float = 2.0
    port_timeout_s: float = 3.0
    dns_timeout_s: float = 3.0
    service_check_url: str | None = None   # optional HTTP health endpoint
    log_path: str | None = None            # optional local log file to scan


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    stream_name: str = os.getenv("REDIS_STREAM", "diagnostics:evidence")
