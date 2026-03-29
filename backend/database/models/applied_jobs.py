from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Sequence, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.job_activity import JobActivity
    from database.models.position import Position
    from database.models.user import User

PIPELINE_STAGES = ["Interested", "Applied", "Interview", "Offer", "Rejected", "Archived"]


class AppliedJobs(Base):
    __tablename__ = "applied_jobs"

    job_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("job_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    position_id: Mapped[int] = mapped_column(
        ForeignKey("position.position_id"), nullable=False
    )
    years_of_experience: Mapped[int] = mapped_column(Integer, nullable=False)
    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    application_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Interested"
    )
    stage_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="applied_jobs")
    position: Mapped["Position"] = relationship(back_populates="applied_jobs")
    activities: Mapped[list["JobActivity"]] = relationship(back_populates="job")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_applied_jobs(
    session: Session,
    user_id: int,
    position_id: int,
    years_of_experience: int,
) -> "AppliedJobs":
    """
    Create a new AppliedJobs row.
    Application date is set to today and status initialised to 'Interested'.
    """
    now = datetime.utcnow()
    new_application = AppliedJobs(
        user_id=user_id,
        position_id=position_id,
        years_of_experience=years_of_experience,
        application_date=date.today(),
        application_status="Interested",
        stage_changed_at=now,
    )
    session.add(new_application)
    session.commit()
    session.refresh(new_application)
    return get_applied_jobs(session, new_application.job_id)


def get_applied_jobs(session: Session, job_id: int) -> "AppliedJobs | None":
    """Return AppliedJobs object by primary key, or None if not found."""
    return session.get(AppliedJobs, job_id)


def update_applied_job(
    session: Session,
    job_id: int,
    application_status: str | None = None,
    years_of_experience: int | None = None,
) -> "AppliedJobs | None":
    """Update mutable fields on an existing application. Returns None if not found."""
    job = get_applied_jobs(session, job_id)
    if job is None:
        return None
    if application_status is not None:
        job.application_status = application_status
        job.stage_changed_at = datetime.utcnow()
    if years_of_experience is not None:
        job.years_of_experience = years_of_experience
    session.commit()
    session.refresh(job)
    return job


def lookup_applied_jobs(session: Session, user_id: int) -> int:
    """Return the number of applied jobs a user has."""
    return (
        session.execute(
            select(func.count())
            .select_from(AppliedJobs)
            .where(AppliedJobs.user_id == user_id)
        ).scalar()
        or 0
    )


def get_all_applied_jobs(session: Session, user_id: int) -> tuple["AppliedJobs", ...]:
    """Return all applied jobs belonging to a user as a tuple."""
    rows = (
        session.execute(select(AppliedJobs).where(AppliedJobs.user_id == user_id))
        .scalars()
        .all()
    )
    return tuple(rows)
