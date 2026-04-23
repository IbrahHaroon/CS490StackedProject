from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.job import Job


class JobActivity(Base):
    """Append-only audit log for a job. Powers timeline + S3-014 analytics."""

    __tablename__ = "job_activity"

    activity_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.job_id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="stage_change"
    )
    from_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    to_stage: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="activities")

    __table_args__ = (Index("idx_job_activity_job", "job_id", "occurred_at"),)


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_job_activity(
    session: Session,
    job_id: int,
    *,
    event_type: str = "stage_change",
    from_stage: str | None = None,
    to_stage: str | None = None,
    notes: str | None = None,
) -> "JobActivity":
    activity = JobActivity(
        job_id=job_id,
        event_type=event_type,
        from_stage=from_stage,
        to_stage=to_stage,
        notes=notes,
        occurred_at=datetime.utcnow(),
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def get_job_activities(session: Session, job_id: int) -> list["JobActivity"]:
    rows = (
        session.execute(
            select(JobActivity)
            .where(JobActivity.job_id == job_id)
            .order_by(JobActivity.occurred_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)
