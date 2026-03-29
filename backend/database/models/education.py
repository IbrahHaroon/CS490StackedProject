from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base
from database.models.address import create_address

if TYPE_CHECKING:
    from database.models.address import Address
    from database.models.user import User


class Education(Base):
    __tablename__ = "education"

    education_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    address_id: Mapped[int] = mapped_column(
        ForeignKey("address.address_id"), nullable=False
    )
    highest_education: Mapped[str] = mapped_column(String(100), nullable=False)
    degree: Mapped[str] = mapped_column(String(100), nullable=False)
    school_or_college: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="educations")
    address: Mapped["Address"] = relationship(back_populates="education")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_education(
    session: Session,
    user_id: int,
    highest_education: str,
    degree: str,
    college: str,
    address: str,
    state: str,
    zip_code: int,
) -> "Education":
    """
    Create an Address row first to obtain an addressID,
    then create and return the Education row.
    """
    new_address = create_address(session, address, state, zip_code)

    new_education = Education(
        user_id=user_id,
        address_id=new_address.address_id,
        highest_education=highest_education,
        degree=degree,
        school_or_college=college,
    )
    session.add(new_education)
    session.commit()
    session.refresh(new_education)
    return get_education(session, new_education.education_id)


def get_education(session: Session, education_id: int) -> "Education | None":
    """Return Education object by primary key, or None if not found."""
    return session.get(Education, education_id)
