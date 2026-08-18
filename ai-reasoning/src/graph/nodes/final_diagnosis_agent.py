"""
Final Diagnosis Agent.

Consumes the validated specialist findings and produces the deterministic
final diagnosis. Per the AI Reasoning Layer README, this agent:

* separates healthy findings from problematic ones,
* ranks problematic findings by severity and evidence confidence,
* selects the strongest current root-cause candidate,
* calculates diagnosis confidence,
* generates evidence-backed recommendations,
* produces a structured diagnosis that can later be passed to the Cloud LLM.

No LLM is involved here - everything is deterministic and evidence-backed,
same as the rest of the current pipeline.
"""

from __future__ import annotations

import json
from typing import Any

from src.graph.state import SEVERITY_WEIGHT, GraphState
from src.llm.client import build_llm_input

DEFAULT_RECOMMENDATION = (
    "Continue monitoring the target and collect additional evidence if the problem persists."
)

# Evidence-backed remediation hints per probe. Only used when the probe's
# finding is actually a problem (severity above "low"); kept intentionally
# short/factual - this is not the explanatory layer, that's the Cloud LLM's job.
RECOMMENDATIONS_BY_PROBE: dict[str, str] = {
    "dns": "Verify the DNS record and resolver configuration for the target.",
    "ping": "Check network path/firewall rules between the diagnostics engine and the target.",
    "port": "Confirm the service is listening on the expected port and not blocked by a firewall.",
    "http": "Inspect the application/service logs for the failing HTTP endpoint.",
    "ssl": "Renew or reissue the TLS certificate before it expires.",
    "service": "Investigate the service health endpoint and recent application logs for errors.",
    "cpu": "Investigate processes consuming CPU on the target host, or scale compute resources.",
    "memory": "Investigate memory usage on the target host and consider scaling or restarting the affected process.",
    "disk": "Free up disk space on the affected mount or provision additional storage.",
}


def _rank(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda f: (SEVERITY_WEIGHT.get(f["severity"], 0), f.get("confidence", 0)),
        reverse=True,
    )


def _confidence(root: dict[str, Any], all_findings: list[dict[str, Any]]) -> float:
    """Root-cause confidence: how much of the total evidence "weight" points
    at the root candidate, scaled by how confident we are in that evidence.

    A single clear problem among mostly-healthy findings scores high; a
    problem that's one of several competing issues (or backed by low-
    confidence evidence) scores lower - reflecting genuine ambiguity rather
    than false precision.
    """
    total_weight = sum(SEVERITY_WEIGHT.get(f["severity"], 0) for f in all_findings)
    if total_weight == 0:
        return 0.0

    root_weight = SEVERITY_WEIGHT.get(root["severity"], 0)
    evidence_confidence = root.get("confidence", 0) / 100

    return round((root_weight / total_weight) * evidence_confidence, 2)


def _recommendations(problems: list[dict[str, Any]]) -> list[str]:
    if not problems:
        return [DEFAULT_RECOMMENDATION]

    recs: list[str] = []
    for finding in problems:
        rec = RECOMMENDATIONS_BY_PROBE.get(finding["probe"])
        if rec and rec not in recs:
            recs.append(rec)

    return recs or [DEFAULT_RECOMMENDATION]


def run(state: GraphState) -> dict:
    validated_findings = state.get("validated_findings", [])

    healthy = [f for f in validated_findings if f["severity"] == "low"]
    problems = _rank([f for f in validated_findings if f["severity"] != "low"])

    if problems:
        root = problems[0]
        root_cause = root["finding"]
        confidence = _confidence(root, validated_findings)
    else:
        root = None
        root_cause = "No significant issues detected."
        confidence = round(len(healthy) / len(validated_findings), 2) if validated_findings else 0.0

    diagnosis = {
        "job_id": state.get("job_id"),
        "target": state.get("target"),
        "root_cause": root_cause,
        "confidence": confidence,
        "recommendations": _recommendations(problems),
        "hypotheses": [
            {
                "agent": f["agent"],
                "probe": f["probe"],
                "finding": f["finding"],
                "severity": f["severity"],
                "confidence": f.get("confidence", 0),
            }
            for f in problems
        ],
        "healthy_findings_count": len(healthy),
    }

    # --- LLM input ---------------------------------------------------
    # Standardized, LLM-ready payload built from the validated findings
    # (not the raw diagnostic evidence) - see ai-reasoning/README.md ->
    # "LLM Input". The Cloud LLM itself isn't wired up yet (next phase),
    # so we just build the payload here for now.
    llm_input = build_llm_input(state, validated_findings)

    # TEMPORARY: print the exact payload that will be sent to the Cloud LLM
    # once that integration lands, so it can be inspected/verified during
    # development. Remove this print once llm/client.py actually calls out
    # to the LLM.
    print("\n[final_diagnosis_agent] LLM input (temporary debug print):")
    print(json.dumps(llm_input, indent=2, default=str))
    print()

    return {"diagnosis": diagnosis, "llm_input": llm_input}
