"""The poller of one state. The host calls it with an HTTP session."""

from __future__ import annotations

from datetime import datetime

from .envelopes import build_envelope
from .tracking import BRT, BulletinState, is_active


class StatePoller:
    """Return the envelopes of the changed points of one state.

    Each state has its own baseline.
    """

    def __init__(self, api, provider) -> None:
        self._api, self._provider = api, provider
        self._state = BulletinState()

    async def __call__(self, session) -> list:
        """Read the feed and return the envelopes."""
        points = await self._provider.fetch(session)
        saved = self._state.snapshot()
        news = self._state.changes(points)
        if not news:
            return []
        try:
            news = await self._provider.complete(session, news)
        except BaseException:
            # A failure or a timeout: try again at the next poll.
            self._state.restore(saved)
            raise
        today = datetime.now(BRT).date()
        label = self._provider.SOURCE_LABEL
        # Past results give no event.
        active = (p for p in news if is_active(p["sample_date"], today))
        return [build_envelope(self._api, p, label) for p in active]


def make_fetch(api, provider) -> StatePoller:
    """Return the poller of one state."""
    return StatePoller(api, provider)
