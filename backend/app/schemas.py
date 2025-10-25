from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None
    token_type: Optional[str] = None  # "access" or "refresh"


class UserStatus(BaseModel):
    user: UserResponse
    is_authenticated: bool = True


# Схемы для клиентов
class ClientBase(BaseModel):
    rating: float = 50.0
    object_number: int


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    rating: Optional[float] = None
    object_number: Optional[int] = None


class ClientTimeUpdate(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    client_number: str  # 4-значный уникальный номер
    user_id: int
    dataset_id: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None
    is_vip: Optional[bool] = None  # VIP статус клиента
    address: Optional[str] = None  # Адрес объекта из датасета
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Схемы для датасета
class DatasetBase(BaseModel):
    object_number: int
    address: str
    latitude: float
    longitude: float
    dynamic_criterion: int
    work_start_time: str
    work_end_time: str
    lunch_start_time: str
    lunch_end_time: str
    client_level: str


class DatasetCreate(DatasetBase):
    pass


class DatasetUpdate(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    dynamic_criterion: Optional[int] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    lunch_start_time: Optional[str] = None
    lunch_end_time: Optional[str] = None
    client_level: Optional[str] = None


class DatasetResponse(DatasetBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    clients: List[ClientResponse] = []

    class Config:
        from_attributes = True


# Схемы для загрузки файлов
class DatasetUploadResponse(BaseModel):
    message: str
    total_records: int
    new_records: int
    updated_records: int
    errors: List[str] = []


class ClientWithDataset(BaseModel):
    client: ClientResponse
    dataset: Optional[DatasetResponse] = None


# Схемы для встреч
class MeetingUpdate(BaseModel):
    meeting_successful: bool  # True если встреча состоялась, False если нет


class MeetingUpdateResponse(BaseModel):
    message: str
    client_number: str
    old_rating: float
    new_rating: float
    meeting_successful: bool


# Схемы для маршрутизации
class RoutePoint(BaseModel):
    object_number: int
    address: str
    latitude: float
    longitude: float
    arrival_time: str  # Время прибытия в формате "HH:MM"
    visit_duration: int  # Длительность посещения в минутах
    is_lunch_break: bool  # Был ли обед перед этой точкой
    client_rating: float
    client_level: str
    dynamic_criterion: int


class RouteResponse(BaseModel):
    tour: List[int]  # Порядок посещения точек
    total_distance: float  # Общая дистанция в км
    total_time: float  # Общее время в минутах
    total_time_hours: int  # Часы
    total_time_minutes: int  # Минуты
    route_points: List[RoutePoint]  # Детальная информация о каждой точке
    lunch_breaks: List[bool]  # Информация об обедах
    success: bool
    message: str


class RouteStats(BaseModel):
    total_points: int
    visited_points: int
    skipped_points: int
    vip_clients: int
    standard_clients: int
    average_rating: float
    total_distance: float
    total_time: float
    lunch_breaks_count: int
    efficiency_score: float  # Оценка эффективности маршрута