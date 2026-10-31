"""Text presenter for the br_south_waterq weather events."""

from __future__ import annotations

from datetime import date

EMOJI = {0: "✅", 2: "🟡"}


def make_presenter(api):
    """Return a presenter class that is bound to the translator of the extension."""

    class BrSouthWaterqPresenter:
        """Text presenter for the bathing water quality events."""

        @classmethod
        def present(cls, display_context, _options=None) -> str:
            """Return the message text for a weather display context."""
            return render(api.t, display_context)

    return BrSouthWaterqPresenter


def render(t, context) -> str:
    """Return the message text. The function t translates a key."""
    md = context.metadata or {}
    level = int(md.get("severity_level") or 0)
    lines = [
        f"{EMOJI.get(level, '⚪')} {context.title}",
        context.headline,
        t("present.status", status=t(f"status.{md.get('status')}")),
        _sample_line(t, md),
        _ecoli_line(t, md),
        _lab_line(t, md),
        _location_line(t, md),
        t("present.criterion"),
        t("present.source", source=md.get("source_label") or ""),
    ]
    return "\n".join(line for line in lines if line)


def _sample_line(t, md: dict) -> str:
    """Return the line with the sample date, if the point has a date."""
    sample = _fmt_date(md.get("sample_date"), t("format.date"))
    return t("present.sample", date=sample) if sample else ""


def _ecoli_line(t, md: dict) -> str:
    """Return the line with the E. coli result, if the point has a result."""
    if md.get("ecoli") is None:
        return ""
    value = f"{md['ecoli']:.10g}".replace(".", t("format.decimal"))
    return t("present.ecoli", value=value)


def _lab_line(t, md: dict) -> str:
    """Return the line with the laboratory, if the point has a laboratory."""
    return t("present.lab", lab=md["laboratorio"]) if md.get("laboratorio") else ""


def _location_line(t, md: dict) -> str:
    """Return the line with the position, if the point has a position."""
    where = _coords(md, t("format.decimal"))
    return t("present.location", coords=where) if where else ""


def _fmt_date(iso, fmt: str) -> str:
    """Return an ISO date in the format of the language."""
    if not iso:
        return ""
    try:
        return date.fromisoformat(iso).strftime(fmt)
    except (TypeError, ValueError):
        return str(iso)


def _coords(md: dict, dec: str) -> str:
    """Return the position with the decimal mark of the language."""
    lat, lon = md.get("latitude"), md.get("longitude")
    if lat is None or lon is None:
        return ""
    return f"{lat:.4f}; {lon:.4f}".replace(".", dec)
