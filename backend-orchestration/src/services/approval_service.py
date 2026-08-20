"""
Approval service: implements the class diagram's
`User.makeApprovalDecision(job, decision)` and
`ApprovalDecision.approve()/reject()/isApproved()`.

This is the "safety-gate" module from the backend README: a DiagnosisJob's
recommendations are only ever suggestions until an admin explicitly
approves (or rejects) a remediation action here. Nothing in this codebase
actually executes remediation - persisting the decision is the full scope
of the safety gate for this prototype.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.approval_decision import ApprovalDecision
from src.models.diagnosis_job import DiagnosisJob


class JobNotFoundError(Exception):
    pass


def make_approval_decision(db: Session, job_id: str, user_id: int, decision: str, remediation_action: str) -> ApprovalDecision:
    job = db.get(DiagnosisJob, job_id)
    if job is None:
        raise JobNotFoundError(job_id)

    approval = ApprovalDecision(
        job_id=job_id,
        user_id=user_id,
        decision=decision,  # "APPROVED" | "REJECTED"
        remediation_action=remediation_action,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)
    return approval


def list_decisions_for_job(db: Session, job_id: str) -> list[ApprovalDecision]:
    stmt = select(ApprovalDecision).where(ApprovalDecision.job_id == job_id).order_by(ApprovalDecision.timestamp.desc())
    return list(db.scalars(stmt))
