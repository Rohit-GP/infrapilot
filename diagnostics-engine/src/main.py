"""
CLI entry point for the diagnostics engine.

Usage:
    python -m src.main --target example.com --ports 80,443
    python -m src.main --target example.com --ports 80,443 --publish
    python -m src.main --target example.com --probes ping,dns
"""

from __future__ import annotations

import argparse
import json
import sys

from src.core.config import ProbeConfig
from src.core.runner import DiagnosticsRunner, PROBE_REGISTRY
from src.core.publisher import EvidencePublisher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agentic NOC - diagnostics engine")
    parser.add_argument("--target", required=True, help="Hostname or IP to diagnose")
    parser.add_argument("--ports", default="80,443", help="Comma-separated TCP ports to check")
    parser.add_argument("--dns-server", default=None, help="Custom DNS server IP (optional)")
    parser.add_argument("--service-url", default=None, help="HTTP health check URL (optional)")
    parser.add_argument("--log-path", default=None, help="Local log file to scan (optional)")
    parser.add_argument(
        "--probes",
        default=",".join(PROBE_REGISTRY.keys()),
        help=f"Comma-separated probes to run. Available: {list(PROBE_REGISTRY.keys())}",
    )
    parser.add_argument("--publish", action="store_true", help="Publish evidence to Redis Stream")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    service_url = args.service_url
    if service_url is None:
        service_url = f"https://{args.target}"

    config = ProbeConfig(
        target=args.target,
        ports=[int(p) for p in args.ports.split(",") if p.strip()],
        dns_server=args.dns_server,
        service_check_url=service_url,
        log_path=args.log_path,
    )
    probes = [p.strip() for p in args.probes.split(",") if p.strip()]

    runner = DiagnosticsRunner(config, probes=probes)
    results = runner.run()

    publisher = EvidencePublisher() if args.publish else None

    output = {"job_id": runner.job_id, "target": config.target, "evidence": []}
    for ev in sorted(results, key=lambda e: e.probe_type.value):
        output["evidence"].append(ev.to_dict())
        if publisher:
            publisher.publish(ev)

    print(json.dumps(output, indent=2, default=str))

    any_failed = any(e.status.value in ("failed", "error") for e in results)
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
