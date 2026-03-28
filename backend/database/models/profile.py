from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date
from sqlalchemy import Integer, String, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from database.base import Base
from database.models.address import create_address

if TYPE_CHECKING:
    from database.models.user import User
    from database.models.address import Address


class Profile(Base):
    __tablename__ = "profile"

    profile_id:   Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id:      Mapped[int]  = mapped_column(ForeignKey("user.user_id"), nullable=False, unique=True)
    address_id:   Mapped[int]  = mapped_column(ForeignKey("address.address_id"), nullable=False)
    first_name:   Mapped[str]  = mapped_column(String(100), nullable=False)
    last_name:    Mapped[str]  = mapped_column(String(100), nullable=False)
    dob:          Mapped[date] = mapped_column(Date, nullable=False)
    phone_number: Mapped[str]  = mapped_column(String(20), nullable=True)
    summary:      Mapped[str]  = mapped_column(String(1000), nullable=True)

    # Relationships
    user:    Mapped["User"]    = relationship(back_populates="profile")
    address: Mapped["Address"] = relationship(back_populates="profile")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #

def create_profile(
    session: Session,
    user_id: int,
    first_name: str,
    last_name: str,
    dob: date,
    address: str,
    state: str,
    zip_code: int,
    phone_number: str | None = None,
    summary: str | None = None,
) -> "Profile":
    """
    Create an Address row first to obtain an addressID,
    then create and return the Profile row.
    """
    new_address = create_address(session, address, state, zip_code)

    new_profile = Profile(
        user_id=user_id,
        address_id=new_address.address_id,
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        phone_number=phone_number,
        summary=summary,
    )
    session.add(new_profile)
    session.commit()
    session.refresh(new_profile)
    return get_profile(session, new_profile.profile_id)


def get_profile(session: Session, profile_id: int) -> "Profile | None":
    """Return Profile object by primary key, or None if not found."""
    return session.get(Profile, profile_id)


def update_profile(session: Session, updated_profile: "Profile") -> bool:
    """Persist all field changes on an already-loaded Profile object."""
    try:
        session.merge(updated_profile)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
