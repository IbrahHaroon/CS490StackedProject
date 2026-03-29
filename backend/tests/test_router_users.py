"""Tests for GET /users/{user_id}."""

from database.models.user import create_user

USERS_URL = "/users"


# ─────────────────────────────────────────────────────────────────────────────
# GET /users/{user_id}
# ─────────────────────────────────────────────────────────────────────────────


class TestReadUser:
    def test_returns_200_for_existing_user(self, client, session):
        user = create_user(session, "reader@example.com")
        response = client.get(f"{USERS_URL}/{user.user_id}")
        assert response.status_code == 200

    def test_response_contains_user_id(self, client, session):
        user = create_user(session, "reader@example.com")
        response = client.get(f"{USERS_URL}/{user.user_id}")
        assert response.json()["user_id"] == user.user_id

    def test_response_contains_email(self, client, session):
        user = create_user(session, "reader@example.com")
        response = client.get(f"{USERS_URL}/{user.user_id}")
        assert response.json()["email"] == "reader@example.com"

    def test_returns_404_for_missing_user(self, client):
        response = client.get(f"{USERS_URL}/99999")
        assert response.status_code == 404

    def test_returns_correct_user_among_multiple(self, client, session):
        u1 = create_user(session, "first@example.com")
        u2 = create_user(session, "second@example.com")
        response = client.get(f"{USERS_URL}/{u2.user_id}")
        assert response.json()["email"] == "second@example.com"
        assert response.json()["user_id"] != u1.user_id

    def test_response_does_not_contain_password(self, client, session):
        user = create_user(session, "noleak@example.com")
        body = client.get(f"{USERS_URL}/{user.user_id}").json()
        assert "password" not in body
        assert "hashed_password" not in body
