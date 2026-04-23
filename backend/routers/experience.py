from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models.experience import (
    create_experience,
    delete_experience,
    get_experience,
    get_experiences_by_user,
    update_experience,
)
from schemas import ExperienceCreate, ExperienceResponse, ExperienceUpdate

router = APIRouter()


@router.post(
    "/", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED
)
def create_experience_endpoint(
    body: ExperienceCreate, session: Session = Depends(get_db)
):
    return create_experience(
        session,
        user_id=body.user_id,
        company=body.company,
        title=body.title,
        start_date=body.start_date,
        end_date=body.end_date,
        description=body.description,
        sort_order=body.sort_order,
        location=body.location,
    )


@router.get("/user/{user_id}", response_model=list[ExperienceResponse])
def read_experiences_by_user(user_id: int, session: Session = Depends(get_db)):
    return get_experiences_by_user(session, user_id)


@router.get("/{experience_id}", response_model=ExperienceResponse)
def read_experience(experience_id: int, session: Session = Depends(get_db)):
    experience = get_experience(session, experience_id)
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return experience


@router.put("/{experience_id}", response_model=ExperienceResponse)
def update_experience_endpoint(
    experience_id: int,
    body: ExperienceUpdate,
    session: Session = Depends(get_db),
):
    experience = update_experience(
        session,
        experience_id=experience_id,
        company=body.company,
        title=body.title,
        start_date=body.start_date,
        end_date=body.end_date,
        clear_end_date=body.clear_end_date,
        description=body.description,
        sort_order=body.sort_order,
        location=body.location,
    )
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return experience


@router.delete("/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experience_endpoint(experience_id: int, session: Session = Depends(get_db)):
    if not delete_experience(session, experience_id):
        raise HTTPException(status_code=404, detail="Experience not found")
