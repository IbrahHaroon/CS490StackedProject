"""
Tests for the Skills model and its CRUD helper functions.
Covers S2-018 (Skills Section CRUD).
"""

from database.models.skills import (
    create_skill,
    delete_skill,
    get_skill,
    get_skills_by_user,
    update_skill,
)
from database.models.user import create_user

# ---------------------------------------------------------------------------
# TestCreateSkill
# ---------------------------------------------------------------------------


class TestCreateSkill:
    def test_creates_with_name_only(self, session):
        user = create_user(session, "a@test.com")
        skill = create_skill(session, user_id=user.user_id, name="Python")
        assert skill.skill_id is not None
        assert skill.user_id == user.user_id
        assert skill.name == "Python"
        assert skill.category is None
        assert skill.proficiency is None

    def test_creates_with_all_fields(self, session):
        user = create_user(session, "b@test.com")
        skill = create_skill(
            session,
            user_id=user.user_id,
            name="React",
            category="Frontend",
            proficiency="Expert",
            sort_order=1,
        )
        assert skill.category == "Frontend"
        assert skill.proficiency == "Expert"
        assert skill.sort_order == 1

    def test_default_sort_order_is_zero(self, session):
        user = create_user(session, "c@test.com")
        skill = create_skill(session, user_id=user.user_id, name="SQL")
        assert skill.sort_order == 0


# ---------------------------------------------------------------------------
# TestGetSkill
# ---------------------------------------------------------------------------


class TestGetSkill:
    def test_returns_by_id(self, session):
        user = create_user(session, "d@test.com")
        created = create_skill(session, user_id=user.user_id, name="Go")
        fetched = get_skill(session, created.skill_id)
        assert fetched is not None
        assert fetched.skill_id == created.skill_id

    def test_returns_none_for_missing_id(self, session):
        assert get_skill(session, 99999) is None


# ---------------------------------------------------------------------------
# TestGetSkillsByUser
# ---------------------------------------------------------------------------


class TestGetSkillsByUser:
    def test_returns_all_for_user(self, session):
        user = create_user(session, "e@test.com")
        create_skill(session, user_id=user.user_id, name="Python", sort_order=0)
        create_skill(session, user_id=user.user_id, name="Go", sort_order=1)
        results = get_skills_by_user(session, user.user_id)
        assert len(results) == 2

    def test_isolation_across_users(self, session):
        user_a = create_user(session, "f@test.com")
        user_b = create_user(session, "g@test.com")
        create_skill(session, user_id=user_a.user_id, name="Python")
        assert get_skills_by_user(session, user_b.user_id) == []

    def test_returns_empty_list_when_no_skills(self, session):
        user = create_user(session, "h@test.com")
        assert get_skills_by_user(session, user.user_id) == []


# ---------------------------------------------------------------------------
# TestUpdateSkill
# ---------------------------------------------------------------------------


class TestUpdateSkill:
    def test_updates_proficiency(self, session):
        user = create_user(session, "i@test.com")
        skill = create_skill(session, user_id=user.user_id, name="Python")
        updated = update_skill(session, skill.skill_id, proficiency="Expert")
        assert updated.proficiency == "Expert"

    def test_updates_category(self, session):
        user = create_user(session, "j@test.com")
        skill = create_skill(session, user_id=user.user_id, name="Docker")
        updated = update_skill(session, skill.skill_id, category="DevOps")
        assert updated.category == "DevOps"

    def test_updates_sort_order(self, session):
        user = create_user(session, "k@test.com")
        skill = create_skill(session, user_id=user.user_id, name="Kubernetes")
        updated = update_skill(session, skill.skill_id, sort_order=3)
        assert updated.sort_order == 3

    def test_returns_none_for_missing_id(self, session):
        assert update_skill(session, 99999, name="X") is None


# ---------------------------------------------------------------------------
# TestDeleteSkill
# ---------------------------------------------------------------------------


class TestDeleteSkill:
    def test_deletes_existing(self, session):
        user = create_user(session, "l@test.com")
        skill = create_skill(session, user_id=user.user_id, name="Rust")
        assert delete_skill(session, skill.skill_id) is True
        assert get_skill(session, skill.skill_id) is None

    def test_returns_false_for_missing_id(self, session):
        assert delete_skill(session, 99999) is False
