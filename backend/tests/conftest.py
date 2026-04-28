"""Shared test fixtures for analytics testing."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base
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
