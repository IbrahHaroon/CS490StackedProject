"""Tests for job_activity v2 — create_job_activity, get_job_activities."""

import pytest

from database.models.job import create_job
from database.models.job_activity import create_job_activity, get_job_activities
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "activity_user@example.com")


@pytest.fixture
def job(session, user):
    return create_job(
        session,
        user_id=user.user_id,
        title="Engineer",
        company_name="Acme Corp",
        years_of_experience=3,
    )


class TestCreateJobActivity:
    def test_returns_activity_object(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Applied")
        assert activity is not None

    def test_activity_id_assigned(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Applied")
        assert activity.activity_id is not None and activity.activity_id >= 1

    def test_to_stage_stored(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Interview")
        assert activity.to_stage == "Interview"

    def test_from_stage_stored(self, session, job):
        activity = create_job_activity(
            session, job.job_id, from_stage="Applied", to_stage="Interview"
        )
        assert activity.from_stage == "Applied"
        assert activity.to_stage == "Interview"

    def test_occurred_at_is_set(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Applied")
        assert activity.occurred_at is not None

    def test_job_id_linked_correctly(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Applied")
        assert activity.job_id == job.job_id

    def test_default_event_type_is_stage_change(self, session, job):
        activity = create_job_activity(session, job.job_id, to_stage="Applied")
        assert activity.event_type == "stage_change"

    def test_custom_event_type(self, session, job):
        activity = create_job_activity(
            session, job.job_id, event_type="interview", notes="Phone screen"
        )
        assert activity.event_type == "interview"
        assert activity.notes == "Phone screen"


class TestGetJobActivities:
    def test_returns_empty_list_for_no_activities(self, session, job):
        assert get_job_activities(session, job.job_id) == []

    def test_returns_one_activity(self, session, job):
        create_job_activity(session, job.job_id, to_stage="Applied")
        assert len(get_job_activities(session, job.job_id)) == 1

    def test_returns_multiple_activities_ordered_desc(self, session, job):
        create_job_activity(session, job.job_id, to_stage="Applied")
        create_job_activity(session, job.job_id, to_stage="Interview")
        results = get_job_activities(session, job.job_id)
        assert len(results) == 2
        assert results[0].occurred_at >= results[1].occurred_at

    def test_returns_empty_list_for_nonexistent_job(self, session):
        assert get_job_activities(session, 99999) == []
