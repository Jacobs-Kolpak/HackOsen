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
