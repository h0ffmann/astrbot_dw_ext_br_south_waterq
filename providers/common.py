"""Helpers for the provider modules."""

from __future__ import annotations

import json
import math
from datetime import date, datetime

SUITABLE = "suitable"
UNSUITABLE = "unsuitable"
DATE_FMT = "%d/%m/%Y"


class FeedFormatError(Exception):
    """A feed sent a JSON value of an unexpected type."""


def to_float(value) -> float | None:
    """Return the value as a finite float, or None."""
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def valid_id(value) -> bool:
    """Return True for a value that can identify a point."""
    return isinstance(value, (int, str)) and not isinstance(value, bool) and value != ""


def status_of(table: dict, value):
    """Return the status of a feed value, or None."""
    return table.get(value) if isinstance(value, (int, str)) else None


def text_or_none(value) -> str | None:
    """Return a text value that is not empty, or None."""
    return value if isinstance(value, str) and value else None


def join_name(*parts) -> str:
    """Join the text parts of a name."""
    return " - ".join(part for part in parts if isinstance(part, str) and part)


def rows(value) -> list[dict]:
    """Return the dict items of a feed list."""
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def to_date(text, fmt: str = DATE_FMT) -> date | None:
    """Return the text as a date, or None."""
    try:
        return datetime.strptime(text, fmt).date()
    except (TypeError, ValueError):
        return None


def point(raw: dict, **fields) -> dict:
    """Return a common point. Missing fields get None."""
    keys = (
        "key",
        "uf",
        "beach",
        "municipio",
        "ibge",
        "latitude",
        "longitude",
        "laboratorio",
        "status",
        "bulletin",
        "sample_date",
    )
    return {"raw": raw, **{k: fields.get(k) for k in keys}}


async def get_json(
    session, url: str, data: dict | None = None, expected: type | None = None
):
    """Send GET, or POST with form data. Read the body as JSON.

    Some servers send JSON as text/html, or with a byte order mark.
    If expected is set, raise FeedFormatError for a different top-level type.
    The host logs the error. Thus, a changed feed does not look like an empty feed.
    """
    request = session.post(url, data=data) if data is not None else session.get(url)
    async with request as resp:
        resp.raise_for_status()
        body = json.loads((await resp.text()).lstrip("﻿"))
    if expected is not None and not isinstance(body, expected):
        raise FeedFormatError(url)
    return body
