"""
Tests for job_activity.py — create_job_activity, get_job_activities.
Covers S2-009 (Persist Stage Transition Timestamps) and S2-010 (Job Activity Timeline).
"""

from datetime import date

import pytest

from database.models.applied_jobs import create_applied_jobs
from database.models.company import create_company
from database.models.job_activity import create_job_activity, get_job_activities
from database.models.position import create_position
from database.models.user import create_user

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(session):
    return create_user(session, "activity_user@example.com")


@pytest.fixture
def job(session, user):
    company = create_company(session, "Acme Corp", "1 Main St", "NY", 10001)
    position = create_position(
        session,
        company.company_id,
        "Engineer",
        None,
        None,
        None,
        None,
        date(2025, 1, 1),
    )
    return create_applied_jobs(session, user.user_id, position.position_id, 3)


# ─────────────────────────────────────────────────────────────────────────────
# TestCreateJobActivity (existing behaviour)
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateJobActivity:
    def test_returns_activity_object(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity is not None

    def test_activity_id_assigned(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.activity_id is not None
        assert activity.activity_id >= 1

    def test_stage_stored_correctly(self, session, job):
        activity = create_job_activity(session, job.job_id, "Interview")
        assert activity.stage == "Interview"

    def test_changed_at_is_set(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.changed_at is not None

    def test_job_id_linked_correctly(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.job_id == job.job_id


# ─────────────────────────────────────────────────────────────────────────────
# TestGetJobActivities (existing behaviour)
# ─────────────────────────────────────────────────────────────────────────────


class TestGetJobActivities:
    def test_returns_empty_list_for_no_activities(self, session, job):
        assert get_job_activities(session, job.job_id) == []

    def test_returns_one_activity(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        results = get_job_activities(session, job.job_id)
        assert len(results) == 1

    def test_returns_multiple_activities_ordered_by_time(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        create_job_activity(session, job.job_id, "Interview")
        results = get_job_activities(session, job.job_id)
        assert len(results) == 2
        assert results[0].changed_at <= results[1].changed_at

    def test_returns_empty_list_for_nonexistent_job(self, session):
        assert get_job_activities(session, 99999) == []


# ─────────────────────────────────────────────────────────────────────────────
# TestJobActivityNewFields — S2-009, S2-010
# ─────────────────────────────────────────────────────────────────────────────


class TestJobActivityNewFields:
    def test_create_activity_default_event_type_is_stage_change(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.event_type == "stage_change"

    def test_create_activity_with_custom_event_type(self, session, job):
        activity = create_job_activity(session, job.job_id, "Interview", event_type="interview")
        assert activity.event_type == "interview"

    def test_create_activity_with_notes(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied", notes="Submitted via LinkedIn")
        assert activity.notes == "Submitted via LinkedIn"

    def test_notes_defaults_null(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.notes is None

    def test_existing_callers_unaffected_by_new_params(self, session, job):
        """Calling create_job_activity without new params still works as before."""
        activity = create_job_activity(session, job.job_id, "Offer")
        assert activity.stage == "Offer"
        assert activity.event_type == "stage_change"
        assert activity.notes is None
        assert activity.changed_at is not None


# ─────────────────────────────────────────────────────────────────────────────
# TestRegression — existing behaviour unbroken after column additions
# ─────────────────────────────────────────────────────────────────────────────


class TestRegression:
    def test_original_create_still_works_without_new_fields(self, session, job):
        activity = create_job_activity(session, job.job_id, "Applied")
        assert activity.activity_id is not None
        assert activity.stage == "Applied"
        assert activity.job_id == job.job_id

    def test_original_get_still_works(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        create_job_activity(session, job.job_id, "Interview")
        results = get_job_activities(session, job.job_id)
        assert len(results) == 2
        assert all(a.stage in ("Applied", "Interview") for a in results)
