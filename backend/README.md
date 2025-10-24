# AuthKeyHub

Защищенная система аутентификации на FastAPI с JWT токенами и SQLite базой данных.

## Возможности

- Регистрация пользователей с валидацией
- Аутентификация с JWT токенами
- Access токены (кратковременные) и Refresh токены (долгосрочные)
- Защищенные маршруты
- Статус пользователя и проверка авторизации
- Хеширование паролей с bcrypt
- SQLite база данных
- CORS поддержка

## Установка и запуск

### 1. Установка зависимостей

```bash
# Активируйте виртуальное окружение
source venv/bin/activate  # На macOS/Linux
# или
venv\\Scripts\\activate  # На Windows

# Установите зависимости
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Файл `.env` уже создан с базовыми настройками. В продакшене обязательно измените:
- `SECRET_KEY` - используйте криптографически стойкий ключ
- Настройки CORS в `main.py`

### 3. Запуск приложения

```bash
# Запуск через main.py
python main.py

# Или через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

## API Эндпоинты

### Основные маршруты
- `GET /` - Корневая страница
- `GET /health` - Проверка состояния приложения
- `GET /docs` - Swagger документация
- `GET /redoc` - ReDoc документация

### Аутентификация (`/api/v1/auth`)

#### `POST /api/v1/auth/register`
Регистрация нового пользователя.

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "is_active": true,
  "created_at": "2024-01-01T12:00:00",
  "updated_at": null
}
```

#### `POST /api/v1/auth/login`
Вход в систему и получение токенов.

**Тело запроса:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### `POST /api/v1/auth/refresh`
Обновление access токена с помощью refresh токена.

**Заголовок:** `Authorization: Bearer <refresh_token>`

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### `GET /api/v1/auth/me`
Получение информации о текущем пользователе (защищенный маршрут).

**Заголовок:** `Authorization: Bearer <access_token>`

**Ответ:**
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "is_active": true,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": null
  },
  "is_authenticated": true
}
```

#### `POST /api/v1/auth/logout`
Выход из системы (клиент должен удалить токены).

#### `GET /api/v1/auth/status`
Проверка работы системы аутентификации.

## Настройка .env

```
# Database
DATABASE_URL=sqlite:///./auth.db

# JWT Settings
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Settings
APP_NAME=AuthKeyHub
DEBUG=True
```


## Система токенов

### Access Token
- **Срок действия:** 30 минут (настраивается в `.env`)
- **Использование:** Для доступа к защищенным ресурсам
- **Тип:** `"access"` в payload токена

### Refresh Token
- **Срок действия:** 7 дней (настраивается в `.env`)
- **Использование:** Для обновления access токена
- **Тип:** `"refresh"` в payload токена

### Переключение между временной и постоянной аутентификацией
Система поддерживает гибкое управление сессиями:
1. **Кратковременная аутентификация:** Используй только access токен
2. **Долгосрочная аутентификация:** Используй refresh токен для автоматического обновлени****я

## Безопасность

- Пароли хешируются с использованием bcrypt
- JWT токены подписываются секретным ключом
- Поддержка CORS для фронтенд приложений
- Валидация всех входящих данных через Pydantic
- Проверка активности пользователя

## База данных

Используется SQLite с автоматическим созданием таблиц при запуске приложения. База данных создается в файле `auth.db` в корневой папке проекта.

## Разработка

Для разработки рекомендуется:
1. Установить все зависимости из `requirements.txt`
2. Использовать режим reload: `uvicorn main:app --reload`
3. Настроить `DEBUG=True` в `.env`
4. Использовать интерактивную документацию по адресу `/docs`

## Производство

Для продакшена обязательно:
1. Изменить `SECRET_KEY` в `.env`
2. Настроить правильные CORS origins
3. Установить `DEBUG=False`
4. Использовать HTTPS
5. Настроить логирование
6. Рассмотреть использование PostgreSQL вместо SQLite