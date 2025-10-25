#!/usr/bin/env python3
import pandas as pd
import numpy as np
import networkx as nx
import osmnx as ox
import folium
from networkx.algorithms.approximation.traveling_salesman import christofides
from tqdm import tqdm
from shapely.geometry import box
from datetime import timedelta  # Не используется, но для ясности

ox.settings.use_cache = True
ox.settings.log_console = True

# ------------------ Настройки ------------------
DATA_CSV = "test.csv"              # CSV с колонками 'Географическая широта', 'Географическая долгота', 'Адрес объекта', 'Начало', 'Конец'
N_POINTS = 10                      # кол-во точек (по CSV)
DEFAULT_SPEED_KPH = 30.0
WORK_START = 9*60                  # 09:00 в минутах
WORK_END = 18*60                   # 18:00 в минутах
LUNCH_START = 13*60                # 13:00 в минутах
LUNCH_END = 14*60                  # 14:00 в минутах
TIME_PER_POINT = 30.0              # минуты на посещение точки
TIME_PENALTY = 60*60               # штраф за пересечение временного окна (сек) — не используется в feasibility
OUTPUT_MAP = "map.html"
# Ростов-на-Дону bbox (расширен для покрытия всех точек)
NORTH, SOUTH, EAST, WEST = 47.3, 47.1, 39.95, 39.6
# ------------------------------------------------

def time_to_minutes(time_str):
    """Преобразует строку времени 'HH:MM' в минуты с 00:00."""
    if pd.isna(time_str):
        return 0
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def read_points(csv_path=DATA_CSV, n=N_POINTS):
    df = pd.read_csv(csv_path)
    lat_col = 'Географическая широта'
    lon_col = 'Географическая долгота'
    addr_col = 'Адрес объекта'
    start_col = 'Начало'
    end_col = 'Конец'
    
    required_cols = [lat_col, lon_col, addr_col, start_col, end_col]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"CSV должен содержать колонки: {missing}")
    
    pts = df[[lat_col, lon_col]].dropna().values[:n]
    start_windows = df[start_col].apply(time_to_minutes).values[:n]
    end_windows = df[end_col].apply(time_to_minutes).values[:n]
    return pts, df, start_windows, end_windows

def build_graph_bbox():
    print("Loading graph for Ростов-на-Дону from bbox...")
    bbox = box(WEST, SOUTH, EAST, NORTH)
    G = ox.graph_from_polygon(bbox, network_type="drive")
    
    # Добавление длин рёбер
    G = ox.distance.add_edge_lengths(G)
    
    for u, v, k, data in G.edges(keys=True, data=True):
        if 'speed_kph' not in data or data.get('speed_kph') is None:
            data['speed_kph'] = DEFAULT_SPEED_KPH
        data['travel_time'] = data['length'] / 1000 / data['speed_kph'] * 3600  # сек (для Dijkstra)
    print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G

def nearest_nodes_for_points(G, points):
    nodes = [ox.distance.nearest_nodes(G, X=lon, Y=lat) for lat, lon in points]
    return nodes

def compute_pairwise_shortest_paths(G, nodes):
    n = len(nodes)
    pair_dist = np.full((n, n), np.inf)  # в секундах
    pair_path = [[None]*n for _ in range(n)]
    for i, ni in tqdm(enumerate(nodes), total=n, desc="Computing shortest paths"):
        lengths, paths = nx.single_source_dijkstra(G, ni, weight='travel_time')
        for j, nj in enumerate(nodes):
            if nj in lengths:
                pair_dist[i,j] = lengths[nj]
                pair_path[i][j] = paths[nj]
            else:
                pair_dist[i,j] = np.inf
                pair_path[i][j] = None
    # Конвертируем в минуты для удобства
    pair_dist_min = pair_dist / 60.0
    return pair_dist_min, pair_path

def greedy_feasible_tour(pair_dist_min, start_windows, end_windows):
    """
    Greedy алгоритм: Начинаем с точки 0, на каждом шаге выбираем ближайшую feasible точку
    (учитывая projected arrival time, обед, ожидание окна, TIME_PER_POINT).
    Пропускаем, если projected_end > end_window.
    """
    n = len(pair_dist_min)
    visited = np.zeros(n, dtype=bool)
    cur_node = 0
    visited[cur_node] = True
    cur_time = WORK_START  # минуты
    
    tour = [cur_node]
    skipped = []
    
    while not np.all(visited):
        candidates = []
        for i in range(n):
            if visited[i]:
                continue
            # Projected travel time (мин)
            travel_time = pair_dist_min[cur_node, i]
            proj_arrival = cur_time + travel_time
            
            # Учёт обеда
            if cur_time < LUNCH_START < proj_arrival:
                proj_arrival = max(proj_arrival, LUNCH_END)
            elif LUNCH_START <= proj_arrival < LUNCH_END:
                proj_arrival = LUNCH_END
            
            # Ожидание начала окна
            window_start = start_windows[i]
            proj_arrival = max(proj_arrival, window_start)
            
            # Projected end of visit
            proj_end = proj_arrival + TIME_PER_POINT
            
            # Проверка: если конец визита > end_window — пропускаем
            if proj_end > end_windows[i]:
                skipped.append(i)
                print(f"Пропускаем точку {i}: projected end {proj_end:.1f} мин > конец окна {end_windows[i]:.1f} мин")
                continue
            
            # Candidate: (distance, index) — greedy по расстоянию
            candidates.append((travel_time, i))
        
        if not candidates:
            print("Нет доступных точек: все оставшиеся окна пропущены.")
            break
        
        # Выбираем ближайшую
        candidates.sort()  # по travel_time
        next_node = candidates[0][1]
        
        # Обновляем cur_time (реальное)
        travel_time = pair_dist_min[cur_node, next_node]
        arrival_time = cur_time + travel_time
        
        # Учёт обеда (реальный)
        if cur_time < LUNCH_START < arrival_time:
            arrival_time = max(arrival_time, LUNCH_END)
        elif LUNCH_START <= arrival_time < LUNCH_END:
            arrival_time = LUNCH_END
        
        # Ожидание окна
        arrival_time = max(arrival_time, start_windows[next_node])
        
        # Visit
        visit_end = arrival_time + TIME_PER_POINT
        cur_time = visit_end
        
        visited[next_node] = True
        cur_node = next_node
        tour.append(next_node)
    
    if skipped:
        print(f"Пропущенные точки: {skipped}")
    
    return tour

def reconstruct_full_route_indices(tour_indices, pair_path):
    full_nodes = []
    for k in range(len(tour_indices)-1):
        a, b = tour_indices[k], tour_indices[k+1]
        path = pair_path[a][b]
        if path is None: 
            continue
        if full_nodes and full_nodes[-1] == path[0]:
            full_nodes.extend(path[1:])
        else:
            full_nodes.extend(path)
    return full_nodes

def plot_route_folium(G, full_nodes, points, tour_indices, df, output_html=OUTPUT_MAP):
    node_xy = {n: (data['y'], data['x']) for n, data in G.nodes(data=True)}
    center = [float(points[:,0].mean()), float(points[:,1].mean())]
    m = folium.Map(location=center, zoom_start=12)
    
    # Маркеры для точек в туре с номерами порядка
    for order, idx in enumerate(tour_indices):
        lat, lon = points[idx]
        addr_col = 'Адрес объекта'
        popup_text = df.iloc[idx][addr_col] if addr_col in df.columns else f"Point {idx}"
        folium.Marker(
            [lat, lon], 
            popup=f"{order+1}. {popup_text}", 
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
    
    # Линия пути по full_nodes
    path_coords = []
    for n in full_nodes:
        if n in node_xy:
            lat, lon = node_xy[n]
            path_coords.append([lat, lon])
    if path_coords:
        folium.PolyLine(
            path_coords, 
            color="blue", 
            weight=4, 
            opacity=0.8
        ).add_to(m)
    
    m.save(output_html)
    print(f"Map saved to {output_html}. Open in browser to view the route.")

def main():
    pts, df, start_windows, end_windows = read_points()
    print(f"Loaded {len(pts)} points from {DATA_CSV}")
    G = build_graph_bbox()
    nodes = nearest_nodes_for_points(G, pts)
    pair_dist_min, pair_path = compute_pairwise_shortest_paths(G, nodes)
    
    # Строим feasible тур (greedy с проверкой времени)
    tour = greedy_feasible_tour(pair_dist_min, start_windows, end_windows)
    
    if len(tour) < 2:
        print("Warning: Тур слишком короткий (только старт), используя все точки без фильтра")
        tour = list(range(len(pts)))
    
    full_nodes = reconstruct_full_route_indices(tour, pair_path)
    print("Feasible tour (order of points):", tour)
    # Карта пути по feasible точкам
    plot_route_folium(G, full_nodes, pts, tour, df)

if __name__ == "__main__":
    main()