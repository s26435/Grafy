import pynauty
import networkx as nx
import matplotlib.pyplot as plt


def load_graph(filename):
    with open(filename) as f:
        n, directed = map(int, f.readline().split())
        adj = {i: [] for i in range(n)}

        for line in f:
            u, v = map(int, line.split())
            adj[u].append(v)

            if not directed:
                adj[v].append(u)

    return pynauty.Graph(n, directed=bool(directed), adjacency_dict=adj)


def tarjan_undirected(g):
    n = g.number_of_vertices
    adj = g.adjacency_dict

    disc = [-1] * n
    low = [-1] * n
    time = 0

    articulation = set()
    bridges = []

    def dfs(u, parent=-1):
        nonlocal time

        disc[u] = low[u] = time
        time += 1
        children = 0

        for v in adj[u]:
            if disc[v] == -1:
                children += 1
                dfs(v, u)

                low[u] = min(low[u], low[v])

                if parent != -1 and low[v] >= disc[u]:
                    articulation.add(u)

                if low[v] > disc[u]:
                    bridges.append((u, v))

            elif v != parent:
                low[u] = min(low[u], disc[v])

        if parent == -1 and children > 1:
            articulation.add(u)

    for u in range(n):
        if disc[u] == -1:
            dfs(u)

    print("disc:", disc)
    print("low:", low)
    print("Przeguby:", sorted(articulation))
    print("Mosty:", bridges)

def visualize_graph(g):
    G = nx.DiGraph() if g.directed else nx.Graph()

    G.add_nodes_from(range(g.number_of_vertices))

    for u, neighbors in g.adjacency_dict.items():
        for v in neighbors:
            G.add_edge(u, v)

    nx.draw(
        G,
        pos=nx.spring_layout(G, seed=42),
        with_labels=True,
        node_color="lightblue",
        node_size=700,
        font_weight="bold",
        arrows=g.directed
    )

    plt.show()

def tarjan_directed(g):
    n = g.number_of_vertices
    adj = g.adjacency_dict

    disc = [-1] * n
    low = [-1] * n
    time = 0

    stack = []
    on_stack = [False] * n
    scc = []

    def dfs(u):
        nonlocal time

        disc[u] = low[u] = time
        time += 1

        stack.append(u)
        on_stack[u] = True

        for v in adj[u]:
            if disc[v] == -1:
                dfs(v)
                low[u] = min(low[u], low[v])

            elif on_stack[v]:
                low[u] = min(low[u], disc[v])

        if low[u] == disc[u]:
            component = []

            while True:
                v = stack.pop()
                on_stack[v] = False
                component.append(v)

                if v == u:
                    break

            scc.append(component)

    for u in range(n):
        if disc[u] == -1:
            dfs(u)

    print("disc:", disc)
    print("low:", low)
    print("Składowe silnej spójności:", scc)


if __name__ == "__main__":
    g = load_graph("nieskierowany.txt")

    visualize_graph(g)


    if g.directed:
        tarjan_directed(g)
    else:
        tarjan_undirected(g)