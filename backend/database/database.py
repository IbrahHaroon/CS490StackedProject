import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Resolve the project root (two levels up from this file: database/ -> backend/ -> root)
_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_ROOT_ENV = os.path.join(_PROJECT_ROOT, ".env")
_BACKEND_ENV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)


class Settings(BaseSettings):
    database_url: str = "postgresql://user:postgres@localhost/jobsdb"
    secret_key: str = "supersecret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    frontend_url: str = "http://localhost:3000"

    openai_api_key: str = ""
    gemini_api_key: str = ""

    # Load root .env first, then backend .env — later files override earlier ones
    model_config = SettingsConfigDict(
        env_file=[_ROOT_ENV, _BACKEND_ENV], extra="ignore"
    )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()

# Create a synchronous connection URL by removing the async driver if present
sync_url = settings.database_url.replace("+asyncpg", "").replace("+aiosqlite", "")

engine = create_engine(
    sync_url,
    echo=True,
    pool_size=20,  # Base pool connections
    max_overflow=10,  # Extra connections when pool exhausted
    pool_pre_ping=True,  # Test connections before using
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
