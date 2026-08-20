"""
Probe trigger service ("probe-trigger" module from the backend README).

Runs the diagnostics engine as a subprocess (`python -m src.main --target
... --job-id ... --publish`) rather than importing it in-process - it's a
separate project with its own venv/requirements
(see diagnostics-engine/requirements.txt), so a subprocess boundary keeps
the two services' dependencies from colliding.

`--publish` makes the diagnostics engine also push each Evidence event to
Redis Streams itself (diagnostics-engine/src/core/publisher.py) - that's
what the AI reasoning layer consumes independently. This service only
needs the same JSON the CLI prints to stdout to persist Evidence rows here.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any

from src.core.config import settings


class ProbeTriggerError(Exception):
    pass


@dataclass
class ProbeRunResult:
    job_id: str
    target: str
    evidence: list[dict[str, Any]]
    any_failed: bool


def run_probes(
    job_id: str,
    target_identifier: str,
    probes: list[str] | None = None,
    ports: list[int] | None = None,
    http_url: str | None = None,
) -> ProbeRunResult:
    """Blocking call - runs the full probe suite for one target. Intended to
    be called from a background thread (see services/job_service.py), not
    directly inside an async request handler."""

    cmd = [
        settings.diagnostics_engine_python,
        "-m", "src.main",
        "--target", target_identifier,
        "--job-id", job_id,
        "--publish",
    ]
    if probes:
        cmd += ["--probes", ",".join(probes)]
    if ports:
        cmd += ["--ports", ",".join(str(p) for p in ports)]
    if http_url:
        cmd += ["--http-url", http_url]

    try:
        proc = subprocess.run(
            cmd,
            cwd=settings.diagnostics_engine_dir,
            capture_output=True,
            text=True,
            timeout=settings.diagnostics_engine_timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProbeTriggerError(f"diagnostics engine timed out for job {job_id}") from exc

    # The CLI's exit code is 1 when any probe reports failed/error status -
    # that's an expected, informative outcome, not a crash. A genuine crash
    # (non-zero *and* no parseable JSON on stdout) is the real failure case.
    try:
        output = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeTriggerError(
            f"diagnostics engine produced no valid output for job {job_id}: {proc.stderr.strip()}"
        ) from exc

    evidence = output.get("evidence", [])
    any_failed = any(ev.get("status") in ("failed", "error") for ev in evidence)

    return ProbeRunResult(job_id=job_id, target=output.get("target", target_identifier), evidence=evidence, any_failed=any_failed)
