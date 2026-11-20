"""Dependency graph construction and reverse dependency analysis."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from repository import Package, get_package

@dataclass
class DependencyGraph:
    root: str
    adjacency: dict[str, list[str]] = field(default_factory=dict)
    depths: dict[str, int] = field(default_factory=dict)
    cycles: list[tuple[str, str]] = field(default_factory=list)

    def edges(self) -> list[tuple[str, str]]:
        return [(source, target) for source, targets in self.adjacency.items() for target in targets]

def _cycle_edges(adjacency: dict[str, list[str]]) -> list[tuple[str, str]]:
    """Find directed back-edges with iterative three-colour DFS."""
    state: dict[str, int] = {}
    cycles: list[tuple[str, str]] = []
    for start in adjacency:
        if state.get(start, 0):
            continue
        state[start] = 1
        stack = [(start, iter(adjacency.get(start, [])))]
        while stack:
            node, children = stack[-1]
            try:
                child = next(children)
            except StopIteration:
                state[node] = 2
                stack.pop()
                continue
            colour = state.get(child, 0)
            if colour == 1:
                cycles.append((node, child))
            elif colour == 0:
                state[child] = 1
                stack.append((child, iter(adjacency.get(child, []))))
    return cycles

def build_dependency_graph(records: dict[str, list[Package]], root: str,
                           max_depth: int = 5, version: str | None = None) -> DependencyGraph:
    """Build a breadth-first dependency graph using recursive level expansion.

    Recursing once per BFS level avoids consuming one Python stack frame per
    package, even when a level contains thousands of dependencies.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    root_package = get_package(records, root, version)
    graph = DependencyGraph(root_package.name, {root_package.name: []}, {root_package.name: 0}, [])

    def expand_level(frontier: list[tuple[str, int]]) -> None:
        if not frontier:
            return
        next_frontier: list[tuple[str, int]] = []
        for node, depth in frontier:
            if depth >= max_depth:
                continue
            try:
                package = get_package(records, node)
            except KeyError:
                # Virtual/unavailable dependency: preserve it as a terminal node.
                continue
            graph.adjacency[node] = list(package.depends)
            for child in package.depends:
                graph.adjacency.setdefault(child, [])
                if child not in graph.depths:
                    graph.depths[child] = depth + 1
                    next_frontier.append((child, depth + 1))
        expand_level(next_frontier)

    expand_level([(root_package.name, 0)])
    graph.cycles = _cycle_edges(graph.adjacency)
    return graph

def recursive_bfs(graph: DependencyGraph) -> list[str]:
    """Return BFS order with recursive processing of successive queue levels."""
    order: list[str] = []
    seen: set[str] = set()

    def visit_level(frontier: list[str]) -> None:
        if not frontier:
            return
        next_level: list[str] = []
        for node in frontier:
            if node in seen:
                continue
            seen.add(node)
            order.append(node)
            next_level.extend(graph.adjacency.get(node, []))
        visit_level(next_level)

    visit_level([graph.root])
    return order

def build_reverse_graph(records: dict[str, list[Package]], target: str) -> DependencyGraph:
    """Create a graph whose outgoing edges point from a dependency to its dependants."""
    reverse: dict[str, list[str]] = {}
    for package_versions in records.values():
        for package in package_versions:
            for dependency in package.depends:
                reverse.setdefault(dependency, [])
                if package.name not in reverse[dependency]:
                    reverse[dependency].append(package.name)
            reverse.setdefault(package.name, [])
    key = target
    if key not in reverse:
        matches = [name for name in reverse if name.lower() == target.lower()]
        if not matches:
            raise KeyError("No reverse dependencies found for '{}'".format(target))
        key = matches[0]
    graph = DependencyGraph(key, {key: []}, {key: 0}, [])
    queue = deque([(key, 0)])
    seen = {key}
    while queue:
        node, depth = queue.popleft()
        children = reverse.get(node, [])
        graph.adjacency[node] = list(children)
        for child in children:
            if child in seen:
                continue
            seen.add(child)
            graph.depths[child] = depth + 1
            graph.adjacency.setdefault(child, [])
            queue.append((child, depth + 1))
    graph.cycles = _cycle_edges(graph.adjacency)
    return graph
