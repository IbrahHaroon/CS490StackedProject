from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.applied_jobs import AppliedJobs
    from database.models.career_preferences import CareerPreferences
    from database.models.credentials import Credentials
    from database.models.documents import Documents
    from database.models.education import Education
    from database.models.experience import Experience
    from database.models.profile import Profile
    from database.models.skills import Skills


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Relationships
    credentials: Mapped["Credentials"] = relationship(
        back_populates="user", uselist=False
    )
    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)
    educations: Mapped[list["Education"]] = relationship(back_populates="user")
    documents: Mapped[list["Documents"]] = relationship(back_populates="user")
    applied_jobs: Mapped[list["AppliedJobs"]] = relationship(back_populates="user")
    experiences: Mapped[list["Experience"]] = relationship(back_populates="user")
    skills: Mapped[list["Skills"]] = relationship(back_populates="user")
    career_preferences: Mapped["CareerPreferences | None"] = relationship(
        back_populates="user", uselist=False
    )


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_user(session: Session, email: str) -> "User":
    """Create a new User row and return the persisted object."""
    new_user = User(email=email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return get_user(session, new_user.user_id)


def get_user(session: Session, user_id: int) -> "User | None":
    """Return User object by primary key, or None if not found."""
    return session.get(User, user_id)


def get_user_by_email(session: Session, email: str) -> "User | None":
    """Return User object by email address, or None if not found."""
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()
