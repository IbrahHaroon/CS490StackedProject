from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Documents(Base):
    __tablename__ = "documents"

    doc_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("doc_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_location: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="documents")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_document(
    session: Session,
    user_id: int,
    document_type: str,
    document_location: str,
) -> "Documents":
    """Create a new Document row and return the persisted object."""
    new_doc = Documents(
        user_id=user_id,
        document_type=document_type,
        document_location=document_location,
    )
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)
    return get_document(session, new_doc.doc_id)


def get_document(session: Session, doc_id: int) -> "Documents | None":
    """Return Document object by primary key, or None if not found."""
    return session.get(Documents, doc_id)


def lookup_documents(session: Session, user_id: int) -> int:
    """Return the number of documents a user has."""
    return (
        session.execute(
            select(func.count())
            .select_from(Documents)
            .where(Documents.user_id == user_id)
        ).scalar()
        or 0
    )


def get_all_documents(session: Session, user_id: int) -> tuple["Documents", ...]:
    """Return all documents belonging to a user as a tuple."""
    rows = (
        session.execute(select(Documents).where(Documents.user_id == user_id))
        .scalars()
        .all()
    )
    return tuple(rows)
