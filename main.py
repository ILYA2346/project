from collections import deque, defaultdict
import re
import networkx as nx
import matplotlib.pyplot as plt
from typing import List, Optional, Set, Dict, Tuple

# --- 1. Граф зависимостей (DependencyGraph) ---
class DependencyGraph:
    def __init__(self):
        self.adj: Dict[str, List[str]] = defaultdict(list)
        self.nodes: Set[str] = set()

    def add_component(self, name: str) -> None:
        self.nodes.add(name)
        if name not in self.adj:
            self.adj[name] = []

    def add_dependency(self, from_node: str, to_node: str) -> None:
        self.add_component(from_node)
        self.add_component(to_node)
        self.adj[from_node].append(to_node)

    def _compute_in_degrees(self) -> Dict[str, int]:
        in_degree = {node: 0 for node in self.nodes}
        for u in self.adj:
            for v in self.adj[u]:
                in_degree[v] += 1
        return in_degree

    def get_topological_order(self) -> Optional[List[str]]:
        in_degree = self._compute_in_degrees()
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []

        while queue:
            u = queue.popleft()
            result.append(u)
            for v in self.adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(result) == len(self.nodes):
            return result
        else:
            return None  # есть цикл

    def is_acyclic(self) -> bool:
        return self.get_topological_order() is not None


# --- 2. Анализатор (BFS + DFS с кэшем) ---
class DependencyAnalyzer:
    def __init__(self, graph: DependencyGraph):
        self.graph = graph
        self._dfs_cache: Dict[str, Set[str]] = {}

    def find_dependencies_bfs(self, start: str) -> List[List[str]]:
        if start not in self.graph.nodes:
            return []

        visited = {start}
        current_level = self.graph.adj[start]
        levels: List[List[str]] = []

        if not current_level:
            return levels

        while current_level:
            next_level_nodes = []
            for node in current_level:
                if node not in visited:
                    visited.add(node)
                    next_level_nodes.append(node)
            if not next_level_nodes:
                break
            levels.append(next_level_nodes)

            current_level = []
            for node in next_level_nodes:
                for neighbor in self.graph.adj[node]:
                    if neighbor not in visited:
                        current_level.append(neighbor)

        return levels

    def find_dependencies_dfs(self, start: str) -> Set[str]:
        if start in self._dfs_cache:
            return self._dfs_cache[start]

        visited = set()

        def dfs(node: str):
            visited.add(node)
            for neighbor in self.graph.adj[node]:
                if neighbor not in visited:
                    dfs(neighbor)

        dfs(start)
        result = visited - {start}  # убираем сам стартовый узел
        self._dfs_cache[start] = result
        return result


# --- 3. Чтение из файла (простой парсер) ---
def load_graph_from_file(filename: str) -> DependencyGraph:
    g = DependencyGraph()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # формат: "A зависит от B, C"
                match = re.match(r"^([A-Za-z0-9_]+)\s+зависит\s+от\s+(.+)$", line)
                if match:
                    from_node = match.group(1).strip()
                    deps = [d.strip() for d in match.group(2).split(",") if d.strip()]
                    for to_node in deps:
                        g.add_dependency(from_node, to_node)
    except FileNotFoundError:
        # Если файла нет — создадим пример вручную, чтобы код точно запустился
        print(f"Файл {filename} не найден. Использую пример из задания.")
        g.add_dependency("A", "B")
        g.add_dependency("A", "C")
        g.add_dependency("B", "D")
        g.add_dependency("C", "D")
        g.add_dependency("C", "E")
        g.add_dependency("E", "B")  # цикл
    return g


# --- 4. Рисование графа ---
def visualize_graph(graph: DependencyGraph, filename: str = "dependencies.png") -> None:
    G = nx.DiGraph()
    for u in graph.adj:
        for v in graph.adj[u]:
            G.add_edge(u, v)

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(10, 7))
    nx.draw(G, pos, with_labels=True, node_color="lightblue",
            edge_color="gray", arrows=True, arrowsize=20,
            node_size=2500, font_size=14, linewidths=2, edgecolors="black")
    plt.title("Граф зависимостей проекта")
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Граф сохранён в {filename}")


# --- Точка входа ---
if __name__ == "__main__":
    # Читаем зависимости из файла dependencies.txt (или используем пример, если файла нет)
    g = load_graph_from_file("dependencies.txt")
    analyzer = DependencyAnalyzer(g)

    # Топологическая сортировка (проверка на циклы)
    topo_order = g.get_topological_order()
    if topo_order is None:
        print("Обнаружен цикл: проект нельзя собрать.")
    else:
        print("Топологический порядок (порядок сборки):", topo_order)

    # BFS для A (по уровням)
    bfs_levels = analyzer.find_dependencies_bfs("A")
    print("BFS уровни зависимостей для A:", bfs_levels)

    # DFS для A (все зависимости)
    dfs_deps = analyzer.find_dependencies_dfs("A")
    print("Все зависимости (DFS) для A:", dfs_deps)

    # Рисуем граф
    visualize_graph(g, "dependencies.png")
