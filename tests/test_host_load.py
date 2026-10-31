"""Load the extension offline with the real extension manager of the host."""

from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

import pytest
from astrbot_plugin_disaster_warning.core.extensions.host_registry import HostRegistry
from astrbot_plugin_disaster_warning.core.extensions.manager import ExtensionManager

EXT_DIR = Path(__file__).resolve().parents[1]
ID = "br_south_waterq"
SOURCE = f"{ID}_balneabilidade"


class FakeService:
    """The part of the host service that the extension manager uses."""

    def __init__(self, settings):
        self.config = {
            "extensions": {"enabled_ids": [ID], "settings": json.dumps({ID: settings})}
        }


@pytest.fixture
def load(tmp_path):
    """Return a function that loads the extension. Remove the registrations at the end."""
    root = tmp_path / "extensions"
    root.mkdir()
    (root / ID).symlink_to(EXT_DIR, target_is_directory=True)

    def _load(settings):
        manager = ExtensionManager(
            FakeService(settings), HostRegistry(), roots=[root], data_dir=tmp_path
        )
        manager.load_all()
        return manager

    yield _load
    HostRegistry().unregister_source_entries(owner=ID)
    HostRegistry().unregister_presenters(owner=ID)


def test_extension_loads_in_the_host(load):
    """Check the manifest, the relative imports and the registrations."""
    (record,) = load({"language": "en"}).status()
    assert record["state"] == "loaded", record["error"]
    assert record["sources"] == [SOURCE]


def test_directory_with_the_repository_name_does_not_load(tmp_path):
    """Check the rule that the installation procedure tells the operator to obey."""
    root = tmp_path / "extensions"
    root.mkdir()
    (root / "astrbot_dw_ext_br_south_waterq").symlink_to(EXT_DIR)
    manager = ExtensionManager(
        FakeService({}), HostRegistry(), roots=[root], data_dir=tmp_path
    )
    manager.load_all()
    assert not manager._apis


def test_pollers_have_the_default_interval_and_timeout(load):
    """Check the values that the host stores for each state."""
    api = load({})._apis[ID]
    assert [spec.interval_seconds for spec in api.pollers] == [21600] * 3
    assert [spec.timeout_seconds for spec in api.pollers] == [60] * 3


def test_host_applies_the_lower_limit_of_the_interval(load):
    """Check that a small interval does not send a request each second."""
    api = load({"poll_interval": 0})._apis[ID]
    assert {spec.interval_seconds for spec in api.pollers} == {api.MIN_INTERVAL_SECONDS}


def test_bad_settings_do_not_stop_the_load(load):
    """Check values that stopped the setup in earlier versions."""
    (record,) = load({"poll_interval": 1e999, "states": "SC"}).status()
    assert record["state"] == "loaded", record["error"]


def test_state_poller_gives_real_host_envelopes(load, fake_session):
    """Check a poller against the real models of the host."""
    api = load({"language": "en", "states": ["RS"]})._apis[ID]
    (spec,) = api.pollers
    recent = date.today().strftime("%d/%m/%Y")
    row = {"codLocal": 7, "nome": "Praia", "situacao": 2, "ultimaColeta": recent}
    url = "https://secweb.procergs.com.br/baln/rest/locais"
    session = fake_session({url: ([row], [{**row, "situacao": 3}])})
    assert asyncio.run(spec.fetch(session)) == []
    (envelope,) = asyncio.run(spec.fetch(session))
    assert envelope.identity.event_id.startswith(f"{ID}_rs_7_")
    assert envelope.identity.source_id == SOURCE
