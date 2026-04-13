from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import get_dashboard_metrics
from database.models.user import User
from database.services.job_sorter import (
    SortField,
    SortOrder,
    get_sorted_jobs,
)
from schemas import ApplicationResponse, DashboardMetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return stage counts, outcome counts, and response rate for the current user."""
    return get_dashboard_metrics(session, current_user.user_id)


@router.get("/dashboard/sorted", response_model=list[ApplicationResponse])
def get_sorted_dashboard(
    sort_by: str = "created_at",
    order: str = "desc",
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return user's job applications with optional sorting.

    Query Parameters:
    - sort_by: Field to sort by (last_activity, deadline, company, created_at)
    - order: Sort order (asc or desc)
    """
    # Validate sort_by parameter
    try:
        sort_field = SortField(sort_by)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort_by. Must be one of: {', '.join([e.value for e in SortField])}",
        )

    # Validate order parameter
    try:
        sort_order = SortOrder(order)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid order. Must be one of: {', '.join([e.value for e in SortOrder])}",
        )

    jobs = get_sorted_jobs(session, current_user.user_id, sort_field, sort_order)
    return list(jobs)
