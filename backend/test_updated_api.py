#!/usr/bin/env python3
"""
Обновленный тестовый скрипт для проверки работы API с датасетом
Теперь клиенты используют 4-значные номера вместо имен
"""

import requests
import json
import os

# Базовый URL API
BASE_URL = "http://localhost:8000/api/jacobs"

def test_api():
    """Тестирует основные функции API"""
    
    # 1. Регистрация пользователя
    print("1. Регистрация пользователя...")
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Тест",
        "last_name": "Пользователь"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            print("✓ Пользователь успешно зарегистрирован")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✓ Пользователь уже существует")
        else:
            print(f"✗ Ошибка регистрации: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        return
    
    # 2. Вход в систему
    print("\n2. Вход в систему...")
    login_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            tokens = response.json()
            access_token = tokens["access_token"]
            print("✓ Успешный вход в систему")
        else:
            print(f"✗ Ошибка входа: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
        return
    
    # 3. Проверка статуса пользователя
    print("\n3. Проверка статуса пользователя...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✓ Пользователь: {user_data['user']['email']}")
        else:
            print(f"✗ Ошибка получения статуса: {response.status_code}")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    # 4. Загрузка тестового CSV файла
    print("\n4. Загрузка тестового CSV файла...")
    
    # Создаем тестовый CSV файл
    test_csv_content = """Номер объекта,Адрес объекта,Географическая широта,Географическая долгота,Динамический критерий,Время начала рабочего дня,Время окончания рабочего дня,Время начала обеда,Время окончания обеда,Уровень клиента
1,"344011, г. Ростов-на-Дону, ул. Большая Садовая, д. 1",47.221532,39.704423,3,09:00,18:00,13:00,14:00,VIP
2,"344002, г. Ростов-на-Дону, пр. Буденновский, д. 15",47.228945,39.718762,1,09:00,18:00,13:00,14:00,Standart"""
    
    # Сохраняем во временный файл
    with open("test_dataset.csv", "w", encoding="utf-8") as f:
        f.write(test_csv_content)
    
    try:
        with open("test_dataset.csv", "rb") as f:
            files = {"file": ("test_dataset.csv", f, "text/csv")}
            response = requests.post(f"{BASE_URL}/dataset/upload", headers=headers, files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✓ Файл загружен: {upload_result['message']}")
            print(f"  Новых записей: {upload_result['new_records']}")
            print(f"  Обновлено записей: {upload_result['updated_records']}")
        else:
            print(f"✗ Ошибка загрузки: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ Ошибка загрузки файла: {e}")
    finally:
        # Удаляем временный файл
        if os.path.exists("test_dataset.csv"):
            os.remove("test_dataset.csv")
    
    # 5. Получение датасетов пользователя
    print("\n5. Получение датасетов пользователя...")
    try:
        response = requests.get(f"{BASE_URL}/dataset/datasets", headers=headers)
        if response.status_code == 200:
            datasets = response.json()
            print(f"✓ Найдено датасетов: {len(datasets)}")
            for dataset in datasets:
                print(f"  - Объект {dataset['object_number']}: {dataset['address'][:50]}...")
        else:
            print(f"✗ Ошибка получения датасетов: {response.status_code}")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    # 6. Получение клиентов пользователя
    print("\n6. Получение клиентов пользователя...")
    try:
        response = requests.get(f"{BASE_URL}/dataset/clients", headers=headers)
        if response.status_code == 200:
            clients = response.json()
            print(f"✓ Найдено клиентов: {len(clients)}")
            for client in clients:
                print(f"  - Клиент #{client['client_number']} (объект {client['object_number']}, рейтинг {client['rating']})")
        else:
            print(f"✗ Ошибка получения клиентов: {response.status_code}")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    # 7. Тест обновления клиента (если есть клиенты)
    print("\n7. Тест обновления клиента...")
    try:
        response = requests.get(f"{BASE_URL}/dataset/clients", headers=headers)
        if response.status_code == 200:
            clients = response.json()
            if clients:
                client_number = clients[0]['client_number']
                print(f"  Обновляем клиента #{client_number}...")
                
                update_data = {"rating": 4.5}
                update_response = requests.put(
                    f"{BASE_URL}/dataset/clients/{client_number}", 
                    headers=headers, 
                    json=update_data
                )
                
                if update_response.status_code == 200:
                    updated_client = update_response.json()
                    print(f"✓ Клиент #{client_number} обновлен. Новый рейтинг: {updated_client['rating']}")
                else:
                    print(f"✗ Ошибка обновления клиента: {update_response.status_code}")
            else:
                print("  Нет клиентов для обновления")
    except Exception as e:
        print(f"✗ Ошибка подключения: {e}")
    
    print("\n✓ Тестирование завершено!")
    print("\n📋 Основные изменения:")
    print("  - Клиенты теперь имеют 4-значные номера вместо имен")
    print("  - Убраны поля first_name, last_name, middle_name")
    print("  - Все маршруты используют client_number вместо client_id")


if __name__ == "__main__":
    print("Тестирование обновленного API для работы с датасетом")
    print("=" * 60)
    test_api()
