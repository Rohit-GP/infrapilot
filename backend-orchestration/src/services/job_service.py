"""
Job service: implements the DiagnosisJob lifecycle from the class diagram
(`start()/complete()/fail()/addEvidence()`) as functions operating on the
ORM model, plus `create_diagnosis_job()` (the class diagram's
`User.createDiagnosisJob()`).

Lifecycle:

    QUEUED -> RUNNING -> AWAITING_DIAGNOSIS -> COMPLETED
                      |-> FAILED               (stays AWAITING_DIAGNOSIS
                                                 if the AI reasoning layer
                                                 hasn't run yet)

This service only ever moves a job as far as AWAITING_DIAGNOSIS - COMPLETED
is set by the AI Reasoning Layer once it persists a final diagnosis (see
ai-reasoning/src/persistence/repository.py), since that's the layer that
actually knows the outcome.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.core.database import SessionLocal
from src.models.diagnosis_job import DiagnosisJob, JobStatus
from src.models.evidence import Evidence
from src.models.hypothesis import Hypothesis
from src.models.target import Target
from src.schemas.diagnosis_job import DiagnosisJobDetailResponse, DiagnosisJobResponse
from src.services.probe_trigger import ProbeTriggerError, run_probes

logger = logging.getLogger("job_service")


class TargetNotFoundError(Exception):
    pass


class JobNotFoundError(Exception):
    pass


def create_diagnosis_job(
    db: Session,
    user_id: int,
    target_id: int,
    probes: list[str] | None = None,
    ports: list[int] | None = None,
    http_url: str | None = None,
) -> DiagnosisJob:
    """User.createDiagnosisJob(target) - creates the row and returns
    immediately with status QUEUED. Probe execution happens afterwards,
    kicked off by the caller via `run_job_in_background`."""
    target = db.get(Target, target_id)
    if target is None:
        raise TargetNotFoundError(target_id)

    job = DiagnosisJob(user_id=user_id, target_id=target_id, status=JobStatus.QUEUED.value)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def run_job_in_background(job_id: str, target_identifier: str, probes: list[str] | None, ports: list[int] | None, http_url: str | None) -> None:
    """Entry point for FastAPI's BackgroundTasks. Opens its own DB session
    since the request's session is closed by the time this runs."""
    db = SessionLocal()
    try:
        job = db.get(DiagnosisJob, job_id)
        if job is None:
            logger.error("run_job_in_background: job %s vanished before probes started", job_id)
            return

        _start(db, job)

        try:
            result = run_probes(job_id, target_identifier, probes, ports, http_url)
        except ProbeTriggerError as exc:
            _fail(db, job, str(exc))
            return

        _add_evidence(db, job, result.evidence)
        # Evidence is collected and already published to Redis by the
        # diagnostics engine (--publish) - now waiting on the AI reasoning
        # layer to consume it and write back a diagnosis.
        job.status = JobStatus.AWAITING_DIAGNOSIS.value
        db.commit()
    finally:
        db.close()


def _start(db: Session, job: DiagnosisJob) -> None:
    job.status = JobStatus.RUNNING.value
    db.commit()


def _fail(db: Session, job: DiagnosisJob, error_message: str) -> None:
    job.status = JobStatus.FAILED.value
    job.error_message = error_message
    db.commit()


def _add_evidence(db: Session, job: DiagnosisJob, evidence_items: list[dict]) -> None:
    for ev in evidence_items:
        db.add(
            Evidence(
                evidence_id=ev["evidence_id"],
                job_id=job.job_id,
                probe_type=ev["probe_type"],
                observed_result=ev.get("message") or "",
                result_status=ev["status"],
                latency_ms=ev.get("latency_ms"),
                evidence_confidence=ev.get("confidence", 0),
                raw_data=ev.get("raw"),
            )
        )
    db.commit()


def get_job(db: Session, job_id: str) -> DiagnosisJob:
    job = db.get(DiagnosisJob, job_id)
    if job is None:
        raise JobNotFoundError(job_id)
    return job


def get_job_with_details(db: Session, job_id: str) -> DiagnosisJob:
    job = db.scalar(
        select(DiagnosisJob)
        .where(DiagnosisJob.job_id == job_id)
        .options(selectinload(DiagnosisJob.evidence), selectinload(DiagnosisJob.hypotheses).selectinload(Hypothesis.evidence_links))
    )
    if job is None:
        raise JobNotFoundError(job_id)
    return job


def list_jobs(db: Session, user_id: int | None = None, limit: int = 50) -> list[DiagnosisJob]:
    stmt = select(DiagnosisJob).order_by(DiagnosisJob.created_at.desc()).limit(limit)
    if user_id is not None:
        stmt = stmt.where(DiagnosisJob.user_id == user_id)
    return list(db.scalars(stmt))


def to_job_response(job: DiagnosisJob) -> DiagnosisJobResponse:
    recommendations = json.loads(job.recommendations) if job.recommendations else None
    return DiagnosisJobResponse(
        job_id=job.job_id,
        user_id=job.user_id,
        target_id=job.target_id,
        status=job.status,
        created_at=job.created_at,
        aggregate_confidence=job.aggregate_confidence,
        root_cause=job.root_cause,
        recommendations=recommendations,
        error_message=job.error_message,
    )


def to_job_detail_response(job: DiagnosisJob) -> DiagnosisJobDetailResponse:
    base = to_job_response(job)
    return DiagnosisJobDetailResponse(**base.model_dump(), evidence=list(job.evidence), hypotheses=list(job.hypotheses))
