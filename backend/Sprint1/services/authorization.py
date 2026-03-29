from fastapi import HTTPException, status


def authorize_resource_owner(resource_owner_id: str, current_user_id: str) -> None:
    if resource_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Forbidden", "detail": "You do not have access to this resource"},
        )
