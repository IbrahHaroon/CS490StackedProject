from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.follow_up import (
    create_follow_up,
    delete_follow_up,
    get_follow_up,
    get_follow_ups_by_job,
    update_follow_up,
)
from database.models.job import get_job
from database.models.job_activity import create_job_activity
from database.models.user import User
from schemas import FollowUpCreate, FollowUpResponse, FollowUpUpdate

router = APIRouter()


def _ensure_owns_job(session, job_id: int, current_user: User):
    job = get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return job


@router.post(
    "/jobs/{job_id}/followups",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_up_endpoint(
    job_id: int,
    body: FollowUpCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owns_job(session, job_id, current_user)
    follow_up = create_follow_up(
        session, job_id=job_id, description=body.description, due_date=body.due_date
    )
    due_str = f" (due {body.due_date})" if body.due_date else ""
    create_job_activity(
        session,
        job_id,
        event_type="follow_up",
        notes=f"Follow-up added: {body.description}{due_str}",
    )
    return follow_up


@router.get("/jobs/{job_id}/followups", response_model=list[FollowUpResponse])
def get_job_follow_ups(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owns_job(session, job_id, current_user)
    return get_follow_ups_by_job(session, job_id)


@router.put("/followups/{followup_id}", response_model=FollowUpResponse)
def update_follow_up_endpoint(
    followup_id: int,
    body: FollowUpUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow_up = get_follow_up(session, followup_id)
    if not follow_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found"
        )
    _ensure_owns_job(session, follow_up.job_id, current_user)
    return update_follow_up(
        session,
        followup_id,
        description=body.description,
        due_date=body.due_date,
        completed=body.completed,
    )


@router.delete("/followups/{followup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_follow_up_endpoint(
    followup_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    follow_up = get_follow_up(session, followup_id)
    if not follow_up:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found"
        )
    _ensure_owns_job(session, follow_up.job_id, current_user)
    delete_follow_up(session, followup_id)
