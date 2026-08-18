"""
Smoke test for the reasoning workflow using synthetic evidence - mirrors
the example in ai-reasoning/README.md -> "LLM Input" / "Final Diagnosis
Output", but built directly (no Redis needed) so the graph wiring and
node logic can be verified in isolation.
"""

from __future__ import annotations

from src.graph.workflow import run_workflow

JOB_ID = "4dcfc8cc-299d-4d7e-ad15-e53e97b6bb94"
TARGET = "x.com"

EVIDENCE = [
    {
        "probe_type": "dns",
        "target": TARGET,
        "status": "ok",
        "message": "DNS resolution completed successfully.",
        "confidence": 100,
        "job_id": JOB_ID,
        "evidence_id": "ev-dns",
    },
    {
        "probe_type": "ping",
        "target": TARGET,
        "status": "ok",
        "message": "Host is reachable using ICMP ping.",
        "confidence": 100,
        "job_id": JOB_ID,
        "evidence_id": "ev-ping",
    },
    {
        "probe_type": "cpu",
        "target": TARGET,
        "status": "ok",
        "message": "CPU utilization is 24.0%.",
        "confidence": 100,
        "job_id": JOB_ID,
        "evidence_id": "ev-cpu",
    },
    {
        "probe_type": "memory",
        "target": TARGET,
        "status": "degraded",
        "message": "Memory utilization is elevated at 81.5%.",
        "confidence": 80,
        "job_id": JOB_ID,
        "evidence_id": "ev-memory",
    },
    {
        "probe_type": "http",
        "target": TARGET,
        "status": "ok",
        "message": "Application returned HTTP 200.",
        "confidence": 100,
        "job_id": JOB_ID,
        "evidence_id": "ev-http",
    },
]


def test_workflow_produces_diagnosis_and_llm_input():
    final_state = run_workflow(job_id=JOB_ID, target=TARGET, evidence=EVIDENCE)

    assert final_state["required_agents"] == ["application", "network", "system"]

    diagnosis = final_state["diagnosis"]
    assert diagnosis["root_cause"] == "Memory utilization is elevated at 81.5%."
    assert 0 < diagnosis["confidence"] <= 1
    assert diagnosis["recommendations"]

    llm_input = final_state["llm_input"]
    assert llm_input["job_id"] == JOB_ID
    assert llm_input["target"] == TARGET
    assert llm_input["required_agents"] == ["application", "network", "system"]
    assert len(llm_input["findings"]) == len(EVIDENCE)
    assert set(llm_input["findings"][0].keys()) == {"agent", "probe", "severity", "finding"}


def test_evidence_agent_drops_findings_without_matching_evidence():
    from src.graph.nodes import evidence_agent

    state = {
        "evidence": [EVIDENCE[0]],
        "network_findings": [
            {
                "agent": "network",
                "probe": "dns",
                "status": "ok",
                "severity": "low",
                "finding": "DNS resolution completed successfully.",
                "confidence": 100,
                "evidence_id": "ev-dns",
            },
            {
                "agent": "network",
                "probe": "ping",
                "status": "ok",
                "severity": "low",
                "finding": "orphaned finding, no matching evidence",
                "confidence": 100,
                "evidence_id": "does-not-exist",
            },
        ],
        "system_findings": [],
        "application_findings": [],
    }

    result = evidence_agent.run(state)
    assert len(result["validated_findings"]) == 1
    assert result["validated_findings"][0]["evidence_id"] == "ev-dns"
