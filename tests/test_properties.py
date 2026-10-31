"""Property tests. The parsers must accept any JSON value without an exception."""

from __future__ import annotations

import math
import types
from datetime import date

from hypothesis import given
from hypothesis import strategies as st

JSON = st.recursive(
    st.none()
    | st.booleans()
    | st.integers()
    | st.floats()
    | st.text(max_size=12)
    | st.sampled_from(["Impropria", "Propria", "IMPRÓPRIO", "PRÓPRIO", "24/02/2026"]),
    lambda children: (
        st.lists(children, max_size=3)
        | st.dictionaries(st.text(max_size=6), children, max_size=3)
    ),
    max_leaves=8,
)
CODE = st.integers(1, 4) | JSON
RS_ROW = st.fixed_dictionaries(
    {
        "codLocal": CODE,
        "nome": JSON,
        "nomeMunicipio": JSON,
        "ibge": JSON,
        "latitude": JSON,
        "longitude": JSON,
        "laboratorio": JSON,
        "situacao": st.sampled_from([0, 1, 2, 3]) | JSON,
        "ultimaColeta": st.just("24/02/2026") | JSON,
    }
)
SC_ROW = st.fixed_dictionaries(
    {
        "CODIGO": CODE,
        "BALNEARIO": JSON,
        "PONTO_NOME": JSON,
        "MUNICIPIO": JSON,
        "MUNICIPIO_COD_IBGE": JSON,
        "LATITUDE": JSON,
        "LONGITUDE": JSON,
        "CONDICAO": st.sampled_from(["PRÓPRIO", "IMPRÓPRIO"]) | JSON,
    }
)
PR_ATTRS = st.fixed_dictionaries(
    {
        "cod": CODE,
        "praia_rio": JSON,
        "local": JSON,
        "municipio": JSON,
        "cod_ibge": JSON,
        "latitude": JSON,
        "longitude": JSON,
        "ano1": JSON,
        "b1": st.sampled_from(["Propria", "Impropria", ""]) | JSON,
        "b1_data": st.just(1766026800000) | JSON,
        "b2": st.sampled_from(["Propria", "Impropria", ""]) | JSON,
        "b2_data": JSON,
    }
)
PR_FEATURE = st.fixed_dictionaries({"attributes": PR_ATTRS | JSON})
TODAY = date(2026, 3, 1)


def text_of(ext, api, point):
    """Return the message text of a point."""
    event = ext.extension.build_envelope(api, point, "Source").event
    context = types.SimpleNamespace(
        title=event.title, headline=event.headline, metadata=event.metadata
    )
    return ext.presenter.make_presenter(api).present(context)


@given(JSON)
def test_all_parsers_accept_any_json(ext, data):
    """Check any top-level value."""
    assert isinstance(ext.rs.parse(data), list)
    assert isinstance(ext.sc.parse(data), list)
    assert isinstance(ext.pr.parse(data), list)


@given(st.lists(RS_ROW | JSON, max_size=5))
def test_rs_points_give_a_message(ext, make_api, rows):
    """Check that each point with a known status gives a text."""
    api = make_api("en")
    for point in ext.rs.parse(rows):
        if point["status"]:
            assert text_of(ext, api, point)


@given(st.lists(SC_ROW | JSON, max_size=5))
def test_sc_points_give_a_message(ext, make_api, rows):
    """Check that each point with a known status gives a text."""
    api = make_api("en")
    for point in ext.sc.parse(rows):
        if point["status"]:
            assert text_of(ext, api, point)


@given(st.lists(PR_FEATURE | JSON, max_size=5))
def test_pr_points_give_a_message(ext, make_api, features):
    """Check that each point with a known status gives a text."""
    api = make_api("en")
    for point in ext.pr.parse({"features": features}):
        if point["status"]:
            assert text_of(ext, api, point)


@given(st.lists(RS_ROW | JSON, max_size=5))
def test_positions_are_finite_or_none(ext, rows):
    """Check that the presenter can format each position."""
    for point in ext.rs.parse(rows):
        for value in (point["latitude"], point["longitude"]):
            assert value is None or math.isfinite(value)


@given(st.lists(SC_ROW, max_size=6))
def test_state_accepts_any_parsed_point(ext, rows):
    """Check that a first poll records a baseline and sends nothing."""
    state = ext.extension.BulletinState()
    assert state.changes(ext.sc.parse(rows), TODAY) == []


@given(st.lists(SC_ROW, max_size=6))
def test_second_poll_of_the_same_feed_sends_nothing(ext, rows):
    """Check that the same feed never gives news."""
    state = ext.extension.BulletinState()
    points = ext.sc.parse(rows)
    state.changes(points, TODAY)
    assert state.changes(points, TODAY) == []


@given(JSON)
def test_selected_states_are_known(ext, value):
    """Check that the result has only known states."""
    assert set(ext.states.selected_states({"states": value})) <= set(ext.states.STATES)


@given(st.dates(), st.dates())
def test_is_active_follows_the_limit(ext, sample, today):
    """Check the 90-day limit."""
    expected = (today - sample).days <= ext.extension.MAX_AGE_DAYS
    assert ext.extension.is_active(sample, today) is expected
