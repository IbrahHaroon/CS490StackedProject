from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.document_version import DocumentVersion
    from database.models.job import Job


class JobDocumentLink(Base):
    """N:N between a Job and a specific DocumentVersion.

    `role` distinguishes the document's purpose for that job
    (e.g. 'resume', 'cover_letter', 'ai_draft').
    """

    __tablename__ = "job_document_link"

    link_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("job.job_id", ondelete="CASCADE"), nullable=False
    )
    version_id: Mapped[int] = mapped_column(
        ForeignKey("document_version.version_id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linked_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )

    # Relationships
    job: Mapped["Job"] = relationship(back_populates="document_links")
    version: Mapped["DocumentVersion"] = relationship(back_populates="job_links")

    __table_args__ = (UniqueConstraint("job_id", "version_id", "role"),)


def link_version_to_job(
    session: Session, *, job_id: int, version_id: int, role: str | None = None
) -> "JobDocumentLink | None":
    """Create a link if one doesn't already exist for this (job, version, role)."""
    existing = session.execute(
        select(JobDocumentLink)
        .where(JobDocumentLink.job_id == job_id)
        .where(JobDocumentLink.version_id == version_id)
        .where(JobDocumentLink.role == role)
    ).scalar_one_or_none()
    if existing:
        return existing
    link = JobDocumentLink(
        job_id=job_id, version_id=version_id, role=role, linked_at=datetime.utcnow()
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def unlink(session: Session, link_id: int) -> bool:
    link = session.get(JobDocumentLink, link_id)
    if link is None:
        return False
    session.delete(link)
    session.commit()
    return True


def get_links_for_job(session: Session, job_id: int) -> list["JobDocumentLink"]:
    rows = (
        session.execute(
            select(JobDocumentLink).where(JobDocumentLink.job_id == job_id)
        )
        .scalars()
        .all()
    )
    return list(rows)
