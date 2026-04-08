"""Tests for recruiter.py — create, get, update, delete."""

import pytest

from database.models.company import create_company
from database.models.recruiter import (
    create_recruiter,
    delete_recruiter,
    get_recruiter,
    get_recruiter_by_user_id,
    update_recruiter,
)
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "rec_user@example.com")


@pytest.fixture
def company(session):
    return create_company(session, "Acme Corp", "1 Main St", "NJ", 8001)


# ─────────────────────────────────────────────────────────────────────────────
# create_recruiter
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateRecruiter:
    def test_returns_recruiter_object(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        assert rec is not None

    def test_recruiter_id_assigned(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        assert rec.recruiter_id is not None
        assert rec.recruiter_id >= 1

    def test_fields_stored_correctly(self, session, user, company):
        rec = create_recruiter(
            session, user.user_id, company.company_id, "Jane", "Doe", "HR Manager"
        )
        assert rec.first_name == "Jane"
        assert rec.last_name == "Doe"
        assert rec.job_title == "HR Manager"

    def test_user_id_linked_correctly(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        assert rec.user_id == user.user_id

    def test_company_id_linked_correctly(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        assert rec.company_id == company.company_id

    def test_job_title_defaults_null(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        assert rec.job_title is None


# ─────────────────────────────────────────────────────────────────────────────
# get_recruiter / get_recruiter_by_user_id
# ─────────────────────────────────────────────────────────────────────────────


class TestGetRecruiter:
    def test_returns_correct_recruiter_by_pk(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.recruiter_id == rec.recruiter_id

    def test_returns_none_for_missing_pk(self, session):
        assert get_recruiter(session, 99999) is None

    def test_returns_none_for_zero_pk(self, session):
        assert get_recruiter(session, 0) is None

    def test_returns_none_for_negative_pk(self, session):
        assert get_recruiter(session, -1) is None

    def test_get_by_user_id_returns_correct_recruiter(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        fetched = get_recruiter_by_user_id(session, user.user_id)
        assert fetched.recruiter_id == rec.recruiter_id

    def test_get_by_user_id_returns_none_for_missing(self, session):
        assert get_recruiter_by_user_id(session, 99999) is None

    def test_fields_match_after_fetch(self, session, user, company):
        rec = create_recruiter(
            session, user.user_id, company.company_id, "Alice", "Smith", "Recruiter"
        )
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.first_name == "Alice"
        assert fetched.last_name == "Smith"
        assert fetched.job_title == "Recruiter"


# ─────────────────────────────────────────────────────────────────────────────
# update_recruiter
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateRecruiter:
    def test_update_first_name(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        rec.first_name = "Janet"
        update_recruiter(session, rec)
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.first_name == "Janet"

    def test_update_last_name(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        rec.last_name = "Smith"
        update_recruiter(session, rec)
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.last_name == "Smith"

    def test_update_job_title(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        rec.job_title = "Talent Acquisition"
        update_recruiter(session, rec)
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.job_title == "Talent Acquisition"

    def test_update_returns_true(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        rec.first_name = "Janet"
        result = update_recruiter(session, rec)
        assert result is True

    def test_other_fields_unaffected(self, session, user, company):
        rec = create_recruiter(
            session, user.user_id, company.company_id, "Jane", "Doe", "HR"
        )
        rec.first_name = "Janet"
        update_recruiter(session, rec)
        fetched = get_recruiter(session, rec.recruiter_id)
        assert fetched.last_name == "Doe"
        assert fetched.job_title == "HR"


# ─────────────────────────────────────────────────────────────────────────────
# delete_recruiter
# ─────────────────────────────────────────────────────────────────────────────


class TestDeleteRecruiter:
    def test_delete_returns_true(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        result = delete_recruiter(session, rec.recruiter_id)
        assert result is True

    def test_recruiter_not_found_after_delete(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        rec_id = rec.recruiter_id
        delete_recruiter(session, rec_id)
        assert get_recruiter(session, rec_id) is None

    def test_delete_missing_returns_false(self, session):
        assert delete_recruiter(session, 99999) is False

    def test_get_by_user_id_returns_none_after_delete(self, session, user, company):
        rec = create_recruiter(session, user.user_id, company.company_id, "Jane", "Doe")
        delete_recruiter(session, rec.recruiter_id)
        assert get_recruiter_by_user_id(session, user.user_id) is None
