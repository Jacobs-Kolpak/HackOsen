# Быстрый старт - API маршрутизации

## 1. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

## 2. Проверка модели

Убедитесь, что модель находится по пути:
```
backend/app/model/improved_gnn_dynamic.pth
```

## 3. Запуск сервера

```bash
python main.py
```

Сервер запустится на `http://localhost:8000`

## 4. Проверка работы

### Проверка статуса системы:
```bash
curl http://localhost:8000/api/jacobs/routing/status
```

### Документация API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 5. Тестирование

```bash
python test_routing.py
```

## 6. Основные endpoints

- `GET /api/jacobs/routing/status` - Статус системы
- `POST /api/jacobs/routing/optimize` - Оптимизация маршрута
- `GET /api/jacobs/routing/stats` - Статистика маршрута

## 7. Авторизация

Для работы с маршрутизацией нужна авторизация:
1. Создайте пользователя через `/api/jacobs/auth/register`
2. Получите токен через `/api/jacobs/auth/login`
3. Используйте токен в заголовке `Authorization: Bearer <token>`

## 8. Загрузка данных

1. Загрузите CSV файл через `/api/jacobs/dataset/upload`
2. Данные автоматически создадут записи в `datasets` и `clients`
3. Запустите оптимизацию через `/api/jacobs/routing/optimize`

## Готово! 🚀

Ваш API маршрутизации готов к использованию!
