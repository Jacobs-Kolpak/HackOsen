#!/usr/bin/env python3
import pandas as pd
import numpy as np
import networkx as nx
import osmnx as ox
import folium
from networkx.algorithms.approximation.traveling_salesman import christofides
from tqdm import tqdm
import osmnx as ox
from shapely.geometry import box

ox.settings.use_cache = True
ox.settings.log_console = True

# ------------------ Настройки ------------------
DATA_CSV = "data.csv"             # CSV с колонками 'Географическая широта', 'Географическая долгота'
N_POINTS = 15                      # кол-во точек
DEFAULT_SPEED_KPH = 30.0
WORK_START = 9*60                  # 09:00
WORK_END = 18*60                   # 18:00
LUNCH_START = 13*60                # 13:00
LUNCH_END = 14*60                  # 14:00
TIME_PENALTY = 60*60               # штраф за пересечение временного окна (сек)
OUTPUT_MAP = "rostov_route_map.html"
# Ростов-на-Дону bbox
NORTH, SOUTH, EAST, WEST = 47.3, 47.1, 39.95, 39.6
# ------------------------------------------------

def read_points(csv_path=DATA_CSV, n=N_POINTS):
    df = pd.read_csv(csv_path)
    lat_col = 'Географическая широта'
    lon_col = 'Географическая долгота'
    pts = df[[lat_col, lon_col]].dropna().values[:n]
    return pts, df

def build_graph_bbox():
    print("Loading graph for Ростов-на-Дону from bbox...")
    bbox = box(WEST, SOUTH, EAST, NORTH)
    G = ox.graph_from_polygon(bbox, network_type="drive")
    
    # Новая запись для добавления длин
    G = ox.distance.add_edge_lengths(G)
    
    for u, v, k, data in G.edges(keys=True, data=True):
        if 'speed_kph' not in data or data.get('speed_kph') is None:
            data['speed_kph'] = DEFAULT_SPEED_KPH
        data['travel_time'] = data['length'] / 1000 / data['speed_kph'] * 3600  # сек
    print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G



def nearest_nodes_for_points(G, points):
    nodes = [ox.distance.nearest_nodes(G, X=lon, Y=lat) for lat, lon in points]
    return nodes

def adjust_edge_weights_time_windows(G):
    for u, v, k, data in G.edges(keys=True, data=True):
        # Простейшее увеличение времени для учета обеденного окна
        data['travel_time'] += TIME_PENALTY * 0.1
    return G

def compute_pairwise_shortest_paths(G, nodes):
    n = len(nodes)
    pair_dist = np.full((n, n), np.inf)
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
    return pair_dist, pair_path

def solve_tsp_christofides(pair_dist):
    n = pair_dist.shape[0]
    Gc = nx.Graph()
    for i in range(n):
        for j in range(i+1, n):
            d = float((pair_dist[i,j] + pair_dist[j,i])/2.0)
            if not np.isfinite(d):
                d = 1e9
            Gc.add_edge(i,j,weight=d)
    cycle = christofides(Gc, weight='weight')
    if 0 in cycle:
        idx = cycle.index(0)
        cycle = cycle[idx:] + cycle[:idx]
    if cycle[0] == cycle[-1]:
        cycle = cycle[:-1]
    return cycle

def reconstruct_full_route_indices(tour_indices, pair_path):
    full_nodes = []
    for k in range(len(tour_indices)-1):
        a, b = tour_indices[k], tour_indices[k+1]
        path = pair_path[a][b]
        if path is None: continue
        if full_nodes and full_nodes[-1] == path[0]:
            full_nodes.extend(path[1:])
        else:
            full_nodes.extend(path)
    return full_nodes

def plot_route_folium(G, full_nodes, points, tour_indices, df, output_html=OUTPUT_MAP):
    node_xy = {n:(data['y'], data['x']) for n, data in G.nodes(data=True)}
    center = [float(points[:,0].mean()), float(points[:,1].mean())]
    m = folium.Map(location=center, zoom_start=12)
    for order, idx in enumerate(tour_indices):
        lat, lon = points[idx]
        popup_text = df.iloc[idx]['Адрес'] if 'Адрес' in df.columns else f"Point {idx}"
        folium.Marker([lat, lon], popup=f"{order+1}. {popup_text}", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
    path_coords = []
    for n in full_nodes:
        if n in node_xy:
            lat, lon = node_xy[n]
            path_coords.append([lat, lon])
    if path_coords:
        folium.PolyLine(path_coords, color="blue", weight=4, opacity=0.8).add_to(m)
    m.save(output_html)
    print(f"Map saved to {output_html}")

def main():
    pts, df = read_points()
    G = build_graph_bbox()
    G = adjust_edge_weights_time_windows(G)
    nodes = nearest_nodes_for_points(G, pts)
    pair_dist, pair_path = compute_pairwise_shortest_paths(G, nodes)
    tour = solve_tsp_christofides(pair_dist)
    if len(tour) != len(pts):
        tour = list(range(len(pts)))
    full_nodes = reconstruct_full_route_indices(tour, pair_path)
    print("Tour (order of points):", tour)
    plot_route_folium(G, full_nodes, pts, tour, df)

if __name__ == "__main__":
    main()
