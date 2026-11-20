import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from repository import parse_test_file
from graph import build_dependency_graph
from visualize import to_ascii_tree, to_plantuml

DATA = Path(__file__).resolve().parents[1] / "testdata"

def test_plantuml_contains_edges():
    graph = build_dependency_graph(parse_test_file(DATA / "simple.txt"), "A")
    text = to_plantuml(graph)
    assert text.startswith("@startuml") and text.rstrip().endswith("@enduml")
    assert "-->" in text

def test_ascii_tree_marks_shared_node():
    graph = build_dependency_graph(parse_test_file(DATA / "simple.txt"), "A")
    assert "already shown" in to_ascii_tree(graph)

def test_ascii_tree_marks_cycles():
    graph = build_dependency_graph(parse_test_file(DATA / "cycle.txt"), "A")
    assert "(cycle)" in to_ascii_tree(graph)
