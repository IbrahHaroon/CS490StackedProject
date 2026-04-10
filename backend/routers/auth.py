import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from utils.email import send_password_reset_email

from database import get_db
from database.auth import (
    create_access_token,
    decode_access_token,
    get_current_recruiter,
    get_current_user,
    get_password_hash,
    oauth2_scheme,
    verify_password,
)
from database.models.credentials import Credentials
from database.models.password_reset import PasswordResetToken
from database.models.recruiter import Recruiter, get_recruiter_by_email
from database.models.recruiter_credentials import RecruiterCredentials
from database.models.token_blacklist import TokenBlacklist
from database.models.user import User
from schemas import (
    ForgotPasswordRequest,
    RecruiterRegisterRequest,
    RecruiterResponse,
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

    access_token = create_access_token(
        data={"sub": db_user.email, "account_type": "user"}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # Always return 200 so we don't reveal whether the email exists
    if not user:
        return {
            "message": "If that email is registered, a reset token has been issued."
        }

    # Invalidate any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.used == False,
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

    send_password_reset_email(user.email, raw_token)
    return {"message": "If that email is registered, a reset token has been issued."}


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(body.token.encode()).hexdigest()

    record = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used == False,
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


# --------------------------------------------------------------------------- #
#  Recruiter Auth                                                               #
# --------------------------------------------------------------------------- #


@router.post(
    "/recruiter/register",
    response_model=RecruiterResponse,
    status_code=status.HTTP_201_CREATED,
)
def recruiter_register(body: RecruiterRegisterRequest, db: Session = Depends(get_db)):
    existing = get_recruiter_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered as a recruiter",
        )

    new_recruiter = Recruiter(
        email=body.email,
        company_id=body.company_id,
        first_name=body.first_name,
        last_name=body.last_name,
        job_title=body.job_title,
    )
    db.add(new_recruiter)
    db.flush()

    new_creds = RecruiterCredentials(
        recruiter_id=new_recruiter.recruiter_id,
        hashed_password=get_password_hash(body.password),
    )
    db.add(new_creds)
    db.commit()
    db.refresh(new_recruiter)

    return new_recruiter


@router.post("/recruiter/login", response_model=Token)
def recruiter_login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    recruiter = get_recruiter_by_email(db, form_data.username)

    if not recruiter:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_creds = (
        db.query(RecruiterCredentials)
        .filter(RecruiterCredentials.recruiter_id == recruiter.recruiter_id)
        .first()
    )

    if not db_creds or not verify_password(form_data.password, db_creds.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": recruiter.email, "account_type": "recruiter"}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/recruiter/me", response_model=RecruiterResponse)
def get_recruiter_me(
    current_recruiter: Recruiter = Depends(get_current_recruiter),
):
    return current_recruiter


@router.post("/recruiter/logout")
def recruiter_logout(
    token: str = Depends(oauth2_scheme),
    _: Recruiter = Depends(get_current_recruiter),
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
