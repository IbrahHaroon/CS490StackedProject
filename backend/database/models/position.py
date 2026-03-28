from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date
from decimal import Decimal
from sqlalchemy import Integer, String, Numeric, Date, Sequence, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from database.base import Base

if TYPE_CHECKING:
    from database.models.company import Company
    from database.models.applied_jobs import AppliedJobs


class Position(Base):
    __tablename__ = "position"

    position_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("position_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    company_id:     Mapped[int]     = mapped_column(ForeignKey("company.company_id"), nullable=False)
    title:          Mapped[str]     = mapped_column(String(255), nullable=False)
    salary:         Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    education_req:  Mapped[str]     = mapped_column(String(255), nullable=True)
    experience_req: Mapped[str]     = mapped_column(String(255), nullable=True)
    description:    Mapped[str]     = mapped_column(String(2000), nullable=True)
    listing_date:   Mapped[date]    = mapped_column(Date, nullable=False)

    # Relationships
    company:      Mapped["Company"]           = relationship(back_populates="positions")
    applied_jobs: Mapped[list["AppliedJobs"]] = relationship(back_populates="position")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #

def create_position(
    session: Session,
    company_id: int,
    title: str,
    salary: Decimal,
    education_req: str,
    experience_req: str,
    description: str,
    listing_date: date,
) -> "Position":
    """Create a new Position row and return the persisted object."""
    new_position = Position(
        company_id=company_id,
        title=title,
        salary=salary,
        education_req=education_req,
        experience_req=experience_req,
        description=description,
        listing_date=listing_date,
    )
    session.add(new_position)
    session.commit()
    session.refresh(new_position)
    return get_position(session, new_position.position_id)


def get_position(session: Session, position_id: int) -> "Position | None":
    """Return Position object by primary key, or None if not found."""
    return session.get(Position, position_id)


def update_position(session: Session, updated_position: "Position") -> bool:
    """Persist all field changes on an already-loaded Position object."""
    try:
        session.merge(updated_position)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
