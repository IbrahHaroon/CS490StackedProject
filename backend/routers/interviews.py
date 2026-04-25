from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.interview import (
    create_interview,
    delete_interview,
    get_interview,
    get_interviews_by_job,
    update_interview,
)
from database.models.job import get_job
from database.models.job_activity import create_job_activity
from database.models.user import User
from schemas import InterviewCreate, InterviewResponse, InterviewUpdate

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
    "/jobs/{job_id}/interviews",
    response_model=InterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_interview_endpoint(
    job_id: int,
    body: InterviewCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owns_job(session, job_id, current_user)
    interview = create_interview(
        session,
        job_id=job_id,
        round_type=body.round_type,
        scheduled_at=body.scheduled_at,
        interviewer=body.interviewer,
        mode=body.mode,
        prep_notes=body.prep_notes,
        notes=body.notes,
    )
    dt_str = body.scheduled_at.strftime("%b %d, %Y %I:%M %p")
    create_job_activity(
        session,
        job_id,
        event_type="interview",
        notes=f"Interview scheduled: {body.round_type} — {dt_str}",
    )
    return interview


@router.get("/jobs/{job_id}/interviews", response_model=list[InterviewResponse])
def get_job_interviews(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_owns_job(session, job_id, current_user)
    return get_interviews_by_job(session, job_id)


@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview_endpoint(
    interview_id: int,
    body: InterviewUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = get_interview(session, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    _ensure_owns_job(session, interview.job_id, current_user)
    return update_interview(
        session,
        interview_id,
        round_type=body.round_type,
        scheduled_at=body.scheduled_at,
        interviewer=body.interviewer,
        mode=body.mode,
        prep_notes=body.prep_notes,
        notes=body.notes,
    )


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview_endpoint(
    interview_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    interview = get_interview(session, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    _ensure_owns_job(session, interview.job_id, current_user)
    delete_interview(session, interview_id)
