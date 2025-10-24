# ant_pipeline.py

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time as dtime
import random
from geopy.distance import geodesic

# --- 1. Парсинг датасета ---
def parse_csv(filename):
    df = pd.read_csv(filename)
    addresses = df['Адрес объекта'].tolist()
    coords = list(zip(df['Географическая широта'], df['Географическая долгота']))
    time_windows = []
    for i, row in df.iterrows():
        work_start = datetime.strptime(row['Время начала рабочего дня'], "%H:%M").time()
        work_end = datetime.strptime(row['Время окончания рабочего дня'], "%H:%M").time()
        lunch_start = datetime.strptime(row['Время начала обеда'], "%H:%M").time()
        lunch_end = datetime.strptime(row['Время окончания обеда'], "%H:%M").time()
        time_windows.append([
            (work_start, lunch_start),
            (lunch_end, work_end)
        ])
    priorities = df['Динамический критерий'].astype(int).tolist()
    priorities = [p + (5 if lvl == 'VIP' else 0) for p, lvl in zip(priorities, df['Уровень клиента'])]
    return addresses, coords, time_windows, priorities

# --- 2. Выбор подмножества точек для теста ---
def get_sample_indices(n, sample_size=15):
    return sorted(random.sample(range(n), sample_size))

# --- 3. Матрица расстояний через geopy ---
def get_distance_matrix_geopy(coords):
    n = len(coords)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = np.inf
            else:
                # Пример: 2 минуты на 1 км
                matrix[i][j] = geodesic(coords[i], coords[j]).km * 2
    return matrix

# --- 4. ACO с учётом окон и приоритетов ---
class AntColony:
    def __init__(
        self,
        distance_matrix,
        time_windows,
        priorities,
        n_ants=20,
        n_best=5,
        n_iterations=100,
        decay=0.95,
        alpha=1,
        beta=2,
        penalty_window=20,
        pheromone_priority_boost=2
    ):
        self.distance_matrix = distance_matrix
        self.time_windows = time_windows
        self.priorities = priorities
        self.n_ants = n_ants
        self.n_best = n_best
        self.n_iterations = n_iterations
        self.decay = decay
        self.alpha = alpha
        self.beta = beta
        self.penalty_window = penalty_window
        self.pheromone_priority_boost = pheromone_priority_boost
        self.pheromone = np.ones(self.distance_matrix.shape) / len(distance_matrix)

    def run(self, start_time=None):
        shortest_path = None
        all_time_shortest_path = ("placeholder", np.inf)
        for i in range(self.n_iterations):
            all_paths = self.gen_all_paths(start_time)
            self.spread_pheromone(all_paths, self.n_best)
            shortest_path = min(all_paths, key=lambda x: x[1])
            if shortest_path[1] < all_time_shortest_path[1]:
                all_time_shortest_path = shortest_path
            self.pheromone *= self.decay
        return all_time_shortest_path

    def gen_path(self, start, start_time=None):
        path = []
        visited = set()
        visited.add(start)
        prev = start
        current_time = start_time or dtime(9, 0)
        for _ in range(len(self.distance_matrix) - 1):
            move = self.pick_move(self.pheromone[prev], self.distance_matrix[prev], visited)
            path.append((prev, move))
            windows = self.time_windows[move]
            arrival_time = (datetime.combine(datetime.today(), current_time) +
                            timedelta(minutes=self.distance_matrix[prev][move])).time()
            penalty = 0
            if not any(w[0] <= arrival_time <= w[1] for w in windows):
                penalty += self.penalty_window
            current_time = (datetime.combine(datetime.today(), arrival_time) +
                            timedelta(minutes=penalty)).time()
            prev = move
            visited.add(move)
        path.append((prev, start))  # возврат к старту
        return path

    def gen_all_paths(self, start_time=None):
        all_paths = []
        for i in range(self.n_ants):
            path = self.gen_path(random.randint(0, len(self.distance_matrix) - 1), start_time)
            all_paths.append((path, self.path_length(path, start_time)))
        return all_paths

    def path_length(self, path, start_time=None):
        total = 0
        current_time = start_time or dtime(9, 0)
        for move in path:
            from_idx, to_idx = move
            travel_time = self.distance_matrix[from_idx][to_idx]
            windows = self.time_windows[to_idx]
            arrival_time = (datetime.combine(datetime.today(), current_time) +
                            timedelta(minutes=travel_time)).time()
            penalty = 0
            if not any(w[0] <= arrival_time <= w[1] for w in windows):
                penalty += self.penalty_window
            total += travel_time + penalty
            current_time = (datetime.combine(datetime.today(), arrival_time) +
                            timedelta(minutes=penalty)).time()
        return total

    def pick_move(self, pheromone, dist, visited):
        pheromone = np.copy(pheromone)
        pheromone[list(visited)] = 0
        priority_weights = np.array(self.priorities)
        pheromone = pheromone * (1 + (priority_weights / max(priority_weights)) * (self.pheromone_priority_boost - 1))
        row = pheromone ** self.alpha * ((1.0 / dist) ** self.beta)
        row[list(visited)] = 0
        norm_row = row / row.sum()
        move = np.random.choice(range(len(pheromone)), 1, p=norm_row)[0]
        return move

    def spread_pheromone(self, all_paths, n_best):
        sorted_paths = sorted(all_paths, key=lambda x: x[1])
        for path, length in sorted_paths[:n_best]:
            for move in path:
                from_idx, to_idx = move
                boost = 1 + (self.priorities[to_idx] / max(self.priorities)) * (self.pheromone_priority_boost - 1)
                self.pheromone[from_idx][to_idx] += boost / self.distance_matrix[from_idx][to_idx]

# --- 5. Метрики ---
def calc_metrics(path, time_windows, priorities, penalty_window):
    total_points = len(time_windows)
    on_time_count = 0
    priority_points = [i for i, p in enumerate(priorities) if p == max(priorities)]
    early_priority_hits = 0
    N = min(5, total_points)
    current_time = dtime(9, 0)
    for idx, move in enumerate(path):
        from_idx, to_idx = move
        windows = time_windows[to_idx]
        arrival_time = (datetime.combine(datetime.today(), current_time) +
                        timedelta(minutes=10)).time()  # 10 мин — пример, замени на реальное время
        if any(w[0] <= arrival_time <= w[1] for w in windows):
            on_time_count += 1
        if idx < N and to_idx in priority_points:
            early_priority_hits += 1
        current_time = arrival_time
    on_time_ratio = on_time_count / total_points
    priority_ratio = early_priority_hits / len(priority_points) if priority_points else 0
    return {
        "on_time_ratio": on_time_ratio,
        "priority_ratio": priority_ratio
    }

# --- 6. Запуск ---
if __name__ == "__main__":
    filename = "ant/dataset.csv"
    addresses, coords, time_windows, priorities = parse_csv(filename)
    print("Загружено точек:", len(addresses))

    sample_size = 15
    sample_indices = get_sample_indices(len(coords), sample_size)
    sample_coords = [coords[i] for i in sample_indices]
    sample_addresses = [addresses[i] for i in sample_indices]
    sample_time_windows = [time_windows[i] for i in sample_indices]
    sample_priorities = [priorities[i] for i in sample_indices]

    print(f"Используем {sample_size} точек для маршрутизации.")
    print("Получаем матрицу расстояний через geopy...")
    distance_matrix = get_distance_matrix_geopy(sample_coords)
    print("Матрица готова. Запускаем ACO...")

    aco = AntColony(
        distance_matrix,
        sample_time_windows,
        sample_priorities,
        n_ants=20,
        n_best=5,
        n_iterations=100,
        decay=0.95,
        alpha=1,
        beta=2,
        penalty_window=20,
        pheromone_priority_boost=2
    )
    shortest_path, length = aco.run(start_time=dtime(9, 0))
    print("Самый короткий маршрут (индексы точек):", shortest_path)
    print("Длина маршрута:", length)
    metrics = calc_metrics(shortest_path, sample_time_windows, sample_priorities, 20)
    print("Метрики:", metrics)
    print("Адреса точек в маршруте:")
    for from_idx, to_idx in shortest_path:
        print(f"{sample_addresses[from_idx]} -> {sample_addresses[to_idx]}")
