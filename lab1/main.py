from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx
import pynauty


CASES = {
    "a": {
        "title": "Dwa grafy izomorficzne przedstawione inaczej",
        "n": 6,
        "G": [
            (0, 2), (0, 4), (1, 2), (1, 4),
            (1, 5), (2, 3), (2, 5), (3, 5),
        ],
        "H": [
            (0, 2), (0, 3), (0, 5), (1, 2),
            (1, 5), (2, 5), (3, 4), (4, 5),
        ],
    },
    "b": {
        "title": "Grafy o różnych sekwencjach stopni",
        "n": 5,
        "G": [(0, 1), (1, 2), (2, 3), (3, 4)],
        "H": [(0, 1), (0, 2), (0, 3), (0, 4)],
    },
    "c": {
        "title": "Ta sama sekwencja stopni, ale grafy nieizomorficzne",
        "n": 6,
        "G": [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)],
        "H": [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)],
    },
}


def adjacency_dict(n, edges):
    """Zwraca słownik sąsiedztwa wymagany przez pynauty."""
    adj = {v: [] for v in range(n)}
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    for v in adj:
        adj[v].sort()
    return adj


def degree_sequence(n, edges):
    """Oblicza posortowaną malejąco sekwencję stopni."""
    adj = adjacency_dict(n, edges)
    return sorted((len(adj[v]) for v in range(n)), reverse=True)


def graph_repr(n, edges):
    """Czytelna reprezentacja grafu do wypisania w terminalu."""
    adj = adjacency_dict(n, edges)
    return "{ " + ", ".join(f"{v}: {adj[v]}" for v in range(n)) + " }"

def to_pynauty_graph(n, edges, coloring=None):
    kwargs = {
        "number_of_vertices": n,
        "directed": False,
        "adjacency_dict": adjacency_dict(n, edges),
    }

    if coloring is not None:
        kwargs["vertex_coloring"] = coloring

    return pynauty.Graph(**kwargs)


def canonical_certificate(n, edges, coloring=None):
    g = to_pynauty_graph(n, edges, coloring)
    return pynauty.certificate(g)


def are_isomorphic(n, edges_g, edges_h):
    if n < 0:
        return False
    return canonical_certificate(n, edges_g) == canonical_certificate(n, edges_h)


def coloring_for_partial_mapping(n, ordered_vertices):
    singled = [{v} for v in ordered_vertices]
    rest = set(range(n)) - set(ordered_vertices)

    if rest:
        singled.append(rest)

    return singled


def find_isomorphism(n, edges_g, edges_h):
    if not are_isomorphic(n, edges_g, edges_h):
        return None

    mapping = {}
    used_h = set()

    for u in range(n):
        found = False

        for v in range(n):
            if v in used_h:
                continue

            ordered_g = list(mapping.keys()) + [u]
            ordered_h = list(mapping.values()) + [v]

            coloring_g = coloring_for_partial_mapping(n, ordered_g)
            coloring_h = coloring_for_partial_mapping(n, ordered_h)

            cert_g = canonical_certificate(n, edges_g, coloring_g)
            cert_h = canonical_certificate(n, edges_h, coloring_h)

            if cert_g == cert_h:
                mapping[u] = v
                used_h.add(v)
                found = True
                break

        if not found:
            raise RuntimeError("dupa")

    return mapping


def draw_pair(case_name, case, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for graph_name in ("G", "H"):
        G = nx.Graph()
        G.add_nodes_from(range(case["n"]))
        G.add_edges_from(case[graph_name])

        pos = nx.spring_layout(G, seed=42)

        plt.figure(figsize=(5, 4))
        nx.draw(
            G,
            pos,
            with_labels=True,
            node_size=900,
            font_size=12,
            width=1.8,
        )
        plt.title(f"Przypadek {case_name}: graf {graph_name}")
        plt.tight_layout()
        plt.savefig(
            output_dir / f"case_{case_name}_{graph_name}.png",
            dpi=200,
            bbox_inches="tight",
        )
        plt.close()


def draw_all_cases(output_dir=Path("diagrams")):
    for name, case in CASES.items():
        draw_pair(name, case, output_dir)


def run_case(name, case):
    n = case["n"]
    edges_g = case["G"]
    edges_h = case["H"]

    deg_g = degree_sequence(n, edges_g)
    deg_h = degree_sequence(n, edges_h)
    iso = are_isomorphic(n, edges_g, edges_h)

    print("=" * 78)
    print(f"PRZYPADEK {name.upper()}: {case['title']}")
    print("=" * 78)
    print("G =", graph_repr(n, edges_g))
    print("H =", graph_repr(n, edges_h))
    print(f"Seq(G) = {deg_g}")
    print(f"Seq(H) = {deg_h}")
    print(f"Izomorficzne: {'TAK' if iso else 'NIE'}")

    if iso:
        mapping = find_isomorphism(n, edges_g, edges_h)
        formatted = ", ".join(f"{u} -> {v}" for u, v in mapping.items())
        print("Izomorfizm f:", formatted)

    print()


def main():
    draw_all_cases(Path("diagrams"))

    try:
        import pynauty
    except ImportError as exc:
        raise SystemExit(
            "Brak biblioteki pynauty.\n"
            "Zainstaluj zależności poleceniem:\n"
            "    pip install pynauty networkx matplotlib\n"
        ) from exc

    print("Wersja pynauty / nauty:", pynauty.Version())
    print()

    for name, case in CASES.items():
        run_case(name, case)

    print("Diagramy zapisano w katalogu: diagrams/")


if __name__ == "__main__":
    main()