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

def _cycle_edges(adjacency:dict[str,list[str]])->list[tuple[str,str]]:
    state:dict[str,int]={}
    cycles=[]
    def visit(node:str)->None:
        state[node]=1
        for child in adjacency.get(node,[]):
            colour=state.get(child,0)
            if colour==1:cycles.append((node,child))
            elif colour==0:visit(child)
        state[node]=2
    for node in adjacency:
        if state.get(node,0)==0:visit(node)
    return cycles

def build_dependency_graph(records:dict[str,list[Package]],root:str,max_depth:int=5,version:str|None=None)->DependencyGraph:
    if max_depth<0:raise ValueError("max_depth must be >= 0")
    pkg=get_package(records,root,version)
    graph=DependencyGraph(pkg.name,{pkg.name:[]},{pkg.name:0},[])
    queue=deque([(pkg.name,0)]);expanded=set()
    def visit():
        if not queue:return
        node,depth=queue.popleft()
        if node in expanded:
            visit();return
        expanded.add(node)
        if depth<max_depth:
            try:
                deps=get_package(records,node).depends
            except KeyError:
                # Virtual or unavailable dependency: keep it as a terminal graph node.
                graph.adjacency.setdefault(node,[])
                visit();return
            graph.adjacency[node]=list(deps)
            for child in deps:
                graph.adjacency.setdefault(child,[])
                if child not in graph.depths:
                    graph.depths[child]=depth+1
                    queue.append((child,depth+1))
        visit()
    visit()
    graph.cycles=_cycle_edges(graph.adjacency)
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
    for versions in records.values():
        for package in versions:
            for dependency in package.depends:
                reverse.setdefault(dependency,[])
                if package.name not in reverse[dependency]:reverse[dependency].append(package.name)
            reverse.setdefault(package.name,[])
    key=target
    if key not in reverse:
        matches=[name for name in reverse if name.lower()==target.lower()]
        if not matches:raise KeyError(f"No reverse dependencies found for '{target}'")
        key=matches[0]
    graph=DependencyGraph(key,{key:[]},{key:0},[])
    queue=deque([(key,0)]);seen={key}
    while queue:
        node,depth=queue.popleft()
        children=reverse.get(node,[])
        graph.adjacency[node]=list(children)
        for child in children:
            if child in seen:continue
            seen.add(child);graph.depths[child]=depth+1
            graph.adjacency.setdefault(child,[]);queue.append((child,depth+1))
    graph.cycles=_cycle_edges(graph.adjacency)
    return graph
