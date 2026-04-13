from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.documents import Documents
    from database.models.follow_up import FollowUp
    from database.models.interview import Interview
    from database.models.job_activity import JobActivity
    from database.models.job_document import JobDocument
    from database.models.outcome import Outcome
    from database.models.position import Position
    from database.models.user import User

PIPELINE_STAGES = [
    "Interested",
    "Applied",
    "Interview",
    "Offer",
    "Rejected",
    "Archived",
    "Withdrawn",
]


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
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recruiter_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="applied_jobs")
    position: Mapped["Position"] = relationship(back_populates="applied_jobs")
    activities: Mapped[list["JobActivity"]] = relationship(back_populates="job")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="job")
    outcome: Mapped["Outcome"] = relationship(
        back_populates="job", uselist=False, cascade="all, delete-orphan"
    )
    job_documents: Mapped[list["JobDocument"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="job")
    documents: Mapped[list["Documents"]] = relationship(back_populates="job")


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
    deadline: date | None = None,
    recruiter_notes: str | None = None,
    outcome_notes: str | None = None,
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
    if deadline is not None:
        job.deadline = deadline
    if recruiter_notes is not None:
        job.recruiter_notes = recruiter_notes
    if outcome_notes is not None:
        job.outcome_notes = outcome_notes
    session.commit()
    session.refresh(job)
    return job


def delete_applied_job(session: Session, job_id: int) -> bool:
    """Delete an application by primary key. Returns True if deleted.

    Deletes associated job_activity, interview, outcome, and job_document rows first
    to satisfy the FK constraints (these have NO ACTION on delete).
    """
    from database.models.interview import Interview
    from database.models.job_activity import JobActivity
    from database.models.job_document import JobDocument
    from database.models.outcome import Outcome

    job = get_applied_jobs(session, job_id)
    if job is None:
        return False
    session.execute(JobActivity.__table__.delete().where(JobActivity.job_id == job_id))
    session.execute(Interview.__table__.delete().where(Interview.job_id == job_id))
    session.execute(JobDocument.__table__.delete().where(JobDocument.job_id == job_id))
    session.execute(Outcome.__table__.delete().where(Outcome.job_id == job_id))
    session.delete(job)
    session.commit()
    return True


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


def get_dashboard_metrics(session: Session, user_id: int) -> dict:
    """Return stage counts, outcome counts, and response rate for a user."""
    from database.models.outcome import OUTCOME_STATES, Outcome

    jobs = get_all_applied_jobs(session, user_id)
    total = len(jobs)

    stage_counts = {stage: 0 for stage in PIPELINE_STAGES}
    for job in jobs:
        if job.application_status in stage_counts:
            stage_counts[job.application_status] += 1

    job_ids = [job.job_id for job in jobs]
    outcome_rows = (
        session.execute(select(Outcome).where(Outcome.job_id.in_(job_ids)))
        .scalars()
        .all()
        if job_ids
        else []
    )

    outcome_counts = {state: 0 for state in OUTCOME_STATES}
    for outcome in outcome_rows:
        if outcome.outcome_state in outcome_counts:
            outcome_counts[outcome.outcome_state] += 1

    applications_with_response = sum(
        1
        for job in jobs
        if job.application_status in ("Interview", "Offer", "Rejected")
    )
    response_rate = (
        round((applications_with_response / total * 100), 1) if total else 0.0
    )

    return {
        "total_applications": total,
        "stage_counts": stage_counts,
        "outcome_counts": outcome_counts,
        "response_rate": response_rate,
    }
