from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.applied_jobs import get_applied_jobs
from database.models.job_document import (
    create_job_document,
    delete_job_document,
    get_job_document,
    get_job_documents,
    update_job_document,
)
from database.models.user import User
from schemas import JobDocumentCreate, JobDocumentResponse, JobDocumentUpdate

router = APIRouter()


@router.post(
    "/jobs/{job_id}/documents",
    response_model=JobDocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_job_document(
    job_id: int,
    body: JobDocumentCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a document (draft, generated content, etc.) linked to a job."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return create_job_document(
        session,
        job_id=job_id,
        title=body.title,
        content=body.content,
    )


@router.get("/jobs/{job_id}/documents", response_model=list[JobDocumentResponse])
def get_documents_for_job(
    job_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all documents for a job application."""
    job = get_applied_jobs(session, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job application not found"
        )
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return get_job_documents(session, job_id)


@router.put("/documents/{document_id}", response_model=JobDocumentResponse)
def update_document(
    document_id: int,
    body: JobDocumentUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing job document."""
    doc = get_job_document(session, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    job = get_applied_jobs(session, doc.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    updated = update_job_document(
        session,
        document_id,
        title=body.title,
        content=body.content,
    )
    return updated


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a job document."""
    doc = get_job_document(session, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    job = get_applied_jobs(session, doc.job_id)
    if job.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    delete_job_document(session, document_id)
