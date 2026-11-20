import gzip
import lzma
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from repository import parse_test_file, parse_packages, get_package, _read_index, _candidate_index_urls

DATA = Path(__file__).resolve().parents[1] / "testdata"

def test_test_repository_uppercases_names():
    records = parse_test_file(DATA / "simple.txt")
    assert "A" in records and records["A"][0].depends == ("B", "C")

def test_apt_packages_parser_and_version():
    records = parse_packages("Package: demo\nVersion: 2.0\nDepends: libc6 (>= 2.3), zlib1g | zlib1g-dev\n\n")
    assert get_package(records, "demo", "2.0").depends == ("libc6", "zlib1g")

def test_missing_version_is_error():
    records = parse_test_file(DATA / "simple.txt")
    with pytest.raises(KeyError):
        get_package(records, "A", "99")

def test_compressed_packages_indexes():
    text = "Package: demo\nVersion: 1\nDepends: libc6\n\n"
    assert "demo" in parse_packages(_read_index(gzip.compress(text.encode()), "https://host/Packages.gz"))
    assert "demo" in parse_packages(_read_index(lzma.compress(text.encode()), "https://host/Packages.xz"))

def test_direct_packages_url_is_supported():
    urls = _candidate_index_urls("https://mirror.example/Packages.xz", "main", "amd64", ("noble",))
    assert urls == ["https://mirror.example/Packages.xz"]

def test_test_file_expands_home_directory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "index.txt").write_text("A: B\nB:\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    records = parse_test_file("~/index.txt")
    assert records["A"][0].depends == ("B",)
