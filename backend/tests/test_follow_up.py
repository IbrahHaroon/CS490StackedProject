"""
Tests for the FollowUp model and its CRUD helper functions.
Covers S2-012 (Follow-Up and Reminder Tracking).
"""

from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.follow_up import (
    create_follow_up,
    delete_follow_up,
    get_follow_up,
    get_follow_ups_by_job,
    update_follow_up,
)
from database.models.job import create_job
from database.models.user import create_user


def _create_job(session, user_id: int) -> int:
    job = create_job(
        session,
        user_id=user_id,
        title="Engineer",
        company_name="Acme",
        years_of_experience=2,
    )
    return job.job_id


# ---------------------------------------------------------------------------
# TestCreateFollowUp
# ---------------------------------------------------------------------------


class TestCreateFollowUp:
    def test_creates_with_required_fields(self, session):
        user = create_user(session, "a@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(
            session, job_id=job_id, description="Send thank-you email"
        )
        assert fu.followup_id is not None
        assert fu.job_id == job_id
        assert fu.description == "Send thank-you email"
        assert fu.due_date is None

    def test_defaults_completed_to_false(self, session):
        user = create_user(session, "b@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(session, job_id=job_id, description="Follow up")
        assert fu.completed is False

    def test_creates_with_due_date(self, session):
        user = create_user(session, "c@test.com")
        job_id = _create_job(session, user.user_id)
        due = date(2026, 5, 15)
        fu = create_follow_up(
            session, job_id=job_id, description="Check in", due_date=due
        )
        assert fu.due_date == due

    def test_invalid_job_id_raises_error(self, session):
        with pytest.raises((IntegrityError, Exception)):
            create_follow_up(session, job_id=99999, description="Test")
            session.flush()


# ---------------------------------------------------------------------------
# TestGetFollowUp
# ---------------------------------------------------------------------------


class TestGetFollowUp:
    def test_returns_by_id(self, session):
        user = create_user(session, "d@test.com")
        job_id = _create_job(session, user.user_id)
        created = create_follow_up(session, job_id=job_id, description="Follow up")
        fetched = get_follow_up(session, created.followup_id)
        assert fetched is not None
        assert fetched.followup_id == created.followup_id

    def test_returns_none_for_missing_id(self, session):
        assert get_follow_up(session, 99999) is None


# ---------------------------------------------------------------------------
# TestGetFollowUpsByJob
# ---------------------------------------------------------------------------


class TestGetFollowUpsByJob:
    def test_returns_all_for_job(self, session):
        user = create_user(session, "e@test.com")
        job_id = _create_job(session, user.user_id)
        create_follow_up(session, job_id=job_id, description="First")
        create_follow_up(session, job_id=job_id, description="Second")
        results = get_follow_ups_by_job(session, job_id)
        assert len(results) == 2

    def test_isolation_across_jobs(self, session):
        user = create_user(session, "f@test.com")
        job_id_a = _create_job(session, user.user_id)
        job_id_b = _create_job(session, user.user_id)
        create_follow_up(session, job_id=job_id_a, description="Only for A")
        assert get_follow_ups_by_job(session, job_id_b) == []


# ---------------------------------------------------------------------------
# TestUpdateFollowUp
# ---------------------------------------------------------------------------


class TestUpdateFollowUp:
    def test_marks_completed(self, session):
        user = create_user(session, "g@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(session, job_id=job_id, description="Do thing")
        updated = update_follow_up(session, fu.followup_id, completed=True)
        assert updated.completed is True

    def test_updates_description(self, session):
        user = create_user(session, "h@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(session, job_id=job_id, description="Old")
        updated = update_follow_up(session, fu.followup_id, description="New")
        assert updated.description == "New"

    def test_updates_due_date(self, session):
        user = create_user(session, "i@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(session, job_id=job_id, description="Task")
        new_due = date(2026, 6, 1)
        updated = update_follow_up(session, fu.followup_id, due_date=new_due)
        assert updated.due_date == new_due

    def test_returns_none_for_missing_id(self, session):
        assert update_follow_up(session, 99999, completed=True) is None


# ---------------------------------------------------------------------------
# TestDeleteFollowUp
# ---------------------------------------------------------------------------


class TestDeleteFollowUp:
    def test_deletes_existing(self, session):
        user = create_user(session, "j@test.com")
        job_id = _create_job(session, user.user_id)
        fu = create_follow_up(session, job_id=job_id, description="Task")
        assert delete_follow_up(session, fu.followup_id) is True
        assert get_follow_up(session, fu.followup_id) is None

    def test_returns_false_for_missing_id(self, session):
        assert delete_follow_up(session, 99999) is False
