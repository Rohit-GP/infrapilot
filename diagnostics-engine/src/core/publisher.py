"""
Redis Streams publisher (Phase 2).

Deliberately uses Streams (XADD) rather than Pub/Sub - per the design doc,
plain Pub/Sub drops events if the LangGraph consumer is down when they're
published. Streams persist evidence until a consumer group acknowledges it.

This module is safe to import even if Redis isn't running yet (Phase 1
doesn't need it) - publish() just logs a warning and returns False instead
of crashing the CLI.
"""

from __future__ import annotations

from src.core.config import RedisConfig
from src.core.models import Evidence


class EvidencePublisher:
    def __init__(self, config: RedisConfig | None = None):
        self.config = config or RedisConfig()
        self._client = None

    def _get_client(self):
        if self._client is None:
            import redis  # imported lazily so Phase 1 doesn't require redis-py installed/running
            self._client = redis.Redis(host=self.config.host, port=self.config.port, decode_responses=True)
            self._ensure_group(self._client)
        return self._client

    def _ensure_group(self, client) -> None:
        """Idempotently create the stream (if missing) and the consumer group.

        MKSTREAM creates the stream if it doesn't exist yet. If the group
        already exists, Redis raises BUSYGROUP - that's expected on every
        run after the first and just means "nothing to do".
        """
        try:
            client.xgroup_create(
                name=self.config.stream_name,
                groupname=self.config.consumer_group,
                id="0",
                mkstream=True,
            )
        except Exception as exc:  # noqa: BLE001
            if "BUSYGROUP" not in str(exc):
                raise

    def publish(self, evidence: Evidence) -> bool:
        try:
            client = self._get_client()
            client.xadd(self.config.stream_name, {"evidence": evidence.to_json()})
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[publisher] WARNING: could not publish to Redis ({exc}). "
                  f"Is Redis running? Continuing without it.")
            return False

    def stream_length(self) -> int | None:
        """Returns current stream length, or None if Redis isn't reachable."""
        try:
            client = self._get_client()
            return client.xlen(self.config.stream_name)
        except Exception:  # noqa: BLE001
            return None
