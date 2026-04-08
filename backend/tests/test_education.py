"""Tests for education.py — create_education, get_education."""

from datetime import date as _date

import pytest

from database.models.education import create_education, get_education
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "edu_user@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# create_education
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateEducation:
    def test_returns_education_object(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Bachelor's",
            "Computer Science",
            "State U",
            "1 Campus Dr",
            "NJ",
            8901,
        )
        assert edu is not None

    def test_education_id_assigned(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Bachelor's",
            "CS",
            "State U",
            "1 Campus Dr",
            "NJ",
            8901,
        )
        assert edu.education_id is not None
        assert edu.education_id >= 1

    def test_degree_stored_correctly(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Master's",
            "Data Science",
            "Tech U",
            "2 Uni Ave",
            "NY",
            10001,
        )
        assert edu.degree == "Data Science"
        assert edu.highest_education == "Master's"

    def test_school_stored_correctly(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Bachelor's",
            "Math",
            "City College",
            "3 College Rd",
            "CA",
            90210,
        )
        assert edu.school_or_college == "City College"

    def test_address_id_created_and_linked(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "PhD",
            "Physics",
            "Research U",
            "4 Lab Blvd",
            "MA",
            2101,
        )
        assert edu.address_id is not None

    def test_user_id_linked_correctly(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Associate's",
            "Business",
            "Comm College",
            "5 Main St",
            "TX",
            73301,
        )
        assert edu.user_id == user.user_id

    def test_one_user_can_have_multiple_degrees(self, session, user):
        edu1 = create_education(
            session, user.user_id, "Bachelor's", "CS", "State U", "1 St", "NJ", 1000
        )
        edu2 = create_education(
            session, user.user_id, "Master's", "AI", "Tech U", "2 Ave", "NY", 2000
        )
        assert edu1.education_id != edu2.education_id


# ─────────────────────────────────────────────────────────────────────────────
# get_education
# ─────────────────────────────────────────────────────────────────────────────


class TestGetEducation:
    def test_returns_correct_education(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Bachelor's",
            "CS",
            "State U",
            "1 Campus Dr",
            "NJ",
            8901,
        )
        fetched = get_education(session, edu.education_id)
        assert fetched.education_id == edu.education_id

    def test_returns_none_for_missing_id(self, session):
        result = get_education(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_education(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session, user):
        edu = create_education(
            session, user.user_id, "PhD", "ML", "Research U", "6 Sci Blvd", "WA", 98101
        )
        fetched = get_education(session, edu.education_id)
        assert fetched.degree == "ML"
        assert fetched.highest_education == "PhD"

    def test_returns_none_for_negative_id(self, session):
        result = get_education(session, -1)
        assert result is None

    def test_school_matches_after_fetch(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Bachelor's",
            "Art",
            "Art Institute",
            "7 Art Ln",
            "IL",
            60601,
        )
        fetched = get_education(session, edu.education_id)
        assert fetched.school_or_college == "Art Institute"


# ─────────────────────────────────────────────────────────────────────────────
# TestEducationNewFields — S2-017
# ─────────────────────────────────────────────────────────────────────────────


class TestEducationNewFields:
    def test_create_education_new_fields_default_null(self, session, user):
        edu = create_education(
            session, user.user_id, "Bachelor's", "CS", "State U", "1 St", "NJ", 8901
        )
        assert edu.field_of_study is None
        assert edu.start_date is None
        assert edu.end_date is None
        assert edu.gpa is None

    def test_create_education_with_all_new_fields(self, session, user):
        edu = create_education(
            session, user.user_id, "Master's", "AI", "Tech U", "2 Ave", "NY", 10001,
            field_of_study="Machine Learning",
            start_date=_date(2022, 9, 1),
            end_date=_date(2024, 5, 31),
            gpa="3.9/4.0",
        )
        assert edu.field_of_study == "Machine Learning"
        assert edu.start_date == _date(2022, 9, 1)
        assert edu.end_date == _date(2024, 5, 31)
        assert edu.gpa == "3.9/4.0"

    def test_gpa_stored_as_string_format(self, session, user):
        edu = create_education(
            session, user.user_id, "Bachelor's", "Math", "City U", "3 Rd", "CA", 90210,
            gpa="3.75/4.0",
        )
        assert edu.gpa == "3.75/4.0"
        assert isinstance(edu.gpa, str)


# ─────────────────────────────────────────────────────────────────────────────
# TestRegression — existing behaviour unbroken after column additions
# ─────────────────────────────────────────────────────────────────────────────


class TestRegression:
    def test_original_create_still_works_without_new_fields(self, session, user):
        edu = create_education(
            session, user.user_id, "Bachelor's", "CS", "State U", "1 Campus Dr", "NJ", 8901
        )
        assert edu.education_id is not None
        assert edu.degree == "CS"
        assert edu.school_or_college == "State U"

    def test_original_get_still_works(self, session, user):
        edu = create_education(
            session, user.user_id, "PhD", "Physics", "Research U", "4 Lab Blvd", "MA", 2101
        )
        fetched = get_education(session, edu.education_id)
        assert fetched is not None
        assert fetched.education_id == edu.education_id
