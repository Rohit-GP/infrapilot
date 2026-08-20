from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import require_admin
from src.core.database import get_db
from src.models.user import User
from src.schemas.approval import ApprovalDecisionCreateRequest, ApprovalDecisionResponse
from src.services import approval_service
from src.services.approval_service import JobNotFoundError

router = APIRouter(prefix="/api/diagnosis-jobs/{job_id}/approval", tags=["approval"])


@router.post("", response_model=ApprovalDecisionResponse, status_code=status.HTTP_201_CREATED)
def create_approval_decision(
    job_id: str,
    payload: ApprovalDecisionCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    """Admin-only. Records approve/reject for a job's suggested remediation
    action - see class diagram's User.makeApprovalDecision()."""
    try:
        decision = approval_service.make_approval_decision(
            db, job_id, current_admin.user_id, payload.decision, payload.remediation_action
        )
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis job not found")
    return decision


@router.get("", response_model=list[ApprovalDecisionResponse])
def list_approval_decisions(job_id: str, db: Session = Depends(get_db), _current_admin: User = Depends(require_admin)):
    return approval_service.list_decisions_for_job(db, job_id)
