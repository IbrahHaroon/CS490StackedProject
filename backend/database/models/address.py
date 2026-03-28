from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Sequence
from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from database.base import Base

if TYPE_CHECKING:
    from database.models.profile import Profile
    from database.models.education import Education
    from database.models.company import Company


class Address(Base):
    __tablename__ = "address"

    address_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("address_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    address:  Mapped[str] = mapped_column(String(255), nullable=False)
    state:    Mapped[str] = mapped_column(String(100), nullable=False)
    zip_code: Mapped[int] = mapped_column(Integer, nullable=False)

    # Back references
    profile:   Mapped["Profile"]   = relationship(back_populates="address")
    education: Mapped["Education"] = relationship(back_populates="address")
    company:   Mapped["Company"]   = relationship(back_populates="address")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #

def create_address(
    session: Session,
    address: str,
    state: str,
    zip_code: int,
) -> "Address":
    """Create a new Address row and return the persisted object."""
    new_address = Address(
        address=address,
        state=state,
        zip_code=zip_code,
    )
    session.add(new_address)
    session.commit()
    session.refresh(new_address)
    return get_address(session, new_address.address_id)


def get_address(session: Session, address_id: int) -> "Address | None":
    """Return Address object by primary key, or None if not found."""
    return session.get(Address, address_id)


def update_address(session: Session, new_address: "Address") -> bool:
    """Persist all field changes on an already-loaded Address object."""
    try:
        session.merge(new_address)
        session.commit()
        return True
    except Exception:
        session.rollback()
        return False
