from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String, select
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
    field_of_study: Mapped[str | None] = mapped_column(String(100), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gpa: Mapped[str | None] = mapped_column(String(10), nullable=True)

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
    field_of_study: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    gpa: str | None = None,
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
        field_of_study=field_of_study,
        start_date=start_date,
        end_date=end_date,
        gpa=gpa,
    )
    session.add(new_education)
    session.commit()
    session.refresh(new_education)
    return get_education(session, new_education.education_id)


def get_education(session: Session, education_id: int) -> "Education | None":
    """Return Education object by primary key, or None if not found."""
    return session.get(Education, education_id)


def get_educations_by_user(session: Session, user_id: int) -> list["Education"]:
    """Return all education records for a user."""
    rows = (
        session.execute(select(Education).where(Education.user_id == user_id))
        .scalars()
        .all()
    )
    return list(rows)


def update_education(
    session: Session,
    education_id: int,
    highest_education: str | None = None,
    degree: str | None = None,
    school_or_college: str | None = None,
    field_of_study: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    clear_end_date: bool = False,
    gpa: str | None = None,
) -> "Education | None":
    """Update mutable fields on an existing education record. Returns None if not found.

    Pass clear_end_date=True to explicitly set end_date to None (still enrolled).
    Address updates must be done separately via update_address.
    """
    education = get_education(session, education_id)
    if education is None:
        return None
    if highest_education is not None:
        education.highest_education = highest_education
    if degree is not None:
        education.degree = degree
    if school_or_college is not None:
        education.school_or_college = school_or_college
    if field_of_study is not None:
        education.field_of_study = field_of_study
    if clear_end_date:
        education.end_date = None
    elif end_date is not None:
        education.end_date = end_date
    if start_date is not None:
        education.start_date = start_date
    if gpa is not None:
        education.gpa = gpa
    session.commit()
    session.refresh(education)
    return education


def delete_education(session: Session, education_id: int) -> bool:
    """Delete an education record by primary key. Returns True if deleted."""
    education = get_education(session, education_id)
    if education is None:
        return False
    session.delete(education)
    session.commit()
    return True
