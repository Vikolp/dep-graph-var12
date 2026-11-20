"""Dependency graph construction with breadth-first traversal and recursion."""
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
    def edges(self): return [(a,b) for a,bs in self.adjacency.items() for b in bs]

def build_dependency_graph(records: dict[str,list[Package]], root: str, max_depth: int=5, version: str|None=None) -> DependencyGraph:
    if max_depth < 0: raise ValueError("max_depth must be >= 0")
    pkg=get_package(records,root,version)
    graph=DependencyGraph(pkg.name,{pkg.name:[]},{pkg.name:0},[])
    queue=deque([(pkg.name,0)])
    expanded=set()
    def visit():
        if not queue: return
        node,depth=queue.popleft()
        if node in expanded:
            visit(); return
        expanded.add(node)
        if depth >= max_depth:
            graph.adjacency.setdefault(node,[])
            visit(); return
        deps=get_package(records,node).depends
        graph.adjacency[node]=list(deps)
        for child in deps:
            if child in graph.depths:
                graph.cycles.append((node,child))
            else:
                graph.depths[child]=depth+1
                graph.adjacency.setdefault(child,[])
                queue.append((child,depth+1))
        visit()
    visit()
    return graph

def recursive_bfs(graph: DependencyGraph) -> list[str]:
    queue,seen,order=deque([graph.root]),set(),[]
    def step():
        if not queue: return
        node=queue.popleft()
        if node not in seen:
            seen.add(node); order.append(node)
            queue.extend(x for x in graph.adjacency.get(node,[]) if x not in seen)
        step()
    step()
    return order
