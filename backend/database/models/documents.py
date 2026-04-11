from __future__ import annotations

import os
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Sequence, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs
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
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=True
    )
    document_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="documents")
    job: Mapped["AppliedJobs | None"] = relationship(back_populates="documents")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_document(
    session: Session,
    user_id: int,
    document_type: str,
    document_location: str | None = None,
    job_id: int | None = None,
    document_name: str | None = None,
    content: str | None = None,
) -> "Documents":
    """Create a new Document row and return the persisted object.

    For uploaded files, provide document_location (file path/URL).
    For AI-generated drafts, provide content (raw text) instead.
    """
    new_doc = Documents(
        user_id=user_id,
        job_id=job_id,
        document_name=document_name,
        document_type=document_type,
        document_location=document_location,
        content=content,
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


def delete_document(session: Session, doc_id: int, user_id: int) -> bool:
    """Delete a document owned by user_id. Returns True if deleted, False if not found."""
    doc = session.get(Documents, doc_id)
    if doc is None or doc.user_id != user_id:
        return False
    if doc.document_location and os.path.isfile(doc.document_location):
        os.remove(doc.document_location)
    session.delete(doc)
    session.commit()
    return True
