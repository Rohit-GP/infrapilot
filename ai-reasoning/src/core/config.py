"""
Runtime configuration for the AI Reasoning Layer.

Mirrors diagnostics-engine/src/core/config.py's RedisConfig so both services
agree on stream/consumer-group names purely through environment variables
(see .env.example at the repo root). Nothing here is reasoning-specific
Redis wiring itself - just the settings.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # picks up a .env file in the working directory if present


@dataclass
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    stream_name: str = os.getenv("REDIS_STREAM", "diagnostics:evidence")
    consumer_group: str = os.getenv("REDIS_CONSUMER_GROUP", "reasoning-agents")
    consumer_name: str = os.getenv("REDIS_CONSUMER_NAME", "reasoning-agent-1")


@dataclass
class ReasoningConfig:
    """Job-accumulation / workflow-trigger settings.

    A diagnostics job publishes one evidence event per probe (see
    diagnostics-engine PROBE_REGISTRY). We don't always know in advance how
    many probes a given job ran (the CLI's --probes flag can subset them),
    so job completion is detected two ways, whichever fires first:

    1. All probe types in `known_probe_types` have been seen for the job.
    2. No new evidence has arrived for the job for `job_idle_timeout_s`
       seconds (handles subsets / a probe that never reported).
    """

    known_probe_types: tuple[str, ...] = field(
        default_factory=lambda: (
            "ping", "dns", "port",
            "service",
            "http", "ssl",
            "cpu", "memory", "disk",
        )
    )
    job_idle_timeout_s: float = float(os.getenv("REASONING_JOB_IDLE_TIMEOUT_S", "15"))
    poll_interval_s: float = float(os.getenv("REASONING_POLL_INTERVAL_S", "1"))
