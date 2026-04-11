from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class CareerPreferences(Base):
    __tablename__ = "career_preferences"

    preference_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"), nullable=False, unique=True
    )
    target_roles: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location_preferences: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    work_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    salary_preference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="career_preferences")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_career_preferences(
    session: Session,
    user_id: int,
    target_roles: str | None = None,
    location_preferences: str | None = None,
    work_mode: str | None = None,
    salary_preference: str | None = None,
) -> "CareerPreferences":
    """Create a new CareerPreferences row and return the persisted object."""
    prefs = CareerPreferences(
        user_id=user_id,
        target_roles=target_roles,
        location_preferences=location_preferences,
        work_mode=work_mode,
        salary_preference=salary_preference,
    )
    session.add(prefs)
    session.commit()
    session.refresh(prefs)
    return get_career_preferences_by_user(session, user_id)


def get_career_preferences_by_user(
    session: Session, user_id: int
) -> "CareerPreferences | None":
    """Return CareerPreferences for a user, or None if not found."""
    return session.execute(
        select(CareerPreferences).where(CareerPreferences.user_id == user_id)
    ).scalar_one_or_none()


def update_career_preferences(
    session: Session,
    user_id: int,
    target_roles: str | None = None,
    location_preferences: str | None = None,
    work_mode: str | None = None,
    salary_preference: str | None = None,
) -> "CareerPreferences":
    """Upsert career preferences for a user — creates if none exist, updates otherwise."""
    prefs = get_career_preferences_by_user(session, user_id)
    if prefs is None:
        return create_career_preferences(
            session,
            user_id=user_id,
            target_roles=target_roles,
            location_preferences=location_preferences,
            work_mode=work_mode,
            salary_preference=salary_preference,
        )
    if target_roles is not None:
        prefs.target_roles = target_roles
    if location_preferences is not None:
        prefs.location_preferences = location_preferences
    if work_mode is not None:
        prefs.work_mode = work_mode
    if salary_preference is not None:
        prefs.salary_preference = salary_preference
    session.commit()
    session.refresh(prefs)
    return prefs


def delete_career_preferences(session: Session, user_id: int) -> bool:
    """Delete career preferences for a user. Returns True if deleted."""
    prefs = get_career_preferences_by_user(session, user_id)
    if prefs is None:
        return False
    session.delete(prefs)
    session.commit()
    return True
