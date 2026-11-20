import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from repository import parse_test_file,parse_packages,get_package
DATA=Path(__file__).resolve().parents[1]/"testdata"
def test_test_repository_uppercases_names():
 records=parse_test_file(DATA/"simple.txt")
 assert "A" in records and records["A"][0].depends==("B","C")
def test_apt_packages_parser_and_version():
 records=parse_packages("Package: demo\nVersion: 2.0\nDepends: libc6 (>= 2.3), zlib1g | zlib1g-dev\n\n")
 assert get_package(records,"demo","2.0").depends==("libc6","zlib1g")
def test_missing_version_is_error():
 records=parse_test_file(DATA/"simple.txt")
 with pytest.raises(KeyError):get_package(records,"A","99")
