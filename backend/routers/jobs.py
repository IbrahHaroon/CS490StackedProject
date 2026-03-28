from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database.models.user import User
from database.models.applied_jobs import get_all_applied_jobs, create_applied_jobs, get_applied_jobs, update_applied_job
from database.models.position import create_position, get_position
from database.auth import get_current_user
from schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate, PositionCreate, PositionResponse

router = APIRouter()


# --------------------------------------------------------------------------- #
#  Positions                                                                    #
# --------------------------------------------------------------------------- #

@router.post("/positions/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Position not found")
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


@router.post("/applications/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_for_job(body: ApplicationCreate, session: Session = Depends(get_db)):
    return create_applied_jobs(session, body.user_id, body.position_id, body.years_of_experience)


@router.put("/applications/{job_id}", response_model=ApplicationResponse)
def update_application(
    job_id: int,
    body: ApplicationUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    if job.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    updated = update_applied_job(
        session, job_id,
        application_status=body.application_status,
        years_of_experience=body.years_of_experience,
    )
    return updated
