import heapq
from collections import deque
from decimal import Decimal, InvalidOperation
from pathlib import Path


def load_graph(filename):
    with open(filename, encoding="utf-8") as f:
        lines = []
        for line in f:
            line = line.partition("#")[0].strip()
            if line:
                lines.append(line)

    if len(lines) < 2:
        raise ValueError("Podaj nagłówek i czasy zadań.")

    n, directed = map(int, lines[0].split())
    if n <= 0 or directed != 1:
        raise ValueError("Nagłówek musi zawierać dodatnią liczbę zadań i flagę 1.")

    durations = list(map(Decimal, lines[1].split()))
    if len(durations) != n or any(not d.is_finite() or d <= 0 for d in durations):
        raise ValueError("Podaj po jednym dodatnim, skończonym czasie dla każdego zadania.")

    adj = {u: set() for u in range(n)}
    for line in lines[2:]:
        u, v = map(int, line.split())
        if u not in adj or v not in adj:
            raise ValueError(f"Nieznane zadanie w zależności {u} -> {v}.")
        adj[u].add(v)
    return adj, durations


def topological_order(adj, predecessors):
    indegree = [len(p) for p in predecessors]
    queue = deque(u for u in adj if indegree[u] == 0)
    order = []

    while queue:
        u = queue.popleft()
        order.append(u)
        for v in sorted(adj[u]):
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    if len(order) != len(adj):
        raise ValueError("Zależności zawierają cykl.")
    return order


def critical_path_method(adj, durations):
    n = len(adj)
    predecessors = [[] for _ in range(n)]
    for u, successors in adj.items():
        for v in successors:
            predecessors[v].append(u)

    order = topological_order(adj, predecessors)
    es = [Decimal(0)] * n
    ef = [Decimal(0)] * n
    parent = [None] * n
    for u in order:
        if predecessors[u]:
            p = max(predecessors[u], key=ef.__getitem__)
            parent[u] = p
            es[u] = ef[p]
        ef[u] = es[u] + durations[u]

    last = max(adj, key=ef.__getitem__)
    makespan = ef[last]
    ls = [Decimal(0)] * n
    lf = [Decimal(0)] * n
    for u in reversed(order):
        lf[u] = min((ls[v] for v in adj[u]), default=makespan)
        ls[u] = lf[u] - durations[u]

    path = []
    while last is not None:
        path.append(last)
        last = parent[last]
    path.reverse()

    return {
        "es": es,
        "ef": ef,
        "ls": ls,
        "lf": lf,
        "slack": [ls[u] - es[u] for u in adj],
        "path": path,
        "makespan": makespan,
    }


def schedule_earliest(cpm):
    es, ef = cpm["es"], cpm["ef"]
    busy = []
    free = []
    schedules = []

    for u in sorted(range(len(es)), key=es.__getitem__):
        while busy and busy[0][0] <= es[u]:
            _, machine = heapq.heappop(busy)
            heapq.heappush(free, machine)

        if free:
            machine = heapq.heappop(free)
        else:
            machine = len(schedules)
            schedules.append([])

        schedules[machine].append(u)
        heapq.heappush(busy, (ef[u], machine))
    return schedules


def print_results(adj, durations, cpm, schedules):
    print("Sieć AN (zadanie -> następniki):")
    for u, successors in adj.items():
        print(f"{u} -> {sorted(successors)}")

    print("\nES/EF - najwcześniejszy start/koniec, LS/LF - najpóźniejszy start/koniec")
    print(f"{'Zad.':<7}{'Czas':>10}{'ES':>10}{'EF':>10}{'LS':>10}{'LF':>10}{'Zapas':>10}")
    for u in adj:
        times = [cpm[key][u] for key in ("es", "ef", "ls", "lf", "slack")]
        print(f"{u:<7}{durations[u]:>10g}" + "".join(f"{time:>10g}" for time in times))

    print("\nŚcieżka krytyczna:", " -> ".join(map(str, cpm["path"])))
    print(f"Długość uszeregowania (długość ścieżki krytycznej): {cpm['makespan']:g}")
    print(f"Liczba wykorzystanych maszyn: {len(schedules)}")

    print("\nHarmonogram wg najwcześniejszych startów:")
    es, ef = cpm["es"], cpm["ef"]
    for machine, tasks in enumerate(schedules, start=1):
        intervals = ", ".join(
            f"zadanie {u} [{es[u]:g}, {ef[u]:g})" for u in tasks
        )
        print(f"Maszyna {machine}: {intervals}")


def main():
    filename = Path(__file__).with_name("graphs.txt")
    try:
        adj, durations = load_graph(filename)
        cpm = critical_path_method(adj, durations)
    except (OSError, ValueError, InvalidOperation) as exc:
        raise SystemExit(f"Błąd: {exc}") from None

    print_results(adj, durations, cpm, schedule_earliest(cpm))


if __name__ == "__main__":
    main()
