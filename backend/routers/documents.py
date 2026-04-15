import base64
import os

from docx import Document as DocxDocument
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PyPDF2 import PdfReader
from sqlalchemy.orm import Session

from database import get_db
from database.auth import get_current_user
from database.database import get_settings
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


def _write_pdf_content(file_path: str, content: str) -> None:
    """
    Write text content to a PDF file.
    Creates a new PDF with the edited text content as plain text pages.
    """
    try:
        from io import BytesIO

        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        # Create document in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Build content
        story = []
        styles = getSampleStyleSheet()

        # Add the edited text as paragraphs
        for line in content.split("\n"):
            if line.strip():
                p = Paragraph(line, styles["Normal"])
                story.append(p)
                story.append(Spacer(1, 0.12 * inch))

        # Build PDF
        doc.build(story)

        # Write to file
        buffer.seek(0)
        with open(file_path, "wb") as f:
            f.write(buffer.read())
    except ImportError:
        raise ValueError(
            "reportlab library not available. PDF editing requires reportlab package."
        )
    except Exception as e:
        raise ValueError(f"Failed to write PDF content: {str(e)}")


def _update_file_content(file_path: str, filename: str, content: str) -> None:
    """Update file content based on file extension."""
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt" or ext == ".md":
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    elif ext == ".docx":
        _write_docx_content(file_path, content)
    elif ext == ".pdf":
        _write_pdf_content(file_path, content)
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
            "editable": True,
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


def _build_position_context(pos) -> str:
    """Build a job context string from a Position ORM object."""
    company_name = pos.company.name if pos.company else "Unknown"
    ctx = ["\nTARGET JOB:", f"Title: {pos.title}", f"Company: {company_name}"]
    if pos.location_type:
        ctx.append(f"Location Type: {pos.location_type}")
    if pos.location:
        ctx.append(f"Location: {pos.location}")
    if pos.description:
        ctx.append(f"Job Description:\n{pos.description}")
    if pos.experience_req:
        ctx.append(f"Experience Required: {pos.experience_req}")
    if pos.education_req:
        ctx.append(f"Education Required: {pos.education_req}")
    return "\n".join(ctx)


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
        except Exception:
            pass  # File cleanup is best-effort; DB record is authoritative

    result = delete_document(session, doc_id)
    if not result:
        raise HTTPException(
            status_code=500, detail="Failed to delete document from database"
        )


@router.post("/generate-resume")
def generate_resume_from_profile(
    body: dict,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a tailored resume draft using OpenAI from the user's profile and optional job context."""
    from datetime import date as date_class

    import openai

    from database.models.education import get_educations_by_user
    from database.models.experience import get_experiences_by_user
    from database.models.skills import get_skills_by_user

    profile = get_profile_by_user_id(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile not found — create a profile before generating a resume",
        )

    experiences = get_experiences_by_user(session, current_user.user_id)
    educations = get_educations_by_user(session, current_user.user_id)
    skills = get_skills_by_user(session, current_user.user_id)

    # Build profile context string
    lines = [f"Name: {profile.first_name} {profile.last_name}"]
    if profile.phone_number:
        lines.append(f"Phone: {profile.phone_number}")
    if profile.summary:
        lines.append(f"Summary: {profile.summary}")

    if experiences:
        lines.append("\nWORK EXPERIENCE:")
        for exp in experiences:
            end = exp.end_date.strftime("%b %Y") if exp.end_date else "Present"
            lines.append(
                f"  {exp.title} at {exp.company} ({exp.start_date.strftime('%b %Y')} - {end})"
            )
            if exp.description:
                lines.append(f"  {exp.description}")

    if educations:
        lines.append("\nEDUCATION:")
        for edu in educations:
            field = f" in {edu.field_of_study}" if edu.field_of_study else ""
            lines.append(f"  {edu.degree}{field} — {edu.school_or_college}")
            if edu.gpa:
                lines.append(f"  GPA: {edu.gpa}")
            if edu.start_date and edu.end_date:
                lines.append(f"  {edu.start_date.year} - {edu.end_date.year}")

    if skills:
        lines.append("\nSKILLS:")
        lines.append("  " + ", ".join(s.name for s in skills))

    profile_text = "\n".join(lines)

    # Fetch job context — accept either job_id (applied application) or position_id (listing)
    job_context = ""
    job_id = body.get("job_id")
    position_id = body.get("position_id")
    resolved_job_id = None  # for linking the saved document
    job_label = ""  # used in the document name

    if job_id:
        from database.models.applied_jobs import get_applied_jobs

        applied_job = get_applied_jobs(session, job_id)
        if applied_job and applied_job.user_id == current_user.user_id:
            job_context = _build_position_context(applied_job.position)
            resolved_job_id = job_id
            company_name = (
                applied_job.position.company.name
                if applied_job.position.company
                else ""
            )
            job_label = (
                f" - {applied_job.position.title} @ {company_name}"
                if company_name
                else f" - {applied_job.position.title}"
            )
    elif position_id:
        from database.models.applied_jobs import get_applied_job_by_position
        from database.models.position import get_position

        pos = get_position(session, position_id)
        if pos:
            job_context = _build_position_context(pos)
            company_name = pos.company.name if pos.company else ""
            job_label = (
                f" - {pos.title} @ {company_name}"
                if company_name
                else f" - {pos.title}"
            )
            # Link to an existing application for this position if one exists
            existing_app = get_applied_job_by_position(
                session, current_user.user_id, position_id
            )
            if existing_app:
                resolved_job_id = existing_app.job_id

    settings = get_settings()
    api_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file.",
        )

    instructions = body.get("instructions", "").strip()

    system_prompt = (
        "You are an expert resume writer and career coach. "
        "Create a professional, ATS-friendly resume draft from the provided profile data. "
        "Rules:\n"
        "- Use clear, professional plain-text formatting with standard resume sections\n"
        "- Use strong action verbs and quantify achievements where possible\n"
        "- Tailor content to highlight relevant skills for the target job if one is provided\n"
        "- Keep the resume concise and impactful (1-2 pages of content)\n"
        "- Return ONLY the resume content — no explanations, preamble, or markdown code blocks\n"
        "- Format with clear section headers (CONTACT INFORMATION, PROFESSIONAL SUMMARY, WORK EXPERIENCE, EDUCATION, SKILLS)\n"
        "- Use plain text suitable for saving as a .txt file"
    )

    user_message = (
        f"Generate a professional resume from this profile:\n\n{profile_text}"
    )
    if job_context:
        user_message += f"\n\n{job_context}"
    if instructions:
        user_message += f"\n\nAdditional instructions: {instructions}"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
            temperature=0.7,
        )
        generated_content = response.choices[0].message.content.strip()
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid OpenAI API key. Please check your OPENAI_API_KEY configuration.",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI rate limit reached. Please try again in a moment.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume generation failed: {str(e)}",
        )

    doc_name = f"AI Resume{job_label} - {date_class.today().strftime('%Y-%m-%d')}.txt"
    new_doc = create_document(
        session,
        current_user.user_id,
        "Resume",
        document_name=doc_name,
        content=generated_content,
        job_id=resolved_job_id,
    )

    return {
        "doc_id": new_doc.doc_id,
        "content": generated_content,
        "document_name": doc_name,
    }


@router.post("/generate-cover-letter")
def generate_cover_letter(
    body: dict,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a tailored cover letter using OpenAI from the user's profile and job context."""
    from datetime import date as date_class

    import openai

    from database.models.experience import get_experiences_by_user
    from database.models.skills import get_skills_by_user

    profile = get_profile_by_user_id(session, current_user.user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User profile not found — create a profile before generating a cover letter",
        )

    experiences = get_experiences_by_user(session, current_user.user_id)
    skills = get_skills_by_user(session, current_user.user_id)

    lines = [f"Name: {profile.first_name} {profile.last_name}"]
    if profile.phone_number:
        lines.append(f"Phone: {profile.phone_number}")
    if profile.summary:
        lines.append(f"Professional Summary: {profile.summary}")

    if experiences:
        lines.append("\nWORK EXPERIENCE:")
        for exp in experiences:
            end = exp.end_date.strftime("%b %Y") if exp.end_date else "Present"
            lines.append(
                f"  {exp.title} at {exp.company} ({exp.start_date.strftime('%b %Y')} - {end})"
            )
            if exp.description:
                lines.append(f"  {exp.description}")

    if skills:
        lines.append("\nSKILLS:")
        lines.append("  " + ", ".join(s.name for s in skills))

    profile_text = "\n".join(lines)

    # Resolve job context
    job_context = ""
    job_id = body.get("job_id")
    position_id = body.get("position_id")
    resolved_job_id = None
    job_label = ""  # used in the document name

    if job_id:
        from database.models.applied_jobs import get_applied_jobs

        applied_job = get_applied_jobs(session, job_id)
        if applied_job and applied_job.user_id == current_user.user_id:
            job_context = _build_position_context(applied_job.position)
            resolved_job_id = job_id
            company_name = (
                applied_job.position.company.name
                if applied_job.position.company
                else ""
            )
            job_label = (
                f" - {applied_job.position.title} @ {company_name}"
                if company_name
                else f" - {applied_job.position.title}"
            )
    elif position_id:
        from database.models.applied_jobs import get_applied_job_by_position
        from database.models.position import get_position

        pos = get_position(session, position_id)
        if pos:
            job_context = _build_position_context(pos)
            company_name = pos.company.name if pos.company else ""
            job_label = (
                f" - {pos.title} @ {company_name}"
                if company_name
                else f" - {pos.title}"
            )
            # Link to an existing application for this position if one exists
            existing_app = get_applied_job_by_position(
                session, current_user.user_id, position_id
            )
            if existing_app:
                resolved_job_id = existing_app.job_id

    settings = get_settings()
    api_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file.",
        )

    instructions = body.get("instructions", "").strip()

    system_prompt = (
        "You are an expert career coach and professional writer specializing in cover letters. "
        "Write a compelling, personalized cover letter based on the provided profile and job details. "
        "Rules:\n"
        "- Address the letter to the hiring team at the specific company if known\n"
        "- Open with a strong hook that connects the candidate's background to the role\n"
        "- Highlight 2-3 most relevant experiences or skills from the profile that match the job\n"
        "- Keep it to 3-4 paragraphs — concise and impactful\n"
        "- Close with a clear call to action (requesting an interview)\n"
        "- Return ONLY the cover letter content — no explanations or preamble\n"
        "- Use plain text suitable for saving as a .txt file\n"
        "- Sign off with the candidate's name"
    )

    user_message = f"Write a cover letter for this candidate:\n\n{profile_text}"
    if job_context:
        user_message += f"\n\n{job_context}"
    else:
        user_message += (
            "\n\nNote: No specific job was provided — write a general cover letter."
        )
    if instructions:
        user_message += f"\n\nAdditional instructions: {instructions}"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2048,
            temperature=0.7,
        )
        generated_content = response.choices[0].message.content.strip()
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid OpenAI API key. Please check your OPENAI_API_KEY configuration.",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI rate limit reached. Please try again in a moment.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation failed: {str(e)}",
        )

    doc_name = (
        f"AI Cover Letter{job_label} - {date_class.today().strftime('%Y-%m-%d')}.txt"
    )
    new_doc = create_document(
        session,
        current_user.user_id,
        "Cover Letter",
        document_name=doc_name,
        content=generated_content,
        job_id=resolved_job_id,
    )

    return {
        "doc_id": new_doc.doc_id,
        "content": generated_content,
        "document_name": doc_name,
    }


@router.post("/{doc_id}/ai-rewrite")
def ai_rewrite_document(
    doc_id: int,
    body: dict,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Use OpenAI to suggest improvements to a document's content."""
    import openai

    document = get_document(session, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if document.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document",
        )

    # Extract text content from the document
    original_content = None
    if document.content:
        original_content = document.content
    elif document.document_location:
        if not os.path.exists(document.document_location):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document file not found on server. Please re-upload the file.",
            )
        # Derive extension from name, fall back to location path
        ext = os.path.splitext(document.document_name or "")[1].lower()
        if not ext:
            ext = os.path.splitext(document.document_location)[1].lower()
        try:
            if ext == ".pdf":
                original_content = _extract_pdf_content(document.document_location)
            elif ext == ".docx":
                original_content = _extract_docx_content(document.document_location)
            elif ext in (".txt", ".md"):
                with open(document.document_location, "r", encoding="utf-8") as f:
                    original_content = f.read()
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type '{ext}'. Only PDF, DOCX, TXT, and MD files are supported.",
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read document content: {str(e)}",
            )

    if not original_content or not original_content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document appears to be empty or contains no extractable text. If this is a scanned PDF, please use a text-based PDF or paste the content manually.",
        )

    settings = get_settings()
    api_key = os.environ.get("OPENAI_API_KEY") or settings.openai_api_key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file.",
        )

    doc_type = document.document_type or "document"
    instructions = body.get("instructions", "").strip()

    system_prompt = (
        f"You are an expert career coach and professional writer specializing in {doc_type.lower()} writing. "
        "Your task is to improve the provided content to make it more professional, impactful, and compelling. "
        "Rules:\n"
        "- Preserve ALL factual information (names, dates, companies, roles, technologies, metrics)\n"
        "- Improve action verbs and make language more dynamic\n"
        "- Enhance clarity and conciseness\n"
        "- Ensure consistent formatting and parallel structure\n"
        "- Make it ATS-friendly by using strong keywords\n"
        "- Return ONLY the improved content — no explanations, no preamble, no markdown code blocks\n"
        "- Match the original document's structure and section ordering"
    )

    user_message = f"Please improve the following {doc_type.lower()} content:\n\n{original_content}"
    if instructions:
        user_message += f"\n\nAdditional instructions: {instructions}"

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=4096,
            temperature=0.7,
        )
        improved_content = response.choices[0].message.content.strip()
    except openai.AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid OpenAI API key. Please check your OPENAI_API_KEY configuration.",
        )
    except openai.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI rate limit reached. Please try again in a moment.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI rewrite failed: {str(e)}",
        )

    return {"original": original_content, "improved": improved_content}
