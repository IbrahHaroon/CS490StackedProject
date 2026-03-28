from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from database.models.user import User
from database.models.credentials import Credentials
from schemas import Token, RegisterRequest, UserResponse
from database.auth import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
def logout(_: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    new_user = User(email=user.email)
    db.add(new_user)
    db.flush()

    new_creds = Credentials(
        user_id=new_user.user_id,
        hashed_password=get_password_hash(user.password)
    )
    db.add(new_creds)
    db.commit()
    db.refresh(new_user)

    return new_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    db_user = db.query(User).filter(User.email == form_data.username).first()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    db_creds = db.query(Credentials).filter(Credentials.user_id == db_user.user_id).first()

    if not db_creds or not verify_password(form_data.password, db_creds.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}