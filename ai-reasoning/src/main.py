"""
Entry point for the AI Reasoning Layer service.

Usage:
    python -m src.main

Starts the Redis Streams consumer, which accumulates evidence per
diagnostics job and runs the LangGraph reasoning workflow once each job's
evidence set is complete (see src/consumers/redis_consumer.py).
"""

from __future__ import annotations

import sys

from src.consumers.redis_consumer import RedisConsumer


def main() -> int:
    consumer = RedisConsumer()
    try:
        consumer.run()
    except KeyboardInterrupt:
        print("\n[main] shutting down")
    return 0


if __name__ == "__main__":
    sys.exit(main())
