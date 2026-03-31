from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import (
    PIPELINE_STAGES,
    create_applied_jobs,
    delete_applied_job,
    get_all_applied_jobs,
    get_applied_jobs,
    update_applied_job,
)
from database.models.job_activity import create_job_activity, get_job_activities
from database.models.position import create_position, get_all_positions, get_position
from database.models.user import User
from schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    JobActivityResponse,
    PositionCreate,
    PositionResponse,
    PositionWithCompanyResponse,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Positions                                                                    #
# --------------------------------------------------------------------------- #


@router.get("/positions/", response_model=list[PositionWithCompanyResponse])
def read_all_positions(session: Session = Depends(get_db)):
    positions = get_all_positions(session)
    result = []
    for p in positions:
        result.append(PositionWithCompanyResponse(
            position_id=p.position_id,
            company_id=p.company_id,
            company_name=p.company.name if p.company else "Unknown",
            title=p.title,
            listing_date=p.listing_date,
            salary=p.salary,
            education_req=p.education_req,
            experience_req=p.experience_req,
            description=p.description,
        ))
    return result


@router.post(
    "/positions/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED
)
def create_position_endpoint(body: PositionCreate, session: Session = Depends(get_db)):
    return create_position(
        session,
        company_id=body.company_id,
        title=body.title,
        salary=body.salary,
        education_req=body.education_req,
        experience_req=body.experience_req,
        description=body.description,
        listing_date=body.listing_date,
    )


@router.get("/positions/{position_id}", response_model=PositionResponse)
def read_position(position_id: int, session: Session = Depends(get_db)):
    position = get_position(session, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    return position


# --------------------------------------------------------------------------- #
#  Applications                                                                 #
# --------------------------------------------------------------------------- #


@router.get("/dashboard", response_model=list[ApplicationResponse])
def get_dashboard(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all job applications for the currently authenticated user."""
    return list(get_all_applied_jobs(session, current_user.user_id))


@router.get("/applications/{user_id}", response_model=list[ApplicationResponse])
def read_applications(user_id: int, session: Session = Depends(get_db)):
    return list(get_all_applied_jobs(session, user_id))


@router.post(
    "/applications/",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def apply_for_job(body: ApplicationCreate, session: Session = Depends(get_db)):
    job = create_applied_jobs(
        session, body.user_id, body.position_id, body.years_of_experience
    )
    create_job_activity(session, job.job_id, "Interested")
    return job


@router.put("/applications/{job_id}", response_model=ApplicationResponse)
def update_application(
    job_id: int,
    body: ApplicationUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if (
        body.application_status is not None
        and body.application_status not in PIPELINE_STAGES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}",
        )
    if body.application_status is not None:
        create_job_activity(session, job_id, body.application_status)
    updated = update_applied_job(
        session,
        job_id,
        application_status=body.application_status,
        years_of_experience=body.years_of_experience,
    )
    return updated


@router.delete("/applications/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if job.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    # Record withdrawal in history before deleting (delete_applied_job will
    # then purge job_activity rows to satisfy the FK constraint)
    create_job_activity(session, job_id, "Withdrawn")
    delete_applied_job(session, job_id)


@router.get("/applications/{job_id}/activity", response_model=list[JobActivityResponse])
def get_application_activity(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the stage history for a job application."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return get_job_activities(session, job_id)
