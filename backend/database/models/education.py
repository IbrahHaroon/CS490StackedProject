from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Education(Base):
    __tablename__ = "education"

    education_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    school: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str] = mapped_column(String(100), nullable=False)
    field_of_study: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gpa: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    school_location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="educations")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_education(
    session: Session,
    user_id: int,
    school: str,
    degree: str,
    *,
    field_of_study: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    gpa: str | None = None,
    school_location: str | None = None,
    sort_order: int = 0,
) -> "Education":
    education = Education(
        user_id=user_id,
        school=school,
        degree=degree,
        field_of_study=field_of_study,
        start_date=start_date,
        end_date=end_date,
        gpa=gpa,
        school_location=school_location,
        sort_order=sort_order,
    )
    session.add(education)
    session.commit()
    session.refresh(education)
    return education


def get_education(session: Session, education_id: int) -> "Education | None":
    return session.get(Education, education_id)


def get_educations_by_user(session: Session, user_id: int) -> list["Education"]:
    rows = (
        session.execute(
            select(Education)
            .where(Education.user_id == user_id)
            .order_by(Education.sort_order)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_education(
    session: Session,
    education_id: int,
    *,
    school: str | None = None,
    degree: str | None = None,
    field_of_study: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    clear_end_date: bool = False,
    gpa: str | None = None,
    school_location: str | None = None,
    sort_order: int | None = None,
) -> "Education | None":
    """Update mutable fields. Pass clear_end_date=True to set end_date to None."""
    education = get_education(session, education_id)
    if education is None:
        return None
    if school is not None:
        education.school = school
    if degree is not None:
        education.degree = degree
    if field_of_study is not None:
        education.field_of_study = field_of_study
    if start_date is not None:
        education.start_date = start_date
    if clear_end_date:
        education.end_date = None
    elif end_date is not None:
        education.end_date = end_date
    if gpa is not None:
        education.gpa = gpa
    if school_location is not None:
        education.school_location = school_location
    if sort_order is not None:
        education.sort_order = sort_order
    session.commit()
    session.refresh(education)
    return education


def delete_education(session: Session, education_id: int) -> bool:
    education = get_education(session, education_id)
    if education is None:
        return False
    session.delete(education)
    session.commit()
    return True
