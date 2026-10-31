"""Build the source entry and the event envelopes of the host."""

from __future__ import annotations

from datetime import datetime, timezone

from .tracking import SEVERITY

ID = "br_south_waterq"
SOURCE = f"{ID}_balneabilidade"
PRESENTER_KEY = f"{ID}_weather"


def _metadata(point: dict, source_label: str) -> dict:
    """Return the event metadata of a common point."""
    status, sample = point["status"], point["sample_date"]
    return {
        "severity_level": SEVERITY[status],
        "hazard": "water_quality",
        "status": status,
        "point": point["key"],
        "beach": point["beach"],
        "municipio": point["municipio"],
        "ibge": point["ibge"],
        "uf": point["uf"],
        "latitude": point["latitude"],
        "longitude": point["longitude"],
        "laboratorio": point["laboratorio"],
        "sample_date": sample.isoformat() if sample else None,
        "ecoli": point.get("ecoli"),
        "source_label": source_label,
    }


def _event_id(point: dict) -> str:
    """Return the event id. The id has the sample date, or the bulletin if no date."""
    sample = point["sample_date"]
    tag = f"{sample:%Y%m%d}" if sample else point["bulletin"]
    return f"{ID}_{point['uf'].lower()}_{point['key']}_{tag}_{point['status']}"


def build_envelope(api, point: dict, source_label: str, now: datetime | None = None):
    """Build the event envelope for a common point.

    The event time is the detection time, not the sample date.
    The host time rule drops events older than 1 h.
    """
    m = api.models
    now = now or datetime.now(timezone.utc)
    metadata = _metadata(point, source_label)
    identity = m.EventIdentity(
        event_id=_event_id(point),
        source_id=SOURCE,
        event_type="weather_alarm",
        provider_family="extension",
        source_enum=SOURCE,
        published_at=now,
    )
    event = m.WeatherEvent(
        title=api.t(f"title.{point['status']}"),
        headline=api.t(
            "headline",
            beach=metadata["beach"] or "-",
            municipio=metadata["municipio"] or "-",
            uf=metadata["uf"],
        ),
        effective_at=now,
        metadata=metadata,
    )
    payload = m.SourcePayload(
        source_id=SOURCE, provider_family="extension", raw=point["raw"]
    )
    return m.EventEnvelope(identity=identity, event=event, payload=payload)


def source_entry(api):
    """Build the host catalog entry of the source."""
    m = api.models
    return m.SourceEntry(
        source_id=SOURCE,
        source_enum=SOURCE,
        source_type=m.SourceType.WEATHER,
        provider_family=m.ProviderFamily.EXTENSION,
        config_group="extensions",
        config_key=SOURCE,
        parser_name="",
        presentation_type="weather",
        text_presenter_key=PRESENTER_KEY,
        report_policy="none",
        intensity_mode="none",
        priority=1,
        display_name=api.t("source.balneabilidade"),
        description=api.t("source.balneabilidade.desc"),
        default_timezone="America/Sao_Paulo",
        fingerprint_prefix=SOURCE,
        dispatch_family=SOURCE,
        provider_aliases=(SOURCE,),
        routing_tags=("extension", "brazil", "south", "http"),
    )
