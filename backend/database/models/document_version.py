from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.document import Document
    from database.models.job_document_link import JobDocumentLink


class DocumentVersion(Base):
    """An immutable content snapshot for a Document."""

    __tablename__ = "document_version"

    version_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.document_id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_location: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        back_populates="versions", foreign_keys=[document_id]
    )
    job_links: Mapped[list["JobDocumentLink"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("document_id", "version_number"),)


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_document_version(
    session: Session,
    document_id: int,
    *,
    storage_location: str | None = None,
    content: str | None = None,
    source: str | None = None,
) -> "DocumentVersion":
    """Create the next version for a document (auto-increments version_number)."""
    next_num = (
        session.execute(
            select(func.coalesce(func.max(DocumentVersion.version_number), 0))
            .where(DocumentVersion.document_id == document_id)
        ).scalar()
        or 0
    ) + 1
    version = DocumentVersion(
        document_id=document_id,
        version_number=next_num,
        storage_location=storage_location,
        content=content,
        source=source,
        created_at=datetime.utcnow(),
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    return version


def get_document_version(
    session: Session, version_id: int
) -> "DocumentVersion | None":
    return session.get(DocumentVersion, version_id)


def get_versions_for_document(
    session: Session, document_id: int
) -> list["DocumentVersion"]:
    rows = (
        session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)
