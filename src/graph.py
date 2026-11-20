"""Dependency graph construction and reverse dependency analysis."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass,field
from repository import Package,get_package

@dataclass
class DependencyGraph:
    root:str
    adjacency:dict[str,list[str]]=field(default_factory=dict)
    depths:dict[str,int]=field(default_factory=dict)
    cycles:list[tuple[str,str]]=field(default_factory=list)
    def edges(self): return [(a,b) for a,bs in self.adjacency.items() for b in bs]

def build_dependency_graph(records:dict[str,list[Package]],root:str,max_depth:int=5,version:str|None=None)->DependencyGraph:
    if max_depth<0: raise ValueError("max_depth must be >= 0")
    pkg=get_package(records,root,version)
    graph=DependencyGraph(pkg.name,{pkg.name:[]},{pkg.name:0},[])
    queue=deque([(pkg.name,0)]); expanded=set()
    def visit():
        if not queue:return
        node,depth=queue.popleft()
        if node in expanded: visit();return
        expanded.add(node)
        if depth>=max_depth:
            graph.adjacency.setdefault(node,[]);visit();return
        deps=get_package(records,node).depends
        graph.adjacency[node]=list(deps)
        for child in deps:
            if child in graph.depths: graph.cycles.append((node,child))
            else:
                graph.depths[child]=depth+1;graph.adjacency.setdefault(child,[])
                queue.append((child,depth+1))
        visit()
    visit()
    return graph

def recursive_bfs(graph:DependencyGraph)->list[str]:
    queue,seen,order=deque([graph.root]),set(),[]
    def step():
        if not queue:return
        node=queue.popleft()
        if node not in seen:
            seen.add(node);order.append(node)
            queue.extend(x for x in graph.adjacency.get(node,[]) if x not in seen)
        step()
    step();return order

def build_reverse_graph(records:dict[str,list[Package]],target:str)->DependencyGraph:
    """Create a graph whose outgoing edges point from a dependency to its dependants."""
    reverse:dict[str,list[str]]={}
    for package_versions in records.values():
        for package in package_versions:
            for dependency in package.depends:
                reverse.setdefault(dependency,[])
                if package.name not in reverse[dependency]: reverse[dependency].append(package.name)
            reverse.setdefault(package.name,[])
    key=target
    if key not in reverse:
        matches=[x for x in reverse if x.lower()==target.lower()]
        if not matches: raise KeyError(f"No reverse dependencies found for '{target}'")
        key=matches[0]
    graph=DependencyGraph(key,{key:[]},{key:0},[])
    queue=deque([(key,0)]);seen={key}
    while queue:
        node,depth=queue.popleft()
        children=reverse.get(node,[])
        graph.adjacency[node]=list(children)
        for child in children:
            if child in seen: graph.cycles.append((node,child));continue
            seen.add(child);graph.depths[child]=depth+1
            graph.adjacency.setdefault(child,[]);queue.append((child,depth+1))
    return graph
