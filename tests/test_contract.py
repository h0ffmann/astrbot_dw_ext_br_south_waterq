"""Checks of the rules for an extension repository (host RFC, issue 256)."""

from __future__ import annotations

import ast
import io
import json
import re
import string
import subprocess
import sys
import tarfile
from datetime import datetime
from pathlib import Path

import pytest
import yaml

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((ROOT / "extension.yaml").read_text("utf-8"))
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text("utf-8"))
META = json.loads((ROOT / "meta.json").read_text("utf-8"))
MODULES = sorted(ROOT.glob("*.py")) + sorted(ROOT.glob("providers/*.py"))
LOCALES = {
    path.stem: json.loads(path.read_text("utf-8"))
    for path in sorted((ROOT / "locale").glob("*.json"))
}
NAMES = ("common.py", "pr_iat.py", "rs_fepam.py", "sc_ima.py")
REQUIRED = [
    "extension.yaml",
    "__init__.py",
    "extension.py",
    "locale/zh-CN.json",
    "README.md",
    "LICENSE",
]
DEV_ONLY = [
    "tests/conftest.py",
    "docs/brazil-water-quality-sources.md",
    ".github/workflows/ci.yml",
    ".claude/skills/asd-ste100/SKILL.md",
    ".devin/wiki.json",
    "scripts/make_mock.py",
    "justfile",
    "flake.nix",
    "flake.lock",
    "pyproject.toml",
    "requirements-dev.txt",
]


def fields(text: str) -> set[str]:
    """Return the names of the format fields in a text."""
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


@pytest.mark.parametrize("path", REQUIRED)
def test_required_file_exists(path):
    """Check section 1.4 of the RFC."""
    assert (ROOT / path).is_file()


def test_manifest_values():
    """Check the id, the versions, the entry point and the permissions."""
    assert re.fullmatch(r"[a-z0-9_]+", MANIFEST["id"])
    assert re.fullmatch(r"\d+\.\d+\.\d+", MANIFEST["version"])
    assert MANIFEST["api_version"] == 1
    assert MANIFEST["permissions"] == ["network"]
    module, function = MANIFEST["entry"].split(":")
    tree = ast.parse((ROOT / f"{module}.py").read_text("utf-8"))
    assert function in {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}


def test_repository_name_matches_the_id():
    """Check section 1.2 of the RFC."""
    name = MANIFEST["repository"].rsplit("/", 1)[1]
    assert name == f"astrbot_dw_ext_{MANIFEST['id']}"
    assert PYPROJECT["project"]["name"] == name


def test_versions_are_the_same():
    """Check that a release has one version."""
    version = MANIFEST["version"]
    assert PYPROJECT["project"]["version"] == version
    changelog = (ROOT / "CHANGELOG.md").read_text("utf-8")
    assert f"## {version}" in changelog


def test_license_is_the_same():
    """Check the manifest, the project data and the license file."""
    assert PYPROJECT["project"]["license"]["text"] == MANIFEST["license"]
    assert "Mozilla Public License Version 2.0" in (ROOT / "LICENSE").read_text("utf-8")


def test_meta_languages_are_the_locale_files():
    """Check that meta.json lists each locale file."""
    assert META["id"] == MANIFEST["id"]
    assert sorted(META["languages"]) == sorted(LOCALES)


def test_meta_documents_exist():
    """Check the document path of each data source."""
    for source in META["data_sources"]:
        assert (ROOT / source["document"]).is_file()


@pytest.mark.parametrize("lang", sorted(LOCALES))
def test_locale_has_the_same_keys_and_fields(lang):
    """Check each translation against the host language."""
    table, reference = LOCALES[lang], LOCALES["zh-CN"]
    assert set(table) == set(reference)
    for key, text in reference.items():
        assert fields(table[key]) == fields(text), key


@pytest.mark.parametrize("lang", sorted(LOCALES))
def test_locale_formats_work(lang):
    """Check the number and date formats of each language."""
    table = LOCALES[lang]
    assert table["format.decimal"] in (".", ",")
    assert datetime(2026, 10, 25, 8, 30).strftime(table["format.date"]).count("2026")


def test_locale_has_each_key_that_the_code_uses():
    """Check the literal keys in the code and the keys with a value in the name."""
    source = "\n".join(path.read_text("utf-8") for path in MODULES)
    keys = set(re.findall(r'"((?:present|format)\.[a-z0-9_.]+)"', source))
    assert keys
    keys |= {"headline", "source.balneabilidade", "source.balneabilidade.desc"}
    for status in ("suitable", "unsuitable"):
        keys |= {f"title.{status}", f"status.{status}"}
    assert keys <= set(LOCALES["zh-CN"])


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_code_imports_only_the_standard_library(path):
    """Check that the extension has no third-party dependency and no host import."""
    for node in ast.walk(ast.parse(path.read_text("utf-8"))):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names = [node.module]
        else:
            continue
        for name in names:
            assert name.split(".")[0] in sys.stdlib_module_names, name


def export_ignored(path: str) -> bool:
    """Return True if git leaves the path out of a release archive."""
    result = subprocess.run(
        ["git", "check-attr", "export-ignore", "--", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().endswith(": set")


def test_release_archive_has_only_runtime_entries():
    """Build the archive of the last commit and read the top-level entries."""
    result = subprocess.run(
        ["git", "archive", "--worktree-attributes", "--format=tar", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        names = {name.split("/")[0] for name in archive.getnames()}
    assert "extension.yaml" in names
    assert not names & {
        "tests",
        "docs",
        "scripts",
        ".github",
        ".claude",
        ".devin",
        ".gitignore",
        ".gitattributes",
        "justfile",
        "pyproject.toml",
    }


def test_deepwiki_settings_obey_the_limits():
    """Check the limits of .devin/wiki.json in the DeepWiki documentation."""
    wiki = json.loads((ROOT / ".devin/wiki.json").read_text("utf-8"))
    pages, notes = wiki["pages"], wiki["repo_notes"]
    titles = [page["title"] for page in pages]
    assert 1 <= len(pages) <= 30
    assert len(notes) <= 100
    assert all(0 < len(note["content"]) <= 10_000 for note in notes)
    assert all(titles) and len(titles) == len(set(titles))
    assert all(page["purpose"] for page in pages)
    assert {page.get("parent") for page in pages} - {None} <= set(titles)


def test_live_tests_use_names_that_exist():
    """Check the live tests offline. The CI does not run them."""
    source = (ROOT / "tests/live/test_br_south_waterq_live.py").read_text("utf-8")
    code = "\n".join((ROOT / "providers").joinpath(n).read_text("utf-8") for n in NAMES)
    names = set(re.findall(r"\bprovider\.([A-Za-z_]+)", source))
    assert names
    for name in names:
        assert re.search(rf"\b{name}\b", code), name


RUNTIME = [str(path.relative_to(ROOT)) for path in MODULES]


@pytest.mark.parametrize("path", RUNTIME + REQUIRED[:-3])
def test_release_has_the_runtime_file(path):
    """Check that the release archive keeps the code."""
    assert not export_ignored(path)


@pytest.mark.parametrize("path", DEV_ONLY)
def test_release_does_not_have_the_development_file(path):
    """Check section 1.5 of the RFC."""
    assert export_ignored(path)
