import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from repository import Package, parse_test_file
from graph import build_dependency_graph, recursive_bfs

DATA = Path(__file__).resolve().parents[1] / "testdata"

def test_bfs_and_shared_dependencies():
    graph = build_dependency_graph(parse_test_file(DATA / "simple.txt"), "A", 5)
    assert recursive_bfs(graph) == ["A", "B", "C", "D", "E", "F"]
    assert ("A", "B") in graph.edges()

def test_max_depth():
    graph = build_dependency_graph(parse_test_file(DATA / "simple.txt"), "A", 1)
    assert graph.depths == {"A": 0, "B": 1, "C": 1}
    assert graph.adjacency["B"] == []

def test_cycles_do_not_loop():
    graph = build_dependency_graph(parse_test_file(DATA / "cycle.txt"), "A", 10)
    assert set(recursive_bfs(graph)) == {"A", "B", "C", "D"}
    assert graph.cycles

def test_wide_graph_does_not_overflow_python_recursion_limit():
    records = {"ROOT": [Package("ROOT", "1", tuple("P{}".format(i) for i in range(1500)))]}
    records.update({"P{}".format(i): [Package("P{}".format(i), "1", ())] for i in range(1500)})
    graph = build_dependency_graph(records, "ROOT", 1)
    assert len(recursive_bfs(graph)) == 1501
