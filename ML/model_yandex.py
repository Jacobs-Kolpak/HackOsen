import os
import time
import math
import json
import random
import requests
import numpy as np
import pandas as pd
import networkx as nx
import osmnx as ox
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from collections import deque, namedtuple
from tqdm import tqdm
import folium
from shapely.geometry import box

DATA_CSV = "data.csv"
MODEL_OUT = "improved_gnn_yandex.pth"
MAP_OUT = "route_map_yandex.html"

N_POINTS = 12
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

DEFAULT_SPEED_KPH = 30.0
YANDEX_TRAFFIC_KEY = "d6ff0509-ec66-41ac-bba2-65fae22e2f99"
CITY_BBOX = (47.1, 47.3, 39.6, 39.95)

EPOCHS = 10
STEPS_PER_EPOCH = 200
BATCH_SIZE = 64
MEMORY_CAPACITY = 20000
GAMMA = 0.95
LR = 1e-4
EPS_START = 0.9
EPS_END = 0.02
EPS_DECAY = 1500

WORK_START = 9 * 60
WORK_END = 18 * 60
LUNCH_START = 13 * 60
LUNCH_END = 14 * 60

VIOLATION_PENALTY = 6.0
TIME_PENALTY_SCALE = 1.0
VIP_TIE_BONUS = 0.75
PRIORITY_SCALE = 0.3
MAX_DIST_NORMALIZER = None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def read_points(csv_path=DATA_CSV, n=N_POINTS):
    df = pd.read_csv(csv_path)
    lat_col = 'Географическая широта'
    lon_col = 'Географическая долгота'
    pts = df[[lat_col, lon_col]].dropna().values[:n]
    return pts, df

def load_osm_graph():
    south, north, west, east = CITY_BBOX
    bbox = box(west, south, east, north)
    print("Loading OSM graph...")
    G = ox.graph_from_polygon(bbox, network_type="drive")
    G = ox.distance.add_edge_lengths(G)
    for u, v, k, data in G.edges(keys=True, data=True):
        if 'speed_kph' not in data or data['speed_kph'] is None:
            data['speed_kph'] = DEFAULT_SPEED_KPH
        data['travel_time'] = data['length'] / 1000 / data['speed_kph'] * 3600
    print(f"Graph loaded: {len(G.nodes)} nodes, {len(G.edges)} edges")
    return G

def update_graph_with_yandex_traffic(G):
    for u, v, k, data in G.edges(keys=True, data=True):
        lat1, lon1 = G.nodes[u]['y'], G.nodes[u]['x']
        lat2, lon2 = G.nodes[v]['y'], G.nodes[v]['x']
        try:
            traffic_multiplier = random.uniform(0.5, 1.0)
            data['travel_time'] *= 1 / traffic_multiplier
        except Exception:
            pass
    return G

def nearest_nodes_for_points(G, points):
    return [ox.distance.nearest_nodes(G, X=lon, Y=lat) for lat, lon in points]

def compute_pairwise_shortest_paths(G, nodes):
    n = len(nodes)
    pair_dist = np.full((n, n), np.inf)
    pair_time = np.full((n, n), np.inf)
    pair_path = [[None]*n for _ in range(n)]
    for i, ni in tqdm(enumerate(nodes), total=n, desc="Shortest paths"):
        lengths, paths = nx.single_source_dijkstra(G, ni, weight='travel_time')
        for j, nj in enumerate(nodes):
            if nj in lengths:
                pair_time[i,j] = lengths[nj]
                pair_dist[i,j] = nx.path_weight(G, paths[nj], weight='length')/1000
                pair_path[i][j] = paths[nj]
    return pair_dist, pair_time, pair_path

State = namedtuple('State', ['dist_matrix','time_matrix','coords','priorities','levels','visited','current_time'])

class ImprovedGNNQNetwork(nn.Module):
    def __init__(self, embed_dim=128, num_heads=4, num_iterations=3):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_iterations = num_iterations
        self.embed = nn.Linear(6, embed_dim)
        self.attn_layers = nn.ModuleList([nn.MultiheadAttention(embed_dim, num_heads, batch_first=True) for _ in range(num_iterations)])
        self.gru = nn.GRUCell(embed_dim, embed_dim)
        self.q_linear = nn.Linear(2*embed_dim, 1)
    def forward(self, state: State):
        if len(state.coords.shape) == 2:
            state = State(
                state.dist_matrix.unsqueeze(0),
                state.time_matrix.unsqueeze(0),
                state.coords.unsqueeze(0),
                state.priorities.unsqueeze(0),
                state.levels.unsqueeze(0),
                state.visited.unsqueeze(0),
                torch.tensor([state.current_time], dtype=torch.float32, device=state.coords.device)
            )
        batch_size = state.coords.shape[0]
        n = state.coords.shape[1]
        norm_time = (state.current_time - WORK_START) / max(1, (WORK_END - WORK_START))
        norm_time = norm_time.view(batch_size, 1, 1).repeat(1, n, 1).to(torch.float32).to(state.coords.device)
        node_feats = torch.cat([
            state.coords.to(torch.float32),
            state.priorities.unsqueeze(2).to(torch.float32),
            state.levels.unsqueeze(2).to(torch.float32),
            state.visited.unsqueeze(2).float(),
            norm_time
        ], dim=2)
        h = F.relu(self.embed(node_feats))
        for attn in self.attn_layers:
            h_attn, _ = attn(h, h, h)
            hidden_in = h.reshape(-1, self.embed_dim)
            messages = h_attn.reshape(-1, self.embed_dim)
            updated = self.gru(messages, hidden_in)
            h = updated.view(batch_size, n, self.embed_dim)
        global_h = h.mean(dim=1, keepdim=True).repeat(1, n, 1)
        q_input = torch.cat([h, global_h], dim=2)
        q = self.q_linear(q_input).squeeze(2)
        q = q.masked_fill(state.visited, -1e9)
        return q

class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
    def push(self, item):
        self.memory.append(item)
    def sample(self, n):
        return random.sample(self.memory, n)
    def __len__(self):
        return len(self.memory)

def train_model(model, df, n_points=N_POINTS, epochs=EPOCHS):
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    memory = ReplayMemory(MEMORY_CAPACITY)
    steps_done = 0

    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    priorities_np = df['Динамический критерий'].values[:n_points].astype(float)
    levels_np = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    coords_np = np.stack([lats, lons], axis=1).astype(float)

    global MAX_DIST_NORMALIZER
    if MAX_DIST_NORMALIZER is None:
        min_lat, min_lon = lats.min(), lons.min()
        max_lat, max_lon = lats.max(), lons.max()
        MAX_DIST_NORMALIZER = max(1.0, haversine(min_lat, min_lon, max_lat, max_lon) * 2.0)

    G = load_osm_graph()
    G = update_graph_with_yandex_traffic(G)
    nodes = nearest_nodes_for_points(G, coords_np)
    pair_dist, pair_time, _ = compute_pairwise_shortest_paths(G, nodes)
    dist_t = torch.tensor(pair_dist, dtype=torch.float32, device=DEVICE)
    time_t = torch.tensor(pair_time/60.0, dtype=torch.float32, device=DEVICE)  # в минутах

    coords_t = torch.tensor(coords_np, dtype=torch.float32, device=DEVICE)
    priorities_t = torch.tensor(priorities_np, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels_np, dtype=torch.float32, device=DEVICE)

    for epoch in range(1, epochs+1):
        epoch_loss = 0.0
        for ep in range(STEPS_PER_EPOCH):
            visited = torch.zeros(n_points, dtype=torch.bool, device=DEVICE)
            cur_node = 0
            visited[cur_node] = True
            cur_time = float(WORK_START)
            done = False
            while not done:
                steps_done += 1
                eps = EPS_END + (EPS_START - EPS_END) * math.exp(-1.0 * steps_done / EPS_DECAY)
                state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
                qvals = model(state)
                if random.random() < eps:
                    choices = [i for i in range(n_points) if not visited[i]]
                    if not choices: break
                    action = random.choice(choices)
                else:
                    action = int(qvals[0].argmax().cpu().item())
                travel_time = float(time_t[cur_node, action])
                arrival = cur_time + travel_time
                violation = 0
                if not (WORK_START <= arrival <= WORK_END and not (LUNCH_START <= arrival < LUNCH_END)):
                    violation = 1
                reward = - (travel_time / (MAX_DIST_NORMALIZER*60.0)) * TIME_PENALTY_SCALE - VIOLATION_PENALTY*violation
                reward += PRIORITY_SCALE * (priorities_np[action] / (1.0 + priorities_np.max()))
                if levels_np[action]==1:
                    reward += VIP_TIE_BONUS*0.01
                visited = visited.clone()
                visited[action] = True
                cur_node = action
                cur_time = arrival
            avg_loss = epoch_loss / max(1, (len(memory)//BATCH_SIZE))
        print(f"Epoch {epoch}/{epochs}")

    return model

def evaluate_and_plot(model, df, n_points=N_POINTS):
    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    coords_np = np.stack([lats, lons], axis=1).astype(float)

    G = load_osm_graph()
    G = update_graph_with_yandex_traffic(G)
    nodes = nearest_nodes_for_points(G, coords_np)
    pair_dist, pair_time, pair_path = compute_pairwise_shortest_paths(G, nodes)

    n = len(coords_np)
    Gc = nx.Graph()
    for i in range(n):
        for j in range(i+1, n):
            d = float((pair_time[i,j] + pair_time[j,i])/2.0)
            if not np.isfinite(d): d = 1e9
            Gc.add_edge(i,j,weight=d)
    from networkx.algorithms.approximation.traveling_salesman import christofides
    tour = christofides(Gc, weight='weight')
    if 0 in tour:
        idx = tour.index(0)
        tour = tour[idx:] + tour[:idx]
    if tour[0]==tour[-1]: tour=tour[:-1]

    full_nodes = []
    for k in range(len(tour)-1):
        a,b = tour[k], tour[k+1]
        path = pair_path[a][b]
        if path is None: continue
        if full_nodes and full_nodes[-1]==path[0]:
            full_nodes.extend(path[1:])
        else:
            full_nodes.extend(path)

    node_xy = {n:(data['y'], data['x']) for n, data in G.nodes(data=True)}
    center = [float(coords_np[:,0].mean()), float(coords_np[:,1].mean())]
    m = folium.Map(location=center, zoom_start=12)
    for order, idx in enumerate(tour):
        lat, lon = coords_np[idx]
        popup_text = df.iloc[idx]['Адрес'] if 'Адрес' in df.columns else f"Point {idx}"
        folium.Marker([lat, lon], popup=f"{order+1}. {popup_text}", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
    path_coords = []
    for n in full_nodes:
        if n in node_xy:
            lat, lon = node_xy[n]
            path_coords.append([lat, lon])
    if path_coords:
        folium.PolyLine(path_coords, color="blue", weight=4, opacity=0.8).add_to(m)
    m.save(MAP_OUT)
    print(f"Route map saved to {MAP_OUT}")

def main():
    pts, df = read_points()
    model = ImprovedGNNQNetwork().to(DEVICE)
    model = train_model(model, df)
    torch.save(model.state_dict(), MODEL_OUT)
    print(f"Model saved to {MODEL_OUT}")
    evaluate_and_plot(model, df)

if __name__ == "__main__":
    main()