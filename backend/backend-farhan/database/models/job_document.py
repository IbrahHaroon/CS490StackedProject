from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Sequence, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs


class JobDocument(Base):
    __tablename__ = "job_document"

    job_document_id: Mapped[int] = mapped_column(
        Integer,
        Sequence("job_document_id_seq", start=1),
        primary_key=True,
        autoincrement=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("applied_jobs.job_id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(String(10000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    job: Mapped["AppliedJobs"] = relationship(back_populates="job_documents")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_job_document(
    session: Session,
    job_id: int,
    title: str,
    content: str,
) -> "JobDocument":
    """Create a new JobDocument row and return the persisted object."""
    now = datetime.utcnow()
    doc = JobDocument(
        job_id=job_id,
        title=title,
        content=content,
        created_at=now,
        updated_at=now,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_job_document(session: Session, job_document_id: int) -> "JobDocument | None":
    """Return JobDocument object by primary key, or None if not found."""
    return session.get(JobDocument, job_document_id)


def get_job_documents(session: Session, job_id: int) -> list["JobDocument"]:
    """Return all documents for a job ordered by creation date."""
    rows = (
        session.execute(
            select(JobDocument)
            .where(JobDocument.job_id == job_id)
            .order_by(JobDocument.created_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_job_document(
    session: Session,
    job_document_id: int,
    title: str | None = None,
    content: str | None = None,
) -> "JobDocument | None":
    """Update mutable fields on an existing job document. Returns None if not found."""
    doc = get_job_document(session, job_document_id)
    if doc is None:
        return None
    if title is not None:
        doc.title = title
    if content is not None:
        doc.content = content
    doc.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(doc)
    return doc


def delete_job_document(session: Session, job_document_id: int) -> bool:
    """Delete a job document by primary key. Returns True if deleted."""
    doc = get_job_document(session, job_document_id)
    if doc is None:
        return False
    session.delete(doc)
    session.commit()
    return True
