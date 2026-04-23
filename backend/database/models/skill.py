from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

from database.base import Base

if TYPE_CHECKING:
    from database.models.user import User


class Skill(Base):
    __tablename__ = "skill"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="skills")


def create_skill(
    session: Session,
    user_id: int,
    name: str,
    *,
    category: str | None = None,
    proficiency: str | None = None,
    sort_order: int = 0,
) -> "Skill":
    skill = Skill(
        user_id=user_id,
        name=name,
        category=category,
        proficiency=proficiency,
        sort_order=sort_order,
    )
    session.add(skill)
    session.commit()
    session.refresh(skill)
    return skill


def get_skill(session: Session, skill_id: int) -> "Skill | None":
    return session.get(Skill, skill_id)


def get_skills_for_user(session: Session, user_id: int) -> list["Skill"]:
    rows = (
        session.execute(
            select(Skill).where(Skill.user_id == user_id).order_by(Skill.sort_order)
        )
        .scalars()
        .all()
    )
    return list(rows)


def update_skill(
    session: Session,
    skill_id: int,
    *,
    name: str | None = None,
    category: str | None = None,
    proficiency: str | None = None,
    sort_order: int | None = None,
) -> "Skill | None":
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
    skill = get_skill(session, skill_id)
    if skill is None:
        return False
    session.delete(skill)
    session.commit()
    return True
