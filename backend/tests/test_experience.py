"""
Tests for the Experience model and its CRUD helper functions.
Covers S2-016 (Experience Section CRUD).
"""

from datetime import date

from database.models.experience import (
    create_experience,
    delete_experience,
    get_experience,
    get_experiences_by_user,
    update_experience,
)
from database.models.user import create_user

# ---------------------------------------------------------------------------
# TestCreateExperience
# ---------------------------------------------------------------------------


class TestCreateExperience:
    def test_creates_with_required_fields(self, session):
        user = create_user(session, "a@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="Acme",
            title="Engineer",
            start_date=date(2023, 1, 1),
        )
        assert exp.experience_id is not None
        assert exp.user_id == user.user_id
        assert exp.company == "Acme"
        assert exp.title == "Engineer"
        assert exp.end_date is None
        assert exp.description is None

    def test_creates_with_optional_end_date_and_description(self, session):
        user = create_user(session, "b@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="Beta",
            title="Lead",
            start_date=date(2021, 6, 1),
            end_date=date(2023, 1, 1),
            description="Led a team of 5",
        )
        assert exp.end_date == date(2023, 1, 1)
        assert exp.description == "Led a team of 5"

    def test_default_sort_order_is_zero(self, session):
        user = create_user(session, "c@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="X",
            title="Y",
            start_date=date(2020, 1, 1),
        )
        assert exp.sort_order == 0


# ---------------------------------------------------------------------------
# TestGetExperience
# ---------------------------------------------------------------------------


class TestGetExperience:
    def test_returns_by_id(self, session):
        user = create_user(session, "d@test.com")
        created = create_experience(
            session,
            user_id=user.user_id,
            company="C",
            title="T",
            start_date=date(2022, 1, 1),
        )
        fetched = get_experience(session, created.experience_id)
        assert fetched is not None
        assert fetched.experience_id == created.experience_id

    def test_returns_none_for_missing_id(self, session):
        assert get_experience(session, 99999) is None


# ---------------------------------------------------------------------------
# TestGetExperiencesByUser
# ---------------------------------------------------------------------------


class TestGetExperiencesByUser:
    def test_returns_all_for_user(self, session):
        user = create_user(session, "e@test.com")
        create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="T1",
            start_date=date(2020, 1, 1),
            sort_order=0,
        )
        create_experience(
            session,
            user_id=user.user_id,
            company="B",
            title="T2",
            start_date=date(2022, 1, 1),
            sort_order=1,
        )
        results = get_experiences_by_user(session, user.user_id)
        assert len(results) == 2

    def test_isolation_across_users(self, session):
        user_a = create_user(session, "f@test.com")
        user_b = create_user(session, "g@test.com")
        create_experience(
            session,
            user_id=user_a.user_id,
            company="A",
            title="T",
            start_date=date(2020, 1, 1),
        )
        assert get_experiences_by_user(session, user_b.user_id) == []

    def test_returns_empty_list_for_user_with_none(self, session):
        user = create_user(session, "h@test.com")
        assert get_experiences_by_user(session, user.user_id) == []


# ---------------------------------------------------------------------------
# TestUpdateExperience
# ---------------------------------------------------------------------------


class TestUpdateExperience:
    def test_updates_title(self, session):
        user = create_user(session, "i@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="Old",
            start_date=date(2020, 1, 1),
        )
        updated = update_experience(session, exp.experience_id, title="New")
        assert updated.title == "New"

    def test_updates_sort_order(self, session):
        user = create_user(session, "j@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="T",
            start_date=date(2020, 1, 1),
        )
        updated = update_experience(session, exp.experience_id, sort_order=5)
        assert updated.sort_order == 5

    def test_clears_end_date_to_null(self, session):
        user = create_user(session, "k@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="T",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 1, 1),
        )
        assert exp.end_date is not None
        updated = update_experience(session, exp.experience_id, clear_end_date=True)
        assert updated.end_date is None

    def test_returns_none_for_missing_id(self, session):
        assert update_experience(session, 99999, title="X") is None


# ---------------------------------------------------------------------------
# TestDeleteExperience
# ---------------------------------------------------------------------------


class TestDeleteExperience:
    def test_deletes_existing(self, session):
        user = create_user(session, "l@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="T",
            start_date=date(2020, 1, 1),
        )
        assert delete_experience(session, exp.experience_id) is True
        assert get_experience(session, exp.experience_id) is None

    def test_returns_false_for_missing_id(self, session):
        assert delete_experience(session, 99999) is False

    def test_user_still_exists_after_delete(self, session):
        from database.models.user import get_user

        user = create_user(session, "m@test.com")
        exp = create_experience(
            session,
            user_id=user.user_id,
            company="A",
            title="T",
            start_date=date(2020, 1, 1),
        )
        delete_experience(session, exp.experience_id)
        assert get_user(session, user.user_id) is not None
