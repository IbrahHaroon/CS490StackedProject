from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.company import Company
    from database.models.recruiter_credentials import RecruiterCredentials


class Recruiter(Base):
    __tablename__ = "recruiter"

    recruiter_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("company.company_id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="recruiters")
    credentials: Mapped["RecruiterCredentials"] = relationship(
        back_populates="recruiter", uselist=False
    )


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_recruiter(
    session: Session,
    email: str,
    company_id: int,
    first_name: str,
    last_name: str,
    job_title: str | None = None,
) -> "Recruiter":
    """Create a new Recruiter row and return the persisted object."""
    new_recruiter = Recruiter(
        email=email,
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        job_title=job_title,
    )
    session.add(new_recruiter)
    session.commit()
    session.refresh(new_recruiter)
    return get_recruiter(session, new_recruiter.recruiter_id)


def get_recruiter(session: Session, recruiter_id: int) -> "Recruiter | None":
    """Return Recruiter object by primary key, or None if not found."""
    return session.get(Recruiter, recruiter_id)


def get_recruiter_by_email(session: Session, email: str) -> "Recruiter | None":
    """Return Recruiter object by email, or None if not found."""
    return session.execute(
        select(Recruiter).where(Recruiter.email == email)
    ).scalar_one_or_none()


def update_recruiter(session: Session, updated_recruiter: "Recruiter") -> bool:
    """Persist all field changes on an already-loaded Recruiter object."""
    try:
        session.merge(updated_recruiter)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False


def delete_recruiter(session: Session, recruiter_id: int) -> bool:
    """Delete a Recruiter row by primary key. Returns True if deleted."""
    recruiter = get_recruiter(session, recruiter_id)
    if recruiter is None:
        return False
    session.delete(recruiter)
    session.commit()
    return True
