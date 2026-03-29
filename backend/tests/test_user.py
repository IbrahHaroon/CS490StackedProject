"""Tests for user.py — create_user, get_user."""

import pytest

from database.models.user import create_user, get_user

# ─────────────────────────────────────────────────────────────────────────────
# create_user
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateUser:
    def test_returns_user_object(self, session):
        user = create_user(session, "alice@example.com")
        assert user is not None

    def test_user_id_assigned(self, session):
        user = create_user(session, "bob@example.com")
        assert user.user_id is not None
        assert user.user_id >= 1

    def test_email_stored_correctly(self, session):
        user = create_user(session, "carol@example.com")
        assert user.email == "carol@example.com"

    def test_multiple_users_get_unique_ids(self, session):
        u1 = create_user(session, "u1@example.com")
        u2 = create_user(session, "u2@example.com")
        assert u1.user_id != u2.user_id

    def test_user_persisted_to_database(self, session):
        user = create_user(session, "dave@example.com")
        fetched = get_user(session, user.user_id)
        assert fetched is not None
        assert fetched.email == "dave@example.com"

    def test_unique_email_constraint(self, session):
        create_user(session, "unique@example.com")
        with pytest.raises(Exception):
            create_user(session, "unique@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# get_user
# ─────────────────────────────────────────────────────────────────────────────


class TestGetUser:
    def test_returns_correct_user(self, session):
        user = create_user(session, "eve@example.com")
        fetched = get_user(session, user.user_id)
        assert fetched.user_id == user.user_id

    def test_returns_none_for_missing_id(self, session):
        result = get_user(session, 99999)
        assert result is None

    def test_returns_none_for_id_zero(self, session):
        result = get_user(session, 0)
        assert result is None

    def test_email_matches_after_fetch(self, session):
        user = create_user(session, "frank@example.com")
        fetched = get_user(session, user.user_id)
        assert fetched.email == "frank@example.com"

    def test_two_users_return_different_records(self, session):
        u1 = create_user(session, "g1@example.com")
        u2 = create_user(session, "g2@example.com")
        f1 = get_user(session, u1.user_id)
        f2 = get_user(session, u2.user_id)
        assert f1.email != f2.email

    def test_returns_none_for_negative_id(self, session):
        result = get_user(session, -5)
        assert result is None
