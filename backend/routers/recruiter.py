from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_recruiter, get_current_user
from database.models.applied_jobs import (
    PIPELINE_STAGES,
    get_applied_jobs,
    update_applied_job,
)
from database.models.job_activity import create_job_activity
from database.models.position import (
    LOCATION_TYPES,
    Position,
    create_position,
    delete_position,
    get_position,
    update_position,
)
from database.models.recruiter import (
    Recruiter,
    create_recruiter,
    get_recruiter_by_user_id,
    update_recruiter,
)
from database.models.user import User
from schemas import (
    ApplicationResponse,
    JobActivityResponse,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
    RecruiterActivityCreate,
    RecruiterApplicationStatusUpdate,
    RecruiterCreate,
    RecruiterResponse,
    RecruiterUpdate,
)

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Recruiter Profile                                                            #
# --------------------------------------------------------------------------- #


@router.post("/", response_model=RecruiterResponse, status_code=status.HTTP_201_CREATED)
def create_recruiter_profile(
    body: RecruiterCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create recruiter profile for another user",
        )
    existing = get_recruiter_by_user_id(session, current_user.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recruiter profile already exists",
        )
    return create_recruiter(
        session,
        user_id=body.user_id,
        company_id=body.company_id,
        first_name=body.first_name,
        last_name=body.last_name,
        job_title=body.job_title,
    )


@router.get("/me", response_model=RecruiterResponse)
def get_my_recruiter_profile(
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    return current_recruiter


@router.put("/me", response_model=RecruiterResponse)
def update_my_recruiter_profile(
    body: RecruiterUpdate,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    if body.first_name is not None:
        current_recruiter.first_name = body.first_name
    if body.last_name is not None:
        current_recruiter.last_name = body.last_name
    if body.job_title is not None:
        current_recruiter.job_title = body.job_title
    update_recruiter(session, current_recruiter)
    return get_recruiter_by_user_id(session, current_recruiter.user_id)


# --------------------------------------------------------------------------- #
#  Position Management                                                          #
# --------------------------------------------------------------------------- #


@router.get("/positions/", response_model=list[PositionResponse])
def list_company_positions(
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    positions = (
        session.execute(
            select(Position).where(Position.company_id == current_recruiter.company_id)
        )
        .scalars()
        .all()
    )
    return list(positions)


@router.post(
    "/positions/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED
)
def create_company_position(
    body: PositionCreate,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    if body.location_type is not None and body.location_type not in LOCATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid location_type. Must be one of: {LOCATION_TYPES}",
        )
    return create_position(
        session,
        company_id=current_recruiter.company_id,
        title=body.title,
        salary=body.salary,
        education_req=body.education_req,
        experience_req=body.experience_req,
        description=body.description,
        listing_date=body.listing_date,
        location=body.location,
        location_type=body.location_type,
    )


@router.put("/positions/{position_id}", response_model=PositionResponse)
def update_company_position(
    position_id: int,
    body: PositionUpdate,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    position = get_position(session, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    if position.company_id != current_recruiter.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if body.location_type is not None and body.location_type not in LOCATION_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid location_type. Must be one of: {LOCATION_TYPES}",
        )
    if body.title is not None:
        position.title = body.title
    if body.listing_date is not None:
        position.listing_date = body.listing_date
    if body.salary is not None:
        position.salary = body.salary
    if body.education_req is not None:
        position.education_req = body.education_req
    if body.experience_req is not None:
        position.experience_req = body.experience_req
    if body.description is not None:
        position.description = body.description
    if body.location_type is not None:
        position.location_type = body.location_type
    if body.location is not None:
        position.location = body.location
    if not update_position(session, position):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update position",
        )
    return get_position(session, position_id)


@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company_position(
    position_id: int,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    position = get_position(session, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    if position.company_id != current_recruiter.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    delete_position(session, position_id)


# --------------------------------------------------------------------------- #
#  Application Evaluation                                                       #
# --------------------------------------------------------------------------- #


@router.get(
    "/positions/{position_id}/applications",
    response_model=list[ApplicationResponse],
)
def list_position_applications(
    position_id: int,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    position = get_position(session, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Position not found"
        )
    if position.company_id != current_recruiter.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    from database.models.applied_jobs import AppliedJobs

    rows = (
        session.execute(
            select(AppliedJobs).where(AppliedJobs.position_id == position_id)
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.put("/applications/{job_id}/status", response_model=ApplicationResponse)
def update_application_status(
    job_id: int,
    body: RecruiterApplicationStatusUpdate,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    position = get_position(session, job.position_id)
    if position.company_id != current_recruiter.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    if body.application_status not in PIPELINE_STAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid stage. Must be one of: {PIPELINE_STAGES}",
        )
    create_job_activity(session, job_id, body.application_status)
    return update_applied_job(
        session,
        job_id,
        application_status=body.application_status,
        outcome_notes=body.outcome_notes,
    )


@router.post(
    "/applications/{job_id}/activity",
    response_model=JobActivityResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_application_activity(
    job_id: int,
    body: RecruiterActivityCreate,
    session: Session = Depends(get_db),
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Application not found"
        )
    position = get_position(session, job.position_id)
    if position.company_id != current_recruiter.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return create_job_activity(
        session,
        job_id=job_id,
        stage=job.application_status,
        event_type=body.event_type,
        notes=body.notes,
    )
