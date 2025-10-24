from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db, User, UserProfile
from app.schemas import UserCreate, UserLogin, UserResponse, Token, UserStatus
from app.security import verify_token, verify_password, hash_password, create_tokens

security = HTTPBearer()
router = APIRouter(tags=["Authentication"])


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_user_with_optional_profile(db: Session, payload: UserCreate) -> User:
    hashed_password = hash_password(payload.password)
    user = User(
        email=payload.email,
        username=payload.username,
        hashed_password=hashed_password
    )
    # Профиль создаётся, если передан
    if payload.profile:
        user.profile = UserProfile(
            full_name=payload.profile.full_name,
            age=payload.profile.age,
            gender=payload.profile.gender,
            current_weight=payload.profile.current_weight,
            height=payload.profile.height,
            goal=payload.profile.goal,
            activity=payload.profile.activity,
            special_needs=payload.profile.special_needs,
            desired_weight=payload.profile.desired_weight,
            tastes=payload.profile.tastes,
        )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Auth deps
def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    email = verify_token(token, expected_token_type="access")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

def verify_refresh_token(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = credentials.credentials
    email = verify_token(token, expected_token_type="refresh")
    if email is None:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

# Routes
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    try:
        db_user = create_user_with_optional_profile(db, user_data)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User registration failed")

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    tokens = create_tokens(user.email)
    return tokens

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(verify_refresh_token)):
    tokens = create_tokens(current_user.email)
    return tokens

@router.get("/me", response_model=UserStatus)
async def get_user_status(current_user: User = Depends(get_current_user)):
    return UserStatus(user=current_user, is_authenticated=True)

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    return {"message": "Successfully logged out. Please remove tokens from client storage."}

@router.get("/status")
async def auth_status():
    return {"status": "AuthKeyHub authentication system is running", "version": "1.0.0"}