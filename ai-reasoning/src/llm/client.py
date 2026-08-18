"""
Cloud LLM client.

The Cloud LLM integration itself is the *next phase* (see
ai-reasoning/README.md -> "Implementation Status"). This module currently
only contains `build_llm_input`, which turns the validated findings into
the compact, standardized payload the LLM will eventually consume - see
the README's "LLM Input" section for the exact shape this mirrors.

`CloudLLMClient` is a stub: the request/response wiring, prompt template,
and provider choice are intentionally not implemented yet.
"""

from __future__ import annotations

from typing import Any

from src.graph.state import GraphState


def build_llm_input(state: GraphState, validated_findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the standardized LLM input payload.

    Deliberately compact: only `agent`, `probe`, `severity`, and `finding`
    per finding, plus job-level context. Raw probe evidence, confidence
    scores, and evidence_ids are left out on purpose - the LLM reasons over
    validated findings, not the complete raw diagnostic payload (raw
    evidence stays available internally for traceability).
    """
    return {
        "job_id": state.get("job_id"),
        "target": state.get("target"),
        "required_agents": state.get("required_agents", []),
        "findings": [
            {
                "agent": f["agent"],
                "probe": f["probe"],
                "severity": f["severity"],
                "finding": f["finding"],
            }
            for f in validated_findings
        ],
    }


class CloudLLMClient:
    """Placeholder for the Cloud LLM integration (next phase).

    Not implemented yet - credentials, provider SDK, prompt construction,
    and response parsing will be added here. Kept as a stub now so the
    Final Diagnosis Agent has a stable place to hand off `llm_input` to
    once this is built.
    """

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise NotImplementedError(
            "Cloud LLM integration is not implemented yet. "
            "See ai-reasoning/README.md -> 'Cloud LLM' / 'Implementation Status'."
        )

    def diagnose(self, llm_input: dict[str, Any]) -> dict[str, Any]:  # pragma: no cover
        raise NotImplementedError("Cloud LLM integration is not implemented yet.")
