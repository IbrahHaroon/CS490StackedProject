from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import get_applied_jobs
from database.models.interview import (
    create_interview,
    delete_interview,
    get_interview,
    get_interviews_for_job,
    update_interview,
)
from database.models.user import User
from schemas import InterviewCreate, InterviewResponse, InterviewUpdate

router = APIRouter()


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
    """Create a new interview for a job."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return create_interview(
        session,
        job_id=job_id,
        round_type=body.round_type,
        date_time=body.date_time,
        notes=body.notes,
    )


@router.get("/jobs/{job_id}/interviews", response_model=list[InterviewResponse])
def get_job_interviews(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all interviews for a job."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return get_interviews_for_job(session, job_id)


@router.put("/interviews/{interview_id}", response_model=InterviewResponse)
def update_interview_endpoint(
    interview_id: int,
    body: InterviewUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing interview."""
    interview = get_interview(session, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )

    job = get_applied_jobs(session, interview.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    updated = update_interview(
        session,
        interview_id,
        round_type=body.round_type,
        date_time=body.date_time,
        notes=body.notes,
    )
    return updated


@router.delete("/interviews/{interview_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_interview_endpoint(
    interview_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an interview."""
    interview = get_interview(session, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )

    job = get_applied_jobs(session, interview.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    delete_interview(session, interview_id)
