from types import SimpleNamespace

import dependencies.auth as auth_dep
import pytest
from fastapi.testclient import TestClient
from main import app
from router.jobs import mock_jobs

client = TestClient(app)


class MockSupabaseAuth:
    def __init__(self, user):
        self._user = user

    def get_user(self, token: str):
        if token in ["valid-token-user-1", "valid-token-user-2"]:
            return SimpleNamespace(user=self._user)
        raise Exception("Invalid token")


class MockSupabase:
    def __init__(self, user):
        self.auth = MockSupabaseAuth(user)


@pytest.fixture(autouse=True)
def reset_jobs():
    mock_jobs.clear()
    mock_jobs.extend(
        [
            {"id": 1, "title": "Job 1", "description": "Desc 1", "user_id": "user-1"},
            {"id": 2, "title": "Job 2", "description": "Desc 2", "user_id": "user-1"},
            {"id": 3, "title": "Job 3", "description": "Desc 3", "user_id": "user-2"},
        ]
    )
    yield


def test_user_can_get_own_jobs(monkeypatch):
    monkeypatch.setattr(
        auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1"))
    )

    response = client.get(
        "/api/jobs",
        headers={"Authorization": "Bearer valid-token-user-1"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_user_cannot_access_other_user_job(monkeypatch):
    monkeypatch.setattr(
        auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1"))
    )

    response = client.get(
        "/api/jobs/3",
        headers={"Authorization": "Bearer valid-token-user-1"},
    )

    assert response.status_code == 403
