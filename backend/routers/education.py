from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database.models.education import create_education, get_education
from schemas import EducationCreate, EducationResponse

router = APIRouter()


@router.post("/", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_education_endpoint(body: EducationCreate, session: Session = Depends(get_db)):
    education = create_education(
        session,
        user_id=body.user_id,
        highest_education=body.highest_education,
        degree=body.degree,
        college=body.school_or_college,
        address=body.address.address,
        state=body.address.state,
        zip_code=body.address.zip_code,
    )
    return education


@router.get("/{education_id}", response_model=EducationResponse)
def read_education(education_id: int, session: Session = Depends(get_db)):
    education = get_education(session, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education
