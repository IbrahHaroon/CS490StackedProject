from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs


class FollowUp(Base):
    __tablename__ = "follow_up"

    followup_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    job: Mapped["AppliedJobs"] = relationship(back_populates="follow_ups")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_follow_up(
    session: Session,
    job_id: int,
    description: str,
    due_date: date | None = None,
) -> "FollowUp":
    """Create a new FollowUp row and return the persisted object."""
    follow_up = FollowUp(
        job_id=job_id,
        description=description,
        due_date=due_date,
        completed=False,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return get_follow_up(session, follow_up.followup_id)


def get_follow_up(session: Session, followup_id: int) -> "FollowUp | None":
    """Return FollowUp object by primary key, or None if not found."""
    return session.get(FollowUp, followup_id)


def get_follow_ups_by_job(session: Session, job_id: int) -> list["FollowUp"]:
    """Return all follow-ups for a job."""
    rows = (
        session.execute(select(FollowUp).where(FollowUp.job_id == job_id))
        .scalars()
        .all()
    )
    return list(rows)


def update_follow_up(
    session: Session,
    followup_id: int,
    description: str | None = None,
    due_date: date | None = None,
    completed: bool | None = None,
) -> "FollowUp | None":
    """Update mutable fields on an existing follow-up. Returns None if not found."""
    follow_up = get_follow_up(session, followup_id)
    if follow_up is None:
        return None
    if description is not None:
        follow_up.description = description
    if due_date is not None:
        follow_up.due_date = due_date
    if completed is not None:
        follow_up.completed = completed
    session.commit()
    session.refresh(follow_up)
    return follow_up


def delete_follow_up(session: Session, followup_id: int) -> bool:
    """Delete a follow-up by primary key. Returns True if deleted."""
    follow_up = get_follow_up(session, followup_id)
    if follow_up is None:
        return False
    session.delete(follow_up)
    session.commit()
    return True
