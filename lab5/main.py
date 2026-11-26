from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D
from matplotlib.patches import Patch


def load_graph(filename):
    with open(filename, encoding="utf-8") as file:
        n, directed = map(int, file.readline().split())
        if n < 0 or directed != 0:
            raise ValueError("Nagłówek musi zawierać liczbę wierzchołków i flagę 0.")

        graph = nx.empty_graph(n)
        for line in file:
            line = line.partition("#")[0].strip()
            if not line:
                continue
            u, v = map(int, line.split())
            if u not in graph or v not in graph or u == v:
                raise ValueError(f"Nieprawidłowa krawędź: {u} {v}.")
            graph.add_edge(u, v)
    return graph


def tarjan_undirected(graph):
    if graph.is_directed() or graph.is_multigraph() or nx.number_of_selfloops(graph):
        raise ValueError("Algorytm wymaga prostego grafu nieskierowanego.")

    disc = {}
    low = {}
    blocks = []
    articulation = set()
    bridges = []
    for root in graph:
        if root in disc:
            continue
        disc[root] = low[root] = len(disc)
        if not graph[root]:
            blocks.append(({root}, []))
            continue

        root_children = 0
        pending_edges = []
        stack = [(root, iter(graph[root]))]
        while stack:
            u, neighbors = stack[-1]
            parent = stack[-2][0] if len(stack) > 1 else None
            v = next(neighbors, None)

            if v is not None:
                if v not in disc:
                    if parent is None:
                        root_children += 1
                    pending_edges.append((u, v))
                    disc[v] = low[v] = len(disc)
                    stack.append((v, iter(graph[v])))
                elif v != parent and disc[v] < disc[u]:
                    pending_edges.append((u, v))
                    low[u] = min(low[u], disc[v])
                continue

            stack.pop()
            if parent is None:
                break
            low[parent] = min(low[parent], low[u])
            if low[u] < disc[parent]:
                continue

            tree_edge = (parent, u)
            if low[u] > disc[parent]:
                bridges.append(tree_edge)
            if len(stack) > 1:
                articulation.add(parent)

            edges = [pending_edges.pop()]
            while edges[-1] != tree_edge:
                edges.append(pending_edges.pop())
            vertices = {vertex for edge in edges for vertex in edge}
            blocks.append((vertices, edges))

        if root_children > 1:
            articulation.add(root)

    return blocks, articulation, bridges


def build_block_cut_forest(blocks, articulation):
    forest = nx.Graph()
    forest.add_nodes_from((("cut", v), {"label": str(v)}) for v in articulation)
    for index, (vertices, _) in enumerate(blocks, start=1):
        block = ("block", index)
        forest.add_node(block, label=f"B{index}")
        forest.add_edges_from((block, ("cut", v)) for v in vertices & articulation)
    return forest


def block_colors(blocks):
    palette = plt.get_cmap("tab20")
    return {i + 1: palette(i % palette.N) for i in range(len(blocks))}


def visualize_graph(graph, blocks, articulation):
    fig, ax = plt.subplots()
    pos = nx.spring_layout(graph, seed=42)
    colors = block_colors(blocks)
    legend = []
    for index, (vertices, edges) in enumerate(blocks, start=1):
        color = colors[index]
        nx.draw_networkx_edges(
            graph, pos, edgelist=edges, edge_color=[color], width=3, ax=ax
        )
        nx.draw_networkx_nodes(
            graph, pos, nodelist=list(vertices - articulation), node_color=[color],
            edgecolors="black", ax=ax,
        )
        legend.append(Patch(facecolor=color, label=f"B{index}"))
    if articulation:
        nx.draw_networkx_nodes(
            graph, pos, nodelist=list(articulation), node_color="white",
            node_shape="D", edgecolors="black", ax=ax,
        )
        legend.append(Line2D(
            [], [], marker="D", linestyle="none", markerfacecolor="white",
            markeredgecolor="black", label="Przegub",
        ))
    nx.draw_networkx_labels(graph, pos, ax=ax)
    if legend:
        ax.legend(handles=legend)
    ax.set_title("Graf wejściowy z blokami i przegubami")
    ax.set_axis_off()
    return fig


def visualize_block_cut_forest(forest, blocks):
    fig, ax = plt.subplots()
    colors = block_colors(blocks)
    pos = nx.spring_layout(forest, seed=42)
    block_nodes = [node for node in forest if node[0] == "block"]
    cut_nodes = [node for node in forest if node[0] == "cut"]
    nx.draw_networkx_edges(forest, pos, ax=ax)
    if block_nodes:
        nx.draw_networkx_nodes(
            forest, pos, nodelist=block_nodes, node_shape="s",
            node_color=[colors[index] for _, index in block_nodes],
            edgecolors="black", ax=ax,
        )
    if cut_nodes:
        nx.draw_networkx_nodes(
            forest, pos, nodelist=cut_nodes, node_shape="D", node_color="white",
            edgecolors="black", ax=ax,
        )
    labels = nx.get_node_attributes(forest, "label")
    nx.draw_networkx_labels(forest, pos, labels=labels, ax=ax)
    ax.set_title("Las blokowo-przegubowy")
    ax.set_axis_off()
    return fig


if __name__ == "__main__":
    graph = load_graph(Path(__file__).with_name("graphs_large.txt"))
    blocks, articulation, bridges = tarjan_undirected(graph)
    forest = build_block_cut_forest(blocks, articulation)
    if max(len(graph), len(forest)) <= 300 and graph.number_of_edges() <= 500:
        visualize_graph(graph, blocks, articulation)
        visualize_block_cut_forest(forest, blocks)
        plt.show()
    else:
        print(f"Bloki: {len(blocks)}, przeguby: {len(articulation)}, mosty: {len(bridges)}")
        print(f"Składowe lasu: {nx.number_connected_components(forest)}")
        print("Pominięto rysowanie dużego grafu.")
