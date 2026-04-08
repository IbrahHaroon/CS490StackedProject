import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
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
