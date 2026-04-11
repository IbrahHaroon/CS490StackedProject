from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models.education import (
    create_education,
    delete_education,
    get_education,
    get_educations_by_user,
    update_education,
)
from schemas import EducationCreate, EducationResponse, EducationUpdate

router = APIRouter()


@router.post("/", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_education_endpoint(
    body: EducationCreate, session: Session = Depends(get_db)
):
    education = create_education(
        session,
        user_id=body.user_id,
        highest_education=body.highest_education,
        degree=body.degree,
        college=body.school_or_college,
        address=body.address.address,
        state=body.address.state,
        zip_code=body.address.zip_code,
        field_of_study=body.field_of_study,
        start_date=body.start_date,
        end_date=body.end_date,
        gpa=body.gpa,
    )
    return education


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
        education_id=education_id,
        highest_education=body.highest_education,
        degree=body.degree,
        school_or_college=body.school_or_college,
        field_of_study=body.field_of_study,
        start_date=body.start_date,
        end_date=body.end_date,
        clear_end_date=body.clear_end_date,
        gpa=body.gpa,
    )
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_education_endpoint(education_id: int, session: Session = Depends(get_db)):
    if not delete_education(session, education_id):
        raise HTTPException(status_code=404, detail="Education record not found")
