"""CLI entry point."""
from __future__ import annotations
import sys
from config import parse_args,print_config
from repository import get_repository,direct_dependencies
from graph import build_dependency_graph,build_reverse_graph,recursive_bfs
from visualize import save_plantuml,render_plantuml,to_ascii_tree

def main(argv:list[str]|None=None)->int:
    config=parse_args(argv)
    print_config(config)
    try:
        records=get_repository(config.repo,config.test_mode)
        if config.reverse:
            graph=build_reverse_graph(records,config.package)
            print(f"\n=== Reverse dependencies of '{config.package}' ===")
            for name in graph.adjacency.get(graph.root,[]):print(f"  - {name}")
        else:
            direct=direct_dependencies(records,config.package,config.version)
            print(f"\n=== Direct dependencies of '{config.package}' ===")
            if direct:
                for name in direct:print(f"  - {name}")
            else:print("  (none)")
            graph=build_dependency_graph(records,config.package,config.max_depth,config.version)
        print("\n=== Graph (BFS order) ===")
        for name in recursive_bfs(graph):print(f"  {name} (depth={graph.depths.get(name,0)})")
        if graph.cycles:
            print("\nDetected repeated/cyclic edges:")
            for source,target in graph.cycles:print(f"  {source} -> {target}")
        if config.ascii_tree:
            print("\n=== ASCII tree ===")
            print(to_ascii_tree(graph))
        path=save_plantuml(graph,config.output_dir)
        print(f"\nPlantUML saved: {path}")
        rendered=render_plantuml(path)
        if rendered:print(f"Rendered image: {rendered}")
        else:print("PlantUML CLI not found; render with: plantuml -tsvg " + str(path))
        return 0
    except (KeyError,ValueError,RuntimeError,OSError) as exc:
        print(f"Error: {exc}",file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
