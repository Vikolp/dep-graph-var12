"""CLI configuration and validation."""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

@dataclass(frozen=True)
class Config:
    package: str
    repo: str
    test_mode: bool = False
    version: str | None = None
    ascii_tree: bool = False
    max_depth: int = 5
    reverse: bool = False
    output_dir: str = "output"

def parse_args(argv: list[str] | None = None) -> Config:
    p = argparse.ArgumentParser(description="Ubuntu apt dependency graph visualizer")
    p.add_argument("-p", "--package", required=True)
    p.add_argument("-r", "--repo", required=True, help="Ubuntu repository URL or test file")
    p.add_argument("--test", action="store_true", help="Use text test repository")
    p.add_argument("-v", "--version")
    p.add_argument("--ascii-tree", action="store_true")
    p.add_argument("-d", "--max-depth", type=int, default=5)
    p.add_argument("--reverse", action="store_true")
    p.add_argument("--output-dir", default="output")
    a = p.parse_args(argv)
    if not a.package.strip(): p.error("package must not be empty")
    if a.max_depth < 0: p.error("max-depth must be >= 0")
    if a.version is not None and not a.version.strip(): p.error("version must not be empty")
    if a.test:
        if not Path(a.repo).expanduser().is_file(): p.error(f"test repository not found: {a.repo}")
    else:
        u = urlparse(a.repo)
        if u.scheme not in ("http", "https") or not u.netloc: p.error("repo must be an http(s) URL (or use --test)")
    return Config(a.package.strip(), a.repo, a.test, a.version, a.ascii_tree, a.max_depth, a.reverse, a.output_dir)

def print_config(c: Config) -> None:
    print("=== Configuration ===")
    for k, v in c.__dict__.items(): print(f"{k}: {v}")
