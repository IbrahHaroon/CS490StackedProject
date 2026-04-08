from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Skills(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="skills")


# --------------------------------------------------------------------------- #
#  Functions                                                                    #
# --------------------------------------------------------------------------- #


def create_skill(
    session: Session,
    user_id: int,
    name: str,
    category: str | None = None,
    proficiency: str | None = None,
    sort_order: int = 0,
) -> "Skills":
    """Create a new Skills row and return the persisted object."""
    skill = Skills(
        user_id=user_id,
        name=name,
        category=category,
        proficiency=proficiency,
        sort_order=sort_order,
    )
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return get_skill(session, skill.skill_id)


def get_skill(session: Session, skill_id: int) -> "Skills | None":
    """Return Skills object by primary key, or None if not found."""
    return session.get(Skills, skill_id)


def get_skills_by_user(session: Session, user_id: int) -> list["Skills"]:
    """Return all skills for a user ordered by sort_order."""
    rows = (
        session.execute(
            select(Skills).where(Skills.user_id == user_id).order_by(Skills.sort_order)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_skill(
    session: Session,
    skill_id: int,
    name: str | None = None,
    category: str | None = None,
    proficiency: str | None = None,
    sort_order: int | None = None,
) -> "Skills | None":
    """Update mutable fields on an existing skill. Returns None if not found."""
    skill = get_skill(session, skill_id)
    if skill is None:
        return None
    if name is not None:
        skill.name = name
    if category is not None:
        skill.category = category
    if proficiency is not None:
        skill.proficiency = proficiency
    if sort_order is not None:
        skill.sort_order = sort_order
    session.commit()
    session.refresh(skill)
    return skill


def delete_skill(session: Session, skill_id: int) -> bool:
    """Delete a skill by primary key. Returns True if deleted."""
    skill = get_skill(session, skill_id)
    if skill is None:
        return False
    session.delete(skill)
    session.commit()
    return True
