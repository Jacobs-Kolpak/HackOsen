# 📋 Запросы для Postman - Обновленная версия

## 🔐 Аутентификация

### 1. Регистрация пользователя
```
POST http://localhost:8000/api/jacobs/auth/register
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "testpassword123",
    "first_name": "Тест",
    "last_name": "Пользователь"
}
```

### 2. Вход в систему
```
POST http://localhost:8000/api/jacobs/auth/login
Content-Type: application/json

{
    "email": "test@example.com",
    "password": "testpassword123"
}
```

### 3. Получение информации о пользователе
```
GET http://localhost:8000/api/jacobs/auth/me
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 4. Обновление токена
```
POST http://localhost:8000/api/jacobs/auth/refresh
Authorization: Bearer YOUR_REFRESH_TOKEN
```

### 5. Выход из системы
```
POST http://localhost:8000/api/jacobs/auth/logout
```

---

## 📊 Управление датасетом

### 6. Загрузка CSV файла
```
POST http://localhost:8000/api/jacobs/dataset/upload
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

Body (form-data):
- Key: file
- Type: File
- Value: [выбери CSV файл]
```

### 7. Получение всех датасетов пользователя
```
GET http://localhost:8000/api/jacobs/dataset/datasets
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 8. Получение конкретного датасета
```
GET http://localhost:8000/api/jacobs/dataset/datasets/1
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 9. Получение всех клиентов пользователя
```
GET http://localhost:8000/api/jacobs/dataset/clients
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 10. Получение конкретного клиента (по 4-значному номеру)
```
GET http://localhost:8000/api/jacobs/dataset/clients/1234
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 11. Обновление данных клиента (по 4-значному номеру)
```
PUT http://localhost:8000/api/jacobs/dataset/clients/1234
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "rating": 4.5,
    "object_number": 1
}
```

### 12. Удаление датасета
```
DELETE http://localhost:8000/api/jacobs/dataset/datasets/1
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 13. Удаление клиента (по 4-значному номеру)
```
DELETE http://localhost:8000/api/jacobs/dataset/clients/1234
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### 14. Обновление встречи с клиентом (по 4-значному номеру)
```
POST http://localhost:8000/api/jacobs/dataset/clients/1234/meeting
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "meeting_successful": true
}
```

**Примеры запросов для встреч:**

**Успешная встреча (рейтинг +1):**
```json
{
    "meeting_successful": true
}
```

**Неуспешная встреча (рейтинг -1):**
```json
{
    "meeting_successful": false
}
```

---

## 📝 Примеры ответов:

### Успешная загрузка файла:
```json
{
    "message": "Файл успешно обработан. Новых записей: 3, обновлено: 0",
    "total_records": 3,
    "new_records": 3,
    "updated_records": 0,
    "errors": []
}
```

### Список клиентов (обновленный формат):
```json
[
    {
        "id": 1,
        "client_number": "1234",
        "rating": 50.0,
        "object_number": 1,
        "user_id": 1,
        "dataset_id": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    {
        "id": 2,
        "client_number": "5678",
        "rating": 50.0,
        "object_number": 2,
        "user_id": 1,
        "dataset_id": 2,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
]
```

### Получение конкретного клиента:
```json
{
    "id": 1,
    "client_number": "1234",
    "rating": 52.0,
    "object_number": 1,
    "user_id": 1,
    "dataset_id": 1,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
}
```

### Ответ на обновление встречи (успешная встреча):
```json
{
    "message": "Встреча с клиентом #1234 состоялась успешно. Рейтинг увеличен.",
    "client_number": "1234",
    "old_rating": 50.0,
    "new_rating": 51.0,
    "meeting_successful": true
}
```

### Ответ на обновление встречи (неуспешная встреча):
```json
{
    "message": "Встреча с клиентом #1234 не состоялась. Рейтинг уменьшен.",
    "client_number": "1234",
    "old_rating": 51.0,
    "new_rating": 50.0,
    "meeting_successful": false
}
```
