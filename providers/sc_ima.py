"""Santa Catarina: IMA bathing water quality.

See docs/brazil-water-quality-sources.md.

The map endpoint gives the status of all points, but no sample date. The samples
endpoint gives the dates of one point. Thus, the provider asks for the samples only
for the changed points. A new sample with the same status is not news in SC.
"""

from __future__ import annotations

from .common import (
    SUITABLE,
    UNSUITABLE,
    get_json,
    join_name,
    point,
    rows,
    status_of,
    text_or_none,
    to_date,
    to_float,
    valid_id,
)

UF = "SC"
SOURCE_LABEL = "IMA/SC"
BASE = "https://balneabilidade.ima.sc.gov.br"
MAP_URL = f"{BASE}/relatorio/mapa"
SAMPLES_URL = f"{BASE}/relatorio/analisesPonto"
STATUS = {"PRÓPRIO": SUITABLE, "IMPRÓPRIO": UNSUITABLE}  # Other values: unknown


def parse(data) -> list[dict]:
    """Keep the points that have a code. The sample date is None."""
    out = []
    for raw in rows(data):
        if not raw.get("CODIGO") or not valid_id(raw.get("CODIGO")):
            continue
        out.append(
            point(
                raw,
                key=raw["CODIGO"],
                uf=UF,
                beach=join_name(raw.get("BALNEARIO"), raw.get("PONTO_NOME")),
                municipio=text_or_none(raw.get("MUNICIPIO")),
                ibge=raw.get("MUNICIPIO_COD_IBGE"),
                latitude=to_float(raw.get("LATITUDE")),
                longitude=to_float(raw.get("LONGITUDE")),
                laboratorio="IMA",
                status=status_of(STATUS, raw.get("CONDICAO")),
            )
        )
    return out


def newest_sample(samples) -> dict | None:
    """Return the sample with the newest date, or None."""
    dated = [(d, s) for s in rows(samples) if (d := to_date(s.get("DATA")))]
    return max(dated, key=lambda item: item[0])[1] if dated else None


async def fetch(session) -> list[dict]:
    """Get all points with the current status."""
    return parse(await get_json(session, MAP_URL, expected=list))


async def complete(session, points: list[dict]) -> list[dict]:
    """Add the date and the E. coli result of the newest sample to each point."""
    for p in points:
        sample = newest_sample(
            await get_json(
                session, SAMPLES_URL, data={"codigo": p["key"]}, expected=list
            )
        )
        if sample is not None:
            p["sample_date"] = to_date(sample["DATA"])
            p["bulletin"] = p["sample_date"].isoformat()
            p["ecoli"] = to_float(sample.get("RESULTADO"))
    return points
