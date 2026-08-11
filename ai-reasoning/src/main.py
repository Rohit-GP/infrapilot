"""
Entry point for the InfraPilot AI reasoning service.

Usage:

    python -m src.main

The service connects to the existing Redis Stream:

    diagnostics:evidence

and consumes evidence published by diagnostics-engine.
"""

from __future__ import annotations

from src.consumers.redis_consumer import (
    RedisEvidenceConsumer,
)


def main() -> None:

    consumer = RedisEvidenceConsumer()

    consumer.run()


if __name__ == "__main__":
    main()