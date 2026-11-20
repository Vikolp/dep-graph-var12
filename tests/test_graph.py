import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from repository import parse_test_file
from graph import build_dependency_graph,recursive_bfs
DATA=Path(__file__).resolve().parents[1]/"testdata"
def test_bfs_shared_nodes():
 g=build_dependency_graph(parse_test_file(DATA/"simple.txt"),"A",5)
 assert recursive_bfs(g)==["A","B","C","D","E","F"]
def test_max_depth():
 g=build_dependency_graph(parse_test_file(DATA/"simple.txt"),"A",1)
 assert g.depths=={"A":0,"B":1,"C":1}
 assert g.adjacency["B"]==[]
def test_cycle():
 g=build_dependency_graph(parse_test_file(DATA/"cycle.txt"),"A",10)
 assert set(recursive_bfs(g))=={"A","B","C","D"}
 assert g.cycles
