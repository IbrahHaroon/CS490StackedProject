"""Shared test fixtures for analytics testing."""

import pytest
from fastapi.testclient import TestClient
from index import app
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from database.auth import get_password_hash
from database.base import Base
from database.database import get_db
from database.models.credentials import Credentials
from database.models.user import User


@pytest.fixture(scope="session")
def test_db_url():
    """Use in-memory SQLite for tests."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Create test database engine."""
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    """Create a fresh test session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    test_session = sessionmaker(bind=connection)()

    yield test_session

    test_session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_user(session: Session) -> User:
    """Create a test user."""
    from database.models.user import create_user

    return create_user(session, email="test@example.com")


@pytest.fixture
def client(session: Session):
    """Create a FastAPI test client with overridden database dependency."""

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user_with_auth(client, session: Session):
    """Create a user, log in, and return (user_id, headers with auth token)."""
    email = "user_a@test.com"
    password = "testpassword123"

    # Create user
    user = User(email=email)
    session.add(user)
    session.flush()

    # Add credentials
    creds = Credentials(
        user_id=user.user_id, hashed_password=get_password_hash(password)
    )
    session.add(creds)
    session.commit()

    # Login to get token
    response = client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    return user.user_id, headers


@pytest.fixture
def other_user_with_auth(client, session: Session):
    """Create another user, log in, and return (user_id, headers with auth token)."""
    email = "user_b@test.com"
    password = "otherpassword123"

    # Create user
    user = User(email=email)
    session.add(user)
    session.flush()

    # Add credentials
    creds = Credentials(
        user_id=user.user_id, hashed_password=get_password_hash(password)
    )
    session.add(creds)
    session.commit()

    # Login to get token
    response = client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    token = response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    return user.user_id, headers
