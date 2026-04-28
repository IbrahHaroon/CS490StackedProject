"""Tests for dashboard analytics (conversion funnel + time-in-stage)."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from database.models.job import create_job
from database.models.job_activity import (
    JobActivity,
    create_job_activity,
    get_stage_analytics,
)
from database.models.user import User


@pytest.fixture
def test_jobs(session: Session, test_user: User):
    """Create test jobs with different progression paths."""
    jobs = []

    # Job 1: Applied only
    j1 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 1",
        company_name="Company A",
        stage="Applied",
    )
    create_job_activity(session, j1.job_id, to_stage="Applied", notes="created")
    jobs.append(j1)

    # Job 2: Applied → Interview
    j2 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 2",
        company_name="Company B",
        stage="Interview",
    )
    create_job_activity(session, j2.job_id, to_stage="Applied", notes="created")
    create_job_activity(session, j2.job_id, from_stage="Applied", to_stage="Interview")
    jobs.append(j2)

    # Job 3: Applied → Interview → Offer
    j3 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 3",
        company_name="Company C",
        stage="Offer",
    )
    create_job_activity(session, j3.job_id, to_stage="Applied", notes="created")
    create_job_activity(session, j3.job_id, from_stage="Applied", to_stage="Interview")
    create_job_activity(session, j3.job_id, from_stage="Interview", to_stage="Offer")
    jobs.append(j3)

    # Job 4: Applied → Interview → Offer → Accepted
    j4 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 4",
        company_name="Company D",
        stage="Accepted",
    )
    create_job_activity(session, j4.job_id, to_stage="Applied", notes="created")
    create_job_activity(session, j4.job_id, from_stage="Applied", to_stage="Interview")
    create_job_activity(session, j4.job_id, from_stage="Interview", to_stage="Offer")
    create_job_activity(session, j4.job_id, from_stage="Offer", to_stage="Accepted")
    jobs.append(j4)

    # Job 5: Applied → Interview → Rejected
    j5 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 5",
        company_name="Company E",
        stage="Rejected",
    )
    create_job_activity(session, j5.job_id, to_stage="Applied", notes="created")
    create_job_activity(session, j5.job_id, from_stage="Applied", to_stage="Interview")
    create_job_activity(session, j5.job_id, from_stage="Interview", to_stage="Rejected")
    jobs.append(j5)

    # Job 6: Just Interested
    j6 = create_job(
        session,
        user_id=test_user.user_id,
        title="Job 6",
        company_name="Company F",
        stage="Interested",
    )
    jobs.append(j6)

    return jobs


class TestConversionFunnel:
    """Test conversion funnel calculations."""

    def test_applied_to_interview(self, session: Session, test_user: User, test_jobs):
        """4 of 5 Applied jobs moved to Interview = 80%."""
        analytics = get_stage_analytics(session, test_user.user_id)
        funnel = analytics["conversion_funnel"]
        assert funnel["Applied→Interview"] == 80.0

    def test_interview_to_offer(self, session: Session, test_user: User, test_jobs):
        """2 of 4 Interview jobs moved to Offer = 50%."""
        analytics = get_stage_analytics(session, test_user.user_id)
        funnel = analytics["conversion_funnel"]
        assert funnel["Interview→Offer"] == 50.0

    def test_offer_to_accepted(self, session: Session, test_user: User, test_jobs):
        """1 of 2 Offer jobs moved to Accepted = 50%."""
        analytics = get_stage_analytics(session, test_user.user_id)
        funnel = analytics["conversion_funnel"]
        assert funnel["Offer→Accepted"] == 50.0


class TestOverallConversion:
    """Test overall conversion rate."""

    def test_overall_rate(self, session: Session, test_user: User, test_jobs):
        """2 of 6 jobs reached Offer+ = 33.3%."""
        analytics = get_stage_analytics(session, test_user.user_id)
        rate = analytics["overall_conversion_rate"]
        expected = round(2 / 6 * 100, 1)
        assert rate == expected


class TestAvgTimeInStage:
    """Test average time in stage calculation."""

    def test_time_in_applied(self, session: Session, test_user: User):
        """Test time spent in Applied stage."""
        user = test_user
        base_time = datetime.utcnow()

        job = create_job(
            session,
            user_id=user.user_id,
            title="Timed Job",
            company_name="Test Co",
            stage="Interview",
        )

        session.query(JobActivity).filter(JobActivity.job_id == job.job_id).delete()

        entry_applied = JobActivity(
            job_id=job.job_id,
            from_stage=None,
            to_stage="Applied",
            occurred_at=base_time,
        )
        exit_applied = JobActivity(
            job_id=job.job_id,
            from_stage="Applied",
            to_stage="Interview",
            occurred_at=base_time + timedelta(days=5),
        )

        session.add_all([entry_applied, exit_applied])
        session.commit()

        analytics = get_stage_analytics(session, user.user_id)
        time_in_stage = analytics["avg_days_in_stage"]

        assert time_in_stage["Applied"] == 5.0


class TestUserScoping:
    """Test that analytics are scoped to user."""

    def test_analytics_isolated_by_user(
        self, session: Session, test_user: User, test_jobs
    ):
        """Verify analytics for test_user don't include other users' data."""
        from database.models.user import create_user

        other_user = create_user(session, email="other@example.com")

        analytics = get_stage_analytics(session, other_user.user_id)

        assert all(v == 0.0 for v in analytics["conversion_funnel"].values())
        assert analytics["overall_conversion_rate"] == 0.0
        assert analytics["avg_days_in_stage"] == {}

        test_user_analytics = get_stage_analytics(session, test_user.user_id)
        assert len(test_user_analytics["conversion_funnel"]) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_no_jobs(self, session: Session, test_user: User):
        """User with no jobs should have 0% analytics."""
        analytics = get_stage_analytics(session, test_user.user_id)

        assert all(v == 0.0 for v in analytics["conversion_funnel"].values())
        assert analytics["overall_conversion_rate"] == 0.0
        assert analytics["avg_days_in_stage"] == {}

    def test_rejected_not_counted(self, session: Session, test_user: User):
        """Rejected jobs should not count toward conversion."""
        job = create_job(
            session,
            user_id=test_user.user_id,
            title="Rejected Job",
            company_name="Test Co",
            stage="Rejected",
        )
        create_job_activity(session, job.job_id, to_stage="Applied", notes="created")
        create_job_activity(
            session, job.job_id, from_stage="Applied", to_stage="Rejected"
        )

        analytics = get_stage_analytics(session, test_user.user_id)

        assert analytics["overall_conversion_rate"] == 0.0

    def test_withdrawn_not_counted(self, session: Session, test_user: User):
        """Withdrawn jobs should not count toward conversion."""
        job = create_job(
            session,
            user_id=test_user.user_id,
            title="Withdrawn Job",
            company_name="Test Co",
            stage="Withdrawn",
        )
        create_job_activity(session, job.job_id, to_stage="Applied", notes="created")
        create_job_activity(
            session, job.job_id, from_stage="Applied", to_stage="Withdrawn"
        )

        analytics = get_stage_analytics(session, test_user.user_id)
        assert analytics["overall_conversion_rate"] == 0.0
