from __future__ import annotations

import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.database import get_settings
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
    CompanyResearchRequest,
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


@router.post("/{job_id}/research")
def generate_company_research(
    job_id: int,
    body: CompanyResearchRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import openai

    job = get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    settings = get_settings()
    api_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured.",
        )

    job_info = f"Job Title: {job.title}\nCompany: {job.company_name}"
    if job.location:
        job_info += f"\nLocation: {job.location}"
    if job.description:
        job_info += f"\nJob Description:\n{job.description}"

    user_context = (body.context or "").strip()
    system_prompt = (
        "You are a career research assistant. Write comprehensive company research notes "
        "for a job applicant. Cover: company overview, culture and values, recent news, "
        "products/services, what interviewers typically look for, and tips to stand out. "
        "Use plain text with clear section headings."
    )
    user_message = f"Generate company research notes for this application:\n\n{job_info}"
    if user_context:
        user_message += f"\n\nContext from the applicant:\n{user_context}"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        notes = response.choices[0].message.content.strip()
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid OpenAI API key.",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI rate limit reached. Try again shortly.",
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI research failed: {e}",
        )

    updated = update_job(session, job_id, company_research_notes=notes)
    return {"company_research_notes": updated.company_research_notes}
