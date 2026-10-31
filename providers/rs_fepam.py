"""Rio Grande do Sul: FEPAM Programa Balneabilidade.

See docs/brazil-water-quality-sources.md.
"""

from __future__ import annotations

from .common import (
    SUITABLE,
    UNSUITABLE,
    get_json,
    point,
    rows,
    status_of,
    text_or_none,
    to_date,
    to_float,
    valid_id,
)

UF = "RS"
SOURCE_LABEL = "FEPAM / PROCERGS"
URL = "https://secweb.procergs.com.br/baln/rest/locais"
# situacao. The values 0 and 1 mean "not collected".
STATUS = {2: SUITABLE, 3: UNSUITABLE}


def parse(data) -> list[dict]:
    """Keep the points that have a code and a known sample date."""
    out = []
    for raw in rows(data):
        code = raw.get("codLocal")
        if not isinstance(code, int) or not valid_id(code):
            continue
        sample = to_date(raw.get("ultimaColeta"))
        if sample is None:
            continue
        out.append(
            point(
                raw,
                key=str(code),
                uf=UF,
                beach=text_or_none(raw.get("nome")),
                municipio=text_or_none(raw.get("nomeMunicipio")),
                ibge=raw.get("ibge"),
                latitude=to_float(raw.get("latitude")),
                longitude=to_float(raw.get("longitude")),
                laboratorio=text_or_none(raw.get("laboratorio")),
                status=status_of(STATUS, raw.get("situacao")),
                bulletin=sample.isoformat(),
                sample_date=sample,
            )
        )
    return out


async def fetch(session) -> list[dict]:
    """Get all points with the result of the last bulletin."""
    return parse(await get_json(session, URL, expected=list))


async def complete(_session, points: list[dict]) -> list[dict]:
    """The points already have the sample dates."""
    return points
