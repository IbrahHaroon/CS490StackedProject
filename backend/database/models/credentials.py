from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Credentials(Base):
    __tablename__ = "credentials"

    credential_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id"), nullable=False, unique=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="credentials")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_credentials(
    session: Session, user_id: int, hashed_password: str
) -> "Credentials":
    """Create a Credentials row for an existing User."""
    new_creds = Credentials(user_id=user_id, hashed_password=hashed_password)
    session.add(new_creds)
    session.commit()
    session.refresh(new_creds)
    return get_credentials_by_user_id(session, new_creds.user_id)


def get_credentials_by_user_id(session: Session, user_id: int) -> "Credentials | None":
    """Return Credentials for a given user_id, or None if not found."""
    return session.execute(
        select(Credentials).where(Credentials.user_id == user_id)
    ).scalar_one_or_none()
