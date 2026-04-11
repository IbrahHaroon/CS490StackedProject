from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Ensure these imports point to your actual file locations
from database import get_db, get_settings
from database.models.token_blacklist import TokenBlacklist
from database.models.user import User

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password: str) -> str:
    """Strictly synchronous password hashing."""
    pwd_bytes = password.encode("utf-8")
    # Use bcrypt directly to avoid passlib incompatibility on Python 3.13
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Strictly synchronous password verification."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def create_access_token(data: dict) -> str:
    """Generates a synchronous JWT access token.

    data must include:
      "sub"          — email address of the account
      "account_type" — "user" or "recruiter"
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    to_encode["exp"] = expire
    to_encode["jti"] = secrets.token_urlsafe(32)
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decodes a JWT token synchronously."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Reject tokens that belong to a recruiter account
    if payload.get("account_type") != "user":
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    jti: str = payload.get("jti")
    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()

    if user is None:
        raise credentials_exception

    return user


def get_current_recruiter(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    from database.models.recruiter import get_recruiter_by_email

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    # Reject tokens that belong to a user (candidate) account
    if payload.get("account_type") != "recruiter":
        raise credentials_exception

    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception

    jti: str = payload.get("jti")
    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        raise credentials_exception

    recruiter = get_recruiter_by_email(db, email)
    if recruiter is None:
        raise credentials_exception

    return recruiter
