#!/usr/bin/env python3
import pandas as pd
import numpy as np
import torch
from model_yandex import ImprovedGNNQNetwork, State, haversine, DEVICE

# ---------------- CONFIG ----------------
MODEL_PATH = "improved_gnn_dynamic.pth"
INPUT_CSV = "test.csv"
N_POINTS = 12
TIME_PER_POINT = 30.0  # минуты на посещение точки
START_TIME_MINUTES = 9*60  # 09:00
LUNCH_START = 13*60  # 13:00
LUNCH_END = 14*60    # 14:00

# ---------------- Helper ----------------
def read_csv(csv_path):
    df = pd.read_csv(csv_path)
    req_cols = ['Географическая широта', 'Географическая долгота']
    for c in req_cols:
        if c not in df.columns:
            raise RuntimeError(f"CSV должен содержать колонку '{c}'")
    coords = np.stack([df['Географическая широта'].values, df['Географическая долгота'].values], axis=1)
    return df, coords

def compute_haversine_matrix(coords, speed_kmh=30.0):
    n = len(coords)
    dist = np.zeros((n, n))
    time = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i==j: continue
            d = haversine(coords[i,0], coords[i,1], coords[j,0], coords[j,1])
            dist[i,j] = d  # км
            time[i,j] = (d / speed_kmh) * 60.0  # минуты
    return dist, time

def minutes_to_hours_minutes(minutes):
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    return h, m

# ---------------- Pipeline ----------------
def run_pipeline(csv_path=INPUT_CSV, model_path=MODEL_PATH, n_points=N_POINTS):
    df, coords_np = read_csv(csv_path)
    coords_np = coords_np[:n_points]
    
    priorities_np = np.ones(len(coords_np))
    levels_np = np.zeros(len(coords_np))
    
    dist_matrix, time_matrix = compute_haversine_matrix(coords_np)
    
    dist_t = torch.tensor(dist_matrix, dtype=torch.float32, device=DEVICE)
    time_t = torch.tensor(time_matrix, dtype=torch.float32, device=DEVICE)
    coords_t = torch.tensor(coords_np, dtype=torch.float32, device=DEVICE)
    priorities_t = torch.tensor(priorities_np, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels_np, dtype=torch.float32, device=DEVICE)
    
    model = ImprovedGNNQNetwork().to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    
    visited = torch.zeros(len(coords_np), dtype=torch.bool, device=DEVICE)
    cur_node = 0
    visited[cur_node] = True
    cur_time = START_TIME_MINUTES
    
    tour = [cur_node]
    total_distance = 0.0  # км
    total_time = 0.0
    arrival_times = [cur_time]
    lunch_flags = [False]  # True, если обед был на маршруте
    
    while not visited.all():
        state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
        with torch.no_grad():
            qvals = model(state)
        next_node = int(qvals[0].argmax().cpu().item())
        if visited[next_node]:
            choices = [i for i in range(len(coords_np)) if not visited[i]]
            if not choices: break
            next_node = choices[0]

        travel_time = time_matrix[cur_node, next_node]
        arrival_time = cur_time + travel_time

        # Если поездка пересекает обед
        if cur_time < LUNCH_START < arrival_time:
            # Делаем паузу на обед
            delta = LUNCH_END - LUNCH_START
            cur_time = LUNCH_END
            arrival_time = cur_time + travel_time
            had_lunch = True
        elif arrival_time >= LUNCH_START and arrival_time < LUNCH_END:
            # Приезжаем во время обеда — сдвигаем начало визита
            cur_time = LUNCH_END
            arrival_time = cur_time
            had_lunch = True
        else:
            had_lunch = False

        # Добавляем расстояние и обновляем время
        total_distance += dist_matrix[cur_node, next_node]
        cur_time = arrival_time
        visit_start = cur_time
        visit_end = visit_start + TIME_PER_POINT
        cur_time = visit_end
        total_time += travel_time + TIME_PER_POINT
        visited[next_node] = True
        cur_node = next_node
        tour.append(next_node)
        arrival_times.append(visit_start)
        lunch_flags.append(had_lunch)
    
    # Перевод времени в часы и минуты
    arrival_times_hm = [minutes_to_hours_minutes(t) for t in arrival_times]
    total_hours, total_minutes = minutes_to_hours_minutes(total_time)
    
    return tour, total_distance, total_time, total_hours, total_minutes, arrival_times_hm, lunch_flags

if __name__ == "__main__":
    tour, dist, time_min, total_h, total_m, arrivals_hm, lunch_flags = run_pipeline()
    print("Оптимальный тур:", tour)
    print(f"Общая дистанция: {dist:.2f} км")
    print(f"Общее время маршрута: {time_min:.2f} минут (~{total_h} ч {total_m} мин)")
    print("Время прибытия на каждую точку:")
    for idx, (h, m), lunch in zip(tour, arrivals_hm, lunch_flags):
        lunch_str = " (Обед!)" if lunch else ""
        print(f"Точка {idx}: {h:02d}:{m:02d}{lunch_str}")
