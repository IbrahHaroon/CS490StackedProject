from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.recruiter import Recruiter


class RecruiterCredentials(Base):
    __tablename__ = "recruiter_credentials"

    credential_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    recruiter_id: Mapped[int] = mapped_column(
        ForeignKey("recruiter.recruiter_id"), nullable=False, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    recruiter: Mapped["Recruiter"] = relationship(back_populates="credentials")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_recruiter_credentials(
    session: Session, recruiter_id: int, hashed_password: str
) -> "RecruiterCredentials":
    """Create a RecruiterCredentials row for an existing Recruiter."""
    new_creds = RecruiterCredentials(
        recruiter_id=recruiter_id, hashed_password=hashed_password
    )
    session.add(new_creds)
    session.commit()
    session.refresh(new_creds)
    return get_recruiter_credentials_by_recruiter_id(session, new_creds.recruiter_id)


def get_recruiter_credentials_by_recruiter_id(
    session: Session, recruiter_id: int
) -> "RecruiterCredentials | None":
    """Return RecruiterCredentials for a given recruiter_id, or None if not found."""
    return session.execute(
        select(RecruiterCredentials).where(
            RecruiterCredentials.recruiter_id == recruiter_id
        )
    ).scalar_one_or_none()
