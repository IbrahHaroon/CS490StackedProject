"""Tests for POST /auth/register and POST /auth/login."""

REGISTER_URL = "/auth/register"
LOGIN_URL = "/auth/login"

VALID_EMAIL = "auth_test@example.com"
VALID_PASSWORD = "securepassword123"


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/register
# ─────────────────────────────────────────────────────────────────────────────


class TestRegister:
    def test_returns_201_on_success(self, client):
        response = client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        assert response.status_code == 201

    def test_response_contains_user_id(self, client):
        response = client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        assert "user_id" in response.json()

    def test_response_contains_email(self, client):
        response = client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        assert response.json()["email"] == VALID_EMAIL

    def test_response_does_not_contain_password(self, client):
        response = client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        body = response.json()
        assert "password" not in body
        assert "hashed_password" not in body

    def test_duplicate_email_returns_400(self, client):
        client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        response = client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )
        assert response.status_code == 400

    def test_invalid_email_format_returns_422(self, client):
        response = client.post(
            REGISTER_URL, json={"email": "notanemail", "password": VALID_PASSWORD}
        )
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post(REGISTER_URL, json={"email": VALID_EMAIL})
        assert response.status_code == 422

    def test_missing_email_returns_422(self, client):
        response = client.post(REGISTER_URL, json={"password": VALID_PASSWORD})
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/login
# ─────────────────────────────────────────────────────────────────────────────


class TestLogin:
    def _register(self, client):
        client.post(
            REGISTER_URL, json={"email": VALID_EMAIL, "password": VALID_PASSWORD}
        )

    def _login(self, client, email=VALID_EMAIL, password=VALID_PASSWORD):
        # OAuth2PasswordRequestForm expects form data with field name "username"
        return client.post(LOGIN_URL, data={"username": email, "password": password})

    def test_returns_200_with_valid_credentials(self, client):
        self._register(client)
        response = self._login(client)
        assert response.status_code == 200

    def test_response_contains_access_token(self, client):
        self._register(client)
        response = self._login(client)
        assert "access_token" in response.json()

    def test_response_token_type_is_bearer(self, client):
        self._register(client)
        response = self._login(client)
        assert response.json()["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client):
        self._register(client)
        response = self._login(client, password="wrongpassword")
        assert response.status_code == 401

    def test_nonexistent_email_returns_401(self, client):
        response = self._login(client, email="nobody@example.com", password="any")
        assert response.status_code == 401

    def test_wrong_password_and_wrong_email_return_same_status(self, client):
        # Both must return 401 — prevents user enumeration
        self._register(client)
        wrong_pass = self._login(client, password="wrong")
        wrong_user = self._login(client, email="nobody@example.com", password="any")
        assert wrong_pass.status_code == wrong_user.status_code == 401

    def test_token_is_a_valid_jwt_string(self, client):
        self._register(client)
        response = self._login(client)
        token = response.json()["access_token"]
        assert len(token.split(".")) == 3


# ─────────────────────────────────────────────────────────────────────────────
# GET /auth/me
# ─────────────────────────────────────────────────────────────────────────────


class TestGetMe:
    def test_returns_200_with_valid_token(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200

    def test_returns_current_user_email(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.get("/auth/me", headers=headers)
        assert response.json()["email"] == "user_a@test.com"

    def test_returns_user_id(self, client, user_with_auth):
        user_id, headers = user_with_auth
        response = client.get("/auth/me", headers=headers)
        assert response.json()["user_id"] == user_id

    def test_unauthenticated_returns_401(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# POST /auth/logout
# ─────────────────────────────────────────────────────────────────────────────


class TestLogout:
    def test_returns_200_with_valid_token(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.post("/auth/logout", headers=headers)
        assert response.status_code == 200

    def test_response_contains_message(self, client, user_with_auth):
        _, headers = user_with_auth
        response = client.post("/auth/logout", headers=headers)
        assert "message" in response.json()

    def test_unauthenticated_logout_returns_401(self, client):
        response = client.post("/auth/logout")
        assert response.status_code == 401
