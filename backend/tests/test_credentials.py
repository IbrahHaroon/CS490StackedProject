"""Tests for database/models/credentials.py — create_credentials, get_credentials_by_user_id."""

import pytest

from database.auth import get_password_hash, verify_password
from database.models.credentials import create_credentials, get_credentials_by_user_id
from database.models.user import create_user


@pytest.fixture
def user(session):
    return create_user(session, "creds_user@example.com")


# ─────────────────────────────────────────────────────────────────────────────
# create_credentials
# ─────────────────────────────────────────────────────────────────────────────


class TestCreateCredentials:
    def test_returns_credentials_object(self, session, user):
        creds = create_credentials(session, user.user_id, get_password_hash("pass"))
        assert creds is not None

    def test_credential_id_assigned(self, session, user):
        creds = create_credentials(session, user.user_id, get_password_hash("pass"))
        assert creds.credential_id is not None
        assert creds.credential_id >= 1

    def test_user_id_linked_correctly(self, session, user):
        creds = create_credentials(session, user.user_id, get_password_hash("pass"))
        assert creds.user_id == user.user_id

    def test_hashed_password_stored(self, session, user):
        hashed = get_password_hash("mypassword")
        creds = create_credentials(session, user.user_id, hashed)
        assert creds.hashed_password == hashed

    def test_hashed_password_verifies_correctly(self, session, user):
        hashed = get_password_hash("mypassword")
        creds = create_credentials(session, user.user_id, hashed)
        assert verify_password("mypassword", creds.hashed_password) is True

    def test_plain_password_not_stored(self, session, user):
        creds = create_credentials(
            session, user.user_id, get_password_hash("mypassword")
        )
        assert creds.hashed_password != "mypassword"

    def test_duplicate_user_id_raises(self, session, user):
        create_credentials(session, user.user_id, get_password_hash("first"))
        with pytest.raises(Exception):
            create_credentials(session, user.user_id, get_password_hash("second"))


# ─────────────────────────────────────────────────────────────────────────────
# get_credentials_by_user_id
# ─────────────────────────────────────────────────────────────────────────────


class TestGetCredentialsByUserId:
    def test_returns_correct_credentials(self, session, user):
        hashed = get_password_hash("pass")
        create_credentials(session, user.user_id, hashed)
        result = get_credentials_by_user_id(session, user.user_id)
        assert result is not None
        assert result.user_id == user.user_id

    def test_returns_none_for_nonexistent_user(self, session):
        result = get_credentials_by_user_id(session, 99999)
        assert result is None

    def test_lookup_uses_user_id_not_credential_id(self, session):
        # Create two users so credential_id and user_id are guaranteed to differ
        u1 = create_user(session, "first@example.com")
        u2 = create_user(session, "second@example.com")
        create_credentials(session, u1.user_id, get_password_hash("pass1"))
        create_credentials(session, u2.user_id, get_password_hash("pass2"))
        result = get_credentials_by_user_id(session, u2.user_id)
        assert result.user_id == u2.user_id

    def test_each_user_gets_their_own_credentials(self, session):
        u1 = create_user(session, "c1@example.com")
        u2 = create_user(session, "c2@example.com")
        create_credentials(session, u1.user_id, get_password_hash("pass1"))
        create_credentials(session, u2.user_id, get_password_hash("pass2"))
        c1 = get_credentials_by_user_id(session, u1.user_id)
        c2 = get_credentials_by_user_id(session, u2.user_id)
        assert c1.hashed_password != c2.hashed_password
