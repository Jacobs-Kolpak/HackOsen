import pandas as pd
import numpy as np
import torch
from model_yandex import ImprovedGNNQNetwork, State, haversine, DEVICE

MODEL_PATH = "improved_gnn_yandex.pth"
INPUT_CSV = "real.csv"
N_POINTS = 12
TIME_PER_POINT = 30.0  
START_TIME_MINUTES = 9*60  
LUNCH_START = 13*60  
LUNCH_END = 14*60

def time_to_minutes(time_str):
    if pd.isna(time_str):
        return 0
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def read_csv(csv_path):
    df = pd.read_csv(csv_path)
    req_cols = ['Географическая широта', 'Географическая долгота', 'Время начала рабочего дня', 'Время окончания рабочего дня']
    for c in req_cols:
        if c not in df.columns:
            raise RuntimeError(f"CSV должен содержать колонку '{c}'")
    coords = np.stack([df['Географическая широта'].values, df['Географическая долгота'].values], axis=1)
    start_window = df['Время начала рабочего дня'].apply(time_to_minutes).astype(float).values
    end_window = df['Время окончания рабочего дня'].apply(time_to_minutes).astype(float).values
    return df, coords, start_window, end_window

def compute_haversine_matrix(coords, speed_kmh=30.0):
    n = len(coords)
    dist = np.zeros((n, n))
    time = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i==j: continue
            d = haversine(coords[i,0], coords[i,1], coords[j,0], coords[j,1])
            dist[i,j] = d  
            time[i,j] = (d / speed_kmh) * 60.0
    return dist, time

def minutes_to_hours_minutes(minutes):
    h = int(minutes // 60)
    m = int(round(minutes % 60))
    return h, m

def check_lunch(time_min):
    return LUNCH_START <= time_min < LUNCH_END

def run_pipeline(csv_path=INPUT_CSV, model_path=MODEL_PATH, n_points=N_POINTS):
    df, coords_np, start_window, end_window = read_csv(csv_path)
    coords_np = coords_np[:n_points]
    start_window = start_window[:n_points]
    end_window = end_window[:n_points]
    
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
    total_distance = 0.0
    total_time = 0.0
    arrival_times = [cur_time]
    lunch_flags = [False]
    
    while not visited.all():
        state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
        with torch.no_grad():
            qvals = model(state)
        
        candidates = []
        for i in range(len(coords_np)):
            if visited[i]:
                continue
            travel_time = time_matrix[cur_node, i]
            proj_arrival = cur_time + travel_time
            
            if cur_time < LUNCH_START < proj_arrival:
                proj_arrival = max(proj_arrival, LUNCH_END)
                
            elif LUNCH_START <= proj_arrival < LUNCH_END:
                proj_arrival = LUNCH_END
                
            if proj_arrival < start_window[i]:
                proj_arrival = start_window[i]
                
            if proj_arrival > end_window[i]:
                print(f"Пропускаем точку {i}: projected arrival {proj_arrival:.1f} мин > конец окна {end_window[i]:.1f} мин")
                continue
            candidates.append(i)
        
        if not candidates:
            print("Нет доступных точек: все оставшиеся окна пропущены.")
            break
        
        qvals_candidates = [qvals[0][j].item() for j in candidates]
        next_idx = np.argmax(qvals_candidates)
        next_node = candidates[next_idx]

        travel_time = time_matrix[cur_node, next_node]
        arrival_time = cur_time + travel_time

        had_lunch = False
        if cur_time < LUNCH_START < arrival_time:
            cur_time = LUNCH_END
            arrival_time = max(arrival_time, cur_time)
            had_lunch = True
        elif LUNCH_START <= arrival_time < LUNCH_END:
            arrival_time = LUNCH_END
            had_lunch = True

        window_start = start_window[next_node]
        window_end = end_window[next_node]
        if arrival_time < window_start:
            arrival_time = window_start
            
        total_distance += dist_matrix[cur_node, next_node]
        visit_start = arrival_time
        visit_end = visit_start + TIME_PER_POINT
        total_time += travel_time + TIME_PER_POINT
        cur_time = visit_end

        visited[next_node] = True
        cur_node = next_node
        tour.append(next_node)
        arrival_times.append(visit_start)
        lunch_flags.append(had_lunch)
    
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