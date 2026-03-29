"""Tests for applied_jobs.py — create_applied_jobs, get_applied_jobs,
lookup_applied_jobs, get_all_applied_jobs."""

from datetime import date
from decimal import Decimal

import pytest

from database.models.applied_jobs import (
    create_applied_jobs,
    get_all_applied_jobs,
    get_applied_jobs,
    lookup_applied_jobs,
)
from database.models.company import create_company
from database.models.position import create_position
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "jobs_user@example.com")


@pytest.fixture
def position(session):
    company = create_company(session, "Jobs Corp", "1 Jobs Way", "NJ", 8534)
    return create_position(
        session,
        company_id=company.company_id,
        title="Software Engineer",
        salary=Decimal("95000.00"),
        education_req="Bachelor's",
        experience_req="2+ years",
        description="Build software.",
        listing_date=date(2025, 1, 1),
    )


# ─────────────────────────────────────────────────────────────────────────────
# create_applied_jobs
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateAppliedJobs:
    def test_returns_applied_jobs_object(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 3)
        assert job is not None

    def test_job_id_assigned(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 3)
        assert job.job_id is not None
        assert job.job_id >= 1

    def test_application_status_initialized_to_pending(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 3)
        assert job.application_status == "pending review"

    def test_application_date_set_to_today(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 3)
        assert job.application_date == date.today()

    def test_user_id_linked_correctly(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 5)
        assert job.user_id == user.user_id

    def test_position_id_linked_correctly(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 5)
        assert job.position_id == position.position_id

    def test_years_of_experience_stored_correctly(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 7)
        assert job.years_of_experience == 7


# ─────────────────────────────────────────────────────────────────────────────
# get_applied_jobs
# ─────────────────────────────────────────────────────────────────────────────


class TestGetAppliedJobs:
    def test_returns_correct_job(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 3)
        fetched = get_applied_jobs(session, job.job_id)
        assert fetched.job_id == job.job_id

    def test_returns_none_for_missing_id(self, session):
        result = get_applied_jobs(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_applied_jobs(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 4)
        fetched = get_applied_jobs(session, job.job_id)
        assert fetched.years_of_experience == 4
        assert fetched.application_status == "pending review"

    def test_returns_none_for_negative_id(self, session):
        result = get_applied_jobs(session, -1)
        assert result is None

    def test_application_date_matches_after_fetch(self, session, user, position):
        job = create_applied_jobs(session, user.user_id, position.position_id, 2)
        fetched = get_applied_jobs(session, job.job_id)
        assert fetched.application_date == date.today()


# ─────────────────────────────────────────────────────────────────────────────
# lookup_applied_jobs
# ─────────────────────────────────────────────────────────────────────────────


class TestLookupAppliedJobs:
    def test_returns_zero_for_user_with_no_applications(self, session, user):
        count = lookup_applied_jobs(session, user.user_id)
        assert count == 0

    def test_returns_one_after_single_application(self, session, user, position):
        create_applied_jobs(session, user.user_id, position.position_id, 3)
        count = lookup_applied_jobs(session, user.user_id)
        assert count == 1

    def test_returns_correct_count_for_multiple_applications(
        self, session, user, position
    ):
        create_applied_jobs(session, user.user_id, position.position_id, 1)
        create_applied_jobs(session, user.user_id, position.position_id, 2)
        create_applied_jobs(session, user.user_id, position.position_id, 3)
        count = lookup_applied_jobs(session, user.user_id)
        assert count == 3

    def test_returns_zero_for_nonexistent_user(self, session):
        count = lookup_applied_jobs(session, 99999)
        assert count == 0

    def test_counts_only_jobs_for_correct_user(self, session, position):
        u1 = create_user(session, "lj1@example.com")
        u2 = create_user(session, "lj2@example.com")
        create_applied_jobs(session, u1.user_id, position.position_id, 1)
        create_applied_jobs(session, u1.user_id, position.position_id, 2)
        create_applied_jobs(session, u2.user_id, position.position_id, 3)
        assert lookup_applied_jobs(session, u1.user_id) == 2
        assert lookup_applied_jobs(session, u2.user_id) == 1

    def test_count_increments_with_each_application(self, session, user, position):
        assert lookup_applied_jobs(session, user.user_id) == 0
        create_applied_jobs(session, user.user_id, position.position_id, 1)
        assert lookup_applied_jobs(session, user.user_id) == 1
        create_applied_jobs(session, user.user_id, position.position_id, 2)
        assert lookup_applied_jobs(session, user.user_id) == 2


# ─────────────────────────────────────────────────────────────────────────────
# get_all_applied_jobs
# ─────────────────────────────────────────────────────────────────────────────


class TestGetAllAppliedJobs:
    def test_returns_empty_tuple_for_no_applications(self, session, user):
        result = get_all_applied_jobs(session, user.user_id)
        assert result == ()

    def test_returns_tuple_type(self, session, user, position):
        create_applied_jobs(session, user.user_id, position.position_id, 3)
        result = get_all_applied_jobs(session, user.user_id)
        assert isinstance(result, tuple)

    def test_returns_correct_number_of_applications(self, session, user, position):
        create_applied_jobs(session, user.user_id, position.position_id, 1)
        create_applied_jobs(session, user.user_id, position.position_id, 2)
        result = get_all_applied_jobs(session, user.user_id)
        assert len(result) == 2

    def test_all_items_are_applied_jobs_objects(self, session, user, position):
        from database.models.applied_jobs import AppliedJobs

        create_applied_jobs(session, user.user_id, position.position_id, 1)
        create_applied_jobs(session, user.user_id, position.position_id, 2)
        result = get_all_applied_jobs(session, user.user_id)
        for job in result:
            assert isinstance(job, AppliedJobs)

    def test_only_returns_jobs_for_correct_user(self, session, position):
        u1 = create_user(session, "ga1@example.com")
        u2 = create_user(session, "ga2@example.com")
        create_applied_jobs(session, u1.user_id, position.position_id, 1)
        create_applied_jobs(session, u2.user_id, position.position_id, 2)
        create_applied_jobs(session, u2.user_id, position.position_id, 3)
        assert len(get_all_applied_jobs(session, u1.user_id)) == 1
        assert len(get_all_applied_jobs(session, u2.user_id)) == 2

    def test_returns_empty_tuple_for_nonexistent_user(self, session):
        result = get_all_applied_jobs(session, 99999)
        assert result == ()
