from enum import Enum

from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from database.models.job import Job
from database.models.job_activity import JobActivity


class SortField(str, Enum):
    LAST_ACTIVITY = "last_activity"
    DEADLINE = "deadline"
    COMPANY = "company"
    CREATED_AT = "created_at"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


def get_sorted_jobs(
    session: Session,
    user_id: int,
    sort_by: SortField = SortField.CREATED_AT,
    order: SortOrder = SortOrder.DESC,
) -> list[Job]:
    """Retrieve a user's jobs with database-level sorting."""
    query = select(Job).where(Job.user_id == user_id)

    if sort_by == SortField.LAST_ACTIVITY:
        # Latest job_activity.occurred_at per job; nulls = jobs with no activity yet
        subquery = (
            select(
                JobActivity.job_id,
                func.max(JobActivity.occurred_at).label("max_occurred_at"),
            )
            .group_by(JobActivity.job_id)
            .subquery()
        )
        query = query.outerjoin(subquery, Job.job_id == subquery.c.job_id)
        sort_column = subquery.c.max_occurred_at
    elif sort_by == SortField.DEADLINE:
        sort_column = Job.deadline
    elif sort_by == SortField.COMPANY:
        sort_column = Job.company_name
    else:  # CREATED_AT
        sort_column = Job.created_at

    query = query.order_by(desc(sort_column) if order == SortOrder.DESC else asc(sort_column))
    return session.execute(query).scalars().unique().all()
