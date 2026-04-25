from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.education import (
    create_education,
    delete_education,
    get_education,
    get_educations_by_user,
    update_education,
)
from database.models.user import User
from schemas import EducationCreate, EducationResponse, EducationUpdate

router = APIRouter()


@router.post("/", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_education_endpoint(
    body: EducationCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create education for another user",
        )
    return create_education(
        session,
        user_id=body.user_id,
        school=body.school,
        degree=body.degree,
        field_of_study=body.field_of_study,
        start_date=body.start_date,
        end_date=body.end_date,
        gpa=body.gpa,
        school_location=body.school_location,
        sort_order=body.sort_order,
    )


@router.get("/user/{user_id}", response_model=list[EducationResponse])
def read_educations_by_user(user_id: int, session: Session = Depends(get_db)):
    return get_educations_by_user(session, user_id)


@router.get("/{education_id}", response_model=EducationResponse)
def read_education(education_id: int, session: Session = Depends(get_db)):
    education = get_education(session, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education


@router.put("/{education_id}", response_model=EducationResponse)
def update_education_endpoint(
    education_id: int,
    body: EducationUpdate,
    session: Session = Depends(get_db),
):
    education = update_education(
        session,
        education_id,
        school=body.school,
        degree=body.degree,
        field_of_study=body.field_of_study,
        start_date=body.start_date,
        end_date=body.end_date,
        clear_end_date=body.clear_end_date,
        gpa=body.gpa,
        school_location=body.school_location,
        sort_order=body.sort_order,
    )
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education_endpoint(education_id: int, session: Session = Depends(get_db)):
    if not delete_education(session, education_id):
        raise HTTPException(status_code=404, detail="Education record not found")
