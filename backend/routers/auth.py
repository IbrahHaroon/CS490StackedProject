import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from database.auth import (
    create_access_token,
    decode_access_token,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)
from database.models.credentials import Credentials
from database.models.password_reset import PasswordResetToken
from database.models.token_blacklist import TokenBlacklist
from database.models.user import User
from schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    RegisterRequest,
    ResetPasswordRequest,
    Token,
    UserResponse,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payload = decode_access_token(token)
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        db.add(TokenBlacklist(jti=jti, expires_at=expires_at))
        db.commit()
    return {"message": "Logged out successfully"}


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    new_user = User(email=user.email)
    db.add(new_user)
    db.flush()

    new_creds = Credentials(
        user_id=new_user.user_id, hashed_password=get_password_hash(user.password)
    )
    db.add(new_creds)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_creds = (
        db.query(Credentials).filter(Credentials.user_id == db_user.user_id).first()
    )

    if not db_creds or not verify_password(
        form_data.password, db_creds.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # Always return 200 so we don't reveal whether the email exists
    if not user:
        return {
            "message": "If that email is registered, a reset token has been issued."
        }

    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.used == False,  # noqa: E712
    ).update({"used": True})

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    db.add(
        PasswordResetToken(
            user_id=user.user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    db.commit()

    return {"message": "If that email is registered, a reset token has been issued."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,  # noqa: E712
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used reset token",
        )

    if datetime.now(timezone.utc) > record.expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired",
        )

    creds = db.query(Credentials).filter(Credentials.user_id == record.user_id).first()
    if not creds:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User credentials not found"
        )

    creds.hashed_password = get_password_hash(body.new_password)
    record.used = True
    db.commit()

    return {"message": "Password updated successfully"}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change password directly — verifies current password then updates the hash."""
    creds = (
        db.query(Credentials)
        .filter(Credentials.user_id == current_user.user_id)
        .first()
    )
    if not creds or not verify_password(body.current_password, creds.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if len(body.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters.",
        )
    creds.hashed_password = get_password_hash(body.new_password)
    db.commit()
    return {"message": "Password updated successfully"}
