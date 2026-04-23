from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.job import Job


class FollowUp(Base):
    __tablename__ = "follow_up"

    followup_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.job_id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    job: Mapped["Job"] = relationship(back_populates="follow_ups")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_follow_up(
    session: Session,
    job_id: int,
    description: str,
    due_date: date | None = None,
) -> "FollowUp":
    follow_up = FollowUp(
        job_id=job_id,
        description=description,
        due_date=due_date,
        completed=False,
    )
    session.add(follow_up)
    session.commit()
    session.refresh(follow_up)
    return follow_up


def get_follow_up(session: Session, followup_id: int) -> "FollowUp | None":
    return session.get(FollowUp, followup_id)


def get_follow_ups_by_job(session: Session, job_id: int) -> list["FollowUp"]:
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
    follow_up = get_follow_up(session, followup_id)
    if follow_up is None:
        return False
    session.delete(follow_up)
    session.commit()
    return True
