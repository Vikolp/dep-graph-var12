"""Load package metadata from a simple test index or Ubuntu Packages indexes."""
from __future__ import annotations
import gzip
import lzma
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

@dataclass(frozen=True)
class Package:
    name: str
    version: str
    depends: tuple[str, ...]

def _clean_depends(value: str) -> tuple[str, ...]:
    result = []
    for item in value.split(","):
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
                current = key.strip()
                fields[current] = value.strip()
        name = fields.get("Package")
        if name:
            package = Package(
                name,
                fields.get("Version", "unknown"),
                _clean_depends(fields.get("Depends", "") + "," + fields.get("Pre-Depends", "")),
            )
            records.setdefault(name, []).append(package)
    return records

def parse_test_file(path: str | Path) -> dict[str, list[Package]]:
    records: dict[str, list[Package]] = {}
    source = Path(path).expanduser()
    for number, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError("{}:{}: expected 'PACKAGE: DEP1 DEP2'".format(source, number))
        name, deps = line.split(":", 1)
        name = name.strip().upper()
        if not name:
            raise ValueError("{}:{}: empty package name".format(source, number))
        dependencies = tuple(dict.fromkeys(item.upper() for item in deps.split()))
        records.setdefault(name, []).append(Package(name, "1.0", dependencies))
    return records

def _read_index(data: bytes, url: str) -> str:
    path = urlparse(url).path
    if path.endswith(".gz"):
        data = gzip.decompress(data)
    elif path.endswith(".xz"):
        data = lzma.decompress(data)
    return data.decode("utf-8", "replace")

def _candidate_index_urls(base_url: str, component: str, architecture: str,
                          suites: tuple[str, ...]) -> list[str]:
    path = urlparse(base_url).path.rstrip("/")
    if path.endswith(("/Packages", "/Packages.gz", "/Packages.xz")):
        return [base_url]
    suffixes = ("Packages.xz", "Packages.gz", "Packages")
    if "/binary-" in path:
        return [base_url.rstrip("/") + "/" + suffix for suffix in suffixes]
    return [
        "{}/dists/{}/{}/binary-{}/{}".format(
            base_url.rstrip("/"), suite, component, architecture, suffix
        )
        for suite in suites
        for suffix in suffixes
    ]

def load_apt_repository(base_url: str, component: str = "main",
                        architecture: str = "amd64",
                        suites: tuple[str, ...] = ("noble", "jammy", "focal")) -> dict[str, list[Package]]:
    """Download and parse an Ubuntu Packages index.

    base_url may be a repository root or a direct Packages, Packages.gz, or
    Packages.xz URL. The default suite list keeps the tool usable on supported
    Ubuntu LTS mirrors; callers may provide another suite explicitly.
    """
    errors = []
    for url in _candidate_index_urls(base_url, component, architecture, suites):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "dep-graph-var12/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                return parse_packages(_read_index(response.read(), url))
        except (urllib.error.URLError, TimeoutError, OSError, EOFError, lzma.LZMAError) as exc:
            errors.append("{}: {}".format(url, exc))
    raise RuntimeError("Could not download Ubuntu Packages index. Tried: " + "; ".join(errors))

def get_repository(repo: str, test_mode: bool) -> dict[str, list[Package]]:
    return parse_test_file(repo) if test_mode else load_apt_repository(repo)

def get_package(records: dict[str, list[Package]], name: str,
                version: str | None = None) -> Package:
    candidates = records.get(name) or records.get(name.upper()) or records.get(name.lower())
    if not candidates:
        raise KeyError("Package '{}' was not found in repository".format(name))
    if version is not None:
        for package in candidates:
            if package.version == version:
                return package
        raise KeyError("Package '{}' has no version '{}'".format(name, version))
    return candidates[0]

def direct_dependencies(records: dict[str, list[Package]], name: str,
                        version: str | None = None) -> tuple[str, ...]:
    return get_package(records, name, version).depends
