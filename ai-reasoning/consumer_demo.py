"""
Phase 2 verification tool - NOT the real AI reasoning layer.

This is a minimal consumer that reads evidence off the Redis Stream using
the same consumer-group pattern the real LangGraph agents will use in
Phase 4. Its only job is to prove "diagnostics engine -> Redis Stream ->
something on the other end" actually works, before any LangGraph code
exists.

Usage:
    python consumer_demo.py
    (leave running in one terminal, then in another terminal run the
     diagnostics engine with --publish)

Ctrl+C to stop. Each message is XACK'd after printing, so re-running
this script won't replay old evidence.
"""

from __future__ import annotations

import json
import os
import sys

import redis
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("REDIS_HOST", "localhost")
PORT = int(os.getenv("REDIS_PORT", "6379"))
STREAM = os.getenv("REDIS_STREAM", "diagnostics:evidence")
GROUP = os.getenv("REDIS_CONSUMER_GROUP", "reasoning-agents")
CONSUMER_NAME = "consumer-demo-1"


def ensure_group(client: redis.Redis) -> None:
    try:
        client.xgroup_create(name=STREAM, groupname=GROUP, id="0", mkstream=True)
    except redis.exceptions.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


def main() -> None:
    client = redis.Redis(host=HOST, port=PORT, decode_responses=True)
    try:
        client.ping()
    except redis.exceptions.ConnectionError:
        print(f"Could not connect to Redis at {HOST}:{PORT}. "
              f"Start it with: docker compose up -d redis")
        sys.exit(1)

    ensure_group(client)
    print(f"Listening on stream '{STREAM}' as consumer '{CONSUMER_NAME}' in group '{GROUP}'...")
    print("Run the diagnostics engine with --publish in another terminal to see evidence here.\n")

    while True:
        # Block up to 5s waiting for new messages ('>' = only undelivered ones)
        response = client.xreadgroup(GROUP, CONSUMER_NAME, {STREAM: ">"}, count=10, block=5000)
        if not response:
            continue

        for _stream_name, messages in response:
            for message_id, fields in messages:
                evidence = json.loads(fields["evidence"])
                print(
                    f"[{message_id}] probe={evidence['probe_type']:8s} "
                    f"status={evidence['status']:8s} target={evidence['target']} "
                    f"-> {evidence['message']}"
                )
                client.xack(STREAM, GROUP, message_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")
