from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.recruiter import Recruiter


class RecruiterPasswordResetToken(Base):
    __tablename__ = "recruiter_password_reset_token"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recruiter_id: Mapped[int] = mapped_column(
        ForeignKey("recruiter.recruiter_id"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recruiter: Mapped["Recruiter"] = relationship()
