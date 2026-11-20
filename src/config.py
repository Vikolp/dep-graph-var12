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
    parser = argparse.ArgumentParser(description="Ubuntu apt dependency graph visualizer")
    parser.add_argument("-p", "--package", required=True)
    parser.add_argument("-r", "--repo", required=True, help="Ubuntu repository URL or test file")
    parser.add_argument("--test", action="store_true", help="Use text test repository")
    parser.add_argument("-v", "--version")
    parser.add_argument("--ascii-tree", action="store_true")
    parser.add_argument("-d", "--max-depth", type=int, default=5)
    parser.add_argument("--reverse", action="store_true")
    parser.add_argument("--output-dir", default="output")
    args = parser.parse_args(argv)
    if not args.package.strip():
        parser.error("--package must not be empty")
    if args.max_depth < 0:
        parser.error("--max-depth must be zero or greater")
    if args.version is not None and not args.version.strip():
        parser.error("--version must not be empty")
    if args.test:
        if not Path(args.repo).expanduser().is_file():
            parser.error("test repository file does not exist: {}".format(args.repo))
    else:
        parsed = urlparse(args.repo)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            parser.error("--repo must be an http(s) URL unless --test is used")
    return Config(args.package.strip(), args.repo, args.test, args.version,
                  args.ascii_tree, args.max_depth, args.reverse, args.output_dir)

def print_config(config: Config) -> None:
    print("=== Configuration ===")
    for key, value in config.__dict__.items():
        print("{}: {}".format(key, value))
