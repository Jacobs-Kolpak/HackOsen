import os
import sys  # Moved to top for global access
import torch
import numpy as np
import pandas as pd
import tempfile
import io
from pathlib import Path  # Moved to top
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db, User, Client, Dataset
from app.schemas import RouteResponse, RoutePoint, RouteStats
from app.auth import get_current_user
from app.model.model_yandex import ImprovedGNNQNetwork, State, haversine, DEVICE

router = APIRouter(tags=["Route Optimization"])

# Константы из модели
MODEL_PATH = "/Users/maksim/HackOsen/backend/app/model/improved_gnn_dynamic.pth"
TIME_PER_POINT = 30.0  # минуты на посещение точки
START_TIME_MINUTES = 9*60  # 09:00
LUNCH_START = 13*60  # 13:00
LUNCH_END = 14*60    # 14:00
DEFAULT_START_TIME = "09:00"
DEFAULT_END_TIME = "18:00"


def time_to_minutes(time_str: str) -> float:
    """Преобразует строку времени 'HH:MM' в минуты с 00:00."""
    if not time_str:
        return 0
    try:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    except:
        return 0


def minutes_to_hours_minutes(minutes: float) -> Tuple[int, int]:
    """Преобразует минуты в часы и минуты."""
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    return h, m


def check_lunch(time_min: float) -> bool:
    """Проверяет, попадает ли время в обеденный перерыв."""
    return LUNCH_START <= time_min < LUNCH_END


def compute_haversine_matrix(coords: np.ndarray, speed_kmh: float = 30.0) -> Tuple[np.ndarray, np.ndarray]:
    """Вычисляет матрицы расстояний и времени между точками."""
    n = len(coords)
    dist = np.zeros((n, n))
    time = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = haversine(coords[i, 0], coords[i, 1], coords[j, 0], coords[j, 1])
            dist[i, j] = d  # км
            time[i, j] = (d / speed_kmh) * 60.0  # минуты
    
    return dist, time


def load_model() -> ImprovedGNNQNetwork:
    """Загружает предобученную модель GNN."""
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Модель не найдена по пути: {MODEL_PATH}"
        )
    
    model = ImprovedGNNQNetwork().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()
    return model


def get_user_data(db: Session, user_id: int) -> Tuple[List[Dataset], List[Client]]:
    """Получает все данные пользователя из базы данных."""
    datasets = db.query(Dataset).filter(Dataset.user_id == user_id).all()
    clients = db.query(Client).filter(Client.user_id == user_id).all()
    return datasets, clients


def prepare_model_input(datasets: List[Dataset], clients: List[Client]) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[dict]]:
    """Подготавливает данные для модели на основе данных из БД."""
    # Создаем словарь клиентов по object_number
    clients_dict = {client.object_number: client for client in clients}
    
    # Подготавливаем данные для модели
    coords_list = []
    start_windows = []
    end_windows = []
    priorities = []
    levels = []
    dataset_info = []
    
    for dataset in datasets:
        coords_list.append([dataset.latitude, dataset.longitude])
        
        # Получаем клиента для этого объекта
        client = clients_dict.get(dataset.object_number)
        
        # Временные окна
        if client and client.start:
            start_windows.append(time_to_minutes(client.start))
        else:
            start_windows.append(time_to_minutes(dataset.work_start_time))
            
        if client and client.end:
            end_windows.append(time_to_minutes(client.end))
        else:
            end_windows.append(time_to_minutes(dataset.work_end_time))
        
        # Приоритеты и уровни
        priorities.append(dataset.dynamic_criterion)
        levels.append(1.0 if dataset.client_level.upper() == "VIP" else 0.0)
        
        # Информация о клиенте
        client_rating = client.rating if client else 0.5
        dataset_info.append({
            'object_number': dataset.object_number,
            'address': dataset.address,
            'client_rating': client_rating,
            'client_level': dataset.client_level,
            'dynamic_criterion': dataset.dynamic_criterion
        })
    
    coords_np = np.array(coords_list)
    start_window = np.array(start_windows)
    end_window = np.array(end_windows)
    priorities_np = np.array(priorities)
    levels_np = np.array(levels)
    
    return coords_np, start_window, end_window, priorities_np, levels_np, dataset_info


def run_route_optimization(
    coords: np.ndarray,
    start_window: np.ndarray,
    end_window: np.ndarray,
    priorities: np.ndarray,
    levels: np.ndarray,
    dataset_info: List[dict]
) -> Tuple[List[int], float, float, List[float], List[bool]]:
    """Запускает оптимизацию маршрута с помощью GNN модели."""
    
    # Загружаем модель
    model = load_model()
    
    # Вычисляем матрицы расстояний и времени
    dist_matrix, time_matrix = compute_haversine_matrix(coords)
    
    # Преобразуем в тензоры
    dist_t = torch.tensor(dist_matrix, dtype=torch.float32, device=DEVICE)
    time_t = torch.tensor(time_matrix, dtype=torch.float32, device=DEVICE)
    coords_t = torch.tensor(coords, dtype=torch.float32, device=DEVICE)
    priorities_t = torch.tensor(priorities, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels, dtype=torch.float32, device=DEVICE)
    
    # Инициализация
    visited = torch.zeros(len(coords), dtype=torch.bool, device=DEVICE)
    cur_node = 0
    visited[cur_node] = True
    cur_time = START_TIME_MINUTES
    
    tour = [cur_node]
    total_distance = 0.0
    total_time = 0.0
    arrival_times = [cur_time]
    lunch_flags = [False]
    
    # Основной цикл оптимизации
    while not visited.all():
        state = State(
            dist_t, time_t, coords_t, priorities_t, levels_t, 
            visited, torch.tensor(cur_time, device=DEVICE)
        )
        
        with torch.no_grad():
            qvals = model(state)
        
        # Ищем доступных кандидатов
        candidates = []
        for i in range(len(coords)):
            if visited[i]:
                continue
                
            # Проекция времени прибытия
            travel_time = time_matrix[cur_node, i]
            proj_arrival = cur_time + travel_time
            
            # Учёт обеда
            if cur_time < LUNCH_START < proj_arrival:
                proj_arrival = max(proj_arrival, LUNCH_END)
            elif LUNCH_START <= proj_arrival < LUNCH_END:
                proj_arrival = LUNCH_END
                
            # Ожидание начала окна
            if proj_arrival < start_window[i]:
                proj_arrival = start_window[i]
                
            # Проверка на опоздание
            if proj_arrival > end_window[i]:
                continue
                
            candidates.append(i)
        
        if not candidates:
            break
        
        # Выбор лучшего кандидата по Q-values
        qvals_candidates = [qvals[0][j].item() for j in candidates]
        next_idx = np.argmax(qvals_candidates)
        next_node = candidates[next_idx]
        
        # Рассчитываем реальное время прибытия
        travel_time = time_matrix[cur_node, next_node]
        arrival_time = cur_time + travel_time
        
        # Учёт обеда
        had_lunch = False
        if cur_time < LUNCH_START < arrival_time:
            cur_time = LUNCH_END
            arrival_time = max(arrival_time, cur_time)
            had_lunch = True
        elif LUNCH_START <= arrival_time < LUNCH_END:
            arrival_time = LUNCH_END
            had_lunch = True
        
        # Учёт временного окна
        window_start = start_window[next_node]
        if arrival_time < window_start:
            arrival_time = window_start
        
        # Обновляем метрики
        total_distance += dist_matrix[cur_node, next_node]
        visit_start = arrival_time
        visit_end = visit_start + TIME_PER_POINT
        total_time += travel_time + TIME_PER_POINT
        cur_time = visit_end
        
        # Обновляем состояние
        visited[next_node] = True
        cur_node = next_node
        tour.append(next_node)
        arrival_times.append(visit_start)
        lunch_flags.append(had_lunch)
    
    return tour, total_distance, total_time, arrival_times, lunch_flags


@router.get("/status")
async def get_routing_status():
    """Проверяет статус системы маршрутизации."""
    model_exists = os.path.exists(MODEL_PATH)
    return {
        "model_available": model_exists,
        "model_path": MODEL_PATH,
        "device": str(DEVICE),
        "status": "ready" if model_exists else "model_not_found"
    }


@router.post("/optimize", response_model=RouteResponse)
async def optimize_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Оптимизирует маршрут для всех объектов пользователя с помощью GNN модели.
    Возвращает ранжированный список точек с временем посещения.
    """
    try:
        # Получаем данные пользователя
        datasets, clients = get_user_data(db, current_user.id)
        
        if not datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У пользователя нет загруженных датасетов"
            )
        
        # Подготавливаем данные для модели
        coords, start_window, end_window, priorities, levels, dataset_info = prepare_model_input(datasets, clients)
        
        # Запускаем оптимизацию
        tour, total_distance, total_time, arrival_times, lunch_flags = run_route_optimization(
            coords, start_window, end_window, priorities, levels, dataset_info
        )
        
        # Преобразуем время прибытия в читаемый формат
        arrival_times_hm = [minutes_to_hours_minutes(t) for t in arrival_times]
        total_hours, total_minutes = minutes_to_hours_minutes(total_time)
        
        # Создаем детальную информацию о точках маршрута
        route_points = []
        for i, (node_idx, (h, m), lunch) in enumerate(zip(tour, arrival_times_hm, lunch_flags)):
            if node_idx < len(dataset_info):
                info = dataset_info[node_idx]
                route_points.append(RoutePoint(
                    object_number=info['object_number'],
                    address=info['address'],
                    latitude=coords[node_idx][0],
                    longitude=coords[node_idx][1],
                    arrival_time=f"{h:02d}:{m:02d}",
                    visit_duration=int(TIME_PER_POINT),
                    is_lunch_break=lunch,
                    client_rating=info['client_rating'],
                    client_level=info['client_level'],
                    dynamic_criterion=info['dynamic_criterion']
                ))
        
        return RouteResponse(
            tour=tour,
            total_distance=round(total_distance, 2),
            total_time=round(total_time, 2),
            total_time_hours=total_hours,
            total_time_minutes=total_minutes,
            route_points=route_points,
            lunch_breaks=lunch_flags,
            success=True,
            message=f"Маршрут успешно оптимизирован. Посещено {len(tour)} точек из {len(datasets)}."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при оптимизации маршрута: {str(e)}"
        )


@router.get("/stats", response_model=RouteStats)
async def get_route_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получает статистику по маршруту пользователя без выполнения оптимизации.
    """
    try:
        # Получаем данные пользователя
        datasets, clients = get_user_data(db, current_user.id)
        
        if not datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="У пользователя нет загруженных датасетов"
            )
        
        # Подсчитываем статистику
        total_points = len(datasets)
        vip_clients = sum(1 for dataset in datasets if dataset.client_level.upper() == "VIP")
        standard_clients = total_points - vip_clients
        
        # Средний рейтинг клиентов
        client_ratings = []
        for dataset in datasets:
            client = next((c for c in clients if c.object_number == dataset.object_number), None)
            rating = client.rating if client else 50.0
            client_ratings.append(rating)
        
        average_rating = sum(client_ratings) / len(client_ratings) if client_ratings else 0.5
        
        # Оценка эффективности (базовая)
        efficiency_score = min(100.0, (average_rating / 50.0) * 100.0)
        
        return RouteStats(
            total_points=total_points,
            visited_points=0,  # Будет заполнено после оптимизации
            skipped_points=0,  # Будет заполнено после оптимизации
            vip_clients=vip_clients,
            standard_clients=standard_clients,
            average_rating=round(average_rating, 2),
            total_distance=0.0,  # Будет заполнено после оптимизации
            total_time=0.0,  # Будет заполнено после оптимизации
            lunch_breaks_count=0,  # Будет заполнено после оптимизации
            efficiency_score=round(efficiency_score, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении статистики: {str(e)}"
        )


# === ВСТАВЬ ВМЕСТО СТАРОГО /optimize/map ===
@router.post("/optimize/map", response_class=HTMLResponse)
async def optimize_route_map(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Оптимизирует маршрут и возвращает HTML-карту.
    Использует pipi_map.py из app/model/
    """
    try:
        print("=== OPTIMIZE MAP ROUTE STARTED ===")
        print(f"User ID: {current_user.id}")

        # --- Динамический импорт pipi_map.py из app/model/ ---
        model_dir = Path(__file__).parent / "model"
        if str(model_dir) not in sys.path:
            sys.path.insert(0, str(model_dir))
            print(f"Добавлен путь: {model_dir}")

        try:
            from pipi_map import (
                build_graph_bbox,
                nearest_nodes_for_points,
                compute_pairwise_shortest_paths,
                greedy_feasible_tour,
                reconstruct_full_route_indices,
                plot_route_folium
            )
            print("pipi_map успешно импортирован из app/model/")
        except Exception as e:
            print(f"ОШИБКА импорта pipi_map: {e}")
            raise HTTPException(status_code=500, detail=f"Не найден pipi_map.py: {e}")

        # --- Данные из БД ---
        datasets, clients = get_user_data(db, current_user.id)
        if not datasets:
            raise HTTPException(status_code=404, detail="Нет загруженных точек")

        coords, start_window, end_window, _, _, dataset_info = prepare_model_input(datasets, clients)

        # --- DataFrame для pipi_map ---
        df = pd.DataFrame({
            'Адрес объекта': [info['address'] for info in dataset_info],
            'Географическая широта': coords[:, 0],
            'Географическая долгота': coords[:, 1],
            'Время начала рабочего дня': [
                f"{int(sw // 60):02d}:{int(sw % 60):02d}" for sw in start_window
            ],
            'Время окончания рабочего дня': [
                f"{int(ew // 60):02d}:{int(ew % 60):02d}" for ew in end_window
            ],
        })

        print(f"Точек: {len(coords)}, DF shape: {df.shape}")

        # --- Маршрут через pipi_map ---
        print("Строим граф...")
        G = build_graph_bbox()

        print("Ищем ближайшие узлы...")
        nodes = nearest_nodes_for_points(G, coords)

        print("Считаем кратчайшие пути...")
        pair_dist_min, pair_path = compute_pairwise_shortest_paths(G, nodes)

        print("Формируем тур...")
        tour = greedy_feasible_tour(pair_dist_min, start_window, end_window)
        if len(tour) < 2:
            print("Тур короткий → используем все точки")
            tour = list(range(len(coords)))

        print("Восстанавливаем маршрут...")
        full_nodes = reconstruct_full_route_indices(tour, pair_path)

        # --- Генерация HTML-карты (возвращаем строку) ---
        print("Генерируем HTML-карту...")
        # Временно сохраняем, чтобы использовать plot_route_folium
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as tmp:
            tmp_path = tmp.name

        plot_route_folium(G, full_nodes, coords, tour, df, output_html=tmp_path)

        with open(tmp_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        os.unlink(tmp_path)  # Удаляем временный файл

        print(f"Карта сгенерирована: {len(html_content)} символов")
        print("=== УСПЕХ ===")
        return HTMLResponse(content=html_content)

    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Ошибка генерации карты: {str(e)}")