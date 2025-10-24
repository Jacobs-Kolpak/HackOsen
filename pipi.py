import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from math import radians, sin, cos, sqrt, atan2
import numpy as np
from collections import namedtuple
import argparse

# Haversine distance function (fallback if no API)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Parse time to minutes since midnight
def time_to_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

# State representation
State = namedtuple('State', ['dist_matrix', 'coords', 'priorities', 'levels', 'visited'])

# GNN Model
class GNNQNetwork(nn.Module):
    def __init__(self, embed_dim=128, num_iterations=3):
        super(GNNQNetwork, self).__init__()
        self.embed_dim = embed_dim
        self.num_iterations = num_iterations
        self.embed = nn.Linear(5, embed_dim)
        self.msg_linear = nn.Linear(embed_dim, embed_dim)
        self.update_linear = nn.Linear(embed_dim, embed_dim)
        self.q_linear = nn.Linear(2 * embed_dim, 1)

    def forward(self, state):
        if len(state.coords.shape) == 2:
            state = State(
                state.dist_matrix.unsqueeze(0),
                state.coords.unsqueeze(0),
                state.priorities.unsqueeze(0),
                state.levels.unsqueeze(0),
                state.visited.unsqueeze(0)
            )
        batch_size = state.coords.shape[0]
        n = state.coords.shape[1]
        node_feats = torch.cat([
            state.coords,
            state.priorities.unsqueeze(2),
            state.levels.unsqueeze(2),
            state.visited.unsqueeze(2).float()
        ], dim=2)
        h = F.relu(self.embed(node_feats))
        edge_weights = 1.0 / (state.dist_matrix + 1e-6)
        edge_weights = edge_weights / edge_weights.sum(dim=2, keepdim=True)
        for _ in range(self.num_iterations):
            messages = torch.bmm(edge_weights, h)
            h = F.relu(self.update_linear(h) + self.msg_linear(messages))
        global_h = h.mean(dim=1, keepdim=True).repeat(1, n, 1)
        q_input = torch.cat([h, global_h], dim=2)
        q = self.q_linear(q_input).squeeze(2)
        q = q.masked_fill(state.visited, -1e10)
        return q

# Function to compute route from CSV
def compute_route(csv_path, model_path='gnn_model.pth', speed_kmh=30):
    df = pd.read_csv(csv_path)
    n_points = len(df)
    
    lats = df['Географическая широта'].values
    lons = df['Географическая долгота'].values
    priorities = df['Динамический критерий'].values.astype(float)
    levels = (df['Уровень клиента'].values == 'VIP').astype(float)
    coords = np.stack([lats, lons], axis=1)
    addresses = df['Адрес объекта'].values
    
    # Compute distance matrix using haversine (or integrate Yandex if API key provided)
    dist_matrix = np.zeros((n_points, n_points))
    for i in range(n_points):
        for j in range(n_points):
            if i != j:
                dist_matrix[i, j] = haversine(lats[i], lons[i], lats[j], lons[j])
    
    model = GNNQNetwork()
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    batch_dist = torch.tensor(dist_matrix, dtype=torch.float)
    batch_coords = torch.tensor(coords, dtype=torch.float)
    batch_priorities = torch.tensor(priorities, dtype=torch.float)
    batch_levels = torch.tensor(levels, dtype=torch.float)
    visited = torch.zeros(n_points, dtype=torch.bool)
    current_node = 0
    visited[current_node] = True
    current_time = float(time_to_minutes('09:00'))
    tour = [current_node]
    
    while not visited.all():
        state = State(batch_dist, batch_coords, batch_priorities, batch_levels, visited)
        with torch.no_grad():
            q_values = model(state)
        next_node = q_values[0].argmax().item()
        dist = dist_matrix[current_node, next_node]
        travel_time = (dist / speed_kmh) * 60
        current_time += travel_time
        visited[next_node] = True
        current_node = next_node
        tour.append(next_node)
    
    route_addresses = [addresses[i] for i in tour]
    
    model_dist = sum(dist_matrix[tour[k], tour[k+1]] for k in range(len(tour)-1))
    model_time = model_dist / speed_kmh
    
    violations = 0
    curr_time = float(time_to_minutes('09:00'))
    for k in range(len(tour)-1):
        dist = dist_matrix[tour[k], tour[k+1]]
        travel_time = (dist / speed_kmh) * 60
        arrival = curr_time + travel_time
        if not (time_to_minutes('09:00') <= arrival <= time_to_minutes('18:00') and not (time_to_minutes('13:00') <= arrival < time_to_minutes('14:00'))):
            violations += 1
        curr_time = arrival
    
    priority_score = sum(priorities[i] for i in tour)
    
    return {
        'route_addresses': route_addresses,
        'total_distance_km': float(model_dist),
        'total_time_hours': float(model_time),
        'violations': violations,
        'priority_score': float(priority_score)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute optimal route from CSV using trained GNN model")
    parser.add_argument("csv_path", type=str, help="Path to the input CSV file")
    parser.add_argument("--model_path", type=str, default="gnn_model.pth", help="Path to the trained model file")
    args = parser.parse_args()
    
    result = compute_route(args.csv_path, args.model_path)
    print("Optimal Route Addresses:")
    for addr in result['route_addresses']:
        print(addr)
    print("\nMetrics:")
    print(f"Total Distance: {result['total_distance_km']} km")
    print(f"Total Time: {result['total_time_hours']} hours")
    print(f"Violations: {result['violations']}")
    print(f"Priority Score: {result['priority_score']}")