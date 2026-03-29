"""Tests for position.py — create_position, get_position, update_position."""

from datetime import date
from decimal import Decimal

import pytest

from database.models.company import create_company
from database.models.position import create_position, get_position, update_position


@pytest.fixture
def company(session):
    return create_company(session, "Test Corp", "1 Corp Way", "NJ", 8534)


def make_position(session, company_id, title="Software Engineer"):
    return create_position(
        session,
        company_id=company_id,
        title=title,
        salary=Decimal("90000.00"),
        education_req="Bachelor's",
        experience_req="2+ years",
        description="Build things.",
        listing_date=date(2025, 1, 1),
    )


# ─────────────────────────────────────────────────────────────────────────────
# create_position
# ─────────────────────────────────────────────────────────────────────────────


class TestCreatePosition:
    def test_returns_position_object(self, session, company):
        pos = make_position(session, company.company_id)
        assert pos is not None

    def test_position_id_assigned(self, session, company):
        pos = make_position(session, company.company_id)
        assert pos.position_id is not None
        assert pos.position_id >= 1

    def test_title_stored_correctly(self, session, company):
        pos = make_position(session, company.company_id, title="Data Scientist")
        assert pos.title == "Data Scientist"

    def test_salary_stored_correctly(self, session, company):
        pos = make_position(session, company.company_id)
        assert pos.salary == Decimal("90000.00")

    def test_company_id_linked_correctly(self, session, company):
        pos = make_position(session, company.company_id)
        assert pos.company_id == company.company_id

    def test_multiple_positions_get_unique_ids(self, session, company):
        p1 = make_position(session, company.company_id, "Engineer")
        p2 = make_position(session, company.company_id, "Designer")
        assert p1.position_id != p2.position_id


# ─────────────────────────────────────────────────────────────────────────────
# get_position
# ─────────────────────────────────────────────────────────────────────────────


class TestGetPosition:
    def test_returns_correct_position(self, session, company):
        pos = make_position(session, company.company_id)
        fetched = get_position(session, pos.position_id)
        assert fetched.position_id == pos.position_id

    def test_returns_none_for_missing_id(self, session):
        result = get_position(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_position(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session, company):
        pos = make_position(session, company.company_id, "DevOps Engineer")
        fetched = get_position(session, pos.position_id)
        assert fetched.title == "DevOps Engineer"
        assert fetched.salary == Decimal("90000.00")

    def test_returns_none_for_negative_id(self, session):
        result = get_position(session, -2)
        assert result is None

    def test_listing_date_matches_after_fetch(self, session, company):
        pos = make_position(session, company.company_id)
        fetched = get_position(session, pos.position_id)
        assert fetched.listing_date == date(2025, 1, 1)


# ─────────────────────────────────────────────────────────────────────────────
# update_position
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdatePosition:
    def test_update_returns_true(self, session, company):
        pos = make_position(session, company.company_id)
        pos.title = "Senior Engineer"
        result = update_position(session, pos)
        assert result is True

    def test_title_updated(self, session, company):
        pos = make_position(session, company.company_id)
        pos.title = "Lead Engineer"
        update_position(session, pos)
        fetched = get_position(session, pos.position_id)
        assert fetched.title == "Lead Engineer"

    def test_salary_updated(self, session, company):
        pos = make_position(session, company.company_id)
        pos.salary = Decimal("120000.00")
        update_position(session, pos)
        fetched = get_position(session, pos.position_id)
        assert fetched.salary == Decimal("120000.00")

    def test_description_updated(self, session, company):
        pos = make_position(session, company.company_id)
        pos.description = "Updated description."
        update_position(session, pos)
        fetched = get_position(session, pos.position_id)
        assert fetched.description == "Updated description."

    def test_education_req_updated(self, session, company):
        pos = make_position(session, company.company_id)
        pos.education_req = "Master's required"
        update_position(session, pos)
        fetched = get_position(session, pos.position_id)
        assert fetched.education_req == "Master's required"

    def test_other_positions_unaffected(self, session, company):
        p1 = make_position(session, company.company_id, "Engineer")
        p2 = make_position(session, company.company_id, "Designer")
        p1.title = "Changed"
        update_position(session, p1)
        fetched_p2 = get_position(session, p2.position_id)
        assert fetched_p2.title == "Designer"
