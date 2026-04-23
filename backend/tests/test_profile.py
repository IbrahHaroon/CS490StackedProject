"""Tests for profile v2 — create_profile, get_profile, update_profile (address inlined)."""

from datetime import date

import pytest

from database.models.profile import create_profile, get_profile, update_profile
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "profile_user@example.com")


def _make(session, user, **overrides):
    defaults = {
        "first_name": "Jane",
        "last_name": "Doe",
        "dob": date(1990, 1, 1),
        "address_line": "1 Main St",
        "state": "NJ",
        "zip_code": "08534",
    }
    defaults.update(overrides)
    return create_profile(session, user.user_id, **defaults)


class TestCreateProfile:
    def test_returns_profile_object(self, session, user):
        assert _make(session, user) is not None

    def test_profile_id_assigned(self, session, user):
        profile = _make(session, user)
        assert profile.profile_id is not None and profile.profile_id >= 1

    def test_name_fields_stored(self, session, user):
        profile = _make(session, user)
        assert profile.first_name == "Jane"
        assert profile.last_name == "Doe"

    def test_dob_stored(self, session, user):
        dob = date(1995, 6, 15)
        profile = _make(session, user, dob=dob)
        assert profile.dob == dob

    def test_address_inlined(self, session, user):
        profile = _make(
            session, user, address_line="3 Pine Rd", state="CA", zip_code="90210"
        )
        assert profile.address_line == "3 Pine Rd"
        assert profile.state == "CA"
        assert profile.zip_code == "90210"

    def test_user_id_linked(self, session, user):
        profile = _make(session, user)
        assert profile.user_id == user.user_id


class TestGetProfile:
    def test_returns_correct_profile(self, session, user):
        profile = _make(session, user)
        fetched = get_profile(session, profile.profile_id)
        assert fetched.profile_id == profile.profile_id

    def test_returns_none_for_missing_id(self, session):
        assert get_profile(session, 99999) is None

    def test_returns_none_for_id_zero(self, session):
        assert get_profile(session, 0) is None

    def test_fields_match_after_fetch(self, session, user):
        profile = _make(session, user, first_name="Alice", last_name="Brown")
        fetched = get_profile(session, profile.profile_id)
        assert fetched.first_name == "Alice"
        assert fetched.last_name == "Brown"

    def test_returns_none_for_negative_id(self, session):
        assert get_profile(session, -1) is None


class TestUpdateProfile:
    def test_update_returns_true(self, session, user):
        profile = _make(session, user)
        profile.first_name = "Janet"
        assert update_profile(session, profile) is True

    def test_first_name_updated(self, session, user):
        profile = _make(session, user)
        profile.first_name = "Janet"
        update_profile(session, profile)
        assert get_profile(session, profile.profile_id).first_name == "Janet"

    def test_summary_updated(self, session, user):
        profile = _make(session, user)
        profile.summary = "Experienced developer."
        update_profile(session, profile)
        assert (
            get_profile(session, profile.profile_id).summary == "Experienced developer."
        )

    def test_phone_updated(self, session, user):
        profile = _make(session, user)
        profile.phone_number = "555-1234"
        update_profile(session, profile)
        assert get_profile(session, profile.profile_id).phone_number == "555-1234"

    def test_other_profiles_unaffected(self, session):
        u1 = create_user(session, "p1@example.com")
        u2 = create_user(session, "p2@example.com")
        p1 = create_profile(session, u1.user_id, "Alice", "A", date(1990, 1, 1))
        p2 = create_profile(session, u2.user_id, "Bob", "B", date(1991, 2, 2))
        p1.first_name = "Changed"
        update_profile(session, p1)
        assert get_profile(session, p2.profile_id).first_name == "Bob"
