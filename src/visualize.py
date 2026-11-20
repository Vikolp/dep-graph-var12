"""PlantUML and terminal visualizations."""
from __future__ import annotations
import shutil
import subprocess
from pathlib import Path
from graph import DependencyGraph

def _alias(index: int) -> str:
    return "pkg_{}".format(index)

def to_plantuml(graph: DependencyGraph) -> str:
    nodes = sorted(graph.adjacency)
    aliases = {name: _alias(index) for index, name in enumerate(nodes)}
    lines = ["@startuml", "left to right direction", "skinparam packageStyle rectangle"]
    for name in nodes:
        label = name.replace("\\", "\\\\").replace('"', '\\"')
        lines.append('package "{}" as {}'.format(label, aliases[name]))
    for source, target in graph.edges():
        if target in aliases:
            lines.append("{} --> {}".format(aliases[source], aliases[target]))
    lines.append("@enduml")
    return "\n".join(lines) + "\n"

def save_plantuml(graph: DependencyGraph, output_dir: str | Path = "output") -> Path:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe = "".join(char if char.isalnum() or char in "-_" else "_" for char in graph.root)
    path = directory / "{}_deps.puml".format(safe)
    path.write_text(to_plantuml(graph), encoding="utf-8")
    return path

def render_plantuml(path: str | Path) -> Path | None:
    executable = shutil.which("plantuml")
    if not executable:
        return None
    source = Path(path)
    result = subprocess.run([executable, "-tsvg", str(source)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "PlantUML rendering failed")
    rendered = source.with_suffix(".svg")
    return rendered if rendered.exists() else None

def to_ascii_tree(graph: DependencyGraph) -> str:
    """Render a tree without recursively descending through every branch."""
    lines = [graph.root]
    expanded = {graph.root}
    stack = [("visit", graph.root, "", frozenset({graph.root}), False)]
    while stack:
        action, node, prefix, ancestors, last = stack.pop()
        if action == "visit":
            children = graph.adjacency.get(node, [])
            for index in range(len(children) - 1, -1, -1):
                stack.append(("child", children[index], prefix, ancestors, index == len(children) - 1))
            continue
        branch = "└── " if last else "├── "
        if node in ancestors:
            suffix = " (cycle)"
        elif node in expanded:
            suffix = " (already shown)"
        else:
            suffix = ""
        lines.append(prefix + branch + node + suffix)
        if not suffix:
            expanded.add(node)
            child_prefix = prefix + ("    " if last else "│   ")
            stack.append(("visit", node, child_prefix, ancestors | {node}, False))
    return "\n".join(lines)
