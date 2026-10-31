"""Read the settings of the extension. A bad value does not stop the setup."""

from __future__ import annotations


def int_setting(api, cfg: dict, key: str, default: int) -> int:
    """Return cfg[key] as an int.

    If the value is not a finite number, log a warning and return the default.
    """
    value = cfg.get(key, default)
    try:
        if not isinstance(value, bool):
            return int(value)
    except (TypeError, ValueError, OverflowError):
        pass
    api.logger.warning(f"Setting '{key}' is not a number. Use {default}.")
    return default
