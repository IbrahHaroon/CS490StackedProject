from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/auth-status")
async def auth_status(current_user=Depends(get_current_user)):
    return {
        "status": "supabase auth active",
        "user_id": current_user.id,
    }
