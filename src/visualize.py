"""PlantUML and terminal visualizations."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from graph import DependencyGraph

def _alias(index:int)->str:
    return f"pkg_{index}"

def to_plantuml(graph:DependencyGraph)->str:
    nodes=sorted(graph.adjacency)
    aliases={name:_alias(i) for i,name in enumerate(nodes)}
    lines=["@startuml","left to right direction","skinparam packageStyle rectangle"]
    for name in nodes:
        label=name.replace("\\","\\\\").replace('"','\\"')
        lines.append(f'package "{label}" as {aliases[name]}')
    for source,target in graph.edges():
        if target in aliases:
            lines.append(f"{aliases[source]} --> {aliases[target]}")
    lines.append("@enduml")
    return "\n".join(lines)+"\n"

def save_plantuml(graph:DependencyGraph,output_dir:str|Path="output")->Path:
    directory=Path(output_dir);directory.mkdir(parents=True,exist_ok=True)
    safe="".join(c if c.isalnum() or c in "-_" else "_" for c in graph.root)
    path=directory/f"{safe}_deps.puml"
    path.write_text(to_plantuml(graph),encoding="utf-8")
    return path

def render_plantuml(path:str|Path)->Path|None:
    executable=shutil.which("plantuml")
    if not executable:return None
    source=Path(path)
    result=subprocess.run([executable,"-tsvg",str(source)],capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "PlantUML rendering failed")
    rendered=source.with_suffix(".svg")
    return rendered if rendered.exists() else None

def to_ascii_tree(graph:DependencyGraph)->str:
    lines=[graph.root]
    expanded=set()
    def walk(node:str,prefix:str,ancestors:set[str])->None:
        children=graph.adjacency.get(node,[])
        for index,child in enumerate(children):
            last=index==len(children)-1
            branch="└── " if last else "├── "
            if child in ancestors:
                suffix=" (cycle)"
            elif child in expanded:
                suffix=" (already shown)"
            else:
                suffix=""
            lines.append(prefix+branch+child+suffix)
            if not suffix:
                expanded.add(child)
                walk(child,prefix+("    " if last else "│   "),ancestors|{child})
    expanded.add(graph.root)
    walk(graph.root,"",{graph.root})
    return "\n".join(lines)
