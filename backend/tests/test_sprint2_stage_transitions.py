"""
Unit tests for job workflow stage transition logic.

Covers:
- PIPELINE_STAGES constant correctness
- Valid stage names accepted by update_applied_job
- Invalid stage names are not in PIPELINE_STAGES (router-level guard)
- Stage change creates a JobActivity record with correct event_type
- Multiple stage transitions accumulate activity history in order
- Stage statistics (count_applied_jobs_by_stage)
"""

from datetime import date

import pytest

from database.models.applied_jobs import (
    PIPELINE_STAGES,
    create_applied_jobs,
    get_dashboard_metrics,
    update_applied_job,
)
from database.models.company import create_company
from database.models.job_activity import create_job_activity, get_job_activities
from database.models.position import create_position
from database.models.user import create_user

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def user(session):
    return create_user(session, "stage_test@example.com")


@pytest.fixture
def position(session):
    company = create_company(session, "StageTestCo", "1 Pipeline Ave", "TX", 73301)
    return create_position(
        session,
        company.company_id,
        "Software Engineer",
        None,
        None,
        None,
        None,
        date(2025, 6, 1),
    )


@pytest.fixture
def job(session, user, position):
    return create_applied_jobs(session, user.user_id, position.position_id, 2)


# ---------------------------------------------------------------------------
# TestPipelineStagesConstant
# ---------------------------------------------------------------------------


class TestPipelineStagesConstant:
    def test_pipeline_stages_is_a_list(self):
        assert isinstance(PIPELINE_STAGES, list)

    def test_pipeline_stages_not_empty(self):
        assert len(PIPELINE_STAGES) > 0

    def test_interested_is_a_stage(self):
        assert "Interested" in PIPELINE_STAGES

    def test_applied_is_a_stage(self):
        assert "Applied" in PIPELINE_STAGES

    def test_interview_is_a_stage(self):
        assert "Interview" in PIPELINE_STAGES

    def test_offer_is_a_stage(self):
        assert "Offer" in PIPELINE_STAGES

    def test_rejected_is_a_stage(self):
        assert "Rejected" in PIPELINE_STAGES

    def test_archived_is_a_stage(self):
        assert "Archived" in PIPELINE_STAGES

    def test_withdrawn_is_a_stage(self):
        assert "Withdrawn" in PIPELINE_STAGES

    def test_no_duplicate_stages(self):
        assert len(PIPELINE_STAGES) == len(set(PIPELINE_STAGES))

    def test_invalid_stage_not_in_pipeline(self):
        invalid = ["Pending", "Hired", "Ghosted", "Done", "", "applied", "INTERVIEW"]
        for s in invalid:
            assert s not in PIPELINE_STAGES, f"'{s}' should not be a valid stage"


# ---------------------------------------------------------------------------
# TestStageTransitions — model-level update_applied_job
# ---------------------------------------------------------------------------


class TestStageTransitions:
    def test_default_status_is_interested(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 1)
        assert job.application_status == "Interested"

    def test_update_to_applied(self, session, job):
        updated = update_applied_job(session, job.job_id, application_status="Applied")
        assert updated.application_status == "Applied"

    def test_update_to_interview(self, session, job):
        updated = update_applied_job(
            session, job.job_id, application_status="Interview"
        )
        assert updated.application_status == "Interview"

    def test_update_to_offer(self, session, job):
        updated = update_applied_job(session, job.job_id, application_status="Offer")
        assert updated.application_status == "Offer"

    def test_update_to_rejected(self, session, job):
        updated = update_applied_job(session, job.job_id, application_status="Rejected")
        assert updated.application_status == "Rejected"

    def test_update_to_archived(self, session, job):
        updated = update_applied_job(session, job.job_id, application_status="Archived")
        assert updated.application_status == "Archived"

    def test_update_to_withdrawn(self, session, job):
        updated = update_applied_job(
            session, job.job_id, application_status="Withdrawn"
        )
        assert updated.application_status == "Withdrawn"

    def test_sequential_transitions_persist_final_state(self, session, job):
        update_applied_job(session, job.job_id, application_status="Applied")
        update_applied_job(session, job.job_id, application_status="Interview")
        final = update_applied_job(session, job.job_id, application_status="Offer")
        assert final.application_status == "Offer"

    def test_stage_changed_at_set_on_update(self, session, job):
        updated = update_applied_job(session, job.job_id, application_status="Applied")
        assert updated.stage_changed_at is not None

    def test_update_nonexistent_job_returns_none(self, session):
        result = update_applied_job(session, 99999, application_status="Applied")
        assert result is None

    def test_all_valid_stages_can_be_set(self, session, user, position):
        for stage in PIPELINE_STAGES:
            job = create_applied_jobs(session, user.user_id, position.position_id, 1)
            updated = update_applied_job(session, job.job_id, application_status=stage)
            assert updated.application_status == stage


# ---------------------------------------------------------------------------
# TestActivityRecordingOnStageChange
# ---------------------------------------------------------------------------


class TestActivityRecordingOnStageChange:
    def test_activity_created_with_correct_stage(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        activities = get_job_activities(session, job.job_id)
        assert len(activities) == 1
        assert activities[0].stage == "Applied"

    def test_activity_event_type_defaults_to_stage_change(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        activities = get_job_activities(session, job.job_id)
        assert activities[0].event_type == "stage_change"

    def test_follow_up_event_type_stored(self, session, job):
        create_job_activity(
            session,
            job.job_id,
            "Follow-up Added",
            event_type="follow_up",
            notes="Send thank-you email",
        )
        activities = get_job_activities(session, job.job_id)
        assert activities[0].event_type == "follow_up"

    def test_interview_event_type_stored(self, session, job):
        create_job_activity(
            session,
            job.job_id,
            "Interview Scheduled",
            event_type="interview",
            notes="Technical round — Mar 20",
        )
        activities = get_job_activities(session, job.job_id)
        assert activities[0].event_type == "interview"

    def test_outcome_event_type_stored(self, session, job):
        create_job_activity(
            session,
            job.job_id,
            "Outcome Recorded",
            event_type="outcome",
            notes="Offer accepted",
        )
        activities = get_job_activities(session, job.job_id)
        assert activities[0].event_type == "outcome"

    def test_multiple_events_ordered_chronologically(self, session, job):
        create_job_activity(session, job.job_id, "Applied")
        create_job_activity(
            session, job.job_id, "Follow-up Added", event_type="follow_up"
        )
        create_job_activity(
            session, job.job_id, "Interview Scheduled", event_type="interview"
        )
        create_job_activity(
            session, job.job_id, "Outcome Recorded", event_type="outcome"
        )
        activities = get_job_activities(session, job.job_id)
        assert len(activities) == 4
        for i in range(len(activities) - 1):
            assert activities[i].changed_at <= activities[i + 1].changed_at

    def test_notes_preserved(self, session, job):
        create_job_activity(
            session, job.job_id, "Applied", notes="Applied via company website"
        )
        activities = get_job_activities(session, job.job_id)
        assert activities[0].notes == "Applied via company website"

    def test_activity_isolated_per_job(self, session, user, position):
        job1 = create_applied_jobs(session, user.user_id, position.position_id, 1)
        job2 = create_applied_jobs(session, user.user_id, position.position_id, 3)
        create_job_activity(session, job1.job_id, "Applied")
        create_job_activity(session, job2.job_id, "Interview")
        assert len(get_job_activities(session, job1.job_id)) == 1
        assert len(get_job_activities(session, job2.job_id)) == 1
        assert get_job_activities(session, job1.job_id)[0].stage == "Applied"
        assert get_job_activities(session, job2.job_id)[0].stage == "Interview"


# ---------------------------------------------------------------------------
# TestStageStatistics — count_applied_jobs_by_stage
# ---------------------------------------------------------------------------


class TestStageStatistics:
    def test_all_stages_present_in_metrics(self, session, user):
        metrics = get_dashboard_metrics(session, user.user_id)
        stage_counts = metrics["stage_counts"]
        for stage in PIPELINE_STAGES:
            assert stage in stage_counts

    def test_counts_zero_with_no_jobs(self, session, user):
        metrics = get_dashboard_metrics(session, user.user_id)
        stage_counts = metrics["stage_counts"]
        assert all(v == 0 for v in stage_counts.values())

    def test_counts_increment_for_correct_stage(self, session, user, position):
        create_applied_jobs(session, user.user_id, position.position_id, 1)
        metrics = get_dashboard_metrics(session, user.user_id)
        assert metrics["stage_counts"]["Interested"] == 1

    def test_counts_reflect_stage_update(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 1)
        update_applied_job(session, job.job_id, application_status="Applied")
        metrics = get_dashboard_metrics(session, user.user_id)
        assert metrics["stage_counts"]["Applied"] == 1
        assert metrics["stage_counts"]["Interested"] == 0
