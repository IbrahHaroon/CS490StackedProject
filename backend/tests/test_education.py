"""Tests for education v2 — create_education, get_education."""

from datetime import date as _date

import pytest

from database.models.education import create_education, get_education
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "edu_user@example.com")


class TestCreateEducation:
    def test_returns_education_object(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            school="State U",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
        )
        assert edu is not None

    def test_education_id_assigned(self, session, user):
        edu = create_education(session, user.user_id, "State U", "BS")
        assert edu.education_id is not None and edu.education_id >= 1

    def test_degree_stored(self, session, user):
        edu = create_education(
            session, user.user_id, "Tech U", "Master of Science", field_of_study="AI"
        )
        assert edu.degree == "Master of Science"
        assert edu.field_of_study == "AI"

    def test_school_stored(self, session, user):
        edu = create_education(session, user.user_id, "City College", "BS")
        assert edu.school == "City College"

    def test_school_location_stored_inline(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            "Research U",
            "PhD",
            school_location="4 Lab Blvd, MA 02101",
        )
        assert edu.school_location == "4 Lab Blvd, MA 02101"

    def test_user_id_linked_correctly(self, session, user):
        edu = create_education(session, user.user_id, "Comm College", "Associate")
        assert edu.user_id == user.user_id

    def test_one_user_can_have_multiple_degrees(self, session, user):
        edu1 = create_education(session, user.user_id, "State U", "BS")
        edu2 = create_education(session, user.user_id, "Tech U", "MS")
        assert edu1.education_id != edu2.education_id


class TestGetEducation:
    def test_returns_correct_education(self, session, user):
        edu = create_education(session, user.user_id, "State U", "BS")
        fetched = get_education(session, edu.education_id)
        assert fetched.education_id == edu.education_id

    def test_returns_none_for_missing_id(self, session):
        assert get_education(session, 99999) is None

    def test_returns_none_for_id_zero(self, session):
        assert get_education(session, 0) is None

    def test_fields_match_after_fetch(self, session, user):
        edu = create_education(
            session, user.user_id, "Research U", "PhD", field_of_study="ML"
        )
        fetched = get_education(session, edu.education_id)
        assert fetched.degree == "PhD"
        assert fetched.field_of_study == "ML"

    def test_returns_none_for_negative_id(self, session):
        assert get_education(session, -1) is None


class TestEducationOptionalFields:
    def test_optional_fields_default_null(self, session, user):
        edu = create_education(session, user.user_id, "State U", "BS")
        assert edu.field_of_study is None
        assert edu.start_date is None
        assert edu.end_date is None
        assert edu.gpa is None
        assert edu.school_location is None

    def test_create_with_all_fields(self, session, user):
        edu = create_education(
            session,
            user.user_id,
            school="Tech U",
            degree="MS",
            field_of_study="Machine Learning",
            start_date=_date(2022, 9, 1),
            end_date=_date(2024, 5, 31),
            gpa="3.9/4.0",
            school_location="2 Ave, NY 10001",
            sort_order=1,
        )
        assert edu.field_of_study == "Machine Learning"
        assert edu.start_date == _date(2022, 9, 1)
        assert edu.end_date == _date(2024, 5, 31)
        assert edu.gpa == "3.9/4.0"
        assert edu.school_location == "2 Ave, NY 10001"
        assert edu.sort_order == 1
