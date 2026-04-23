from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.follow_up import FollowUp
    from database.models.interview import Interview
    from database.models.job_activity import JobActivity
    from database.models.job_document_link import JobDocumentLink
    from database.models.user import User

# Pipeline values used across the dashboard. The `Withdrawn` and `Archived`
# stages exist for historical bookkeeping; the active pipeline is the first
# five entries.
PIPELINE_STAGES = [
    "Interested",
    "Applied",
    "Interview",
    "Offer",
    "Rejected",
    "Archived",
    "Withdrawn",
    # Imported from legacy `outcome.outcome_state` (see Phase-3 import).
    "Accepted",
]


class Job(Base):
    """A user-owned opportunity record.

    Replaces the legacy `applied_jobs` + `position` + `company` join. Company
    and title are denormalized strings — there is no shared catalog.
    """

    __tablename__ = "job"

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    stage: Mapped[str] = mapped_column(String(50), nullable=False, default="Interested")
    stage_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    application_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_research_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    outcome_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="jobs")
    activities: Mapped[list["JobActivity"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    interviews: Mapped[list["Interview"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    document_links: Mapped[list["JobDocumentLink"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_job_user_stage", "user_id", "stage"),)


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_job(
    session: Session,
    user_id: int,
    title: str,
    company_name: str,
    *,
    location: str | None = None,
    source_url: str | None = None,
    description: str | None = None,
    stage: str = "Interested",
    application_date: date | None = None,
    deadline: date | None = None,
    priority: str | None = None,
    salary: Decimal | None = None,
    years_of_experience: int | None = None,
    notes: str | None = None,
) -> "Job":
    now = datetime.utcnow()
    job = Job(
        user_id=user_id,
        title=title,
        company_name=company_name,
        location=location,
        source_url=source_url,
        description=description,
        stage=stage,
        stage_changed_at=now,
        application_date=application_date,
        deadline=deadline,
        priority=priority,
        salary=salary,
        years_of_experience=years_of_experience,
        notes=notes,
        created_at=now,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job(session: Session, job_id: int) -> "Job | None":
    return session.get(Job, job_id)


def get_jobs_for_user(session: Session, user_id: int) -> list["Job"]:
    rows = (
        session.execute(
            select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_job(
    session: Session,
    job_id: int,
    *,
    title: str | None = None,
    company_name: str | None = None,
    location: str | None = None,
    source_url: str | None = None,
    description: str | None = None,
    stage: str | None = None,
    application_date: date | None = None,
    deadline: date | None = None,
    priority: str | None = None,
    salary: Decimal | None = None,
    years_of_experience: int | None = None,
    notes: str | None = None,
    company_research_notes: str | None = None,
    outcome_notes: str | None = None,
    archived_at: datetime | None = None,
) -> "Job | None":
    job = get_job(session, job_id)
    if job is None:
        return None
    for field, value in {
        "title": title,
        "company_name": company_name,
        "location": location,
        "source_url": source_url,
        "description": description,
        "application_date": application_date,
        "deadline": deadline,
        "priority": priority,
        "salary": salary,
        "years_of_experience": years_of_experience,
        "notes": notes,
        "company_research_notes": company_research_notes,
        "outcome_notes": outcome_notes,
        "archived_at": archived_at,
    }.items():
        if value is not None:
            setattr(job, field, value)
    if stage is not None and stage != job.stage:
        job.stage = stage
        job.stage_changed_at = datetime.utcnow()
    session.commit()
    session.refresh(job)
    return job


def delete_job(session: Session, job_id: int) -> bool:
    job = get_job(session, job_id)
    if job is None:
        return False
    session.delete(job)
    session.commit()
    return True


def count_jobs(session: Session, user_id: int) -> int:
    return (
        session.execute(
            select(func.count()).select_from(Job).where(Job.user_id == user_id)
        ).scalar()
        or 0
    )


def get_dashboard_metrics(session: Session, user_id: int) -> dict:
    """Stage counts + response rate, derived directly from job rows."""
    jobs = get_jobs_for_user(session, user_id)
    total = len(jobs)

    stage_counts = {stage: 0 for stage in PIPELINE_STAGES}
    for job in jobs:
        if job.stage in stage_counts:
            stage_counts[job.stage] += 1

    # Same logical buckets the legacy outcome table tracked, derivable from stage.
    outcome_states = ["Applied", "Rejected", "Offer", "Accepted", "Withdrawn"]
    outcome_counts = {state: stage_counts.get(state, 0) for state in outcome_states}

    responses = sum(
        1 for j in jobs if j.stage in ("Interview", "Offer", "Rejected", "Accepted")
    )
    response_rate = round((responses / total * 100), 1) if total else 0.0

    return {
        "total_applications": total,
        "stage_counts": stage_counts,
        "outcome_counts": outcome_counts,
        "response_rate": response_rate,
    }
