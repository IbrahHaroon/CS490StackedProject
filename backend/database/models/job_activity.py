from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs


class JobActivity(Base):
    __tablename__ = "job_activity"

    activity_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stage_change"
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relationships
    job: Mapped["AppliedJobs"] = relationship(back_populates="activities")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_job_activity(
    session: Session,
    job_id: int,
    stage: str,
    event_type: str = "stage_change",
    notes: str | None = None,
) -> "JobActivity":
    """Record a stage change event for a job."""
    activity = JobActivity(
        job_id=job_id,
        stage=stage,
        changed_at=datetime.utcnow(),
        event_type=event_type,
        notes=notes,
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def get_job_activities(session: Session, job_id: int) -> list["JobActivity"]:
    """Return all activity records for a job ordered by time."""
    rows = (
        session.execute(
            select(JobActivity)
            .where(JobActivity.job_id == job_id)
            .order_by(JobActivity.changed_at)
        )
        .scalars()
        .all()
    )
    return list(rows)
