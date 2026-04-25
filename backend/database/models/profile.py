from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Profile(Base):
    __tablename__ = "profile"

    profile_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"), nullable=False, unique=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Address denormalized inline (was a separate table in v1)
    address_line: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_profile(
    session: Session,
    user_id: int,
    first_name: str,
    last_name: str,
    dob: date,
    *,
    phone_number: str | None = None,
    summary: str | None = None,
    address_line: str | None = None,
    city: str | None = None,
    state: str | None = None,
    zip_code: str | None = None,
    country: str | None = None,
) -> "Profile":
    profile = Profile(
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone_number=phone_number,
        summary=summary,
        address_line=address_line,
        city=city,
        state=state,
        zip_code=zip_code,
        country=country,
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


def get_profile(session: Session, profile_id: int) -> "Profile | None":
    return session.get(Profile, profile_id)


def get_profile_by_user_id(session: Session, user_id: int) -> "Profile | None":
    return session.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()


def update_profile(session: Session, updated_profile: "Profile") -> bool:
    """Persist all field changes on an already-loaded Profile object."""
    try:
        session.merge(updated_profile)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
