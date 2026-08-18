"""
Redis Streams consumer for the AI Reasoning Layer (production consumer).

Reads Evidence events published by the diagnostics engine (see
diagnostics-engine/src/core/publisher.py) via a consumer group on the
`diagnostics:evidence` stream, accumulates them by job_id, and runs the
LangGraph workflow once a job's complete evidence set has arrived.

Job completion is detected two ways, whichever fires first (see
src/core/config.py::ReasoningConfig):
1. Evidence has been seen for every known probe type.
2. No new evidence has arrived for the job for `job_idle_timeout_s` seconds.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

import redis

from src.core.config import ReasoningConfig, RedisConfig
from src.graph.workflow import run_workflow


@dataclass
class _JobAccumulator:
    target: str = ""
    evidence: list[dict[str, Any]] = field(default_factory=list)
    probe_types_seen: set[str] = field(default_factory=set)
    last_seen: float = field(default_factory=time.time)

    def add(self, ev: dict[str, Any]) -> None:
        self.target = ev.get("target") or self.target
        self.evidence.append(ev)
        self.probe_types_seen.add(ev.get("probe_type"))
        self.last_seen = time.time()

    def is_complete(self, config: ReasoningConfig) -> bool:
        if set(config.known_probe_types) <= self.probe_types_seen:
            return True
        return (time.time() - self.last_seen) >= config.job_idle_timeout_s


class RedisConsumer:
    def __init__(self, redis_config: RedisConfig | None = None, reasoning_config: ReasoningConfig | None = None):
        self.redis_config = redis_config or RedisConfig()
        self.reasoning_config = reasoning_config or ReasoningConfig()
        self._client: redis.Redis | None = None
        self._jobs: dict[str, _JobAccumulator] = {}

    # --- connection setup -------------------------------------------------
    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=self.redis_config.host,
                port=self.redis_config.port,
                decode_responses=True,
            )
            self._ensure_group(self._client)
        return self._client

    def _ensure_group(self, client: redis.Redis) -> None:
        """Idempotently create the stream (if missing) and the consumer
        group. Mirrors EvidencePublisher._ensure_group - either side may be
        the first to connect."""
        try:
            client.xgroup_create(
                name=self.redis_config.stream_name,
                groupname=self.redis_config.consumer_group,
                id="0",
                mkstream=True,
            )
        except Exception as exc:  # noqa: BLE001
            if "BUSYGROUP" not in str(exc):
                raise

    # --- main loop ----------------------------------------------------
    def run(self) -> None:
        client = self._get_client()
        print(
            f"[redis] consumer '{self.redis_config.consumer_name}' listening on "
            f"stream='{self.redis_config.stream_name}' group='{self.redis_config.consumer_group}'"
        )

        while True:
            messages = client.xreadgroup(
                groupname=self.redis_config.consumer_group,
                consumername=self.redis_config.consumer_name,
                streams={self.redis_config.stream_name: ">"},
                count=10,
                block=int(self.reasoning_config.poll_interval_s * 1000),
            )

            if messages:
                self._handle_messages(client, messages)

            self._check_completed_jobs()

    def _handle_messages(self, client: redis.Redis, messages) -> None:
        for _stream_name, entries in messages:
            for message_id, fields in entries:
                try:
                    evidence = json.loads(fields["evidence"])
                except (KeyError, json.JSONDecodeError) as exc:
                    print(f"[redis] WARNING: could not parse message {message_id}: {exc}")
                    client.xack(self.redis_config.stream_name, self.redis_config.consumer_group, message_id)
                    continue

                job_id = evidence.get("job_id") or "unknown-job"
                self._jobs.setdefault(job_id, _JobAccumulator()).add(evidence)

                print(
                    f"[redis] evidence received job={job_id} "
                    f"probe={evidence.get('probe_type')} status={evidence.get('status')}"
                )

                client.xack(self.redis_config.stream_name, self.redis_config.consumer_group, message_id)

    def _check_completed_jobs(self) -> None:
        completed_job_ids = [
            job_id for job_id, job in self._jobs.items() if job.evidence and job.is_complete(self.reasoning_config)
        ]

        for job_id in completed_job_ids:
            job = self._jobs.pop(job_id)
            print(f"[reasoning] job={job_id} evidence complete ({len(job.evidence)} probes) - running workflow")
            self._run_workflow(job_id, job)

    def _run_workflow(self, job_id: str, job: _JobAccumulator) -> None:
        try:
            final_state = run_workflow(job_id=job_id, target=job.target, evidence=job.evidence)
        except Exception as exc:  # noqa: BLE001 - keep the consumer alive across a bad job
            print(f"[reasoning] ERROR: workflow failed for job={job_id}: {exc}")
            return

        diagnosis = final_state.get("diagnosis", {})
        print(f"[reasoning] job={job_id} diagnosis: {json.dumps(diagnosis, indent=2, default=str)}")
        
if __name__ == "__main__":
    RedisConsumer().run()
