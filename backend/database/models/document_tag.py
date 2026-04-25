from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.document import Document


class DocumentTag(Base):
    """One free-text tag attached to a document. Many tags per document."""

    __tablename__ = "document_tag"

    tag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.document_id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="tags")

    __table_args__ = (UniqueConstraint("document_id", "label"),)


def add_tag(session: Session, document_id: int, label: str) -> "DocumentTag | None":
    """Add a tag if not already present. Returns the existing or new row."""
    label = label.strip()
    if not label:
        return None
    existing = session.execute(
        select(DocumentTag)
        .where(DocumentTag.document_id == document_id)
        .where(DocumentTag.label == label)
    ).scalar_one_or_none()
    if existing:
        return existing
    tag = DocumentTag(document_id=document_id, label=label)
    session.add(tag)
    session.commit()
    session.refresh(tag)
    return tag


def remove_tag(session: Session, document_id: int, label: str) -> bool:
    tag = session.execute(
        select(DocumentTag)
        .where(DocumentTag.document_id == document_id)
        .where(DocumentTag.label == label)
    ).scalar_one_or_none()
    if tag is None:
        return False
    session.delete(tag)
    session.commit()
    return True


def get_tags_for_document(session: Session, document_id: int) -> list["DocumentTag"]:
    rows = (
        session.execute(
            select(DocumentTag).where(DocumentTag.document_id == document_id)
        )
        .scalars()
        .all()
    )
    return list(rows)
