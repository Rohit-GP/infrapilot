"""
Diagnostics runner - fans out all configured probes concurrently
(they're I/O-bound: network calls, subprocess calls) and collects
their Evidence results. This is what the CLI, and later the
Spring Boot trigger, will call into.
"""

from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.config import ProbeConfig
from src.core.models import Evidence
from src.probes import ping_probe, dns_probe, port_probe, service_probe

# Registry of available probes. Add new probes here as they're built
# (this is the extension point mentioned in Section 9 of the design doc
# for DB/infra probes).
PROBE_REGISTRY = {
    "ping": ping_probe.run,
    "dns": dns_probe.run,
    "port": port_probe.run,
    "service": service_probe.run,
}


class DiagnosticsRunner:
    def __init__(self, config: ProbeConfig, probes: list[str] | None = None):
        self.config = config
        self.probes = probes or list(PROBE_REGISTRY.keys())
        self.job_id = str(uuid.uuid4())

    def run(self) -> list[Evidence]:
        results: list[Evidence] = []
        with ThreadPoolExecutor(max_workers=len(self.probes) or 1) as pool:
            future_to_probe = {
                pool.submit(PROBE_REGISTRY[name], self.config, self.job_id): name
                for name in self.probes
                if name in PROBE_REGISTRY
            }
            for future in as_completed(future_to_probe):
                results.append(future.result())
        return results
