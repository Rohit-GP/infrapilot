"""
Redis Streams consumer for InfraPilot AI reasoning.

Compatible with the existing diagnostics-engine publisher:

    stream_name = diagnostics:evidence
    consumer_group = reasoning-agents

Publisher message format:

    {
        "evidence": "<Evidence.to_json()>"
    }

The consumer aggregates evidence by job_id.

As evidence arrives, the current accumulated diagnosis for that
job is re-evaluated by LangGraph.

No LLM is used.
"""

from __future__ import annotations

import json
import os
import socket
import time
from collections import defaultdict
from typing import Any

import redis

from src.graph.workflow import build_diagnosis_graph


class RedisEvidenceConsumer:

    def __init__(
        self,
        stream_name: str | None = None,
        consumer_group: str | None = None,
        consumer_name: str | None = None,
        host: str | None = None,
        port: int | None = None,
    ):

        self.host = host or os.getenv(
            "REDIS_HOST",
            "localhost",
        )

        self.port = port or int(
            os.getenv(
                "REDIS_PORT",
                "6379",
            )
        )

        self.stream_name = (
            stream_name
            or os.getenv(
                "REDIS_STREAM",
                "diagnostics:evidence",
            )
        )

        self.consumer_group = (
            consumer_group
            or os.getenv(
                "REDIS_CONSUMER_GROUP",
                "reasoning-agents",
            )
        )

        self.consumer_name = (
            consumer_name
            or os.getenv(
                "REDIS_CONSUMER_NAME",
                f"reasoning-{socket.gethostname()}",
            )
        )

        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            decode_responses=True,
        )

        self.graph = build_diagnosis_graph()

        # -----------------------------------------------------
        # Accumulate evidence by diagnostics job.
        #
        # Example:
        #
        # {
        #     "job-123": [
        #         dns evidence,
        #         ping evidence,
        #         http evidence,
        #     ]
        # }
        # -----------------------------------------------------

        self.jobs: dict[
            str,
            list[dict[str, Any]]
        ] = defaultdict(list)

    # ---------------------------------------------------------
    # Redis group
    # ---------------------------------------------------------

    def ensure_consumer_group(self) -> None:

        try:

            self.client.xgroup_create(
                name=self.stream_name,
                groupname=self.consumer_group,
                id="0",
                mkstream=True,
            )

            print(
                "[redis] consumer group created: "
                f"{self.consumer_group}"
            )

        except redis.ResponseError as exc:

            if "BUSYGROUP" in str(exc):

                print(
                    "[redis] consumer group already exists: "
                    f"{self.consumer_group}"
                )

            else:
                raise

    # ---------------------------------------------------------
    # Parse publisher message
    # ---------------------------------------------------------

    @staticmethod
    def parse_evidence(
        message: dict[str, Any],
    ) -> dict[str, Any] | None:

        evidence_json = message.get(
            "evidence"
        )

        if not evidence_json:
            return None

        try:

            evidence = json.loads(
                evidence_json
            )

        except json.JSONDecodeError as exc:

            print(
                "[redis] invalid evidence JSON: "
                f"{exc}"
            )

            return None

        if not isinstance(
            evidence,
            dict,
        ):
            return None

        return evidence

    # ---------------------------------------------------------
    # Add evidence to job
    # ---------------------------------------------------------

    def add_evidence(
        self,
        evidence: dict[str, Any],
    ) -> str:

        job_id = evidence.get(
            "job_id"
        )

        if not job_id:

            # Fallback for malformed/legacy evidence.
            job_id = (
                "unknown-"
                + str(
                    evidence.get(
                        "evidence_id",
                        time.time_ns(),
                    )
                )
            )

        # -----------------------------------------------------
        # Avoid duplicate evidence.
        # -----------------------------------------------------

        evidence_id = evidence.get(
            "evidence_id"
        )

        if evidence_id:

            already_exists = any(
                item.get("evidence_id")
                == evidence_id
                for item in self.jobs[job_id]
            )

            if already_exists:
                return job_id

        self.jobs[job_id].append(
            evidence
        )

        return job_id

    # ---------------------------------------------------------
    # Run LangGraph
    # ---------------------------------------------------------

    def diagnose_job(
        self,
        job_id: str,
    ) -> dict[str, Any]:

        evidence = self.jobs.get(
            job_id,
            [],
        )

        if not evidence:

            return {
                "job_id": job_id,
                "root_cause": (
                    "No evidence available."
                ),
                "confidence": 0.0,
            }

        target = evidence[0].get(
            "target",
            "unknown",
        )

        initial_state = {
            "job_id": job_id,
            "target": target,
            "evidence": evidence,

            "network_findings": [],
            "system_findings": [],
            "application_findings": [],

            "validated_findings": [],

            "required_agents": [],

            "root_cause": "",
            "confidence": 0.0,
            "recommendations": [],

            "errors": [],
        }

        result = self.graph.invoke(
            initial_state
        )

        return result

    # ---------------------------------------------------------
    # Process one Redis message
    # ---------------------------------------------------------

    def process_message(
        self,
        message_id: str,
        message: dict[str, Any],
    ) -> None:

        evidence = self.parse_evidence(
            message
        )

        if evidence is None:

            print(
                f"[redis] skipping invalid message "
                f"{message_id}"
            )

            return

        job_id = self.add_evidence(
            evidence
        )

        probe_type = evidence.get(
            "probe_type",
            "unknown",
        )

        status = evidence.get(
            "status",
            "unknown",
        )

        print(
            f"[redis] evidence received "
            f"job={job_id} "
            f"probe={probe_type} "
            f"status={status}"
        )

        # -----------------------------------------------------
        # Run the current diagnosis using all evidence received
        # so far for this job.
        # -----------------------------------------------------

        result = self.diagnose_job(
            job_id
        )

        self.print_diagnosis(
            result
        )

    # ---------------------------------------------------------
    # Print diagnosis
    # ---------------------------------------------------------

    @staticmethod
    def print_diagnosis(
        result: dict[str, Any],
    ) -> None:

        print()
        print("=" * 70)
        print("INFRA PILOT DIAGNOSIS")
        print("=" * 70)

        print(
            f"Job ID: {result.get('job_id')}"
        )

        print(
            f"Target: {result.get('target')}"
        )

        print(
            f"Root Cause: "
            f"{result.get('root_cause')}"
        )

        print(
            f"Confidence: "
            f"{result.get('confidence')}"
        )

        print()
        print("Required Agents:")

        for agent in result.get(
            "required_agents",
            [],
        ):
            print(
                f"  - {agent}"
            )

        print()
        print("Validated Findings:")

        for finding in result.get(
            "validated_findings",
            [],
        ):

            print(
                f"  [{finding.get('severity')}] "
                f"{finding.get('finding')}"
            )

        print()
        print("Recommendations:")

        for recommendation in result.get(
            "recommendations",
            [],
        ):

            print(
                f"  - {recommendation}"
            )

        print("=" * 70)
        print()

    # ---------------------------------------------------------
    # Consumer loop
    # ---------------------------------------------------------

    def run(
        self,
        block_ms: int = 5000,
        count: int = 10,
    ) -> None:

        self.ensure_consumer_group()

        print()
        print(
            "InfraPilot Redis Consumer"
        )

        print(
            f"Redis: {self.host}:{self.port}"
        )

        print(
            f"Stream: {self.stream_name}"
        )

        print(
            f"Group: {self.consumer_group}"
        )

        print(
            f"Consumer: {self.consumer_name}"
        )

        print()
        print(
            "Waiting for evidence..."
        )

        while True:

            try:

                response = self.client.xreadgroup(
                    groupname=self.consumer_group,
                    consumername=self.consumer_name,
                    streams={
                        self.stream_name: ">"
                    },
                    count=count,
                    block=block_ms,
                )

                if not response:
                    continue

                for (
                    stream,
                    messages,
                ) in response:

                    for (
                        message_id,
                        message,
                    ) in messages:

                        try:

                            self.process_message(
                                message_id,
                                message,
                            )

                            self.client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id,
                            )

                        except Exception as exc:

                            print(
                                "[redis] processing error "
                                f"for {message_id}: {exc}"
                            )

                            # Do not ACK a failed message.
                            # Redis Streams can redeliver it.

            except KeyboardInterrupt:

                print(
                    "\n[redis] consumer stopped."
                )

                break

            except redis.RedisError as exc:

                print(
                    f"[redis] connection error: {exc}"
                )

                time.sleep(2)