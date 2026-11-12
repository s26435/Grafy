import heapq
from collections import deque

import pynauty
import networkx as nx
import matplotlib.pyplot as plt

EPS = 1e-9

def load_graph(filename):
    with open(filename, encoding="utf-8") as f:
        lines = [line.split("#", 1)[0].strip() for line in f]
    lines = [line for line in lines if line]

    if len(lines) < 2:
        raise ValueError("")

    n, directed = map(int, lines[0].split())
    if n <= 0 or directed != 1:
        raise ValueError("")

    durations = list(map(float, lines[1].split()))
    if len(durations) != n or any(d <= 0 for d in durations):
        raise ValueError("")

    adj = {i: set() for i in range(n)}
    for line in lines[2:]:
        u, v = map(int, line.split())
        if not (0 <= u < n and 0 <= v < n):
            raise ValueError(f"{u} -> {v}")
        adj[u].add(v)

    g = pynauty.Graph(n, directed=True, adjacency_dict=adj)
    return g, durations


def topological_order(g):
    n = g.number_of_vertices
    adj = g.adjacency_dict
    indegree = [0] * n
    for u in range(n):
        for v in adj[u]:
            indegree[v] += 1

    queue = deque(i for i in range(n) if indegree[i] == 0)
    order = []

    while queue:
        u = queue.popleft()
        order.append(u)
        for v in sorted(adj[u]):
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    if len(order) != n:
        raise ValueError("")
    return order


def critical_path_method(g, durations):
    n = g.number_of_vertices
    adj = g.adjacency_dict
    order = topological_order(g)

    predecessors = [[] for _ in range(n)]
    for u in range(n):
        for v in adj[u]:
            predecessors[v].append(u)

    es = [0.0] * n
    ef = [0.0] * n
    parent = [None] * n
    for u in order:
        if predecessors[u]:
            parent[u] = max(predecessors[u], key=lambda p: ef[p])
            es[u] = ef[parent[u]]
        ef[u] = es[u] + durations[u]

    makespan = max(ef)

    ls = [0.0] * n
    lf = [0.0] * n
    for u in reversed(order):
        lf[u] = min(ls[v] for v in adj[u]) if adj[u] else makespan
        ls[u] = lf[u] - durations[u]

    slack = [ls[u] - es[u] for u in range(n)]

    last = max(range(n), key=lambda u: ef[u])
    path = []
    while last is not None:
        path.append(last)
        last = parent[last]
    path.reverse()

    return {
        "order": order,
        "predecessors": predecessors,
        "es": es,
        "ef": ef,
        "ls": ls,
        "lf": lf,
        "slack": slack,
        "path": path,
        "makespan": makespan,
    }


def schedule_earliest(cpm):
    tasks = sorted(range(len(cpm["es"])), key=lambda u: (cpm["es"][u], u))
    busy = []             
    free_machines = []
    assigned = {}
    machine_count = 0

    for u in tasks:
        start = cpm["es"][u]
        while busy and busy[0][0] <= start + EPS:
            _, machine = heapq.heappop(busy)
            heapq.heappush(free_machines, machine)

        if free_machines:
            machine = heapq.heappop(free_machines)
        else:
            machine_count += 1
            machine = machine_count

        assigned[u] = machine
        heapq.heappush(busy, (cpm["ef"][u], machine))

    return assigned, machine_count


def print_results(g, durations, cpm, assigned, machine_count):
    print("\nCzasy zadań (AN / CPM):")
    print(f"{'Zad.':<7}{'Czas':>7}{'ES':>8}{'EF':>8}{'LS':>8}{'LF':>8}{'Zapas':>9}{'Maszyna':>10}")
    for u in range(g.number_of_vertices):
        print(
            f"{u:<7}{durations[u]:>7g}"
            f"{cpm['es'][u]:>8g}{cpm['ef'][u]:>8g}"
            f"{cpm['ls'][u]:>8g}{cpm['lf'][u]:>8g}"
            f"{cpm['slack'][u]:>9g}{assigned[u]:>10}"
        )

    print("\nZadania krytyczne:", [u for u, s in enumerate(cpm["slack"]) if abs(s) < EPS])
    print("Ścieżka krytyczna:", " -> ".join(map(str, cpm["path"])))
    print(f"Długość ścieżki krytycznej: {cpm['makespan']:g}")
    print(f"Długość harmonogramu: {max(cpm['ef']):g}")
    print(f"Liczba wykorzystanych maszyn: {machine_count}")

    print("\nHarmonogram wg najwcześniejszych startów:")
    for u in sorted(assigned, key=lambda i: (cpm["es"][i], assigned[i], i)):
        print(f"Zadanie {u}: maszyna {assigned[u]}, [{cpm['es'][u]:g}, {cpm['ef'][u]:g})")


def visualize_graph(g, durations, cpm):
    G = nx.DiGraph()
    G.add_nodes_from(range(g.number_of_vertices))
    for u, neighbors in g.adjacency_dict.items():
        for v in neighbors:
            G.add_edge(u, v)

    layer = {}
    for u in cpm["order"]:
        layer[u] = 1 + max((layer[p] for p in cpm["predecessors"][u]), default=-1)
    nx.set_node_attributes(G, layer, "layer")
    pos = nx.multipartite_layout(G, subset_key="layer", align="vertical")

    critical = {u for u, s in enumerate(cpm["slack"]) if abs(s) < EPS}
    critical_edges = {
        (u, v) for u, v in G.edges
        if u in critical and v in critical
        and abs(cpm["ef"][u] - cpm["es"][v]) < EPS
    }
    node_colors = ["salmon" if u in critical else "lightblue" for u in G.nodes]
    edge_colors = ["firebrick" if e in critical_edges else "gray" for e in G.edges]
    labels = {u: f"{u}\nczas: {durations[u]:g}" for u in G.nodes}

    plt.figure(figsize=(11, 6))
    nx.draw_networkx(
        G, pos, labels=labels,
        node_color=node_colors, node_size=1700,
        edge_color=edge_colors, width=2, arrows=True,
        arrowsize=20, font_size=10, font_weight="bold",
    )
    plt.title("Sieć AN (czerwone zadania i krawędzie są krytyczne)")
    plt.axis("off")
    plt.tight_layout()


def visualize_schedule(durations, cpm, assigned, machine_count):
    fig, ax = plt.subplots(figsize=(11, max(3, machine_count * 0.6 + 1)))
    for u in sorted(assigned, key=lambda u: (assigned[u], cpm["es"][u])):
        machine = assigned[u]
        color = "salmon" if abs(cpm["slack"][u]) < EPS else "lightblue"
        ax.barh(machine, durations[u], left=cpm["es"][u], height=0.6,
                color=color, edgecolor="black")
        ax.text(cpm["es"][u] + durations[u] / 2, machine,
                str(u), ha="center", va="center", fontsize=10)

    ax.set_yticks(range(1, machine_count + 1))
    ax.set_yticklabels([f"Maszyna {m}" for m in range(1, machine_count + 1)])
    ax.set_xlim(0, cpm["makespan"] * 1.05)
    ax.set_xlabel("Czas")
    ax.set_title("Harmonogram (starty ES, czerwone = zadania krytyczne)")
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    fig.tight_layout()


def main():
    filename = "graphs.txt"
    g, durations = load_graph(filename)
    cpm = critical_path_method(g, durations)
    assigned, machine_count = schedule_earliest(cpm)
    print_results(g, durations, cpm, assigned, machine_count)
    visualize_graph(g, durations, cpm)
    visualize_schedule(durations, cpm, assigned, machine_count)
    plt.show()


if __name__ == "__main__":
    main()
