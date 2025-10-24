import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from math import radians, sin, cos, sqrt, atan2
import numpy as np
from collections import namedtuple, deque
import random
import networkx as nx
from networkx.algorithms.approximation.traveling_salesman import christofides
import folium
import webbrowser
from datetime import datetime

# ========== НАСТРОЙКИ ==========
USE_YANDEX_API = False
SPEED_KMH = 30
WORK_START = '09:00'
WORK_END = '18:00'
LUNCH_START = '13:00'
LUNCH_END = '14:00'
# ===============================

# --- Haversine ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# --- Offline Distance Matrix ---
def get_yandex_dist_matrix(lats, lons, api_key=None, mode='driving', departure_time=None, speed_kmh=SPEED_KMH):
    n = len(lats)
    dist_matrix = np.zeros((n, n))
    time_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                d = haversine(lats[i], lons[i], lats[j], lons[j])
                dist_matrix[i, j] = d
                time_matrix[i, j] = (d / speed_kmh) * 60  # мин
    return dist_matrix, time_matrix

def time_to_minutes(t):
    h, m = map(int, t.split(':'))
    return h * 60 + m

State = namedtuple('State', ['dist_matrix', 'time_matrix', 'coords', 'priorities', 'levels', 'visited', 'current_time'])

# --- Improved GNN ---
class ImprovedGNNQNetwork(nn.Module):
    def __init__(self, embed_dim=128, num_heads=4, num_iterations=5):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_iterations = num_iterations
        self.embed = nn.Linear(6, embed_dim)
        self.attn_layers = nn.ModuleList([
            nn.MultiheadAttention(embed_dim, num_heads, dropout=0.1)
            for _ in range(num_iterations)
        ])
        self.gate = nn.GRUCell(embed_dim, embed_dim)
        self.q_linear = nn.Linear(2 * embed_dim, 1)

    def forward(self, state):
        if len(state.coords.shape) == 2:
            state = State(
                state.dist_matrix.unsqueeze(0),
                state.time_matrix.unsqueeze(0),
                state.coords.unsqueeze(0),
                state.priorities.unsqueeze(0),
                state.levels.unsqueeze(0),
                state.visited.unsqueeze(0),
                torch.tensor([state.current_time])
            )
        batch_size = state.coords.shape[0]
        n = state.coords.shape[1]

        norm_time = (state.current_time - time_to_minutes(WORK_START)) / (
            time_to_minutes(WORK_END) - time_to_minutes(WORK_START)
        )
        norm_time = norm_time.view(batch_size, 1, 1).repeat(1, n, 1).to(torch.float32)

        node_feats = torch.cat([
            state.coords.to(torch.float32),
            state.priorities.unsqueeze(2).to(torch.float32),
            state.levels.unsqueeze(2).to(torch.float32),
            state.visited.unsqueeze(2).float(),
            norm_time
        ], dim=2)

        h = F.relu(self.embed(node_feats))
        h = h.transpose(0, 1)

        for attn in self.attn_layers:
            h_attn, _ = attn(h, h, h)
            messages = h_attn.transpose(0, 1)
            h = self.gate(messages.reshape(-1, self.embed_dim),
                          h.transpose(0, 1).reshape(-1, self.embed_dim))
            h = h.view(batch_size, n, self.embed_dim).transpose(0, 1)

        h = h.transpose(0, 1)
        global_h = h.mean(dim=1, keepdim=True).repeat(1, n, 1)
        q_input = torch.cat([h, global_h], dim=2)
        q = self.q_linear(q_input).squeeze(2)
        q = q.masked_fill(state.visited, -1e10)
        return q

class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
    def push(self, x):
        self.memory.append(x)
    def sample(self, n):
        return random.sample(self.memory, n)
    def __len__(self):
        return len(self.memory)

# --- TRAIN ---
def train_model(model, df, api_key=None, n_points=10, epochs=50, batch_size=32, memory_capacity=2000, gamma=0.99,
                eps_start=0.9, eps_end=0.05, eps_decay=300, speed_kmh=SPEED_KMH):
    optimizer = optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    memory = ReplayMemory(memory_capacity)
    steps = 0

    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    priorities = df['Динамический критерий'].values[:n_points].astype(float)
    levels = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    coords = np.stack([lats, lons], axis=1)

    dist_matrix, time_matrix = get_yandex_dist_matrix(lats, lons)
    max_dist = dist_matrix.max() * 2
    work_start, work_end = time_to_minutes(WORK_START), time_to_minutes(WORK_END)
    lunch_start, lunch_end = time_to_minutes(LUNCH_START), time_to_minutes(LUNCH_END)

    for epoch in range(epochs):
        for _ in range(batch_size):
            visited = torch.zeros(n_points, dtype=torch.bool)
            current_node = 0
            visited[current_node] = True
            current_time = float(work_start)

            state = State(
                torch.tensor(dist_matrix, dtype=torch.float32),
                torch.tensor(time_matrix, dtype=torch.float32),
                torch.tensor(coords, dtype=torch.float32),
                torch.tensor(priorities, dtype=torch.float32),
                torch.tensor(levels, dtype=torch.float32),
                visited,
                current_time
            )

            done = False
            while not done:
                steps += 1
                eps = eps_end + (eps_start - eps_end) * np.exp(-steps / eps_decay)
                q_values = model(state)
                if random.random() < eps:
                    available = [i for i in range(n_points) if not visited[i]]
                    action = random.choice(available) if available else None
                else:
                    action = q_values[0].argmax().item()
                if action is None:
                    break

                dist = dist_matrix[current_node, action]
                travel_time = time_matrix[current_node, action]
                arrival_time = current_time + travel_time

                violation = 0
                if not (work_start <= arrival_time <= work_end and not (lunch_start <= arrival_time < lunch_end)):
                    violation = 1

                reward = - (dist / max_dist) - 5 * violation + 2 * levels[action] + priorities[action] / 5
                visited = visited.clone()
                visited[action] = True
                current_time = arrival_time
                current_node = action
                next_state = State(state.dist_matrix, state.time_matrix, state.coords, state.priorities, state.levels, visited, current_time)
                memory.push((state, action, reward, next_state))
                state = next_state
                done = visited.all()

        if len(memory) >= batch_size:
            experiences = memory.sample(batch_size)
            states, actions, rewards, next_states = zip(*experiences)
            batch_states = State(
                torch.stack([s.dist_matrix for s in states]),
                torch.stack([s.time_matrix for s in states]),
                torch.stack([s.coords for s in states]),
                torch.stack([s.priorities for s in states]),
                torch.stack([s.levels for s in states]),
                torch.stack([s.visited for s in states]),
                torch.tensor([s.current_time for s in states])
            )
            batch_next_states = State(
                torch.stack([s.dist_matrix for s in next_states]),
                torch.stack([s.time_matrix for s in next_states]),
                torch.stack([s.coords for s in next_states]),
                torch.stack([s.priorities for s in next_states]),
                torch.stack([s.levels for s in next_states]),
                torch.stack([s.visited for s in next_states]),
                torch.tensor([s.current_time for s in next_states])
            )
            batch_actions = torch.tensor(actions, dtype=torch.long)
            batch_rewards = torch.tensor(rewards, dtype=torch.float)

            q_current = model(batch_states).gather(1, batch_actions.unsqueeze(1)).squeeze(1)
            q_next = model(batch_next_states).max(1)[0].detach()
            target = batch_rewards + gamma * q_next
            loss = F.smooth_l1_loss(q_current, target)

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        print(f"Epoch {epoch+1}/{epochs} done ✅")

    return model

# --- Evaluate + Plot ---
def evaluate_and_plot(model, df, output_file='route_map.html', n_points=10):
    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    priorities = df['Динамический критерий'].values[:n_points].astype(float)
    levels = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    coords = np.stack([lats, lons], axis=1)
    dist_matrix, time_matrix = get_yandex_dist_matrix(lats, lons)

    visited = torch.zeros(n_points, dtype=torch.bool)
    current_node = 0
    visited[current_node] = True
    current_time = float(time_to_minutes(WORK_START))
    tour = [current_node]

    while not visited.all():
        state = State(
            torch.tensor(dist_matrix, dtype=torch.float32),
            torch.tensor(time_matrix, dtype=torch.float32),
            torch.tensor(coords, dtype=torch.float32),
            torch.tensor(priorities, dtype=torch.float32),
            torch.tensor(levels, dtype=torch.float32),
            visited,
            current_time
        )
        q_values = model(state)
        next_node = q_values[0].argmax().item()
        current_time += time_matrix[current_node, next_node]
        visited[next_node] = True
        tour.append(next_node)
        current_node = next_node

    print("Маршрут:", tour)

    # --- Рисуем карту ---
    start_lat, start_lon = lats[tour[0]], lons[tour[0]]
    route_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

    for i, idx in enumerate(tour):
        folium.Marker(
            [lats[idx], lons[idx]],
            popup=f"Точка {i+1}: {df.iloc[idx]['Адрес'] if 'Адрес' in df.columns else idx}",
            icon=folium.Icon(color="green" if i == 0 else "blue")
        ).add_to(route_map)

    path = [[lats[i], lons[i]] for i in tour]
    folium.PolyLine(path, color="red", weight=3, opacity=0.8).add_to(route_map)

    route_map.save(output_file)
    print(f"✅ Карта сохранена в {output_file}")
    webbrowser.open(output_file)

# --- MAIN ---
if __name__ == "__main__":
    df = pd.read_csv('data.csv')
    model = ImprovedGNNQNetwork()
    trained = train_model(model, df)
    torch.save(trained.state_dict(), 'gnn_model_offline.pth')
    print("✅ Модель сохранена.")
    evaluate_and_plot(trained, df)
