from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import get_all_applied_jobs
from database.models.user import User
from database.services.job_sorter import (
    SortField,
    SortOrder,
    get_sorted_jobs,
)
from schemas import ApplicationResponse

router = APIRouter()


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


@router.get("/metrics")
def get_dashboard_metrics(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return aggregate metrics for the current user's applications.

    Response:
    - total: total number of applications
    - by_stage: count per pipeline stage
    - awaiting_response: applications stuck in the "Applied" stage
    - response_rate: percentage of submitted applications that received a
      response (moved to Interview, Offer, or Rejected)
    """
    apps = list(get_all_applied_jobs(session, current_user.user_id))

    total = len(apps)
    by_stage: dict[str, int] = {}
    for app in apps:
        s = app.application_status
        by_stage[s] = by_stage.get(s, 0) + 1

    # Submitted = Applied + Interview + Offer + Rejected + Accepted + Withdrawn
    submitted = sum(
        by_stage.get(s, 0)
        for s in ("Applied", "Interview", "Offer", "Rejected", "Withdrawn")
    )
    responded = sum(
        by_stage.get(s, 0) for s in ("Interview", "Offer", "Rejected")
    )
    response_rate = round(responded / submitted * 100, 1) if submitted > 0 else 0.0

    return {
        "total": total,
        "by_stage": by_stage,
        "awaiting_response": by_stage.get("Applied", 0),
        "response_rate": response_rate,
    }
