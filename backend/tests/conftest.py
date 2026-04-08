"""
conftest.py
-----------
Shared pytest fixtures using SQLite in-memory database.

Tables are dropped and recreated before every test function, giving
complete isolation without requiring PostgreSQL.  For a shared in-memory
database StaticPool is used so all engine operations hit the same DB.
"""

import os
import sys

# Add backend dir so `database/`, `schemas`, `routers`, and `index` are all importable.
_tests_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_tests_dir)

sys.path.insert(0, _backend_dir)

# Set env vars before any project module is imported
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-production")

# Patch httpx.Client to handle Starlette 0.36 TestClient compatibility issue
import httpx

_original_init = httpx.Client.__init__


def _patched_init(self, *args, **kwargs):
    # Remove 'app' kwarg if present (from Starlette TestClient)
    kwargs.pop("app", None)
    _original_init(self, *args, **kwargs)


httpx.Client.__init__ = _patched_init

import pytest
from index import app
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

import database.models  # noqa: F401 — registers all ORM classes with Base
from database import get_db
from database.base import Base

# ---------------------------------------------------------------------------
# Session-scoped engine — StaticPool shares one in-memory DB across tests.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(eng, "connect")
    def enable_foreign_keys(dbapi_conn, _):  # noqa: F811
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(eng)
    yield eng


# ---------------------------------------------------------------------------
# Function-scoped session — wipes and rebuilds tables before every test.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def session(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Function-scoped TestClient — shares the same fresh session.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def client(session):
    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth helpers — register + login a user, return (user_id, auth_headers).
# ---------------------------------------------------------------------------


def _register_and_login(
    client, email: str, password: str = "testpass123"
) -> tuple[int, dict]:
    reg = client.post("/auth/register", json={"email": email, "password": password})
    user_id = reg.json()["user_id"]
    login = client.post("/auth/login", data={"username": email, "password": password})
    token = login.json()["access_token"]
    return user_id, {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_with_auth(client) -> tuple[int, dict]:
    """Return (user_id, auth_headers) for a freshly registered user."""
    return _register_and_login(client, "user_a@test.com")


@pytest.fixture(scope="function")
def other_user_with_auth(client) -> tuple[int, dict]:
    """Return (user_id, auth_headers) for a second user — used for ownership tests."""
    return _register_and_login(client, "user_b@test.com")
