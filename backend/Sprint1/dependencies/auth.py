from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import supabase

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Any:
    """
    Dependency to get the current authenticated user.

    Returns a dict with user info including token.
    Raises HTTPException if authentication fails.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "detail": "Invalid or missing authentication token"},
        )
    token = credentials.credentials

    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase client not configured",
        )

    try:
        result = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "detail": "Invalid or missing authentication token"},
        )

    user = None
    if hasattr(result, "user") and result.user:
        user = result.user
    elif hasattr(result, "data"):
        data = result.data
        user = data.get("user") if isinstance(data, dict) else getattr(data, "user", None)

    if not user or not getattr(user, "id", None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "detail": "Invalid or missing authentication token"},
        )
    return user
