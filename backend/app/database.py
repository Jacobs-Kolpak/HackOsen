from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, UniqueConstraint, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 1:1 профиль
    profile = relationship("UserProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")

class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_profiles_user_id"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Поля профиля
    full_name = Column(String(128), nullable=True)      # Имя пользователя
    age = Column(Integer, nullable=True)                # Возраст
    gender = Column(String(16), nullable=True)          # "male" | "female" | "other"
    current_weight = Column(Float, nullable=True)       # кг
    height = Column(Float, nullable=True)               # см
    goal = Column(Integer, nullable=True)               # 1-5
    activity = Column(Integer, nullable=True)           # 1-4
    special_needs = Column(Integer, nullable=True)      # 1-4
    desired_weight = Column(Float, nullable=True)       # кг
    tastes = Column(Integer, nullable=True)             # 1-4

    user = relationship("User", back_populates="profile")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()