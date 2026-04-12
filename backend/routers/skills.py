from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from database.models.skills import (
    create_skill,
    delete_skill,
    get_skill,
    get_skills_by_user,
    update_skill,
)
from schemas import SkillCreate, SkillResponse, SkillUpdate

router = APIRouter()


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
def create_skill_endpoint(body: SkillCreate, session: Session = Depends(get_db)):
    return create_skill(
        session,
        user_id=body.user_id,
        name=body.name,
        category=body.category,
        proficiency=body.proficiency,
        sort_order=body.sort_order,
    )


@router.get("/user/{user_id}", response_model=list[SkillResponse])
def read_skills_by_user(user_id: int, session: Session = Depends(get_db)):
    return get_skills_by_user(session, user_id)


@router.get("/{skill_id}", response_model=SkillResponse)
def read_skill(skill_id: int, session: Session = Depends(get_db)):
    skill = get_skill(session, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill_endpoint(
    skill_id: int,
    body: SkillUpdate,
    session: Session = Depends(get_db),
):
    skill = get_skill(session, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(skill, field, value)
    session.commit()
    session.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill_endpoint(skill_id: int, session: Session = Depends(get_db)):
    if not delete_skill(session, skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
