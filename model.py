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

# Haversine distance function
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

# State representation (removed current_time and current_node)
State = namedtuple('State', ['dist_matrix', 'coords', 'priorities', 'levels', 'visited'])

# GNN Model (Q-Network with message passing)
class GNNQNetwork(nn.Module):
    def __init__(self, embed_dim=128, num_iterations=3):
        super(GNNQNetwork, self).__init__()
        self.embed_dim = embed_dim
        self.num_iterations = num_iterations
        # Embed node features: coords (2), priority (1), level (1), visited (1) -> 5 dims
        self.embed = nn.Linear(5, embed_dim)
        # Message passing layers
        self.msg_linear = nn.Linear(embed_dim, embed_dim)
        self.update_linear = nn.Linear(embed_dim, embed_dim)
        # Q-value head (concat local + global embedding)
        self.q_linear = nn.Linear(2 * embed_dim, 1)

    def forward(self, state):
        # Add batch dimension if missing
        if len(state.coords.shape) == 2:  # (n, 2) -> (1, n, 2)
            state = State(
                state.dist_matrix.unsqueeze(0),
                state.coords.unsqueeze(0),
                state.priorities.unsqueeze(0),
                state.levels.unsqueeze(0),
                state.visited.unsqueeze(0)
            )

        batch_size = state.coords.shape[0]
        n = state.coords.shape[1]
        # Node features: coords + priority + level + visited
        node_feats = torch.cat([
            state.coords,  # (batch, n, 2)
            state.priorities.unsqueeze(2),  # (batch, n, 1)
            state.levels.unsqueeze(2),  # (batch, n, 1)
            state.visited.unsqueeze(2).float()  # (batch, n, 1)
        ], dim=2)  # (batch, n, 5)
        
        h = F.relu(self.embed(node_feats))  # (batch, n, embed_dim)
        
        # Edge weights: inverse distance for attention-like weighting (normalized)
        edge_weights = 1.0 / (state.dist_matrix + 1e-6)  # (batch, n, n)
        edge_weights = edge_weights / edge_weights.sum(dim=2, keepdim=True)  # Normalize
        
        for _ in range(self.num_iterations):
            # Message passing: weighted sum of neighbor embeddings
            messages = torch.bmm(edge_weights, h)  # (batch, n, embed_dim)
            h = F.relu(self.update_linear(h) + self.msg_linear(messages))
        
        # Global pooling (mean)
        global_h = h.mean(dim=1, keepdim=True).repeat(1, n, 1)  # (batch, n, embed_dim)
        
        # Q-values for each possible next node
        q_input = torch.cat([h, global_h], dim=2)  # (batch, n, 2*embed_dim)
        q = self.q_linear(q_input).squeeze(2)  # (batch, n)
        
        # Mask visited nodes
        q = q.masked_fill(state.visited, -1e10)
        
        return q

# Memory for experiences
class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
    
    def push(self, experience):
        self.memory.append(experience)
    
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        return len(self.memory)

# Training function
def train_model(model, df, n_points=15, epochs=50, batch_size=32, memory_capacity=10000, gamma=0.99, eps_start=0.9, eps_end=0.05, eps_decay=200, speed_kmh=30):
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    memory = ReplayMemory(memory_capacity)
    steps = 0
    
    # Load data
    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    priorities_np = df['Динамический критерий'].values[:n_points].astype(float)
    levels_np = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    coords_np = np.stack([lats, lons], axis=1)  # (n, 2)
    
    # Time windows in minutes
    work_start = time_to_minutes('09:00')
    work_end = time_to_minutes('18:00')
    lunch_start = time_to_minutes('13:00')
    lunch_end = time_to_minutes('14:00')
    
    # For training, generate random batches (simulate multiple instances)
    for epoch in range(epochs):
        for _ in range(batch_size):  # Simulate batch with random perturbations for training
            perturbed_coords = coords_np + np.random.normal(0, 0.01, coords_np.shape)
            dist_matrix_pert = np.zeros((n_points, n_points))
            for i in range(n_points):
                for j in range(n_points):
                    if i != j:
                        dist_matrix_pert[i, j] = haversine(perturbed_coords[i, 0], perturbed_coords[i, 1], perturbed_coords[j, 0], perturbed_coords[j, 1])
            
            batch_dist = torch.tensor(dist_matrix_pert, dtype=torch.float)  # (n, n)
            batch_coords = torch.tensor(perturbed_coords, dtype=torch.float)  # (n, 2)
            batch_priorities = torch.tensor(priorities_np, dtype=torch.float)  # (n,)
            batch_levels = torch.tensor(levels_np, dtype=torch.float)  # (n,)
            
            # Start episode
            visited = torch.zeros(n_points, dtype=torch.bool)  # (n,)
            current_node = 0  # Start from first point
            visited[current_node] = True
            current_time = float(work_start)  # Start at 9:00, as float
            
            state = State(batch_dist, batch_coords, batch_priorities, batch_levels, visited)
            
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
                
                # Compute reward
                dist = dist_matrix_pert[current_node, action]
                travel_time = (dist / speed_kmh) * 60  # minutes
                arrival_time = current_time + travel_time
                
                violation = 0
                if not (work_start <= arrival_time <= work_end and not (lunch_start <= arrival_time < lunch_end)):
                    violation = 1
                
                reward = - (dist / 10) - 10 * violation  # Normalized
                
                # Update state
                visited = visited.clone()  # To avoid modifying in place if needed
                visited[action] = True
                current_time = arrival_time
                current_node = action
                next_state = State(batch_dist, batch_coords, batch_priorities, batch_levels, visited)
                
                # Store experience
                memory.push((state, action, reward, next_state))
                
                state = next_state
                done = visited.all()
        
        # Train on batch
        if len(memory) >= batch_size:
            experiences = memory.sample(batch_size)
            states, actions, rewards, next_states = zip(*experiences)
            
            # Stack for batch processing
            batch_states = State(*[torch.stack(t) for t in zip(*[(s.dist_matrix, s.coords, s.priorities, s.levels, s.visited) for s in states])])
            batch_next_states = State(*[torch.stack(t) for t in zip(*[(s.dist_matrix, s.coords, s.priorities, s.levels, s.visited) for s in next_states])])
            batch_actions = torch.tensor(actions, dtype=torch.long)
            batch_rewards = torch.tensor(rewards, dtype=torch.float)
            
            q_current = model(batch_states).gather(1, batch_actions.unsqueeze(1)).squeeze(1)
            
            next_terminal = torch.tensor([ns.visited.all() for ns in next_states], dtype=torch.bool)
            q_next = model(batch_next_states).max(1)[0].detach()
            q_next = torch.where(next_terminal, torch.zeros_like(q_next), q_next)
            target = batch_rewards + gamma * q_next
            
            loss = F.smooth_l1_loss(q_current, target)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        
            print(f"Epoch {epoch+1}/{epochs}, Loss: {loss.item()}")
        else:
            print(f"Epoch {epoch+1}/{epochs}, Loss: N/A")

    return model

# Evaluation metrics
def evaluate_model(model, df, n_points=15, speed_kmh=30):
    # Load data (same as training)
    lats = df['Географическая широта'].values[:n_points]
    lons = df['Географическая долгота'].values[:n_points]
    priorities = df['Динамический критерий'].values[:n_points].astype(float)
    levels = (df['Уровень клиента'].values[:n_points] == 'VIP').astype(float)
    coords = np.stack([lats, lons], axis=1)
    
    dist_matrix = np.zeros((n_points, n_points))
    for i in range(n_points):
        for j in range(n_points):
            if i != j:
                dist_matrix[i, j] = haversine(lats[i], lons[i], lats[j], lons[j])
    
    # Baseline: Christofides algorithm
    G = nx.complete_graph(n_points)
    for i, j in G.edges():
        G[i][j]['weight'] = dist_matrix[i, j]
    baseline_tour = christofides(G, weight='weight')
    baseline_dist = sum(dist_matrix[baseline_tour[k], baseline_tour[k+1]] for k in range(len(baseline_tour)-1))
    
    # Model tour (greedy decode)
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
        q_values = model(state)
        next_node = q_values[0].argmax().item()
        dist = dist_matrix[current_node, next_node]
        travel_time = (dist / speed_kmh) * 60
        current_time += travel_time
        visited[next_node] = True
        current_node = next_node
        tour.append(next_node)
    
    model_dist = sum(dist_matrix[tour[k], tour[k+1]] for k in range(len(tour)-1))
    model_time = model_dist / speed_kmh
    
    # Violations
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
    
    approx_ratio = model_dist / baseline_dist if baseline_dist > 0 else 1.0
    
    metrics = {
        'total_distance_km': model_dist,
        'total_time_hours': model_time,
        'violations': violations,
        'priority_score': priority_score,
        'approx_ratio': approx_ratio,
        'model_tour': tour,
        'baseline_tour': baseline_tour,
        'baseline_distance_km': baseline_dist
    }
    
    return metrics

# Main execution
df = pd.read_csv('data.csv')
model = GNNQNetwork()
trained_model = train_model(model, df)  # Train
torch.save(trained_model.state_dict(), 'gnn_model.pth')
print("Model saved to gnn_model.pth")
metrics = evaluate_model(trained_model, df)
print("Metrics:", metrics)