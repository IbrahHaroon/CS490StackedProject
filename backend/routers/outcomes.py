from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import get_applied_jobs
from database.models.job_activity import create_job_activity
from database.models.outcome import (
    OUTCOME_STATES,
    create_outcome,
    delete_outcome,
    get_outcome,
    get_outcome_by_job,
    update_outcome,
)
from database.models.user import User
from schemas import OutcomeCreate, OutcomeResponse, OutcomeUpdate

router = APIRouter()


@router.post(
    "/jobs/{job_id}/outcome",
    response_model=OutcomeResponse,
    status_code=status.HTTP_201_CREATED,
)
def set_job_outcome(
    job_id: int,
    body: OutcomeCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set or create outcome for a job application."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if body.outcome_state not in OUTCOME_STATES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid outcome_state. Must be one of: {OUTCOME_STATES}",
        )

    # Check if outcome already exists for this job
    existing = get_outcome_by_job(session, job_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Outcome already exists for this job. Use PUT to update.",
        )

    result = create_outcome(
        session,
        job_id=job_id,
        outcome_state=body.outcome_state,
        outcome_notes=body.outcome_notes,
    )
    notes_str = f" — {body.outcome_notes}" if body.outcome_notes else ""
    create_job_activity(
        session,
        job_id=job_id,
        stage="Outcome Recorded",
        event_type="outcome",
        notes=f"{body.outcome_state}{notes_str}",
    )
    return result


@router.get("/jobs/{job_id}/outcome", response_model=OutcomeResponse)
def get_job_outcome(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve outcome for a job application."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    outcome = get_outcome_by_job(session, job_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outcome not found"
        )
    return outcome


@router.put("/outcome/{outcome_id}", response_model=OutcomeResponse)
def update_job_outcome(
    outcome_id: int,
    body: OutcomeUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing outcome."""
    outcome = get_outcome(session, outcome_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outcome not found"
        )

    job = get_applied_jobs(session, outcome.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    if body.outcome_state and body.outcome_state not in OUTCOME_STATES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid outcome_state. Must be one of: {OUTCOME_STATES}",
        )

    updated = update_outcome(
        session,
        outcome_id,
        outcome_state=body.outcome_state,
        outcome_notes=body.outcome_notes,
    )
    return updated


@router.delete("/outcome/{outcome_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_outcome(
    outcome_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an outcome."""
    outcome = get_outcome(session, outcome_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Outcome not found"
        )

    job = get_applied_jobs(session, outcome.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    delete_outcome(session, outcome_id)
