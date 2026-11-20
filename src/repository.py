"""Load package metadata from a simple test index or Ubuntu Packages indexes."""
from __future__ import annotations
import gzip
import lzma
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

@dataclass(frozen=True)
class Package:
    name: str
    version: str
    depends: tuple[str, ...]

def _clean_depends(value: str) -> tuple[str, ...]:
    result = []
    for item in value.split(","):
        # apt alternatives: choose the first alternative; strip version/arch qualifiers.
        first = item.strip().split("|", 1)[0].strip()
        match = re.match(r"([A-Za-z0-9+._:-]+)", first)
        if match and match.group(1) not in result:
            result.append(match.group(1))
    return tuple(result)

def parse_packages(text: str) -> dict[str, list[Package]]:
    records: dict[str, list[Package]] = {}
    for block in re.split(r"\n\s*\n", text.strip()):
        fields: dict[str, str] = {}
        current = None
        for line in block.splitlines():
            if line[:1].isspace() and current:
                fields[current] += " " + line.strip()
            elif ":" in line:
                key, value = line.split(":", 1)
                current, value = key.strip(), value.strip()
                fields[current] = value
        name = fields.get("Package")
        if name:
            pkg = Package(name, fields.get("Version", "unknown"),
                          _clean_depends(fields.get("Depends", "") + "," + fields.get("Pre-Depends", "")))
            records.setdefault(name, []).append(pkg)
    return records

def parse_test_file(path: str | Path) -> dict[str, list[Package]]:
    records: dict[str, list[Package]] = {}
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"{path}:{number}: expected 'PACKAGE: DEP1 DEP2'")
        name, deps = line.split(":", 1)
        name = name.strip().upper()
        if not name:
            raise ValueError(f"{path}:{number}: empty package name")
        dependencies = tuple(dict.fromkeys(x.upper() for x in deps.split()))
        records.setdefault(name, []).append(Package(name, "1.0", dependencies))
    return records

def _read_index(data: bytes, url: str) -> str:
    if url.endswith(".gz"): return gzip.decompress(data).decode("utf-8", "replace")
    if url.endswith(".xz"): return lzma.decompress(data).decode("utf-8", "replace")
    return data.decode("utf-8", "replace")

def load_apt_repository(base_url: str, component: str = "main", architecture: str = "amd64") -> dict[str, list[Package]]:
    """Fetch Ubuntu's binary Packages index for the current stable distribution.

    base_url should point to a repository root, e.g. http://archive.ubuntu.com/ubuntu.
    """
    # Try noble then jammy, and compressed formats commonly published by apt mirrors.
    errors = []
    for codename in ("noble", "jammy", "focal"):
        for suffix in ("Packages.xz", "Packages.gz", "Packages"):
            url = f"{base_url.rstrip('/')}/dists/{codename}/{component}/binary-{architecture}/{suffix}"
            try:
                request = urllib.request.Request(url, headers={"User-Agent": "dep-graph-var12/1.0"})
                with urllib.request.urlopen(request, timeout=30) as response:
                    return parse_packages(_read_index(response.read(), url))
            except Exception as exc:
                errors.append(f"{url}: {exc}")
    raise RuntimeError("Could not download Ubuntu Packages index. Tried: " + "; ".join(errors[-3:]))

def get_repository(repo: str, test_mode: bool) -> dict[str, list[Package]]:
    return parse_test_file(repo) if test_mode else load_apt_repository(repo)

def get_package(records: dict[str, list[Package]], name: str, version: str | None = None) -> Package:
    candidates = records.get(name) or records.get(name.upper()) or records.get(name.lower())
    if not candidates:
        raise KeyError(f"Package '{name}' was not found in repository")
    if version:
        for package in candidates:
            if package.version == version:
                return package
        raise KeyError(f"Package '{name}' has no version '{version}'")
    return candidates[0]

def direct_dependencies(records: dict[str, list[Package]], name: str, version: str | None = None) -> tuple[str, ...]:
    return get_package(records, name, version).depends
