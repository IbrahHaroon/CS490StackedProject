from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base
from database.models.address import create_address

if TYPE_CHECKING:
    from database.models.address import Address
    from database.models.position import Position


class Company(Base):
    __tablename__ = "company"

    company_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    address_id: Mapped[int] = mapped_column(
        ForeignKey("address.address_id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    address: Mapped["Address"] = relationship(back_populates="company")
    positions: Mapped[list["Position"]] = relationship(back_populates="company")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_company(
    session: Session,
    company_name: str,
    address: str,
    state: str,
    zip_code: int,
) -> "Company":
    """
    Create an Address row first to obtain an addressID,
    then create and return the Company row.
    """
    new_address = create_address(session, address, state, zip_code)

    new_company = Company(
        name=company_name,
        address_id=new_address.address_id,
    )
    session.add(new_company)
    session.commit()
    session.refresh(new_company)
    return get_company(session, new_company.company_id)


def get_company(session: Session, company_id: int) -> "Company | None":
    """Return Company object by primary key, or None if not found."""
    return session.get(Company, company_id)
