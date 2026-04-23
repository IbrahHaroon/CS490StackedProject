from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.job import (
    PIPELINE_STAGES,
    create_job,
    delete_job,
    get_job,
    get_jobs_for_user,
    update_job,
)
from database.models.job_activity import create_job_activity, get_job_activities
from database.models.user import User
from schemas import (
    JobActivityResponse,
    JobCreate,
    JobResponse,
    JobUpdate,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Job CRUD (scoped to the authenticated user)                                  #
# --------------------------------------------------------------------------- #


@router.get("/dashboard", response_model=list[JobResponse])
def get_dashboard(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all jobs for the currently authenticated user."""
    return get_jobs_for_user(session, current_user.user_id)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job_endpoint(
    body: JobCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.stage not in PIPELINE_STAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}",
        )

    # Default application_date to today when the user is creating an Applied+ stage
    application_date = body.application_date
    if application_date is None and body.stage in (
        "Applied",
        "Interview",
        "Offer",
        "Rejected",
        "Accepted",
        "Withdrawn",
    ):
        application_date = date.today()

    job = create_job(
        session,
        user_id=current_user.user_id,
        title=body.title,
        company_name=body.company_name,
        location=body.location,
        source_url=body.source_url,
        description=body.description,
        stage=body.stage,
        application_date=application_date,
        deadline=body.deadline,
        priority=body.priority,
        salary=body.salary,
        years_of_experience=body.years_of_experience,
        notes=body.notes,
    )
    create_job_activity(session, job.job_id, to_stage=body.stage, notes="created")
    return job


@router.get("/{job_id}", response_model=JobResponse)
def read_job(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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


@router.put("/{job_id}", response_model=JobResponse)
def update_job_endpoint(
    job_id: int,
    body: JobUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if body.stage is not None and body.stage not in PIPELINE_STAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}",
        )

    previous_stage = job.stage
    updated = update_job(
        session,
        job_id,
        title=body.title,
        company_name=body.company_name,
        location=body.location,
        source_url=body.source_url,
        description=body.description,
        stage=body.stage,
        application_date=body.application_date,
        deadline=body.deadline,
        priority=body.priority,
        salary=body.salary,
        years_of_experience=body.years_of_experience,
        notes=body.notes,
        company_research_notes=body.company_research_notes,
        outcome_notes=body.outcome_notes,
    )
    if body.stage is not None and body.stage != previous_stage:
        create_job_activity(
            session,
            job_id,
            from_stage=previous_stage,
            to_stage=body.stage,
        )
    return updated


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_endpoint(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    delete_job(session, job_id)


@router.get("/{job_id}/activity", response_model=list[JobActivityResponse])
def get_activity(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_job(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return get_job_activities(session, job_id)
