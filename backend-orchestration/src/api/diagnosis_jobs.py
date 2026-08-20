from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.core.database import get_db
from src.models.target import Target
from src.models.user import User
from src.schemas.diagnosis_job import DiagnosisJobCreateRequest, DiagnosisJobDetailResponse, DiagnosisJobResponse
from src.schemas.evidence import EvidenceResponse
from src.schemas.hypothesis import HypothesisResponse
from src.services import job_service
from src.services.job_service import JobNotFoundError, TargetNotFoundError
from src.websocket.job_status import notify_job_status

router = APIRouter(prefix="/api/diagnosis-jobs", tags=["diagnosis-jobs"])


@router.post("", response_model=DiagnosisJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_diagnosis_job(
    payload: DiagnosisJobCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Creates the job row (status=QUEUED) and returns immediately - probe
    execution happens in the background. Poll GET /{job_id} or use the
    WebSocket at /ws/jobs/{job_id} for status updates."""
    try:
        job = job_service.create_diagnosis_job(db, current_user.user_id, payload.target_id, payload.probes, payload.ports, payload.http_url)
    except TargetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")

    target = db.get(Target, payload.target_id)
    background_tasks.add_task(
        _run_and_notify, job.job_id, target.identifier, payload.probes, payload.ports, payload.http_url
    )
    return job_service.to_job_response(job)


def _run_and_notify(job_id: str, target_identifier: str, probes, ports, http_url) -> None:
    job_service.run_job_in_background(job_id, target_identifier, probes, ports, http_url)
    notify_job_status(job_id)


@router.get("", response_model=list[DiagnosisJobResponse])
def list_diagnosis_jobs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Admins see every job (needed for the approval queue); regular users see their own.
    user_filter = None if current_user.role == "ADMIN" else current_user.user_id
    jobs = job_service.list_jobs(db, user_id=user_filter)
    return [job_service.to_job_response(j) for j in jobs]


@router.get("/{job_id}", response_model=DiagnosisJobDetailResponse)
def get_diagnosis_job(job_id: str, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    try:
        job = job_service.get_job_with_details(db, job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis job not found")
    return job_service.to_job_detail_response(job)


@router.get("/{job_id}/evidence", response_model=list[EvidenceResponse])
def get_job_evidence(job_id: str, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    try:
        job = job_service.get_job_with_details(db, job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis job not found")
    return list(job.evidence)


@router.get("/{job_id}/hypotheses", response_model=list[HypothesisResponse])
def get_job_hypotheses(job_id: str, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    try:
        job = job_service.get_job_with_details(db, job_id)
    except JobNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnosis job not found")
    return sorted(job.hypotheses, key=lambda h: h.rank)
