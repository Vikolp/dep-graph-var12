import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from repository import parse_test_file
from graph import build_reverse_graph,recursive_bfs
DATA=Path(__file__).resolve().parents[1]/"testdata"
def test_reverse_dependencies_transitive():
 g=build_reverse_graph(parse_test_file(DATA/"simple.txt"),"D")
 assert recursive_bfs(g)==["D","B","C","A"]
def test_reverse_for_leaf():
 g=build_reverse_graph(parse_test_file(DATA/"simple.txt"),"F")
 assert recursive_bfs(g)==["F","E","C","A"]
