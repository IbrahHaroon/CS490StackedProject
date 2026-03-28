from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from database.models.documents import create_document, get_document, get_all_documents
from schemas import DocumentCreate, DocumentResponse

router = APIRouter()


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def create_document_endpoint(body: DocumentCreate, session: Session = Depends(get_db)):
    return create_document(session, body.user_id, body.document_type, body.document_location)


@router.get("/user/{user_id}", response_model=list[DocumentResponse])
def read_all_documents(user_id: int, session: Session = Depends(get_db)):
    return list(get_all_documents(session, user_id))


@router.get("/{doc_id}", response_model=DocumentResponse)
def read_document(doc_id: int, session: Session = Depends(get_db)):
    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
