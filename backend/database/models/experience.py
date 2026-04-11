from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Experience(Base):
    __tablename__ = "experience"

    experience_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="experiences")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_experience(
    session: Session,
    user_id: int,
    company: str,
    title: str,
    start_date: date,
    end_date: date | None = None,
    description: str | None = None,
    sort_order: int = 0,
) -> "Experience":
    """Create a new Experience row and return the persisted object."""
    experience = Experience(
        user_id=user_id,
        company=company,
        title=title,
        start_date=start_date,
        end_date=end_date,
        description=description,
        sort_order=sort_order,
    )
    session.add(experience)
    session.commit()
    session.refresh(experience)
    return get_experience(session, experience.experience_id)


def get_experience(session: Session, experience_id: int) -> "Experience | None":
    """Return Experience object by primary key, or None if not found."""
    return session.get(Experience, experience_id)


def get_experiences_by_user(session: Session, user_id: int) -> list["Experience"]:
    """Return all experience records for a user ordered by sort_order."""
    rows = (
        session.execute(
            select(Experience)
            .where(Experience.user_id == user_id)
            .order_by(Experience.sort_order)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_experience(
    session: Session,
    experience_id: int,
    company: str | None = None,
    title: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    clear_end_date: bool = False,
    description: str | None = None,
    sort_order: int | None = None,
) -> "Experience | None":
    """Update mutable fields on an existing experience. Returns None if not found.

    Pass clear_end_date=True to explicitly set end_date to None (current role).
    """
    experience = get_experience(session, experience_id)
    if experience is None:
        return None
    if company is not None:
        experience.company = company
    if title is not None:
        experience.title = title
    if start_date is not None:
        experience.start_date = start_date
    if clear_end_date:
        experience.end_date = None
    elif end_date is not None:
        experience.end_date = end_date
    if description is not None:
        experience.description = description
    if sort_order is not None:
        experience.sort_order = sort_order
    session.commit()
    session.refresh(experience)
    return experience


def delete_experience(session: Session, experience_id: int) -> bool:
    """Delete an experience by primary key. Returns True if deleted."""
    experience = get_experience(session, experience_id)
    if experience is None:
        return False
    session.delete(experience)
    session.commit()
    return True
