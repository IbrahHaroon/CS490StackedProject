from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs

OUTCOME_STATES = [
    "Applied",
    "Rejected",
    "Offer",
    "Accepted",
    "Withdrawn",
]


class Outcome(Base):
    __tablename__ = "outcome"

    outcome_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("outcome_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False, unique=True
    )
    outcome_state: Mapped[str] = mapped_column(String(50), nullable=False)
    outcome_notes: Mapped[str] = mapped_column(String(2000), nullable=True)

    # Relationships
    job: Mapped["AppliedJobs"] = relationship(back_populates="outcome")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_outcome(
    session: Session,
    job_id: int,
    outcome_state: str,
    outcome_notes: str | None = None,
) -> "Outcome":
    """Create a new Outcome row and return the persisted object."""
    outcome = Outcome(
        job_id=job_id,
        outcome_state=outcome_state,
        outcome_notes=outcome_notes,
    )
    session.add(outcome)
    session.commit()
    session.refresh(outcome)
    return outcome


def get_outcome(session: Session, outcome_id: int) -> "Outcome | None":
    """Return Outcome object by primary key, or None if not found."""
    return session.get(Outcome, outcome_id)


def get_outcome_by_job(session: Session, job_id: int) -> "Outcome | None":
    """Return Outcome object for a job, or None if not found."""
    return session.execute(
        select(Outcome).where(Outcome.job_id == job_id)
    ).scalar_one_or_none()


def update_outcome(
    session: Session,
    outcome_id: int,
    outcome_state: str | None = None,
    outcome_notes: str | None = None,
) -> "Outcome | None":
    """Update mutable fields on an existing outcome. Returns None if not found."""
    outcome = get_outcome(session, outcome_id)
    if outcome is None:
        return None
    if outcome_state is not None:
        outcome.outcome_state = outcome_state
    if outcome_notes is not None:
        outcome.outcome_notes = outcome_notes
    session.commit()
    session.refresh(outcome)
    return outcome


def delete_outcome(session: Session, outcome_id: int) -> bool:
    """Delete an outcome by primary key. Returns True if deleted."""
    outcome = get_outcome(session, outcome_id)
    if outcome is None:
        return False
    session.delete(outcome)
    session.commit()
    return True
