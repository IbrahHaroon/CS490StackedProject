from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.profile import (
    create_profile,
    get_profile,
    get_profile_by_user_id,
    update_profile,
)
from database.models.user import User
from schemas import ProfileCreate, ProfileResponse, ProfileUpdate

router = APIRouter()


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile_by_user_id(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    return profile


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
def create_profile_endpoint(
    body: ProfileCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create profile for another user",
        )
    return create_profile(
        session,
        user_id=body.user_id,
        first_name=body.first_name,
        last_name=body.last_name,
        dob=body.dob,
        phone_number=body.phone_number,
        summary=body.summary,
        address_line=body.address_line,
        city=body.city,
        state=body.state,
        zip_code=body.zip_code,
        country=body.country,
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
def read_profile(
    profile_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile(session, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    if profile.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )
    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile_endpoint(
    profile_id: int,
    body: ProfileUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile(session, profile_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )
    if profile.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    for field in (
        "first_name",
        "last_name",
        "dob",
        "phone_number",
        "summary",
        "address_line",
        "city",
        "state",
        "zip_code",
        "country",
    ):
        value = getattr(body, field)
        if value is not None:
            setattr(profile, field, value)

    update_profile(session, profile)
    return get_profile(session, profile_id)
