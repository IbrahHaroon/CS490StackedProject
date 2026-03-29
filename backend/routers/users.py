from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from database.models.user import get_user
from schemas import UserResponse

router = APIRouter()


@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, session: Session = Depends(get_db)):
    user = get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
