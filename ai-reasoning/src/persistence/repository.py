"""
Persists the outcome of a completed LangGraph workflow run back to
Postgres, closing the loop the class diagram describes: DiagnosisJob
"generates" Hypothesis rows, each linked to the Evidence that supports it
via HypothesisEvidence.

Called from src/consumers/redis_consumer.py right after `run_workflow()`
returns for a job. Failures here are logged and swallowed rather than
raised - a persistence hiccup shouldn't crash the consumer loop or lose
the in-memory diagnosis that was already printed/logged.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import select, update

from src.graph.state import GraphState
from src.persistence.db import diagnosis_jobs, hypotheses, hypothesis_evidence

logger = logging.getLogger("persistence")


def save_diagnosis(session, final_state: GraphState) -> bool:
    """Returns True if the diagnosis was persisted, False if it was
    skipped (e.g. no matching DiagnosisJob row - happens when the workflow
    is run standalone/in tests without the backend having created one)."""
    job_id = final_state.get("job_id")
    diagnosis = final_state.get("diagnosis", {})
    if not job_id or not diagnosis:
        return False

    job_exists = session.scalar(select(diagnosis_jobs.c.job_id).where(diagnosis_jobs.c.job_id == job_id))
    if job_exists is None:
        logger.info("persistence: no DiagnosisJob row for job=%s (running standalone?) - skipping DB write", job_id)
        return False

    try:
        session.execute(
            update(diagnosis_jobs)
            .where(diagnosis_jobs.c.job_id == job_id)
            .values(
                status="COMPLETED",
                aggregate_confidence=diagnosis.get("confidence"),
                root_cause=diagnosis.get("root_cause"),
                recommendations=json.dumps(diagnosis.get("recommendations", [])),
            )
        )

        for h in diagnosis.get("hypotheses", []):
            result = session.execute(
                hypotheses.insert().values(
                    job_id=job_id,
                    rank=h["rank"],
                    description=h["finding"],
                    explanation=h["explanation"],
                    hypothesis_confidence=h["hypothesis_confidence"],
                )
            )
            hypothesis_id = result.inserted_primary_key[0]

            evidence_id = h.get("evidence_id")
            if evidence_id:
                session.execute(
                    hypothesis_evidence.insert().values(
                        hypothesis_id=hypothesis_id,
                        evidence_id=evidence_id,
                        relation="SUPPORTS",
                    )
                )

        session.commit()
        logger.info(
            "persistence: job=%s COMPLETED (%d hypotheses persisted)",
            job_id, len(diagnosis.get("hypotheses", [])),
        )
        return True

    except Exception:  # noqa: BLE001 - never let a persistence bug take down the consumer
        session.rollback()
        logger.exception("persistence: failed to save diagnosis for job=%s", job_id)
        return False
