"""Runtime configuration for the diagnostics engine."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # picks up a .env file in the working directory if present


@dataclass
class ProbeConfig:
    target: str
    ports: list[int] = field(default_factory=lambda: [80, 443])
    dns_server: str | None = None          # None = use system resolver
    ping_count: int = 4
    ping_timeout_s: float = 2.0
    port_timeout_s: float = 3.0
    dns_timeout_s: float = 3.0
    service_check_url: str | None = None   # optional HTTP health endpoint (observability probe)
    log_path: str | None = None            # optional local log file to scan

    # --- Application layer (new) ---
    http_url: str | None = None            # if None, http probe is skipped
    http_expect_status: int = 200
    http_expect_text: str | None = None
    http_timeout_s: float = 5.0
    http_warn_latency_ms: float = 1000.0
    http_crit_latency_ms: float = 3000.0

    ssl_port: int = 443
    ssl_timeout_s: float = 5.0
    ssl_warn_days: int = 30
    ssl_crit_days: int = 7

    # --- System layer (new) ---
    cpu_warn_pct: float = 75.0
    cpu_crit_pct: float = 90.0
    memory_warn_pct: float = 80.0
    memory_crit_pct: float = 95.0
    disk_warn_pct: float = 80.0
    disk_crit_pct: float = 90.0
    disk_path: str | None = None           # None = check all mounted partitions


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    stream_name: str = os.getenv("REDIS_STREAM", "diagnostics:evidence")
    # Consumer group the AI reasoning layer (Phase 4) will read from.
    # Created lazily/idempotently by whoever connects first (publisher or consumer).
    consumer_group: str = os.getenv("REDIS_CONSUMER_GROUP", "reasoning-agents")
