from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
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
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Связи с клиентами и датасетами
    clients = relationship("Client", back_populates="user", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="user", cascade="all, delete-orphan")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_number = Column(String(4), nullable=False, unique=True, index=True)  # 4-значный уникальный номер
    rating = Column(Float, default=50.0)  # Рейтинг клиента
    object_number = Column(Integer, nullable=False)  # Номер объекта из датасета
    
    # Связь с пользователем
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="clients")
    
    # Связь с датасетом
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    dataset = relationship("Dataset", back_populates="clients")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    object_number = Column(Integer, nullable=False, index=True)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    dynamic_criterion = Column(Integer, nullable=False)
    work_start_time = Column(String, nullable=False)  # Время начала рабочего дня
    work_end_time = Column(String, nullable=False)    # Время окончания рабочего дня
    lunch_start_time = Column(String, nullable=False) # Время начала обеда
    lunch_end_time = Column(String, nullable=False)   # Время окончания обеда
    client_level = Column(String, nullable=False)     # Уровень клиента (VIP, Standart)
    
    # Связь с пользователем
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="datasets")
    
    # Связь с клиентами
    clients = relationship("Client", back_populates="dataset")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()