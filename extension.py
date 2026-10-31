"""South of Brazil (RS, SC, PR): bathing water quality of the state agencies.

Each state has a provider module (see providers/ and states.py). The extension sends
an event when a point becomes unsuitable or suitable again. A result with a sample
older than MAX_AGE_DAYS, or with no known sample date, is past. The extension does
not send it.
"""

from __future__ import annotations

from .envelopes import PRESENTER_KEY, SOURCE, build_envelope, source_entry
from .pollers import make_fetch
from .presenter import make_presenter
from .settings import int_setting
from .states import STATES, selected_states
from .tracking import MAX_AGE_DAYS, BulletinState, is_active

__all__ = [
    "MAX_AGE_DAYS",
    "BulletinState",
    "build_envelope",
    "int_setting",
    "is_active",
    "make_fetch",
    "setup",
]

DEFAULT_INTERVAL = 21600  # 6 h. The agencies publish about one bulletin each week.


def _states(api, cfg: dict) -> tuple[str, ...]:
    """Return the selected states. Log a warning if the setting is not usable."""
    ufs = selected_states(cfg)
    if not ufs:
        api.logger.warning(
            f"No known state in 'states'. Use all states {list(STATES)}."
        )
        return tuple(STATES)
    if cfg.get("states") and not isinstance(cfg["states"], (list, tuple)):
        api.logger.warning("Setting 'states' is not a list. Use all states.")
    return ufs


def setup(api) -> None:
    """Entry point of the extension.

    Register the presenter and the source. Register one poller for each selected
    state. An error in one state does not stop the pollers of the other states.
    """
    cfg = api.config or {}
    ufs = _states(api, cfg)
    interval = int_setting(api, cfg, "poll_interval", DEFAULT_INTERVAL)
    api.register_presenter(PRESENTER_KEY, make_presenter(api))
    api.register_source(source_entry(api))
    for uf in ufs:
        api.register_poller(
            SOURCE,
            make_fetch(api, STATES[uf]),
            interval_seconds=interval,
            timeout_seconds=60,  # SC asks for the samples of each changed point
        )
