"""
Demo script: tails the Redis evidence stream live and prints each piece of
evidence as it arrives.

This is intentionally separate from the production RedisConsumer
(src/consumers/redis_consumer.py) - it uses plain XREAD from '$' (only new
messages) instead of a consumer group, so running it never competes for or
acknowledges messages the real reasoning consumer needs to process. It's
just for watching evidence flow in while developing/debugging, matching the
"Watch Evidence on Redis Streams" step in the top-level README.

Usage:
    python consumer_demo.py
"""

from __future__ import annotations

import json

import redis

from src.core.config import RedisConfig


def main() -> None:
    config = RedisConfig()
    client = redis.Redis(host=config.host, port=config.port, decode_responses=True)

    print(f"[demo] tailing stream='{config.stream_name}' on {config.host}:{config.port} (Ctrl+C to stop)")

    last_id = "$"  # start from "now" - only show evidence published after the demo starts

    try:
        while True:
            messages = client.xread({config.stream_name: last_id}, count=10, block=1000)
            if not messages:
                continue

            for _stream_name, entries in messages:
                for message_id, fields in entries:
                    last_id = message_id
                    try:
                        evidence = json.loads(fields["evidence"])
                    except (KeyError, json.JSONDecodeError):
                        print(f"[demo] could not parse message {message_id}: {fields}")
                        continue

                    print(
                        f"[redis] evidence received job={evidence.get('job_id')} "
                        f"probe={evidence.get('probe_type')} status={evidence.get('status')}"
                    )
    except KeyboardInterrupt:
        print("\n[demo] stopped")


if __name__ == "__main__":
    main()
