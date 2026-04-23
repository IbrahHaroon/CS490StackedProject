from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs
    from database.models.document_version import DocumentVersion
    from database.models.user import User


DOCUMENT_TYPES = ["Resume", "Cover Letter", "Portfolio", "Other"]
DOCUMENT_STATUSES = ["Draft", "Final", "Archived"]


class Documents(Base):
    __tablename__ = "documents"

    doc_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("doc_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    job_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=True
    )
    document_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    document_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default="Draft"
    )
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="documents")
    job: Mapped["Optional[AppliedJobs]"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


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
    title: str | None = None,
    content: str | None = None,
    status: str | None = None,
    tags: str | None = None,
) -> "Documents":
    """Create a new Document row and return the persisted object.

    For uploaded files, provide document_location (file path/URL).
    For AI-generated drafts, provide content (raw text) instead.
    """
    now = datetime.utcnow()
    new_doc = Documents(
        user_id=user_id,
        job_id=job_id,
        document_name=document_name,
        title=title,
        document_type=document_type,
        document_location=document_location,
        content=content,
        status=status or "Draft",
        tags=tags,
        created_at=now,
        updated_at=now,
        is_archived=False,
    )
    session.add(new_doc)
    session.commit()
    session.refresh(new_doc)
    return get_document(session, new_doc.doc_id)


def get_document(session: Session, doc_id: int) -> "Documents | None":
    """Return Document object by primary key, or None if not found."""
    print(
        f"[DB-GET] Looking up document with doc_id={doc_id} (type: {type(doc_id).__name__})"
    )
    result = session.get(Documents, doc_id)
    if result:
        print(
            f"[DB-GET] ✓ Found: doc_id={result.doc_id}, user_id={result.user_id}, name={result.document_name}"
        )
    else:
        print(f"[DB-GET] ❌ Not found - doc_id={doc_id}")
    return result


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
    """Return all non-archived documents belonging to a user."""
    rows = (
        session.execute(
            select(Documents)
            .where(Documents.user_id == user_id)
            .where(Documents.is_archived == False)  # noqa: E712
        )
        .scalars()
        .all()
    )
    return tuple(rows)


def get_archived_documents(session: Session, user_id: int) -> tuple["Documents", ...]:
    """Return all archived documents belonging to a user."""
    rows = (
        session.execute(
            select(Documents)
            .where(Documents.user_id == user_id)
            .where(Documents.is_archived == True)  # noqa: E712
        )
        .scalars()
        .all()
    )
    return tuple(rows)


def update_document(
    session: Session,
    doc_id: int,
    content: str | None = None,
    document_name: str | None = None,
    title: str | None = None,
    document_type: str | None = None,
    status: str | None = None,
    tags: str | None = None,
    is_archived: bool | None = None,
) -> "Documents | None":
    """Update document fields. Returns updated document or None if not found."""
    document = get_document(session, doc_id)
    if document is None:
        return None

    if content is not None:
        document.content = content
    if document_name is not None:
        document.document_name = document_name
    if title is not None:
        document.title = title
    if document_type is not None:
        document.document_type = document_type
    if status is not None:
        document.status = status
    if tags is not None:
        document.tags = tags
    if is_archived is not None:
        document.is_archived = is_archived

    document.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(document)
    return document


def delete_document(session: Session, doc_id: int) -> bool:
    """Delete a document by ID. Returns True if deleted, False if not found."""
    print(f"[DB-DELETE] Attempting to delete document {doc_id}")
    document = get_document(session, doc_id)
    if document is None:
        print(f"[DB-DELETE] ❌ Document {doc_id} not found in session.get()")
        return False

    try:
        print(f"[DB-DELETE] Calling session.delete() on document {doc_id}")
        session.delete(document)
        print(f"[DB-DELETE] Calling session.commit() for document {doc_id}")
        session.commit()
        print(f"[DB-DELETE] ✓ Successfully deleted document {doc_id}")
        return True
    except Exception as e:
        print(f"[DB-DELETE] ❌ Error deleting {doc_id}: {e}")
        print("[DB-DELETE] Rolling back transaction")
        session.rollback()
        return False
