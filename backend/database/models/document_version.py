from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.documents import Documents


class DocumentVersion(Base):
    __tablename__ = "document_version"

    version_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.doc_id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    document: Mapped["Documents"] = relationship(back_populates="versions")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_version(
    session: Session,
    doc_id: int,
    content: str | None = None,
    document_location: str | None = None,
) -> "DocumentVersion":
    """Snapshot the current state of a document as a new version.

    The version_number is auto-calculated as max(existing) + 1 for the document.
    """
    max_version = (
        session.execute(
            select(func.max(DocumentVersion.version_number)).where(
                DocumentVersion.doc_id == doc_id
            )
        ).scalar()
        or 0
    )
    version = DocumentVersion(
        doc_id=doc_id,
        version_number=max_version + 1,
        content=content,
        document_location=document_location,
        created_at=datetime.utcnow(),
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def get_versions(session: Session, doc_id: int) -> list["DocumentVersion"]:
    """Return all versions for a document ordered by version_number ascending."""
    rows = (
        session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.doc_id == doc_id)
            .order_by(DocumentVersion.version_number)
        )
        .scalars()
        .all()
    )
    return list(rows)


def get_version(session: Session, version_id: int) -> "DocumentVersion | None":
    """Return a single version by primary key, or None if not found."""
    return session.get(DocumentVersion, version_id)


def get_latest_version(session: Session, doc_id: int) -> "DocumentVersion | None":
    """Return the highest version_number entry for a document, or None."""
    return (
        session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.doc_id == doc_id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
