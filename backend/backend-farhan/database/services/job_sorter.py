from enum import Enum

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from database.models.applied_jobs import AppliedJobs
from database.models.company import Company
from database.models.job_activity import JobActivity
from database.models.position import Position


class SortField(str, Enum):
    """Valid sort fields for job listings."""

    LAST_ACTIVITY = "last_activity"
    DEADLINE = "deadline"
    COMPANY = "company"
    CREATED_AT = "created_at"


class SortOrder(str, Enum):
    """Valid sort orders."""

    ASC = "asc"
    DESC = "desc"


def get_sorted_jobs(
    session: Session,
    user_id: int,
    sort_by: SortField = SortField.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
) -> list[AppliedJobs]:
    """
    Retrieve jobs for a user with database-level sorting.

    Args:
        session: Database session
        user_id: User ID to filter jobs
        sort_by: Field to sort by (last_activity, deadline, company, created_at)
        order: Sort order (asc or desc)

    Returns:
        List of AppliedJobs sorted according to parameters
    """
    query = select(AppliedJobs).where(AppliedJobs.user_id == user_id)

    # Determine sort column and join requirements
    if sort_by == SortField.LAST_ACTIVITY:
        # Join with JobActivity and sort by latest changed_at, with nulls last
        subquery = (
            select(
                JobActivity.job_id,
                func.max(JobActivity.changed_at).label("max_changed_at"),
            )
            .group_by(JobActivity.job_id)
            .subquery()
        )
        query = query.outerjoin(subquery, AppliedJobs.job_id == subquery.c.job_id)
        sort_column = subquery.c.max_changed_at
    elif sort_by == SortField.DEADLINE:
        # Sort by position listing_date (assuming deadline proxy)
        query = query.join(Position, AppliedJobs.position_id == Position.position_id)
        sort_column = Position.listing_date
    elif sort_by == SortField.COMPANY:
        # Sort by company name, requiring joins
        query = query.join(
            Position, AppliedJobs.position_id == Position.position_id
        ).join(Company, Position.company_id == Company.company_id)
        sort_column = Company.name
    else:  # created_at (application_date)
        sort_column = AppliedJobs.application_date

    # Apply sort order
    if order == SortOrder.DESC:
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    return session.execute(query).scalars().unique().all()
