#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API маршрутизации
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
AUTH_URL = f"{BASE_URL}/api/jacobs/auth"
ROUTING_URL = f"{BASE_URL}/api/jacobs/routing"

def test_routing_api():
    """Тестирует API маршрутизации"""
    
    # 1. Проверяем статус системы
    print("1. Проверяем статус системы маршрутизации...")
    try:
        response = requests.get(f"{ROUTING_URL}/status")
        if response.status_code == 200:
            status_data = response.json()
            print(f"   Статус: {status_data['status']}")
            print(f"   Модель доступна: {status_data['model_available']}")
            print(f"   Устройство: {status_data['device']}")
        else:
            print(f"   Ошибка: {response.status_code}")
            return
    except Exception as e:
        print(f"   Ошибка подключения: {e}")
        return
    
    # 2. Получаем токен авторизации (нужно заменить на реальные данные)
    print("\n2. Авторизация...")
    auth_data = {
        "email": "test@example.com",  # Замените на реальный email
        "password": "testpassword"    # Замените на реальный пароль
    }
    
    try:
        response = requests.post(f"{AUTH_URL}/login", json=auth_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print("   Авторизация успешна")
        else:
            print(f"   Ошибка авторизации: {response.status_code}")
            print("   Убедитесь, что пользователь существует в системе")
            return
    except Exception as e:
        print(f"   Ошибка авторизации: {e}")
        return
    
    # 3. Тестируем оптимизацию маршрута
    print("\n3. Тестируем оптимизацию маршрута...")
    headers = {"Authorization": f"Bearer {access_token}"}
    
    try:
        response = requests.post(f"{ROUTING_URL}/optimize", headers=headers)
        if response.status_code == 200:
            route_data = response.json()
            print("   ✅ Маршрут успешно оптимизирован!")
            print(f"   Общая дистанция: {route_data['total_distance']} км")
            print(f"   Общее время: {route_data['total_time_hours']}ч {route_data['total_time_minutes']}м")
            print(f"   Количество точек: {len(route_data['tour'])}")
            
            print("\n   Детали маршрута:")
            for i, point in enumerate(route_data['route_points']):
                lunch_str = " (Обед!)" if point['is_lunch_break'] else ""
                print(f"   {i+1}. Точка {point['object_number']}: {point['arrival_time']}{lunch_str}")
                print(f"      Адрес: {point['address']}")
                print(f"      Рейтинг: {point['client_rating']}, Уровень: {point['client_level']}")
        else:
            print(f"   Ошибка оптимизации: {response.status_code}")
            print(f"   Ответ: {response.text}")
    except Exception as e:
        print(f"   Ошибка оптимизации: {e}")

def test_without_auth():
    """Тестирует endpoints, не требующие авторизации"""
    print("Тестирование endpoints без авторизации...")
    
    # Проверяем статус
    try:
        response = requests.get(f"{ROUTING_URL}/status")
        print(f"Статус системы: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Модель доступна: {data['model_available']}")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    print("=== Тестирование API маршрутизации ===\n")
    
    # Сначала тестируем без авторизации
    test_without_auth()
    
    print("\n" + "="*50)
    
    # Затем полный тест с авторизацией
    test_routing_api()
    
    print("\n=== Тестирование завершено ===")
