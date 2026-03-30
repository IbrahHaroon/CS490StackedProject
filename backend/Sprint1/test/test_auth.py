from types import SimpleNamespace

import dependencies.auth as auth_dep
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class MockSupabaseAuth:
    def __init__(self, user):
        self._user = user

    def get_user(self, token: str):
        if token == "valid-token-user-1":
            return SimpleNamespace(user=self._user)
        raise Exception("Invalid token")


class MockSupabase:
    def __init__(self, user):
        self.auth = MockSupabaseAuth(user)


def test_missing_token():
    response = client.get("/api/jobs")
    assert response.status_code == 401


def test_invalid_token(monkeypatch):
    monkeypatch.setattr(
        auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1"))
    )

    response = client.get(
        "/api/jobs",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_valid_token(monkeypatch):
    monkeypatch.setattr(
        auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1"))
    )

    response = client.get(
        "/api/jobs",
        headers={"Authorization": "Bearer valid-token-user-1"},
    )

    assert response.status_code == 200
