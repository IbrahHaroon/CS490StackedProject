from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import dependencies.auth as auth_dep
from main import app
from router.jobs import mock_jobs

client = TestClient(app)

class MockSupabaseAuth:
    def __init__(self, user):
        self._user = user

    def get_user(self, token: str):
        if token == "valid-token-user-1":
            return SimpleNamespace(user=self._user)
        if token == "valid-token-user-2":
            return SimpleNamespace(user=self._user)
        raise Exception("Invalid token")


class MockSupabase:
    def __init__(self, user):
        self.auth = MockSupabaseAuth(user)


@pytest.fixture(autouse=True)
def reset_mock_jobs():
    """Reset mock jobs before each test."""
    mock_jobs.clear()
    mock_jobs.extend([
        {"id": 1, "title": "Job 1", "description": "Desc 1", "user_id": "user-1"},
        {"id": 2, "title": "Job 2", "description": "Desc 2", "user_id": "user-1"},
        {"id": 3, "title": "Job 3", "description": "Desc 3", "user_id": "user-2"},
    ])
    yield


def test_user_can_access_own_jobs(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.get("/api/jobs", headers=headers)
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2  # user 1 has 2 jobs
    assert all(job["user_id"] == "user-1" for job in jobs)


def test_user_can_access_own_job_detail(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.get("/api/jobs/1", headers=headers)
    assert response.status_code == 200
    job = response.json()
    assert job["user_id"] == "user-1"
    assert job["id"] == 1


def test_user_cannot_access_other_users_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.get("/api/jobs/3", headers=headers)  # job 3 belongs to user 2
    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden", "detail": "You do not have access to this resource"}


def test_user_cannot_update_other_users_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    update_data = {"title": "Updated", "description": "Updated desc"}
    response = client.put("/api/jobs/3", json=update_data, headers=headers)
    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden", "detail": "You do not have access to this resource"}


def test_user_cannot_delete_other_users_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.delete("/api/jobs/3", headers=headers)
    assert response.status_code == 403
    assert response.json() == {"error": "Forbidden", "detail": "You do not have access to this resource"}


def test_user_can_update_own_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}
    update_data = {"title": "Updated Job 1", "description": "Updated desc"}
    response = client.put("/api/jobs/1", json=update_data, headers=headers)
    assert response.status_code == 200
    job = response.json()
    assert job["title"] == "Updated Job 1"
    assert job["user_id"] == "user-1"


def test_user_can_delete_own_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.delete("/api/jobs/1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"message": "Job deleted successfully"}

    # Verify it's deleted
    response = client.get("/api/jobs/1", headers=headers)
    assert response.status_code == 404


def test_access_non_existent_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    response = client.get("/api/jobs/999", headers=headers)
    assert response.status_code == 404
    assert response.json() == {"error": "Error", "detail": "Job not found"}


def test_user_can_create_job(monkeypatch):
    monkeypatch.setattr(auth_dep, "supabase", MockSupabase(SimpleNamespace(id="user-1")))
    headers = {"Authorization": "Bearer valid-token-user-1"}

    create_data = {"title": "New Job", "description": "New desc"}
    response = client.post("/api/jobs", json=create_data, headers=headers)
    assert response.status_code == 200
    job = response.json()
    assert job["title"] == "New Job"
    assert job["user_id"] == "user-1"
