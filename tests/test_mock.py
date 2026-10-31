"""Check the page of "just mock" with the recorded feeds."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mock_page_has_real_messages_in_each_language(tmp_path):
    """Make the page offline and read the data in it."""
    root = tmp_path / "extensions"
    root.mkdir()
    (root / "br_south_waterq").symlink_to(ROOT, target_is_directory=True)
    output = tmp_path / "mock.html"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/make_mock.py"),
            str(root),
            str(output),
            "--offline",
        ],
        check=True,
        cwd=tmp_path,
        env=os.environ,
    )
    html = output.read_text("utf-8")
    assert "__DATA__" not in html
    assert "It is not a real warning" in html
    found = re.search(r'type="application/json">(.*?)</script>', html, re.S)
    scenarios = json.loads(found.group(1))["scenarios"]
    assert list(scenarios) == ["recorded"]
    assert sorted(scenarios["recorded"]) == ["en", "ja-JP", "pt-BR", "zh-CN"]
    for result in scenarios["recorded"].values():
        assert {item["status"] for item in result["items"]} == {
            "suitable",
            "unsuitable",
        }
