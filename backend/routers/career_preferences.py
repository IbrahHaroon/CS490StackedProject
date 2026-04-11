from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.career_preferences import (
    get_career_preferences_by_user,
    update_career_preferences,
)
from database.models.user import User
from schemas import CareerPreferencesResponse, CareerPreferencesUpdate

router = APIRouter()


@router.get("/me", response_model=CareerPreferencesResponse | None)
def get_my_career_preferences(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the career preferences for the current user."""
    return get_career_preferences_by_user(session, current_user.user_id)


@router.put("/me", response_model=CareerPreferencesResponse)
def upsert_my_career_preferences(
    body: CareerPreferencesUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update career preferences for the current user."""
    return update_career_preferences(
        session,
        user_id=current_user.user_id,
        target_roles=body.target_roles,
        location_preferences=body.location_preferences,
        work_mode=body.work_mode,
        salary_preference=body.salary_preference,
    )
