"""Point-in-time O(N) asset-native relative momentum research."""

import json
import math
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from typing import Mapping, cast

from qap.scanner.basket_protocol import (
    SCANNER_V1_BASKET,
    BasketProtocol,
    basket_protocol_identity,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon
from qap.scanner.slices import EvaluatedSeries
from qap.scanner.universe import UniverseSnapshot


class AssetMomentumError(ValueError):
    """Raised when an asset-momentum generation is internally inconsistent."""


class MomentumObservationStatus(StrEnum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class AssetMomentumObservation:
    asset_id: str
    venue_symbol: str
    status: MomentumObservationStatus
    reason: str
    source_artifact_fingerprint: str
    selection_slice_fingerprint: str
    bar_coverage: float
    longest_missing_run: int
    own_momentum: float | None
    common_mode: float | None
    relative_momentum: float | None
    common_mode_member_count: int
    rank: int | None = None


@dataclass(frozen=True, slots=True)
class AssetMomentumGeneration:
    protocol_id: str
    protocol_identity: str
    source_scan_id: str
    venue: str
    horizon: ScannerHorizon
    as_of: datetime
    universe_snapshot_id: str
    resolution: str
    formation_seconds: int
    observations: tuple[AssetMomentumObservation, ...]

    @property
    def momentum_scan_id(self) -> str:
        payload = {
            "schema": "qap.scanner.asset-momentum.v1",
            "protocol_identity": self.protocol_identity,
            "venue": self.venue,
            "horizon": self.horizon.value,
            "as_of": self.as_of.isoformat(),
            "universe_snapshot_id": self.universe_snapshot_id,
            "resolution": self.resolution,
            "formation_seconds": self.formation_seconds,
            "selected_slices": [
                [item.asset_id, item.selection_slice_fingerprint]
                for item in sorted(self.observations, key=lambda row: row.asset_id)
            ],
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


def _utc(value: datetime) -> datetime:
    if not isinstance(cast(object, value), datetime):
        raise TypeError("as_of must be a datetime")
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise AssetMomentumError("as_of must be timezone-aware UTC")
    return value.astimezone(UTC)


def _own_momentum(
    evaluated: EvaluatedSeries,
    *,
    as_of: datetime,
) -> tuple[float | None, str]:
    if evaluated.bar_coverage < SCANNER_V1_SLICE1.minimum_asset_coverage:
        return None, "insufficient_bar_coverage"
    if evaluated.longest_missing_run > SCANNER_V1_SLICE1.maximum_missing_generator_bars:
        return None, "missing_run_too_long"
    if not evaluated.bars:
        return None, "no_completed_bars"
    first = evaluated.bars[0]
    last = evaluated.bars[-1]
    if first.candle_open_time != evaluated.window_start:
        return None, "formation_start_price_missing"
    if last.bar_end_exclusive != as_of:
        return None, "formation_end_price_missing"
    start_price = first.open
    end_price = last.close
    if (
        not math.isfinite(start_price)
        or not math.isfinite(end_price)
        or start_price <= 0
        or end_price <= 0
    ):
        return None, "invalid_boundary_price"
    return math.log(end_price / start_price), "valid"


def build_asset_momentum_generation(
    snapshot: UniverseSnapshot,
    evaluated_by_asset: Mapping[str, EvaluatedSeries],
    *,
    as_of: datetime,
    protocol: BasketProtocol = SCANNER_V1_BASKET,
) -> AssetMomentumGeneration:
    """Compute one venue/horizon relative-momentum table without pair enumeration."""

    if not isinstance(cast(object, snapshot), UniverseSnapshot):
        raise TypeError("snapshot must be a UniverseSnapshot")
    cutoff = _utc(as_of)
    if snapshot.venue not in protocol.venues:
        raise AssetMomentumError("snapshot venue is not admitted by basket protocol")
    rule = protocol.momentum_rule(snapshot.horizon)
    by_asset = dict(evaluated_by_asset)
    expected_assets = {record.asset_id for record in snapshot.records}
    if set(by_asset) != expected_assets:
        raise AssetMomentumError("evaluated assets must match the universe snapshot")

    provisional: list[AssetMomentumObservation] = []
    valid_scores: list[tuple[str, float]] = []
    for record in snapshot.records:
        evaluated = by_asset[record.asset_id]
        if evaluated.instrument.venue != snapshot.venue:
            raise AssetMomentumError("evaluated asset venue mismatch")
        if evaluated.interval != rule.resolution:
            raise AssetMomentumError("evaluated asset resolution mismatch")
        if evaluated.eligible_information_end != cutoff:
            raise AssetMomentumError("evaluated asset cutoff mismatch")
        if evaluated.window_start != cutoff - rule.formation:
            raise AssetMomentumError("evaluated asset formation window mismatch")
        admitted = record.automatic_eligible or record.forensic_research_allowed
        score: float | None = None
        reason = record.eligibility_reason
        if admitted:
            score, reason = _own_momentum(evaluated, as_of=cutoff)
        status = (
            MomentumObservationStatus.VALID
            if admitted and score is not None
            else MomentumObservationStatus.INVALID
        )
        if score is not None:
            valid_scores.append((record.asset_id, score))
        provisional.append(
            AssetMomentumObservation(
                asset_id=record.asset_id,
                venue_symbol=record.venue_symbol,
                status=status,
                reason=reason,
                source_artifact_fingerprint=evaluated.source_artifact_fingerprint,
                selection_slice_fingerprint=evaluated.selection_slice_fingerprint,
                bar_coverage=evaluated.bar_coverage,
                longest_missing_run=evaluated.longest_missing_run,
                own_momentum=score,
                common_mode=None,
                relative_momentum=None,
                common_mode_member_count=len(valid_scores),
            )
        )

    valid_count = len(valid_scores)
    if valid_count < 2:
        observations = tuple(
            replace(
                item,
                status=MomentumObservationStatus.INVALID,
                reason=(
                    "insufficient_valid_assets_for_common_mode"
                    if item.own_momentum is not None
                    else item.reason
                ),
                common_mode_member_count=valid_count,
            )
            for item in provisional
        )
    else:
        common_mode = sum(score for _, score in valid_scores) / valid_count
        relatives = {asset_id: score - common_mode for asset_id, score in valid_scores}
        ranked = sorted(relatives, key=lambda asset: (-relatives[asset], asset))
        ranks = {asset_id: index for index, asset_id in enumerate(ranked, start=1)}
        observations = tuple(
            replace(
                item,
                common_mode=(common_mode if item.own_momentum is not None else None),
                relative_momentum=(
                    relatives[item.asset_id] if item.asset_id in relatives else None
                ),
                common_mode_member_count=valid_count,
                rank=ranks.get(item.asset_id),
            )
            for item in provisional
        )

    return AssetMomentumGeneration(
        protocol_id=protocol.protocol_id,
        protocol_identity=basket_protocol_identity(protocol),
        source_scan_id=snapshot.scan_id,
        venue=snapshot.venue,
        horizon=snapshot.horizon,
        as_of=cutoff,
        universe_snapshot_id=snapshot.universe_snapshot_id,
        resolution=rule.resolution.label,
        formation_seconds=int(rule.formation.total_seconds()),
        observations=tuple(sorted(observations, key=lambda item: item.asset_id)),
    )


__all__ = [
    "AssetMomentumError",
    "AssetMomentumGeneration",
    "AssetMomentumObservation",
    "MomentumObservationStatus",
    "build_asset_momentum_generation",
]
