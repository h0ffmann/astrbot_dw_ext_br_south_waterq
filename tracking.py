"""The state that decides which results are news. The state is in memory.

After a restart, the first poll records a new baseline and sends nothing.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from .providers.common import SUITABLE, UNSUITABLE

BRT = timezone(timedelta(hours=-3))  # Brasília time, no daylight saving time
SEVERITY = {SUITABLE: 0, UNSUITABLE: 2}  # white and yellow
MAX_AGE_DAYS = 90  # Hard limit. An older sample is past, not active.
PAST = "past"  # Saved status of a past result. It gave no alert, so no recovery.


def is_active(sample: date | None, today: date) -> bool:
    """Return True if the sample date is known and MAX_AGE_DAYS old or newer."""
    return sample is not None and (today - sample).days <= MAX_AGE_DAYS


def _is_news(prev, key) -> bool:
    """Return True for a new unsuitable bulletin or a recovery."""
    if key[1] == UNSUITABLE:
        return prev != key  # A new unsuitable bulletin
    return prev is not None and prev[1] == UNSUITABLE  # Suitable again


def _state_key(point: dict, today: date) -> tuple:
    """Return the value to store for a point. A past sample has the status PAST."""
    sample = point.get("sample_date")
    if sample is not None and not is_active(sample, today):
        return point["bulletin"], PAST
    return point["bulletin"], point["status"]


class BulletinState:
    """Store the last (bulletin, status) of each point of one state.

    The first call only records the baseline. A restart does not send old bulletins.
    """

    def __init__(self) -> None:
        self._seen: dict = {}
        self._ready = False

    def changes(self, points: list[dict], today: date | None = None) -> list[dict]:
        """Return the points with a new unsuitable bulletin or a recovery."""
        today = today or datetime.now(BRT).date()
        out = []
        # A point can be in a feed two times. The last row gives the one result.
        # Without this, the two results replace each other at each poll.
        for p in {point["key"]: point for point in points}.values():
            if p["status"] not in SEVERITY:
                continue  # Not collected or unknown: keep the last known state
            key = _state_key(p, today)
            prev = self._seen.get(p["key"])
            self._seen[p["key"]] = key
            if self._ready and key[1] != PAST and _is_news(prev, key):
                out.append(p)
        if points:
            self._ready = True
        return out

    def snapshot(self) -> tuple[dict, bool]:
        """Return a copy of the state."""
        return dict(self._seen), self._ready

    def restore(self, saved: tuple[dict, bool]) -> None:
        """Set the state back to a snapshot."""
        self._seen, self._ready = dict(saved[0]), saved[1]
