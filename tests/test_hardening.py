"""Regression tests for feeds and settings with unexpected values."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import types
from datetime import date

import pytest


def rs_row(**changes):
    """Return a valid FEPAM row."""
    row = {
        "codLocal": 7,
        "nome": "Praia",
        "nomeMunicipio": "Torres",
        "situacao": 3,
        "ultimaColeta": "24/02/2026",
    }
    return {**row, **changes}


def sc_row(**changes):
    """Return a valid IMA map row."""
    row = {
        "CODIGO": "abc",
        "BALNEARIO": "Canasvieiras",
        "PONTO_NOME": "Ponto 1",
        "MUNICIPIO": "Florianópolis",
        "CONDICAO": "IMPRÓPRIO",
    }
    return {**row, **changes}


def pr_row(**changes):
    """Return a valid IAT layer row."""
    row = {
        "cod": "PR1",
        "praia_rio": "Matinhos",
        "local": "Centro",
        "municipio": "Matinhos",
        "ano1": "2025",
        "b1": "Impropria",
        "b1_data": 1766026800000,
    }
    return {"attributes": {**row, **changes}}


@pytest.fixture
def run():
    """Return a function that runs a coroutine."""
    return asyncio.run


# ---------------------------------------------------------------- feeds


@pytest.mark.parametrize("data", [None, {}, "text", 3, [1, "x", None, []]])
def test_rs_and_sc_accept_a_feed_of_a_wrong_type(ext, data):
    """Check that the parsers accept any value."""
    assert ext.rs.parse(data) == []
    assert ext.sc.parse(data) == []


@pytest.mark.parametrize(
    "data", [None, [], "text", 3, {}, {"features": "x"}, {"features": [1, {}, None]}]
)
def test_pr_accepts_a_feed_of_a_wrong_type(ext, data):
    """Check that the parser accepts any value."""
    assert ext.pr.parse(data) == []


@pytest.mark.parametrize(
    "bad",
    [
        rs_row(codLocal=True),
        rs_row(codLocal="7"),
        rs_row(ultimaColeta=None),
    ],
)
def test_bad_rs_row_does_not_stop_the_good_row(ext, bad):
    """Check that the parser skips only the row that it cannot use."""
    assert [p["key"] for p in ext.rs.parse([bad, rs_row(codLocal=8)])] == ["8"]


@pytest.mark.parametrize("value", [[3], {"a": 1}, None, 1.5])
def test_rs_status_of_a_wrong_type_is_unknown(ext, value):
    """Check that a list in the status field does not stop the poll."""
    assert ext.rs.parse([rs_row(situacao=value)])[0]["status"] is None


@pytest.mark.parametrize("code", [["a"], {"a": 1}, True, "", None, 0])
def test_bad_sc_code_does_not_stop_the_good_row(ext, code):
    """Check that a code that cannot be a dict key does not stop the poll."""
    data = [sc_row(CODIGO=code), sc_row(CODIGO="good")]
    assert [p["key"] for p in ext.sc.parse(data)] == ["good"]


def test_sc_name_with_a_wrong_type_is_ignored(ext):
    """Check that a number in the name does not stop the poll."""
    data = [sc_row(BALNEARIO=5, MUNICIPIO=["x"], CONDICAO=["x"])]
    point = ext.sc.parse(data)[0]
    assert point["beach"] == "Ponto 1"
    assert point["municipio"] is None
    assert point["status"] is None


@pytest.mark.parametrize("value", [5, ["x"], {"a": 1}, True])
def test_pr_campaign_of_a_wrong_type_is_ignored(ext, value):
    """Check that only a text is a campaign result."""
    point = ext.pr.parse({"features": [pr_row(b2=value)]})[0]
    assert point["bulletin"] == "2025-b1"


@pytest.mark.parametrize("value", [True, math.nan, math.inf, 10**30, "x", [1]])
def test_pr_date_that_is_not_usable_is_ignored(ext, value):
    """Check that a bad date does not stop the poll."""
    point = ext.pr.parse({"features": [pr_row(b1_data=value)]})[0]
    assert point["sample_date"] is None


def test_pr_date_is_midnight_in_brasilia(ext):
    """Check that 03:00 UTC is the same day in Brasília. The layer uses this time."""
    point = ext.pr.parse({"features": [pr_row(b1_data=1766026800000)]})[0]
    assert point["sample_date"] == date(2025, 12, 18)


@pytest.mark.parametrize("value", ["x", math.nan, math.inf, True, [1], 10**400])
def test_position_that_is_not_a_number_gives_no_position_line(ext, make_api, value):
    """Check that a text in the position does not stop the message."""
    api = make_api("en")
    point = ext.pr.parse({"features": [pr_row(latitude=value, longitude=-48.5)]})[0]
    point["sample_date"] = date(2026, 10, 1)
    env = ext.extension.build_envelope(api, point, "IAT/PR")
    assert point["latitude"] is None
    context = types.SimpleNamespace(
        title=env.event.title, headline=env.event.headline, metadata=env.event.metadata
    )
    assert "Position" not in ext.presenter.make_presenter(api).present(context)


def test_point_with_no_name_has_no_none_text(ext, make_api):
    """Check the headline of a point with no names."""
    api = make_api("en")
    point = ext.rs.parse([rs_row(nome=None, nomeMunicipio=None)])[0]
    env = ext.extension.build_envelope(api, point, "FEPAM")
    assert "None" not in env.event.headline


@pytest.mark.parametrize("body", ["{}", "null", "3", '"text"'])
def test_rs_reports_a_changed_feed(ext, fake_session, run, body):
    """Check that a changed feed gives an error and not an empty result."""
    with pytest.raises(sys_common(ext).FeedFormatError):
        run(ext.rs.fetch(fake_session({ext.rs.URL: body})))


@pytest.mark.parametrize("body", ["{}", "null", "3"])
def test_sc_reports_a_changed_feed(ext, fake_session, run, body):
    """Check the map endpoint."""
    with pytest.raises(sys_common(ext).FeedFormatError):
        run(ext.sc.fetch(fake_session({ext.sc.MAP_URL: body})))


@pytest.mark.parametrize(
    "body", ["[]", "null", '{"error": {"code": 500}}', '{"features": "x"}']
)
def test_pr_reports_an_arcgis_error(ext, fake_session, run, body):
    """Check that an ArcGIS error with HTTP 200 does not look like an empty layer."""
    with pytest.raises(sys_common(ext).FeedFormatError):
        run(ext.pr.fetch(fake_session({ext.pr.URL: body})))


def sys_common(ext):
    """Return the common module of the loaded package."""
    import sys

    return sys.modules[ext.rs.__name__.rsplit(".", 1)[0] + ".common"]


def test_failed_samples_keep_the_change_for_the_next_poll(ext, make_api, fake_session):
    """Check that a changed samples feed does not lose the alert."""
    good = json.dumps(
        [{"DATA": date.today().strftime("%d/%m/%Y"), "RESULTADO": "5000"}]
    )
    api = make_api("en")
    fetch = ext.extension.make_fetch(api, ext.sc)
    clean = [sc_row(CONDICAO="PRÓPRIO")]
    bodies = {ext.sc.MAP_URL: (clean, [sc_row()]), ext.sc.SAMPLES_URL: "{}"}
    session = fake_session(bodies)
    assert asyncio.run(fetch(session)) == []
    with pytest.raises(sys_common(ext).FeedFormatError):
        asyncio.run(fetch(session))
    session.bodies[ext.sc.SAMPLES_URL] = good
    assert len(asyncio.run(fetch(session))) == 1
    assert asyncio.run(fetch(session)) == []


def test_point_two_times_in_a_feed_does_not_repeat_alerts(ext):
    """Check that two rows of one point do not give news at each poll."""
    rows = [sc_row(), sc_row(CONDICAO="PRÓPRIO"), sc_row()]
    points = ext.sc.parse(rows)
    state = ext.extension.BulletinState()
    state.changes(points, date(2026, 3, 1))
    assert state.changes(points, date(2026, 3, 1)) == []


# ------------------------------------------------------------- settings


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan, True, "a", None, []])
def test_interval_that_is_not_a_number_uses_the_default(ext, make_api, value, caplog):
    """Check that the setup logs a warning and uses the default."""
    api = make_api("en", {"poll_interval": value})
    with caplog.at_level(logging.WARNING):
        ext.extension.setup(api)
    assert {poller[2] for poller in api.all_pollers} == {21600}
    assert caplog.text.count("poll_interval") == 1


def test_states_that_are_not_a_list_log_a_warning(ext, make_api, caplog):
    """Check that the setup tells the operator about this mistake."""
    api = make_api("en", {"states": "SC"})
    with caplog.at_level(logging.WARNING):
        ext.extension.setup(api)
    assert len(api.all_pollers) == 3
    assert "not a list" in caplog.text


def test_unknown_states_use_all_states(ext, make_api, caplog):
    """Check the warning for a list with no known state."""
    api = make_api("en", {"states": ["XX"]})
    with caplog.at_level(logging.WARNING):
        ext.extension.setup(api)
    assert len(api.all_pollers) == 3
    assert "No known state" in caplog.text


# ------------------------------------------------------------ presenter


@pytest.mark.parametrize("value", [123, "not a date"])
def test_presenter_shows_a_bad_date_as_text(ext, make_api, value):
    """Check that a bad date does not stop the message."""
    presenter = ext.presenter.make_presenter(make_api("en"))
    context = types.SimpleNamespace(
        title="Title",
        headline="",
        metadata={"status": "unsuitable", "sample_date": value, "severity_level": 2},
    )
    assert str(value) in presenter.present(context)
