from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.job import get_dashboard_metrics
from database.models.job_activity import get_stage_analytics
from database.models.user import User
from database.services.job_sorter import SortField, SortOrder, get_sorted_jobs
from schemas import AnalyticsResponse, DashboardMetricsResponse, JobResponse

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Conversion funnel and avg time-in-stage from stored job_activity events."""
    return get_stage_analytics(session, current_user.user_id)


@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_metrics(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stage counts, outcome counts, and response rate for the current user."""
    return get_dashboard_metrics(session, current_user.user_id)


@router.get("/dashboard/sorted", response_model=list[JobResponse])
def get_sorted_dashboard(
    sort_by: str = "created_at",
    order: str = "desc",
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        sort_field = SortField(sort_by)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid sort_by. Must be one of: {', '.join([e.value for e in SortField])}",
        )
    try:
        sort_order = SortOrder(order)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid order. Must be one of: {', '.join([e.value for e in SortOrder])}",
        )
    return list(get_sorted_jobs(session, current_user.user_id, sort_field, sort_order))
