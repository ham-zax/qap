# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Read-only projections over persisted Phase-10 relationship evidence."""

from collections import defaultdict
from datetime import datetime
from typing import Any, cast

from qap.api.relationship_views import requested_pair_orientation
from qap.api.schemas import (
    PairEvidenceDto,
    RelationshipEvidencePointDto,
    RelationshipEvidenceSeriesDto,
)
from qap.experiment import LoadedRunArtifacts
from qap.portfolio import AssetId, PairOrientation
from qap.relationship import EvidenceReciprocity
from qap.relationship.models import reorient_model_evidence_value


def _text(row: dict[str, Any], field: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"evidence field {field} must be a non-empty string")
    return value


def _integer(row: dict[str, Any], field: str) -> int:
    value = row.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"evidence field {field} must be an integer")
    return value


def pair_evidence(
    loaded: LoadedRunArtifacts,
    *,
    asset_x: str,
    asset_y: str,
    orientation: str | None,
) -> PairEvidenceDto:
    """Project persisted model evidence for one canonical pair without fitting."""

    requested = requested_pair_orientation(
        asset_x=asset_x,
        asset_y=asset_y,
        orientation=orientation,
    )
    pair_id = requested.pair_id
    table = loaded.evidence
    if table is None:
        return PairEvidenceDto(
            run_id=loaded.provenance.run_id,
            canonical_pair=(pair_id.first.key, pair_id.second.key),
            requested_orientation=f"{requested.base.key}/{requested.quote.key}",
            series=(),
        )

    groups: dict[
        tuple[str, str, str, str, str, str, str, str],
        list[RelationshipEvidencePointDto],
    ] = defaultdict(list)
    raw_rows = cast(list[dict[str, Any]], table.to_pylist())
    for row in raw_rows:
        if (
            _text(row, "canonical_first") != pair_id.first.key
            or _text(row, "canonical_second") != pair_id.second.key
        ):
            continue
        base = _text(row, "orientation_base")
        quote = _text(row, "orientation_quote")
        persisted_orientation = PairOrientation(
            base=AssetId(base),
            quote=AssetId(quote),
        )
        model_id = _text(row, "model_id")
        evidence_field = _text(row, "evidence_field")
        evidence_reciprocity = EvidenceReciprocity(_text(row, "evidence_reciprocity"))
        group_key = (
            f"{base}/{quote}",
            model_id,
            _text(row, "model_version"),
            evidence_field,
            _text(row, "fit_reciprocity"),
            evidence_reciprocity.value,
            _text(row, "base_source_fingerprint"),
            _text(row, "quote_source_fingerprint"),
        )
        timestamp = row.get("timestamp")
        if not isinstance(timestamp, datetime):
            raise ValueError("evidence timestamp must be a datetime")
        raw_value = row.get("value")
        if raw_value is not None and not isinstance(raw_value, float):
            raise ValueError("evidence value must be a float or null")
        oriented_value = reorient_model_evidence_value(
            model_id=model_id,
            evidence_field=evidence_field,
            evidence_reciprocity=evidence_reciprocity,
            persisted_orientation=persisted_orientation,
            requested_orientation=requested,
            value=raw_value,
        )
        groups[group_key].append(
            RelationshipEvidencePointDto(
                timestamp=timestamp,
                value=oriented_value,
                status=_text(row, "status"),
                window_observations=_integer(row, "window_observations"),
                required_observations=_integer(row, "required_observations"),
                coverage_observations=_integer(row, "coverage_observations"),
                input_fingerprint=_text(row, "input_fingerprint"),
            )
        )

    series = tuple(
        RelationshipEvidenceSeriesDto(
            persisted_orientation=key[0],
            model_id=key[1],
            model_version=key[2],
            evidence_field=key[3],
            fit_reciprocity=key[4],
            evidence_reciprocity=key[5],
            base_source_fingerprint=key[6],
            quote_source_fingerprint=key[7],
            points=tuple(sorted(points, key=lambda point: point.timestamp)),
        )
        for key, points in sorted(groups.items())
    )
    return PairEvidenceDto(
        run_id=loaded.provenance.run_id,
        canonical_pair=(pair_id.first.key, pair_id.second.key),
        requested_orientation=f"{requested.base.key}/{requested.quote.key}",
        series=series,
    )


__all__ = ["pair_evidence"]
