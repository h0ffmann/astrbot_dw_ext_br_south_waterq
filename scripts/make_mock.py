"""Make a page that shows the messages of the extension in a mock chat.

The text is the real output of the extension, through the host loader and presenter.
The pollers send a message only when a point changes, and the first poll records a
baseline. Thus, this script makes a message for each current result.
Usage: make_mock.py <extensions_root> <output_file> [--offline]
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = Path(os.environ["DW_HOST_DIR"])
ID = "br_south_waterq"
PACKAGE = f"_dw_ext_{ID}"
LANGS = {
    "en": "English",
    "zh-CN": "简体中文",
    "pt-BR": "Português (Brasil)",
    "ja-JP": "日本語",
}
LIVE_LIMIT = 4  # The live page shows this number of results for each state.
BRT = timezone(timedelta(hours=-3))
# The recorded file for each URL attribute of a provider module.
RECORDED = {
    "RS": "fepam_rs_locais.json",
    "SC": "ima_sc_mapa.json",
    "PR": "iat_pr_layer.json",
}


class _Response:
    def __init__(self, body):
        self._body = body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_exc):
        return False

    def raise_for_status(self):
        return None

    async def text(self):
        return self._body


class RecordedSession:
    """Return the recorded feeds. Each SC point gets the recorded samples."""

    def __init__(self, bodies, samples):
        self._bodies, self._samples = bodies, samples

    def get(self, url):
        return _Response(self._bodies[url])

    def post(self, _url, data=None):
        return _Response(self._samples)


def load_host():
    """Add the AstrBot stubs and return the host names that this script uses."""
    path = HOST / "tests/conftest.py"
    spec = importlib.util.spec_from_file_location("_dw_host_bootstrap", path)
    spec.loader.exec_module(importlib.util.module_from_spec(spec))
    importlib.import_module("astrbot_plugin_disaster_warning.core.app.disaster_service")
    package = "astrbot_plugin_disaster_warning.core"
    manager = importlib.import_module(f"{package}.extensions.manager")
    registry = importlib.import_module(f"{package}.extensions.host_registry")
    presenters = importlib.import_module(
        f"{package}.message.presenters.presenter_registry"
    )
    return manager, registry.HostRegistry, presenters.present_message


def recorded_session(states) -> RecordedSession:
    """Return a session with the recorded feeds in tests/fixtures."""
    fixtures = ROOT / "tests/fixtures"
    bodies = {
        getattr(provider, "URL", None) or provider.MAP_URL: (
            fixtures / RECORDED[uf]
        ).read_text("utf-8")
        for uf, provider in states.items()
    }
    samples = (fixtures / "ima_sc_analises.json").read_text("utf-8")
    return RecordedSession(bodies, samples)


def live_session(manager_module):
    """Return a real HTTP session."""
    import aiohttp

    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=manager_module._build_ssl_context()),
        timeout=aiohttp.ClientTimeout(total=45),
        headers={"User-Agent": "Mozilla/5.0"},
    )


async def state_points(provider, session, today, active_only, limit):
    """Return the unsuitable points of one state, and the number of results."""
    points = await provider.fetch(session)
    unsuitable = [p for p in points if p["status"] == "unsuitable"]
    completed = await provider.complete(session, unsuitable[: limit * 3])
    tracking = sys.modules[f"{PACKAGE}.tracking"]
    if active_only:
        completed = [
            p for p in completed if tracking.is_active(p["sample_date"], today)
        ]
    return completed[:limit], len(unsuitable)


def as_item(host, extension_api, point, label) -> dict:
    """Return the data of one message for a point."""
    present = host[2]
    envelopes = sys.modules[f"{PACKAGE}.envelopes"]
    envelope = envelopes.build_envelope(extension_api, point, label)
    return {
        "text": present(envelope, envelope.source_id),
        "level": envelope.event.metadata["severity_level"],
        "status": point["status"],
        "uf": point["uf"],
    }


async def messages(host, roots: Path, lang: str, session_of, active_only: bool) -> dict:
    """Load the extension in one language and return the messages."""
    manager_module, registry, _present = host

    class Service:
        config = {
            "extensions": {
                "enabled_ids": [ID],
                "settings": json.dumps({ID: {"language": lang}}),
            }
        }

    items, total = [], 0
    today = datetime.now(BRT).date()
    with tempfile.TemporaryDirectory() as data_dir:
        manager = manager_module.ExtensionManager(
            Service(), registry(), roots=[roots], data_dir=Path(data_dir)
        )
        manager.load_all()
        (row,) = manager.status()
        if row["state"] != "loaded":
            raise RuntimeError(row["error"])
        api = manager._apis[ID]
        states = sys.modules[f"{PACKAGE}.states"].STATES
        session = session_of(states)
        limit = LIVE_LIMIT if active_only else 1
        try:
            for provider in states.values():
                points, count = await state_points(
                    provider, session, today, active_only, limit
                )
                total += count
                items += [as_item(host, api, p, provider.SOURCE_LABEL) for p in points]
                if points and not active_only:
                    recovered = {**points[0], "status": "suitable"}
                    items.append(as_item(host, api, recovered, provider.SOURCE_LABEL))
        finally:
            close = getattr(session, "close", None)
            if close:
                await close()
    registry().unregister_source_entries(owner=ID)
    registry().unregister_presenters(owner=ID)
    return {"total": total, "items": items}


def short_commit(directory: Path) -> str:
    """Return the short commit of a directory, or "unknown"."""
    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "unknown"


async def live_scenario(host, roots: Path) -> dict | None:
    """Return the live messages, or None if a request fails."""
    import aiohttp

    def session_of(_states):
        return live_session(host[0])

    try:
        return {
            lang: await messages(host, roots, lang, session_of, True) for lang in LANGS
        }
    except (aiohttp.ClientError, TimeoutError) as e:
        print(f"No live data: {type(e).__name__}", file=sys.stderr)
        return None


async def main(roots: Path, output: Path, offline: bool) -> None:
    """Write the page."""
    host = load_host()
    scenarios = {}
    live = None if offline else await live_scenario(host, roots)
    if live:
        scenarios["live"] = live
    scenarios["recorded"] = {
        lang: await messages(host, roots, lang, recorded_session, False)
        for lang in LANGS
    }
    data = {
        "langs": LANGS,
        "captured": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": short_commit(ROOT),
        "host": short_commit(HOST),
        "scenarios": scenarios,
    }
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "scripts/mock_template.html").read_text("utf-8")
    output.write_text(template.replace("__DATA__", payload), "utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--offline"]
    asyncio.run(main(Path(args[0]), Path(args[1]), "--offline" in sys.argv))
