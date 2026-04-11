from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models.career_preferences import (
    create_career_preferences,
    delete_career_preferences,
    get_career_preferences_by_user,
    update_career_preferences,
)
from schemas import (
    CareerPreferencesCreate,
    CareerPreferencesResponse,
    CareerPreferencesUpdate,
)

router = APIRouter()


@router.post(
    "/", response_model=CareerPreferencesResponse, status_code=status.HTTP_201_CREATED
)
def create_career_preferences_endpoint(
    body: CareerPreferencesCreate, session: Session = Depends(get_db)
):
    existing = get_career_preferences_by_user(session, body.user_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Career preferences already exist for this user",
        )
    return create_career_preferences(
        session,
        user_id=body.user_id,
        target_roles=body.target_roles,
        location_preferences=body.location_preferences,
        work_mode=body.work_mode,
        salary_preference=body.salary_preference,
    )


@router.get("/user/{user_id}", response_model=CareerPreferencesResponse)
def read_career_preferences(user_id: int, session: Session = Depends(get_db)):
    prefs = get_career_preferences_by_user(session, user_id)
    if not prefs:
        raise HTTPException(status_code=404, detail="Career preferences not found")
    return prefs


@router.put("/user/{user_id}", response_model=CareerPreferencesResponse)
def update_career_preferences_endpoint(
    user_id: int,
    body: CareerPreferencesUpdate,
    session: Session = Depends(get_db),
):
    return update_career_preferences(
        session,
        user_id=user_id,
        target_roles=body.target_roles,
        location_preferences=body.location_preferences,
        work_mode=body.work_mode,
        salary_preference=body.salary_preference,
    )


@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_career_preferences_endpoint(
    user_id: int, session: Session = Depends(get_db)
):
    if not delete_career_preferences(session, user_id):
        raise HTTPException(status_code=404, detail="Career preferences not found")
