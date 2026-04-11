from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Sequence, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs


class Interview(Base):
    __tablename__ = "interview"

    interview_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("interview_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False
    )
    round_type: Mapped[str] = mapped_column(String(100), nullable=False)
    date_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str] = mapped_column(String(2000), nullable=True)

    # Relationships
    job: Mapped["AppliedJobs"] = relationship(back_populates="interviews")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_interview(
    session: Session,
    job_id: int,
    round_type: str,
    date_time: datetime,
    notes: str | None = None,
) -> "Interview":
    """Create a new Interview row and return the persisted object."""
    interview = Interview(
        job_id=job_id,
        round_type=round_type,
        date_time=date_time,
        notes=notes,
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


def get_interview(session: Session, interview_id: int) -> "Interview | None":
    """Return Interview object by primary key, or None if not found."""
    return session.get(Interview, interview_id)


def get_interviews_for_job(session: Session, job_id: int) -> list["Interview"]:
    """Return all interviews for a job ordered by date_time."""
    rows = (
        session.execute(
            select(Interview)
            .where(Interview.job_id == job_id)
            .order_by(Interview.date_time)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_interview(
    session: Session,
    interview_id: int,
    round_type: str | None = None,
    date_time: datetime | None = None,
    notes: str | None = None,
) -> "Interview | None":
    """Update mutable fields on an existing interview. Returns None if not found."""
    interview = get_interview(session, interview_id)
    if interview is None:
        return None
    if round_type is not None:
        interview.round_type = round_type
    if date_time is not None:
        interview.date_time = date_time
    if notes is not None:
        interview.notes = notes
    session.commit()
    session.refresh(interview)
    return interview


def delete_interview(session: Session, interview_id: int) -> bool:
    """Delete an interview by primary key. Returns True if deleted."""
    interview = get_interview(session, interview_id)
    if interview is None:
        return False
    session.delete(interview)
    session.commit()
    return True
