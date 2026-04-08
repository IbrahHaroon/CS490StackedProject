"""
Tests for the CareerPreferences model and its CRUD helper functions.
Covers S2-019 (Career Preferences Section CRUD).
"""

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.career_preferences import (
    create_career_preferences,
    get_career_preferences_by_user,
    update_career_preferences,
)
from database.models.user import create_user

# ---------------------------------------------------------------------------
# TestCreateCareerPreferences
# ---------------------------------------------------------------------------


class TestCreateCareerPreferences:
    def test_creates_with_all_fields(self, session):
        user = create_user(session, "a@test.com")
        prefs = create_career_preferences(
            session,
            user_id=user.user_id,
            target_roles="Software Engineer, Backend",
            location_preferences="New York, Remote",
            work_mode="Hybrid",
            salary_preference="120k-150k",
        )
        assert prefs.preference_id is not None
        assert prefs.user_id == user.user_id
        assert prefs.target_roles == "Software Engineer, Backend"
        assert prefs.work_mode == "Hybrid"
        assert prefs.salary_preference == "120k-150k"

    def test_creates_with_all_nullable_fields_omitted(self, session):
        user = create_user(session, "b@test.com")
        prefs = create_career_preferences(session, user_id=user.user_id)
        assert prefs.preference_id is not None
        assert prefs.target_roles is None
        assert prefs.location_preferences is None
        assert prefs.work_mode is None
        assert prefs.salary_preference is None

    def test_unique_constraint_prevents_duplicate_per_user(self, session):
        user = create_user(session, "c@test.com")
        create_career_preferences(session, user_id=user.user_id, work_mode="Remote")
        with pytest.raises((IntegrityError, Exception)):
            create_career_preferences(
                session, user_id=user.user_id, work_mode="On-site"
            )
            session.flush()


# ---------------------------------------------------------------------------
# TestGetCareerPreferencesByUser
# ---------------------------------------------------------------------------


class TestGetCareerPreferencesByUser:
    def test_returns_preferences_for_user(self, session):
        user = create_user(session, "d@test.com")
        create_career_preferences(session, user_id=user.user_id, work_mode="Remote")
        prefs = get_career_preferences_by_user(session, user.user_id)
        assert prefs is not None
        assert prefs.work_mode == "Remote"

    def test_returns_none_for_user_with_no_preferences(self, session):
        user = create_user(session, "e@test.com")
        assert get_career_preferences_by_user(session, user.user_id) is None


# ---------------------------------------------------------------------------
# TestUpdateCareerPreferences (upsert)
# ---------------------------------------------------------------------------


class TestUpdateCareerPreferences:
    def test_updates_work_mode(self, session):
        user = create_user(session, "f@test.com")
        create_career_preferences(session, user_id=user.user_id, work_mode="On-site")
        updated = update_career_preferences(
            session, user_id=user.user_id, work_mode="Remote"
        )
        assert updated.work_mode == "Remote"

    def test_updates_salary_preference(self, session):
        user = create_user(session, "g@test.com")
        create_career_preferences(
            session, user_id=user.user_id, salary_preference="80k"
        )
        updated = update_career_preferences(
            session, user_id=user.user_id, salary_preference="100k+"
        )
        assert updated.salary_preference == "100k+"

    def test_upsert_creates_when_none_exists(self, session):
        user = create_user(session, "h@test.com")
        assert get_career_preferences_by_user(session, user.user_id) is None
        result = update_career_preferences(
            session, user_id=user.user_id, work_mode="Remote"
        )
        assert result is not None
        assert result.work_mode == "Remote"

    def test_upsert_updates_when_already_exists(self, session):
        user = create_user(session, "i@test.com")
        create_career_preferences(session, user_id=user.user_id, work_mode="On-site")
        result = update_career_preferences(
            session, user_id=user.user_id, work_mode="Hybrid"
        )
        assert result.work_mode == "Hybrid"
        # Should still be one record, not two
        from sqlalchemy import select

        from database.models.career_preferences import CareerPreferences

        count = (
            session.execute(
                select(CareerPreferences).where(
                    CareerPreferences.user_id == user.user_id
                )
            )
            .scalars()
            .all()
        )
        assert len(count) == 1
