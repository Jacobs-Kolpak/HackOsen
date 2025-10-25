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
MODEL_OUT = "rl_dqn.pth"
MAP_OUT = "route_map_rl.html"

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
TARGET_UPDATE = 100

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

Transition = namedtuple('Transition', ['state', 'action', 'next_state', 'reward'])

State = namedtuple('State', ['dist_matrix','time_matrix','coords','priorities','levels','visited','current_time'])

def flatten_state(state, n_points):
    device = state.dist_matrix.device
    flat_dist = state.dist_matrix.flatten()
    flat_time = state.time_matrix.flatten()
    flat_coords = state.coords.flatten()
    flat_priorities = state.priorities.flatten()
    flat_levels = state.levels.flatten()
    flat_visited = state.visited.flatten().float()
    norm_val = state.current_time / torch.tensor(WORK_END - WORK_START, dtype=torch.float32, device=device)
    flat_time_norm = norm_val.repeat(n_points)
    return torch.cat([flat_dist, flat_time, flat_coords, flat_priorities, flat_levels, flat_visited, flat_time_norm])

class DQN(nn.Module):
    def __init__(self, input_size, n_actions, hidden_dim=256):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, n_actions)
    
    def forward(self, state):
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        q = self.fc3(x)
        return q

class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
    
    def push(self, *args):
        self.memory.append(Transition(*args))
    
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        return len(self.memory)

def train_model(df, n_points=N_POINTS, epochs=EPOCHS):
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
    time_t = torch.tensor(pair_time/60.0, dtype=torch.float32, device=DEVICE)

    coords_t = torch.tensor(coords_np, dtype=torch.float32, device=DEVICE)
    priorities_t = torch.tensor(priorities_np, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels_np, dtype=torch.float32, device=DEVICE)

    input_size = dist_t.numel() + time_t.numel() + coords_t.numel() + priorities_t.numel() + levels_t.numel() + n_points * 2
    n_actions = n_points

    policy_net = DQN(input_size, n_actions).to(DEVICE)
    target_net = DQN(input_size, n_actions).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.AdamW(policy_net.parameters(), lr=LR, weight_decay=1e-4)
    memory = ReplayMemory(MEMORY_CAPACITY)
    steps_done = 0

    def compute_reward(cur_node, action, cur_time, time_matrix):
        travel_time = float(time_matrix[cur_node, action])
        arrival = cur_time + travel_time
        violation = 0
        if not (WORK_START <= arrival <= WORK_END and not (LUNCH_START <= arrival < LUNCH_END)):
            violation = 1
        reward = - (travel_time / (MAX_DIST_NORMALIZER*60.0)) * TIME_PENALTY_SCALE - VIOLATION_PENALTY*violation
        reward += PRIORITY_SCALE * (priorities_np[action] / (1.0 + priorities_np.max()))
        if levels_np[action]==1:
            reward += VIP_TIE_BONUS*0.01
        return reward, arrival

    for epoch in range(1, epochs+1):
        epoch_loss = 0.0
        num_updates = 0
        pbar = tqdm(range(STEPS_PER_EPOCH), desc=f"Epoch {epoch}/{epochs}")
        for _ in pbar:
            visited = torch.zeros(n_points, dtype=torch.bool, device=DEVICE)
            cur_node = 0
            visited[cur_node] = True
            cur_time = float(WORK_START)
            state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
            done = False
            while not done:
                steps_done += 1
                eps = EPS_END + (EPS_START - EPS_END) * math.exp(-1.0 * steps_done / EPS_DECAY)
                
                flat_state = flatten_state(state, n_points).unsqueeze(0).to(DEVICE)
                qvals = policy_net(flat_state).squeeze(0)
                qvals = qvals.masked_fill(visited, -1e9)
                
                if torch.all(qvals == -1e9):
                    done = True
                    break
                
                if random.random() < eps:
                    choices = [i for i in range(n_points) if not visited[i]]
                    if not choices:
                        done = True
                        break
                    action = random.choice(choices)
                else:
                    action = qvals.argmax().item()
                
                reward, next_time = compute_reward(cur_node, action, cur_time, time_t)
                r_tensor = torch.tensor([reward], device=DEVICE)
                
                next_visited = visited.clone()
                next_visited[action] = True
                next_state = State(dist_t, time_t, coords_t, priorities_t, levels_t, next_visited, torch.tensor(next_time, device=DEVICE))
                
                done = next_visited.sum().item() == n_points
                memory.push(state, action, next_state if not done else None, r_tensor)
                
                state = next_state
                cur_node = action
                cur_time = next_time
            
            if len(memory) >= BATCH_SIZE:
                transitions = memory.sample(BATCH_SIZE)
                batch = Transition(*zip(*transitions))
                
                non_final_mask = torch.tensor(tuple(map(lambda s: s is not None, batch.next_state)), device=DEVICE, dtype=torch.bool)
                non_final_next_states = torch.stack([flatten_state(s, n_points) for s in batch.next_state if s is not None])
                
                state_batch = torch.stack([flatten_state(s, n_points) for s in batch.state])
                action_batch = torch.tensor(batch.action, device=DEVICE).unsqueeze(1)
                reward_batch = torch.cat(batch.reward)
                
                state_action_values = policy_net(state_batch).gather(1, action_batch)
                
                next_state_values = torch.zeros(BATCH_SIZE, device=DEVICE)
                if non_final_mask.any():
                    with torch.no_grad():
                        next_qvals = target_net(non_final_next_states)
                        next_state_values[non_final_mask] = next_qvals.max(1)[0].detach()
                
                expected_state_action_values = (next_state_values * GAMMA) + reward_batch
                
                loss = F.smooth_l1_loss(state_action_values, expected_state_action_values.unsqueeze(1))
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_value_(policy_net.parameters(), 100)
                optimizer.step()
                
                epoch_loss += loss.item()
                num_updates += 1
                
                if steps_done % TARGET_UPDATE == 0:
                    target_net.load_state_dict(policy_net.state_dict())
            
            pbar.set_postfix({'Loss': f"{epoch_loss / max(1, num_updates):.4f}"})
        
        print(f"Epoch {epoch}/{epochs} completed. Avg Loss: {epoch_loss / max(1, num_updates):.4f}")

    return policy_net, target_net

def evaluate_and_plot(model, df, n_points=N_POINTS):
    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    coords_np = np.stack([lats, lons], axis=1).astype(float)

    G = load_osm_graph()
    G = update_graph_with_yandex_traffic(G)
    nodes = nearest_nodes_for_points(G, coords_np)
    pair_dist, pair_time, pair_path = compute_pairwise_shortest_paths(G, nodes)

    dist_t = torch.tensor(pair_dist, dtype=torch.float32, device=DEVICE)
    time_t = torch.tensor(pair_time/60.0, dtype=torch.float32, device=DEVICE)
    coords_t = torch.tensor(coords_np, dtype=torch.float32, device=DEVICE)
    priorities_np = df['Динамический критерий'].values[:n_points].astype(float)
    levels_np = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    priorities_t = torch.tensor(priorities_np, dtype=torch.float32, device=DEVICE)
    levels_t = torch.tensor(levels_np, dtype=torch.float32, device=DEVICE)

    input_size = dist_t.numel() + time_t.numel() + coords_t.numel() + priorities_t.numel() + levels_t.numel() + n_points * 2
    eval_net = DQN(input_size, n_points).to(DEVICE)
    eval_net.load_state_dict(model.state_dict())
    eval_net.eval()

    visited = torch.zeros(n_points, dtype=torch.bool, device=DEVICE)
    cur_node = 0
    visited[cur_node] = True
    cur_time = float(WORK_START)
    tour = [cur_node.item()]
    
    with torch.no_grad():
        while visited.sum().item() < n_points:
            state = State(dist_t, time_t, coords_t, priorities_t, levels_t, visited, torch.tensor(cur_time, device=DEVICE))
            flat_state = flatten_state(state, n_points).unsqueeze(0).to(DEVICE)
            qvals = eval_net(flat_state).squeeze(0)
            qvals = qvals.masked_fill(visited, -1e9)
            if qvals.max() == -1e9:
                break
            action = qvals.argmax().item()
            tour.append(action)
            
            travel_time = float(time_t[cur_node, action])
            arrival = cur_time + travel_time
            cur_time = arrival
            visited[action] = True
            cur_node = action

    tour.append(tour[0])

    full_nodes = []
    for k in range(len(tour)-1):
        a, b = tour[k], tour[k+1]
        path = pair_path[a][b]
        if path is None: continue
        if full_nodes and full_nodes[-1]==path[0]:
            full_nodes.extend(path[1:])
        else:
            full_nodes.extend(path)

    # plot
    node_xy = {n:(data['y'], data['x']) for n, data in G.nodes(data=True)}
    center = [float(coords_np[:,0].mean()), float(coords_np[:,1].mean())]
    m = folium.Map(location=center, zoom_start=12)
    for order, idx in enumerate(tour[:-1]):
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
    return tour[:-1]

def main():
    pts, df = read_points()
    model, _ = train_model(df)
    torch.save(model.state_dict(), MODEL_OUT)
    print(f"Model saved to {MODEL_OUT}")
    tour = evaluate_and_plot(model, df)
    print(f"RL Tour: {tour}")

if __name__ == "__main__":
    main()