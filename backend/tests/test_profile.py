"""Tests for profile.py — create_profile, get_profile, update_profile."""

from datetime import date

import pytest

from database.models.profile import create_profile, get_profile, update_profile
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "profile_user@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# create_profile
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateProfile:
    def test_returns_profile_object(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        assert profile is not None

    def test_profile_id_assigned(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        assert profile.profile_id is not None
        assert profile.profile_id >= 1

    def test_name_fields_stored_correctly(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        assert profile.first_name == "Jane"
        assert profile.last_name == "Doe"

    def test_dob_stored_correctly(self, session, user):
        dob = date(1995, 6, 15)
        profile = create_profile(
            session, user.user_id, "John", "Smith", dob, "2 Oak Ave", "NY", 10001
        )
        assert profile.dob == dob

    def test_address_id_created_and_linked(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "3 Pine Rd",
            "CA",
            90210,
        )
        assert profile.address_id is not None

    def test_user_id_linked_correctly(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "4 Elm St",
            "TX",
            73301,
        )
        assert profile.user_id == user.user_id


# ─────────────────────────────────────────────────────────────────────────────
# get_profile
# ─────────────────────────────────────────────────────────────────────────────


class TestGetProfile:
    def test_returns_correct_profile(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        fetched = get_profile(session, profile.profile_id)
        assert fetched.profile_id == profile.profile_id

    def test_returns_none_for_missing_id(self, session):
        result = get_profile(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_profile(session, 0)
        assert result is None

    def test_fields_match_after_fetch(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Alice",
            "Brown",
            date(1988, 3, 22),
            "5 Birch Ln",
            "FL",
            33101,
        )
        fetched = get_profile(session, profile.profile_id)
        assert fetched.first_name == "Alice"
        assert fetched.last_name == "Brown"

    def test_returns_none_for_negative_id(self, session):
        result = get_profile(session, -1)
        assert result is None

    def test_dob_matches_after_fetch(self, session, user):
        dob = date(2000, 12, 31)
        profile = create_profile(
            session, user.user_id, "Bob", "Green", dob, "6 Cedar Ct", "WA", 98101
        )
        fetched = get_profile(session, profile.profile_id)
        assert fetched.dob == dob


# ─────────────────────────────────────────────────────────────────────────────
# update_profile
# ─────────────────────────────────────────────────────────────────────────────


class TestUpdateProfile:
    def test_update_returns_true(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        profile.first_name = "Janet"
        result = update_profile(session, profile)
        assert result is True

    def test_first_name_updated(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        profile.first_name = "Janet"
        update_profile(session, profile)
        fetched = get_profile(session, profile.profile_id)
        assert fetched.first_name == "Janet"

    def test_last_name_updated(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        profile.last_name = "Smith"
        update_profile(session, profile)
        fetched = get_profile(session, profile.profile_id)
        assert fetched.last_name == "Smith"

    def test_summary_updated(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        profile.summary = "Experienced developer."
        update_profile(session, profile)
        fetched = get_profile(session, profile.profile_id)
        assert fetched.summary == "Experienced developer."

    def test_phone_number_updated(self, session, user):
        profile = create_profile(
            session,
            user.user_id,
            "Jane",
            "Doe",
            date(1990, 1, 1),
            "1 Main St",
            "NJ",
            8534,
        )
        profile.phone_number = "555-1234"
        update_profile(session, profile)
        fetched = get_profile(session, profile.profile_id)
        assert fetched.phone_number == "555-1234"

    def test_other_profiles_unaffected(self, session):
        u1 = create_user(session, "p1@example.com")
        u2 = create_user(session, "p2@example.com")
        p1 = create_profile(
            session, u1.user_id, "Alice", "A", date(1990, 1, 1), "1 St", "NJ", 1000
        )
        p2 = create_profile(
            session, u2.user_id, "Bob", "B", date(1991, 2, 2), "2 St", "NY", 2000
        )
        p1.first_name = "Changed"
        update_profile(session, p1)
        fetched_p2 = get_profile(session, p2.profile_id)
        assert fetched_p2.first_name == "Bob"
