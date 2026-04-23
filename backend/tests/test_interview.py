"""
Tests for the Interview model and its CRUD helper functions.
Covers S2-011 (Interview Tracking in Job Detail).
"""

from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from database.models.interview import (
    create_interview,
    delete_interview,
    get_interview,
    get_interviews_by_job,
    update_interview,
)
from database.models.job import create_job
from database.models.user import create_user


def _create_job(session, user_id: int) -> int:
    """Create a v2 Job for the user. Returns the job_id."""
    job = create_job(
        session,
        user_id=user_id,
        title="Engineer",
        company_name="Acme",
        location="NY",
        years_of_experience=2,
    )
    return job.job_id


_SCHEDULED = datetime(2026, 5, 1, 10, 0, 0)


# ---------------------------------------------------------------------------
# TestCreateInterview
# ---------------------------------------------------------------------------


class TestCreateInterview:
    def test_creates_with_required_fields_only(self, session):
        user = create_user(session, "a@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session, job_id=job_id, round_type="Phone Screen", scheduled_at=_SCHEDULED
        )
        assert interview.interview_id is not None
        assert interview.job_id == job_id
        assert interview.round_type == "Phone Screen"
        assert interview.scheduled_at == _SCHEDULED
        assert interview.notes is None

    def test_creates_with_notes(self, session):
        user = create_user(session, "b@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session,
            job_id=job_id,
            round_type="Technical",
            scheduled_at=_SCHEDULED,
            notes="Focus on system design",
        )
        assert interview.notes == "Focus on system design"

    def test_invalid_job_id_raises_integrity_error(self, session):
        with pytest.raises((IntegrityError, Exception)):
            create_interview(
                session, job_id=99999, round_type="Technical", scheduled_at=_SCHEDULED
            )
            session.flush()


# ---------------------------------------------------------------------------
# TestGetInterview
# ---------------------------------------------------------------------------


class TestGetInterview:
    def test_returns_interview_by_id(self, session):
        user = create_user(session, "c@test.com")
        job_id = _create_job(session, user.user_id)
        created = create_interview(
            session, job_id=job_id, round_type="Final", scheduled_at=_SCHEDULED
        )
        fetched = get_interview(session, created.interview_id)
        assert fetched is not None
        assert fetched.interview_id == created.interview_id

    def test_returns_none_for_missing_id(self, session):
        assert get_interview(session, 99999) is None


# ---------------------------------------------------------------------------
# TestGetInterviewsByJob
# ---------------------------------------------------------------------------


class TestGetInterviewsByJob:
    def test_returns_all_interviews_for_job(self, session):
        user = create_user(session, "d@test.com")
        job_id = _create_job(session, user.user_id)
        create_interview(
            session,
            job_id=job_id,
            round_type="Phone",
            scheduled_at=datetime(2026, 5, 1),
        )
        create_interview(
            session,
            job_id=job_id,
            round_type="Technical",
            scheduled_at=datetime(2026, 5, 8),
        )
        results = get_interviews_by_job(session, job_id)
        assert len(results) == 2

    def test_returns_empty_list_for_job_with_none(self, session):
        user = create_user(session, "e@test.com")
        job_id = _create_job(session, user.user_id)
        assert get_interviews_by_job(session, job_id) == []

    def test_does_not_return_other_jobs_interviews(self, session):
        user = create_user(session, "f@test.com")
        job_id_a = _create_job(session, user.user_id)
        job_id_b = _create_job(session, user.user_id)
        create_interview(
            session, job_id=job_id_a, round_type="Phone", scheduled_at=_SCHEDULED
        )
        results = get_interviews_by_job(session, job_id_b)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# TestUpdateInterview
# ---------------------------------------------------------------------------


class TestUpdateInterview:
    def test_updates_round_type(self, session):
        user = create_user(session, "g@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session, job_id=job_id, round_type="Phone", scheduled_at=_SCHEDULED
        )
        updated = update_interview(session, interview.interview_id, round_type="Final")
        assert updated.round_type == "Final"

    def test_updates_notes(self, session):
        user = create_user(session, "h@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session, job_id=job_id, round_type="Phone", scheduled_at=_SCHEDULED
        )
        updated = update_interview(
            session, interview.interview_id, notes="Bring portfolio"
        )
        assert updated.notes == "Bring portfolio"

    def test_returns_none_for_missing_id(self, session):
        assert update_interview(session, 99999, round_type="Final") is None


# ---------------------------------------------------------------------------
# TestDeleteInterview
# ---------------------------------------------------------------------------


class TestDeleteInterview:
    def test_deletes_existing_interview(self, session):
        user = create_user(session, "i@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session, job_id=job_id, round_type="Phone", scheduled_at=_SCHEDULED
        )
        assert delete_interview(session, interview.interview_id) is True
        assert get_interview(session, interview.interview_id) is None

    def test_returns_false_for_missing_id(self, session):
        assert delete_interview(session, 99999) is False

    def test_job_still_exists_after_interview_deleted(self, session):
        from database.models.job import get_job

        user = create_user(session, "j@test.com")
        job_id = _create_job(session, user.user_id)
        interview = create_interview(
            session, job_id=job_id, round_type="Phone", scheduled_at=_SCHEDULED
        )
        delete_interview(session, interview.interview_id)
        assert get_job(session, job_id) is not None
