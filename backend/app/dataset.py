import uuid
import io
import random
import pandas as pd
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db, User, Client, Dataset
from app.schemas import (
    ClientCreate, ClientResponse, ClientUpdate, ClientTimeUpdate,
    DatasetCreate, DatasetResponse, DatasetUpdate,
    DatasetUploadResponse, ClientWithDataset,
    MeetingUpdate, MeetingUpdateResponse
)
from app.auth import get_current_user

router = APIRouter(tags=["Dataset Management"])


def generate_client_number(db: Session) -> str:
    """Генерирует уникальный 4-значный номер клиента"""
    while True:
        # Генерируем случайный 4-значный номер
        client_number = f"{random.randint(1000, 9999)}"
        
        # Проверяем, что номер уникален
        existing_client = db.query(Client).filter(Client.client_number == client_number).first()
        if not existing_client:
            return client_number


def parse_csv_data(file_content: bytes) -> List[dict]:
    """Парсит CSV файл и возвращает список словарей с данными"""
    try:
        # Пробуем разные кодировки
        encodings = ['utf-8', 'cp1251', 'latin-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    io.StringIO(file_content.decode(encoding)),
                    sep=',',
                    encoding=encoding
                )
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            raise ValueError("Не удалось декодировать файл")
        
        # Преобразуем DataFrame в список словарей
        data = df.to_dict('records')
        
        # Проверяем наличие обязательных колонок
        required_columns = [
            'Номер объекта', 'Адрес объекта', 'Географическая широта',
            'Географическая долгота', 'Динамический критерий',
            'Время начала рабочего дня', 'Время окончания рабочего дня',
            'Время начала обеда', 'Время окончания обеда', 'Уровень клиента'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")
        
        return data
        
    except Exception as e:
        raise ValueError(f"Ошибка при парсинге CSV файла: {str(e)}")


def create_client_from_dataset(
    db: Session, 
    user_id: int, 
    dataset_record: dict, 
    dataset_id: int
) -> Client:
    """Создает клиента на основе записи датасета"""
    client_number = generate_client_number(db)
    
    client = Client(
        client_number=client_number,
        rating=50.0,
        object_number=dataset_record['Номер объекта'],
        user_id=user_id,
        dataset_id=dataset_id
    )
    
    db.add(client)
    return client


def update_existing_dataset(
    db: Session, 
    existing_dataset: Dataset, 
    new_data: dict
) -> Dataset:
    """Обновляет существующий датасет новыми данными"""
    existing_dataset.address = new_data['Адрес объекта']
    existing_dataset.latitude = float(new_data['Географическая широта'])
    existing_dataset.longitude = float(new_data['Географическая долгота'])
    existing_dataset.dynamic_criterion = int(new_data['Динамический критерий'])
    existing_dataset.work_start_time = new_data['Время начала рабочего дня']
    existing_dataset.work_end_time = new_data['Время окончания рабочего дня']
    existing_dataset.lunch_start_time = new_data['Время начала обеда']
    existing_dataset.lunch_end_time = new_data['Время окончания обеда']
    existing_dataset.client_level = new_data['Уровень клиента']
    
    return existing_dataset


# API Routes
@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Загружает датасет из CSV файла.
    Если записи с такими номерами объектов уже существуют у пользователя,
    они будут обновлены, сохраняя рейтинги клиентов.
    """
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только CSV и Excel файлы"
        )
    
    try:
        file_content = await file.read()
        
        if file.filename.endswith('.csv'):
            data = parse_csv_data(file_content)
        else:
            # Для Excel файлов
            df = pd.read_excel(io.BytesIO(file_content))
            data = df.to_dict('records')
        
        new_records = 0
        updated_records = 0
        errors = []
        
        for record in data:
            try:
                object_number = record['Номер объекта']
                
                # Проверяем, существует ли уже запись с таким номером объекта у пользователя
                existing_dataset = db.query(Dataset).filter(
                    Dataset.user_id == current_user.id,
                    Dataset.object_number == object_number
                ).first()
                
                if existing_dataset:
                    # Обновляем существующую запись
                    update_existing_dataset(db, existing_dataset, record)
                    updated_records += 1
                else:
                    # Создаем новую запись
                    dataset = Dataset(
                        object_number=object_number,
                        address=record['Адрес объекта'],
                        latitude=float(record['Географическая широта']),
                        longitude=float(record['Географическая долгота']),
                        dynamic_criterion=int(record['Динамический критерий']),
                        work_start_time=record['Время начала рабочего дня'],
                        work_end_time=record['Время окончания рабочего дня'],
                        lunch_start_time=record['Время начала обеда'],
                        lunch_end_time=record['Время окончания обеда'],
                        client_level=record['Уровень клиента'],
                        user_id=current_user.id
                    )
                    
                    db.add(dataset)
                    db.flush()  # Получаем ID
                    
                    # Создаем клиента для этого датасета
                    create_client_from_dataset(db, current_user.id, record, dataset.id)
                    new_records += 1
                    
            except Exception as e:
                errors.append(f"Ошибка при обработке записи {record.get('Номер объекта', 'неизвестно')}: {str(e)}")
        
        db.commit()
        
        return DatasetUploadResponse(
            message=f"Файл успешно обработан. Новых записей: {new_records}, обновлено: {updated_records}",
            total_records=len(data),
            new_records=new_records,
            updated_records=updated_records,
            errors=errors
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )


@router.get("/datasets", response_model=List[DatasetResponse])
async def get_user_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает все датасеты текущего пользователя"""
    datasets = db.query(Dataset).filter(Dataset.user_id == current_user.id).all()
    return datasets


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает конкретный датасет пользователя"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Датасет не найден"
        )
    
    return dataset


@router.get("/clients", response_model=List[ClientResponse])
async def get_user_clients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает всех клиентов текущего пользователя"""
    clients = db.query(Client).filter(Client.user_id == current_user.id).all()
    return clients


@router.get("/clients/{client_number}", response_model=ClientResponse)
async def get_client(
    client_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получает конкретного клиента пользователя с VIP статусом"""
    client = db.query(Client).filter(
        Client.client_number == client_number,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    # Определяем VIP статус из связанного датасета
    is_vip = None
    address = None
    if client.dataset_id:
        dataset = db.query(Dataset).filter(Dataset.id == client.dataset_id).first()
        if dataset:
            is_vip = dataset.client_level.upper() == "VIP"
            address = dataset.address
    
    # Создаем словарь с данными клиента и добавляем VIP статус и адрес
    client_data = {
        "id": client.id,
        "client_number": client.client_number,
        "rating": client.rating,
        "object_number": client.object_number,
        "user_id": client.user_id,
        "dataset_id": client.dataset_id,
        "start": client.start,
        "end": client.end,
        "is_vip": is_vip,
        "address": address,
        "created_at": client.created_at,
        "updated_at": client.updated_at
    }
    
    return ClientResponse(**client_data)


@router.put("/clients/{client_number}", response_model=ClientResponse)
async def update_client(
    client_number: str,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновляет данные клиента"""
    client = db.query(Client).filter(
        Client.client_number == client_number,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    # Обновляем только переданные поля
    update_data = client_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return client


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаляет датасет и связанных клиентов"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Датасет не найден"
        )
    
    # Удаляем связанных клиентов
    db.query(Client).filter(Client.dataset_id == dataset_id).delete()
    
    # Удаляем датасет
    db.delete(dataset)
    db.commit()
    
    return {"message": "Датасет и связанные клиенты успешно удалены"}


@router.delete("/clients/{client_number}")
async def delete_client(
    client_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаляет клиента"""
    client = db.query(Client).filter(
        Client.client_number == client_number,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    db.delete(client)
    db.commit()
    
    return {"message": "Клиент успешно удален"}


@router.post("/clients/{client_number}/meeting", response_model=MeetingUpdateResponse)
async def update_meeting(
    client_number: str,
    meeting_data: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновляет рейтинг клиента на основе результата встречи.
    Если встреча состоялась (meeting_successful=True) - рейтинг +1
    Если встреча не состоялась (meeting_successful=False) - рейтинг -1
    """
    # Находим клиента
    client = db.query(Client).filter(
        Client.client_number == client_number,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    # Сохраняем старый рейтинг
    old_rating = client.rating
    
    # Обновляем рейтинг в зависимости от результата встречи
    if meeting_data.meeting_successful:
        client.rating += 1.0
        message = f"Встреча с клиентом #{client_number} состоялась успешно. Рейтинг увеличен."
    else:
        client.rating -= 1.0
        message = f"Встреча с клиентом #{client_number} не состоялась. Рейтинг уменьшен."
    
    # Убеждаемся, что рейтинг не уходит в отрицательные значения
    if client.rating < 0:
        client.rating = 0.0
    
    db.commit()
    db.refresh(client)
    
    return MeetingUpdateResponse(
        message=message,
        client_number=client_number,
        old_rating=old_rating,
        new_rating=client.rating,
        meeting_successful=meeting_data.meeting_successful
    )


@router.put("/clients/{client_number}/time", response_model=ClientResponse)
async def update_client_time(
    client_number: str,
    time_data: ClientTimeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Обновляет временные промежутки для клиента.
    Поля start и end должны быть в том же формате, что и времена в датасете (например, "09:00").
    """
    # Находим клиента
    client = db.query(Client).filter(
        Client.client_number == client_number,
        Client.user_id == current_user.id
    ).first()
    
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Клиент не найден"
        )
    
    # Обновляем временные поля
    update_data = time_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    
    return client
