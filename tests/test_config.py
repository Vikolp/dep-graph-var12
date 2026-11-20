import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config import parse_args

DATA = Path(__file__).resolve().parents[1] / "testdata"

def test_cli_parses_all_stage_one_options():
    config = parse_args(["-p", "A", "-r", str(DATA / "simple.txt"), "--test",
                         "-v", "1.0", "--ascii-tree", "-d", "2"])
    assert config.package == "A"
    assert config.test_mode is True
    assert config.version == "1.0"
    assert config.ascii_tree is True
    assert config.max_depth == 2

def test_cli_rejects_negative_depth():
    with pytest.raises(SystemExit):
        parse_args(["-p", "A", "-r", str(DATA / "simple.txt"), "--test", "-d", "-1"])

def test_cli_rejects_missing_test_file():
    with pytest.raises(SystemExit):
        parse_args(["-p", "A", "-r", str(DATA / "missing.txt"), "--test"])
