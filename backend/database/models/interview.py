from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.job import Job


class Interview(Base):
    __tablename__ = "interview"

    interview_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.job_id", ondelete="CASCADE"), nullable=False
    )
    round_type: Mapped[str] = mapped_column(String(100), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    interviewer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prep_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="interviews")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_interview(
    session: Session,
    job_id: int,
    round_type: str,
    scheduled_at: datetime,
    *,
    interviewer: str | None = None,
    mode: str | None = None,
    prep_notes: str | None = None,
    notes: str | None = None,
) -> "Interview":
    interview = Interview(
        job_id=job_id,
        round_type=round_type,
        scheduled_at=scheduled_at,
        interviewer=interviewer,
        mode=mode,
        prep_notes=prep_notes,
        notes=notes,
    )
    session.add(interview)
    session.commit()
    session.refresh(interview)
    return interview


def get_interview(session: Session, interview_id: int) -> "Interview | None":
    return session.get(Interview, interview_id)


def get_interviews_by_job(session: Session, job_id: int) -> list["Interview"]:
    rows = (
        session.execute(
            select(Interview)
            .where(Interview.job_id == job_id)
            .order_by(Interview.scheduled_at)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_interview(
    session: Session,
    interview_id: int,
    *,
    round_type: str | None = None,
    scheduled_at: datetime | None = None,
    interviewer: str | None = None,
    mode: str | None = None,
    prep_notes: str | None = None,
    notes: str | None = None,
) -> "Interview | None":
    interview = get_interview(session, interview_id)
    if interview is None:
        return None
    if round_type is not None:
        interview.round_type = round_type
    if scheduled_at is not None:
        interview.scheduled_at = scheduled_at
    if interviewer is not None:
        interview.interviewer = interviewer
    if mode is not None:
        interview.mode = mode
    if prep_notes is not None:
        interview.prep_notes = prep_notes
    if notes is not None:
        interview.notes = notes
    session.commit()
    session.refresh(interview)
    return interview


def delete_interview(session: Session, interview_id: int) -> bool:
    interview = get_interview(session, interview_id)
    if interview is None:
        return False
    session.delete(interview)
    session.commit()
    return True
