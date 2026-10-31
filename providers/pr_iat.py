"""Paraná: IAT bathing water quality (ArcGIS layer).

See docs/brazil-water-quality-sources.md.

The layer stores dates at midnight in Brasília time (03:00 UTC).
The layer has one row for each point of the season, and one column for each campaign
(b1 to b11, with the dates in b1_data to b11_data). The last campaign with a result
is the current result. Many campaigns have no date. Then the sample date is the newest
date of this campaign or of an earlier campaign. The real sample is not older than
this date, so the 90-day limit is never too lenient.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .common import (
    SUITABLE,
    UNSUITABLE,
    FeedFormatError,
    get_json,
    join_name,
    point,
    rows,
    status_of,
    text_or_none,
    to_float,
    valid_id,
)

UF = "PR"
SOURCE_LABEL = "IAT/PR"
URL = (
    "https://geopr.iat.pr.gov.br/server/rest/services/Geoprocessamento/"
    "balneabilidade/FeatureServer/0/query"
    "?where=1%3D1&outFields=*&returnGeometry=false&f=json"
)
CAMPAIGNS = 11
STATUS = {"Propria": SUITABLE, "Impropria": UNSUITABLE}
BRT = timezone(timedelta(hours=-3))


def _epoch_date(ms):
    """Return the date of an epoch time in milliseconds, or None."""
    if isinstance(ms, bool) or not isinstance(ms, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ms / 1000, BRT).date()
    except (ValueError, OverflowError, OSError):  # NaN, or a date out of range
        return None


def last_campaign(attrs: dict):
    """Return (campaign number, status, sample date) of the last campaign with a result.

    Return None if no campaign has a result.
    """
    known = None
    last = None
    for n in range(1, CAMPAIGNS + 1):
        known = _epoch_date(attrs.get(f"b{n}_data")) or known
        value = attrs.get(f"b{n}")
        value = value.strip() if isinstance(value, str) else ""
        if value:
            last = (n, status_of(STATUS, value), known)
    return last


def parse(data) -> list[dict]:
    """Keep the points that have a code and a result."""
    out = []
    features = data.get("features") if isinstance(data, dict) else None
    for feature in rows(features):
        attrs = feature.get("attributes")
        if isinstance(attrs, dict) and attrs.get("cod") and valid_id(attrs.get("cod")):
            last = last_campaign(attrs)
            if last is not None:
                out.append(_point(attrs, *last))
    return out


def _point(attrs: dict, number: int, status, sample) -> dict:
    """Return the common point of one layer row."""
    return point(
        attrs,
        key=str(attrs["cod"]),
        uf=UF,
        beach=join_name(attrs.get("praia_rio"), attrs.get("local")),
        municipio=text_or_none(attrs.get("municipio")),
        ibge=attrs.get("cod_ibge"),
        latitude=to_float(attrs.get("latitude")),
        longitude=to_float(attrs.get("longitude")),
        laboratorio="IAT",
        status=status,
        bulletin=f"{attrs.get('ano1')}-b{number}",
        sample_date=sample,
    )


async def fetch(session) -> list[dict]:
    """Get all points of the season with the last campaign."""
    data = await get_json(session, URL, expected=dict)
    # ArcGIS sends an error as a JSON object with HTTP 200.
    if not isinstance(data.get("features"), list):
        raise FeedFormatError(URL)
    return parse(data)


async def complete(_session, points: list[dict]) -> list[dict]:
    """The points already have a sample date (or None)."""
    return points
