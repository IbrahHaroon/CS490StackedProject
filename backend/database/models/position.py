from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, Sequence, String
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs
    from database.models.company import Company

LOCATION_TYPES = ["Remote", "Hybrid", "Onsite"]


class Position(Base):
    __tablename__ = "position"

    position_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("position_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    company_id: Mapped[int] = mapped_column(
        ForeignKey("company.company_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    salary: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    education_req: Mapped[str] = mapped_column(String(255), nullable=True)
    experience_req: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=True)
    listing_date: Mapped[date] = mapped_column(Date, nullable=False)
    # nullable=True so existing rows (before migration) don't break.
    # Run this in Supabase SQL editor before deploying:
    #   ALTER TABLE position ADD COLUMN IF NOT EXISTS is_manual BOOLEAN DEFAULT FALSE;
    #   UPDATE position p SET is_manual = TRUE
    #     FROM company c JOIN address a ON c.address_id = a.address_id
    #     WHERE p.company_id = c.company_id AND a.address = 'N/A';
    is_manual: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="positions")
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
    location: str | None = None,
    location_type: str | None = None,
    is_manual: bool = False,
) -> "Position":
    """Create a new Position row and return the persisted object."""
    new_position = Position(
        company_id=company_id,
        title=title,
        location_type=location_type,
        location=location,
        salary=salary,
        education_req=education_req,
        experience_req=experience_req,
        description=description,
        listing_date=listing_date,
        is_manual=is_manual,
    )
    session.add(new_position)
    session.commit()
    session.refresh(new_position)
    return get_position(session, new_position.position_id)


def get_position(session: Session, position_id: int) -> "Position | None":
    """Return Position object by primary key, or None if not found."""
    return session.get(Position, position_id)


def get_all_positions(
    session: Session, exclude_manual: bool = False
) -> list["Position"]:
    """Return all positions. When exclude_manual=True, positions with
    is_manual=True are omitted so they don't appear on the public job board.
    Requires the migration SQL in the is_manual column comment above to have
    been run in Supabase first."""
    from sqlalchemy import select

    stmt = select(Position)
    if exclude_manual:
        # is_manual IS NOT TRUE covers both FALSE and NULL (pre-migration rows)
        stmt = stmt.where(Position.is_manual.is_not(True))
    return session.execute(stmt).scalars().all()


def update_position(session: Session, updated_position: "Position") -> bool:
    """Persist all field changes on an already-loaded Position object."""
    try:
        session.merge(updated_position)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False


def delete_position(session: Session, position_id: int) -> bool:
    """Delete a position by primary key. Returns True if deleted."""
    position = get_position(session, position_id)
    if position is None:
        return False
    session.delete(position)
    session.commit()
    return True
