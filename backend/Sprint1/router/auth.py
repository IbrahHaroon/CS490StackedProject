from fastapi import APIRouter, Depends
from dependencies.auth import get_current_user

router = APIRouter()


# Assuming a User model exists, but not implemented for brevity
# def get_user_by_username(db: Session, username: str):
#     return db.query(User).filter(User.username == username).first()


@router.get("/auth-status")
async def auth_status(current_user=Depends(get_current_user)):
    return {"status": "supabase auth active", "user_id": current_user.id}
