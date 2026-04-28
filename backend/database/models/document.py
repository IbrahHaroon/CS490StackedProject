from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship, selectinload

from database.base import Base

if TYPE_CHECKING:
    from database.models.document_tag import DocumentTag
    from database.models.document_version import DocumentVersion
    from database.models.user import User


class Document(Base):
    """A user-owned document (resume, cover letter, AI draft, etc).

    Document content lives on `DocumentVersion` rows. `current_version_id`
    is denormalized for cheap "show the latest" queries.
    """

    __tablename__ = "document"

    document_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Draft")
    current_version_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("document_version.version_id", use_alter=True), nullable=True
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="DocumentVersion.document_id",
    )
    current_version: Mapped[Optional["DocumentVersion"]] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )
    tags: Mapped[list["DocumentTag"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_document_user", "user_id"),)


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_document(
    session: Session,
    user_id: int,
    title: str,
    document_type: str,
    *,
    status: str = "Draft",
) -> "Document":
    now = datetime.utcnow()
    doc = Document(
        user_id=user_id,
        title=title,
        document_type=document_type,
        status=status,
        created_at=now,
        updated_at=now,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document(session: Session, document_id: int) -> "Document | None":
    return session.get(Document, document_id)


def get_documents_for_user(
    session: Session, user_id: int, *, include_deleted: bool = False
) -> list["Document"]:
    stmt = (
        select(Document)
        .where(Document.user_id == user_id)
        .options(selectinload(Document.tags))
    )
    if not include_deleted:
        stmt = stmt.where(Document.is_deleted.is_(False))
    stmt = stmt.order_by(Document.updated_at.desc())
    return list(session.execute(stmt).scalars().all())


def update_document(
    session: Session,
    document_id: int,
    *,
    title: str | None = None,
    document_type: str | None = None,
    status: str | None = None,
    is_deleted: bool | None = None,
    current_version_id: int | None = None,
) -> "Document | None":
    doc = get_document(session, document_id)
    if doc is None:
        return None
    if title is not None:
        doc.title = title
    if document_type is not None:
        doc.document_type = document_type
    if status is not None:
        doc.status = status
    if is_deleted is not None:
        doc.is_deleted = is_deleted
    if current_version_id is not None:
        doc.current_version_id = current_version_id
    doc.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(doc)
    return doc


def hard_delete_document(session: Session, document_id: int) -> bool:
    """Permanent delete (cascades versions/tags). Prefer `is_deleted=True` for archive."""
    doc = get_document(session, document_id)
    if doc is None:
        return False
    session.delete(doc)
    session.commit()
    return True


def count_documents(session: Session, user_id: int) -> int:
    return (
        session.execute(
            select(func.count())
            .select_from(Document)
            .where(Document.user_id == user_id, Document.is_deleted.is_(False))
        ).scalar()
        or 0
    )
