from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs
    from database.models.documents import Documents


class DocumentJobLink(Base):
    __tablename__ = "document_job_link"

    link_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_id: Mapped[int] = mapped_column(ForeignKey("documents.doc_id"), nullable=False)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False
    )
    linked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    document: Mapped["Documents"] = relationship()
    job: Mapped["AppliedJobs"] = relationship()


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def link_document_to_job(
    session: Session, doc_id: int, job_id: int
) -> "DocumentJobLink":
    """Link a document to a job. Returns existing link if already linked."""
    existing = session.execute(
        select(DocumentJobLink).where(
            DocumentJobLink.doc_id == doc_id,
            DocumentJobLink.job_id == job_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return existing

    link = DocumentJobLink(
        doc_id=doc_id,
        job_id=job_id,
        linked_at=datetime.utcnow(),
    )
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def unlink_document_from_job(session: Session, doc_id: int, job_id: int) -> bool:
    """Remove a document-job link. Returns True if removed, False if not found."""
    link = session.execute(
        select(DocumentJobLink).where(
            DocumentJobLink.doc_id == doc_id,
            DocumentJobLink.job_id == job_id,
        )
    ).scalar_one_or_none()

    if link is None:
        return False

    session.delete(link)
    session.commit()
    return True


def get_documents_for_job(session: Session, job_id: int) -> list["DocumentJobLink"]:
    """Return all document links for a job."""
    rows = (
        session.execute(
            select(DocumentJobLink)
            .where(DocumentJobLink.job_id == job_id)
            .order_by(DocumentJobLink.linked_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def get_jobs_for_document(session: Session, doc_id: int) -> list["DocumentJobLink"]:
    """Return all job links for a document."""
    rows = (
        session.execute(
            select(DocumentJobLink)
            .where(DocumentJobLink.doc_id == doc_id)
            .order_by(DocumentJobLink.linked_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)
