from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.core.database import get_db
from src.models.target import Target
from src.models.user import User
from src.schemas.target import TargetCreateRequest, TargetResponse

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.post("", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
def create_target(payload: TargetCreateRequest, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    target = Target(name=payload.name, identifier=payload.identifier, type=payload.type)
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("", response_model=list[TargetResponse])
def list_targets(db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    return list(db.scalars(select(Target).order_by(Target.target_id)))


@router.get("/{target_id}", response_model=TargetResponse)
def get_target(target_id: int, db: Session = Depends(get_db), _current_user: User = Depends(get_current_user)):
    target = db.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    return target
