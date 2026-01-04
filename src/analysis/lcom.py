from collections import deque
from typing import Dict, NamedTuple, Set

from analysis.class_info import ClassMetrics, get_methods


class LCOM(NamedTuple):
    lcom_value: float

    method_count: int
    attr_count: int

    connected_components: int
    stateless_method_count: int

    avg_attrs_per_method: float


def _build_method_graph(usage: Dict[str, frozenset[str]]) -> Dict[str, Set[str]]:
    methods = list(usage.keys())
    graph = {method: set() for method in methods}

    for i, method in enumerate(methods):
        for _method in methods[i + 1 :]:
            attrs1 = usage[method]
            attrs2 = usage[_method]

            if attrs1 & attrs2:
                graph[method].add(_method)
                graph[_method].add(method)

    return graph


def _count_connected_components(graph: Dict[str, Set[str]]) -> int:
    if not graph:
        return 0

    visited = set()
    count = 0

    for node in graph.keys():
        if node in visited:
            continue

        count += 1
        queue = deque([node])
        visited.add(node)

        while queue:
            n = queue.popleft()

            for s in graph[n]:
                if s not in visited:
                    visited.add(s)
                    queue.append(s)

    return count


def calculate_lcom(metrics: ClassMetrics) -> LCOM:
    methods = get_methods(metrics)

    usage = {
        method: attrs
        for method, attrs in metrics.method_attr_usage.items()
        if method in methods
    }

    method_count = len(usage)
    attr_count = len(metrics.instance_attrs)

    if method_count == 0 or attr_count == 0:
        return LCOM(
            lcom_value=0.0,
            method_count=method_count,
            attr_count=attr_count,
            connected_components=0,
            stateless_method_count=0,
            avg_attrs_per_method=0.0,
        )

    stateless_method_count = sum(1 for attrs in usage.values() if len(attrs) == 0)

    total_attr_uses = sum(len(attrs) for attrs in usage.values())
    avg_attrs_per_method = total_attr_uses / method_count if method_count > 0 else 0.0
    graph = _build_method_graph(usage)

    connected_components = _count_connected_components(graph)

    lcom_value = connected_components / method_count if method_count > 0 else 0.0

    return LCOM(
        lcom_value=lcom_value,
        method_count=method_count,
        attr_count=attr_count,
        connected_components=connected_components,
        stateless_method_count=stateless_method_count,
        avg_attrs_per_method=avg_attrs_per_method,
    )
