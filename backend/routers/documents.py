import base64
import os

from docx import Document as DocxDocument
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.models.documents import create_document, get_all_documents, get_document
from database.models.profile import get_profile_by_user_id
from database.models.user import User
from schemas import DocumentCreate, DocumentResponse

router = APIRouter()

# Base directory where uploaded files are stored (sibling of backend/ directory)
_ROUTERS_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_ROUTERS_DIR)
UPLOAD_BASE = os.path.join(_BACKEND_DIR, "uploads")


def _extract_pdf_content(file_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        with open(file_path, "rb") as f:
            pdf_reader = PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract PDF content: {str(e)}")


def _extract_docx_content(file_path: str) -> str:
    """Extract text content from a DOCX file."""
    try:
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract DOCX content: {str(e)}")


def _write_docx_content(file_path: str, content: str) -> None:
    """Write text content to a DOCX file."""
    try:
        doc = DocxDocument()
        # Split content by newlines and add as paragraphs
        for line in content.split("\n"):
            doc.add_paragraph(line)
        doc.save(file_path)
    except Exception as e:
        raise ValueError(f"Failed to write DOCX content: {str(e)}")


def _update_file_content(file_path: str, filename: str, content: str) -> None:
    """Update file content based on file extension."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt" or ext == ".md":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif ext == ".docx":
        _write_docx_content(file_path, content)
    elif ext == ".pdf":
        # PDF editing not supported - text extraction only
        raise ValueError(
            "PDF editing via text extraction not yet implemented. Please use DOCX or TXT."
        )
    else:
        raise ValueError(f"Unsupported file type for editing: {ext}")


def _get_file_content_and_format(file_path: str, filename: str) -> dict:
    """
    Get file content and return it with format info.
    For text files, returns the text. For binary files, returns base64-encoded data.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        text_content = _extract_pdf_content(file_path)
        # Also return base64-encoded PDF for display
        with open(file_path, "rb") as f:
            pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
        return {
            "content": text_content,
            "format": "pdf",
            "binary_data": pdf_base64,
            "editable": False,  # PDF viewing only for now
        }
    elif ext == ".docx":
        text_content = _extract_docx_content(file_path)
        return {
            "content": text_content,
            "format": "docx",
            "editable": True,
        }
    elif ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "content": content,
            "format": ext[1:],  # "txt" or "md"
            "editable": True,
        }
    else:
        return {
            "content": f"[Unsupported file type: {ext}]",
            "format": "unknown",
            "editable": False,
        }


def _build_upload_path(
    base: str, first_name: str, last_name: str, user_id: int, filename: str
) -> str:
    """Return the full filesystem path for an uploaded file."""
    last_initial = last_name[0].upper()
    first_initial = first_name[0].upper()
    full_name = f"{first_name} {last_name}"
    return os.path.join(
        base, last_initial, first_initial, full_name, str(user_id), filename
    )


@router.post(
    "/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_profile_by_user_id(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile not found — create a profile before uploading documents",
        )

    dest_path = _build_upload_path(
        UPLOAD_BASE,
        profile.first_name,
        profile.last_name,
        current_user.user_id,
        file.filename,
    )
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    return create_document(
        session,
        current_user.user_id,
        document_type,
        document_location=dest_path,
        document_name=file.filename,
    )


@router.get("/me", response_model=list[DocumentResponse])
def read_my_documents(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list(get_all_documents(session, current_user.user_id))


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document_endpoint(body: DocumentCreate, session: Session = Depends(get_db)):
    return create_document(
        session,
        body.user_id,
        body.document_type,
        document_location=body.document_location,
        job_id=body.job_id,
        document_name=body.document_name,
        content=body.content,
    )


@router.get("/user/{user_id}", response_model=list[DocumentResponse])
def read_all_documents(user_id: int, session: Session = Depends(get_db)):
    return list(get_all_documents(session, user_id))


@router.get("/{doc_id}", response_model=DocumentResponse)
def read_document(doc_id: int, session: Session = Depends(get_db)):
    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{doc_id}/content")
def read_document_content(
    doc_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Read document content (for viewing/editing resumes and documents)."""
    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this document",
        )

    # If document has stored content (text-based)
    if document.content:
        return {"content": document.content, "format": "text"}

    # If document is a file, try to read it
    if document.document_location and os.path.exists(document.document_location):
        try:
            file_info = _get_file_content_and_format(
                document.document_location, document.document_name
            )
            return file_info
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to read file: {str(e)}",
            )

    raise HTTPException(
        status_code=404, detail="Document content not found or not accessible"
    )


@router.put("/{doc_id}", response_model=DocumentResponse)
def update_document_content(
    doc_id: int,
    body: dict,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update document content (for editing resumes and documents)."""
    from database.models.documents import update_document

    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to edit this document",
        )

    content = body.get("content")
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content field is required",
        )

    # If document is stored in database, update directly
    if document.content is not None:
        updated_doc = update_document(session, doc_id, content=content)
        return updated_doc

    # If document is a file, update the file and also store in DB
    if document.document_location and os.path.exists(document.document_location):
        try:
            _update_file_content(
                document.document_location, document.document_name, content
            )
            # Also store in DB for quick access
            updated_doc = update_document(session, doc_id, content=content)
            return updated_doc
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update document: {str(e)}",
            )

    raise HTTPException(status_code=404, detail="Document not found or not accessible")


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_endpoint(
    doc_id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document."""
    from database.models.documents import delete_document

    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this document",
        )

    # Delete file from disk if it exists
    if document.document_location and os.path.exists(document.document_location):
        try:
            os.remove(document.document_location)
        except Exception as e:
            print(f"Warning: Could not delete file {document.document_location}: {e}")

    delete_document(session, doc_id)
