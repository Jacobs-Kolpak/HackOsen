#!/usr/bin/env python3
import pandas as pd
import numpy as np
import torch
from model_yandex import ImprovedGNNQNetwork, State, haversine, DEVICE

# ---------------- CONFIG ----------------
MODEL_PATH = "improved_gnn_dynamic.pth"
INPUT_CSV = "test.csv"  # CSV с колонками: "Адрес", "Географическая широта", "Географическая долгота"
N_POINTS = 12

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
            dist[i,j] = d
            time[i,j] = (d / speed_kmh) * 60.0
    return dist, time

# ---------------- Pipeline ----------------
def run_pipeline(csv_path=INPUT_CSV, model_path=MODEL_PATH, n_points=N_POINTS):
    df, coords_np = read_csv(csv_path)
    coords_np = coords_np[:n_points]
    
    # заглушка при отсутствии приоритетов/уровней
    priorities_np = np.ones(len(coords_np))
    levels_np = np.zeros(len(coords_np))
    
    dist_matrix, time_matrix = compute_haversine_matrix(coords_np)
    
    # тензоры
    dist_t = torch.tensor(dist_matrix, dtype=torch.float32, device=DEVICE)
    time_t = torch.tensor(time_matrix, dtype=torch.float32, device=DEVICE)
    coords_t = torch.tensor(coords_np, dtype=torch.float32, device=DEVICE)
    priorities_t = torch.tensor(priorities_np, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels_np, dtype=torch.float32, device=DEVICE)
    
    # модель
    model = ImprovedGNNQNetwork().to(DEVICE)
    model.load_state_dict(torch.load(model_path, map_location=DEVICE))
    model.eval()
    
    visited = torch.zeros(len(coords_np), dtype=torch.bool, device=DEVICE)
    cur_node = 0
    visited[cur_node] = True
    cur_time = 9*60  # стартовое время 09:00
    
    tour = [cur_node]
    while not visited.all():
        state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
        qvals = model(state)
        next_node = int(qvals[0].argmax().cpu().item())
        if visited[next_node]:
            choices = [i for i in range(len(coords_np)) if not visited[i]]
            if not choices: break
            next_node = choices[0]
        visited[next_node] = True
        cur_node = next_node
        tour.append(next_node)
    # возвращаем список индексов точек
    return tour

if __name__ == "__main__":
    tour = run_pipeline()
    print("Оптимальный тур:", tour)
