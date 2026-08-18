"""Deterministic normalized-log SSD candidate graph."""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import cast

from qap.portfolio import AssetId, PairId
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    ScannerProtocol,
)
from qap.scanner.slices import EvaluatedSeries
from qap.scanner.universe import UniverseSnapshot


def normalized_log_ssd(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    """Return mean squared distance between normalized log-price paths."""

    if len(left) != len(right):
        raise ValueError("normalized-log SSD paths must have equal length")
    if len(left) < 2:
        raise ValueError("normalized-log SSD requires at least two observations")
    if any(not math.isfinite(value) or value <= 0.0 for value in (*left, *right)):
        raise ValueError("normalized-log SSD prices must be positive finite")

    left_origin = math.log(left[0])
    right_origin = math.log(right[0])
    squared: list[float] = []
    for left_value, right_value in zip(left, right, strict=True):
        left_normalized = math.log(left_value) - left_origin
        right_normalized = math.log(right_value) - right_origin
        difference = left_normalized - right_normalized
        squared.append(difference * difference)
    result = math.fsum(squared) / len(squared)
    if not math.isfinite(result):
        raise ValueError("normalized-log SSD must remain finite")
    return result


def _pair_key(first: AssetId, second: AssetId) -> str:
    pair = PairId(first, second)
    return f"{pair.first.key}/{pair.second.key}"


@dataclass(frozen=True, slots=True)
class ManualPairPin:
    asset_a: AssetId
    asset_b: AssetId

    def __post_init__(self) -> None:
        if not isinstance(cast(object, self.asset_a), AssetId) or not isinstance(
            cast(object, self.asset_b), AssetId
        ):
            raise TypeError("manual pin assets must be AssetId values")
        pair = PairId(self.asset_a, self.asset_b)
        object.__setattr__(self, "asset_a", pair.first)
        object.__setattr__(self, "asset_b", pair.second)

    @property
    def pair_id(self) -> str:
        return _pair_key(self.asset_a, self.asset_b)


@dataclass(frozen=True, slots=True)
class NeighborRecord:
    scan_id: str
    venue: str
    horizon: str
    pair_id: str
    asset_a: str
    asset_b: str
    ssd_distance: float
    rank_from_a: int
    rank_from_b: int
    selected_by_a: bool
    selected_by_b: bool
    automatic_neighbor_selected: bool
    manual_pinned: bool


@dataclass(frozen=True, slots=True)
class SsdGraph:
    scan_id: str
    venue: str
    horizon: str
    universe_snapshot_id: str
    eligible_asset_count: int
    total_valid_pair_comparisons: int
    distance_digest: str
    records: tuple[NeighborRecord, ...]


@dataclass(frozen=True, slots=True)
class GraphMetadataRecord:
    scan_id: str
    venue: str
    horizon: str
    universe_snapshot_id: str
    generator_version: str
    graph_interval: str
    graph_window_seconds: int
    neighbors_per_asset: int
    minimum_pair_coverage: float
    maximum_missing_generator_bars: int
    eligible_asset_count: int
    total_valid_pair_comparisons: int
    input_selection_slice_fingerprints: tuple[str, ...]
    distance_digest: str


@dataclass(frozen=True, slots=True)
class _Comparison:
    pair_id: str
    asset_a: str
    asset_b: str
    distance: float


def _common_closes(
    left: EvaluatedSeries,
    right: EvaluatedSeries,
) -> tuple[tuple[float, ...], tuple[float, ...], float]:
    if left.interval != right.interval:
        raise ValueError("graph series must share one interval")
    if (
        left.window_start != right.window_start
        or left.eligible_information_end != right.eligible_information_end
    ):
        raise ValueError("graph series must share one evaluation window")
    if left.expected_bar_count != right.expected_bar_count:
        raise ValueError("graph series must share one expected grid")

    left_by_end = {bar.bar_end_exclusive: bar.close for bar in left.bars}
    right_by_end = {bar.bar_end_exclusive: bar.close for bar in right.bars}
    common = tuple(sorted(set(left_by_end) & set(right_by_end)))
    coverage = len(common) / left.expected_bar_count
    return (
        tuple(left_by_end[timestamp] for timestamp in common),
        tuple(right_by_end[timestamp] for timestamp in common),
        coverage,
    )


def _distance_digest(
    *,
    venue: str,
    horizon: str,
    comparisons: tuple[_Comparison, ...],
) -> str:
    digest = sha256()
    for comparison in sorted(comparisons, key=lambda item: item.pair_id):
        for value in (
            venue,
            horizon,
            comparison.pair_id,
            comparison.distance.hex(),
        ):
            digest.update(value.encode("utf-8"))
            digest.update(b"\0")
    return digest.hexdigest()


def build_ssd_graph(
    snapshot: UniverseSnapshot,
    *,
    series_by_asset: Mapping[str, EvaluatedSeries],
    manual_pins: tuple[ManualPairPin, ...] = (),
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> SsdGraph:
    """Build one venue/horizon SSD neighborhood graph from admitted assets only."""

    if not isinstance(cast(object, snapshot), UniverseSnapshot):
        raise TypeError("snapshot must be a UniverseSnapshot")
    if not isinstance(cast(object, series_by_asset), Mapping):
        raise TypeError("series_by_asset must be a mapping")

    eligible_records = snapshot.eligible_records
    eligible_assets = tuple(sorted(record.asset_id for record in eligible_records))
    eligible_set = set(eligible_assets)
    if len(eligible_assets) != len(eligible_set):
        raise ValueError("eligible universe contains duplicate assets")

    series: dict[str, EvaluatedSeries] = {}
    for asset in eligible_assets:
        try:
            evaluated = series_by_asset[asset]
        except KeyError as exc:
            raise ValueError(
                f"missing evaluated series for eligible asset {asset}"
            ) from exc
        if not isinstance(cast(object, evaluated), EvaluatedSeries):
            raise TypeError("series_by_asset values must be EvaluatedSeries")
        if evaluated.instrument.venue != snapshot.venue:
            raise ValueError("graph series must belong to the requested venue")
        if evaluated.interval != protocol.horizon(snapshot.horizon).graph_interval:
            raise ValueError("graph series interval must match the requested horizon")
        if evaluated.bar_coverage < protocol.minimum_asset_coverage:
            raise ValueError("eligible graph series violates asset coverage contract")
        if evaluated.longest_missing_run > protocol.maximum_missing_generator_bars:
            raise ValueError("eligible graph series violates missing-run contract")
        series[asset] = evaluated

    comparisons: list[_Comparison] = []
    by_pair: dict[str, _Comparison] = {}
    for left_index, left_asset in enumerate(eligible_assets):
        for right_asset in eligible_assets[left_index + 1 :]:
            left_values, right_values, common_coverage = _common_closes(
                series[left_asset],
                series[right_asset],
            )
            if common_coverage < protocol.minimum_pair_coverage or len(left_values) < 2:
                continue
            try:
                distance = normalized_log_ssd(left_values, right_values)
            except ValueError:
                continue
            pair_id = _pair_key(AssetId(left_asset), AssetId(right_asset))
            comparison = _Comparison(
                pair_id=pair_id,
                asset_a=min(left_asset, right_asset),
                asset_b=max(left_asset, right_asset),
                distance=distance,
            )
            comparisons.append(comparison)
            by_pair[pair_id] = comparison

    peer_rows: dict[str, list[tuple[float, str, str]]] = {
        asset: [] for asset in eligible_assets
    }
    for comparison in comparisons:
        peer_rows[comparison.asset_a].append(
            (comparison.distance, comparison.pair_id, comparison.asset_b)
        )
        peer_rows[comparison.asset_b].append(
            (comparison.distance, comparison.pair_id, comparison.asset_a)
        )

    ranks: dict[tuple[str, str], int] = {}
    for asset, peers in peer_rows.items():
        ordered = sorted(peers, key=lambda item: (item[0], item[1]))
        for rank, (_distance, _pair_id_value, peer) in enumerate(ordered, start=1):
            ranks[(asset, peer)] = rank

    retained: set[str] = set()
    k = protocol.neighbors_per_asset
    for comparison in comparisons:
        if (
            ranks[(comparison.asset_a, comparison.asset_b)] <= k
            or ranks[(comparison.asset_b, comparison.asset_a)] <= k
        ):
            retained.add(comparison.pair_id)

    pinned_pairs: set[str] = set()
    for pin in manual_pins:
        if not isinstance(cast(object, pin), ManualPairPin):
            raise TypeError("manual_pins must contain ManualPairPin values")
        if pin.asset_a.key not in eligible_set or pin.asset_b.key not in eligible_set:
            raise ValueError(
                "manual pin assets must be eligible for this venue/horizon"
            )
        if pin.pair_id not in by_pair:
            raise ValueError("manual pin pair lacks valid common graph data")
        pinned_pairs.add(pin.pair_id)
        retained.add(pin.pair_id)

    records: list[NeighborRecord] = []
    for pair_id in sorted(retained):
        comparison = by_pair[pair_id]
        rank_a = ranks[(comparison.asset_a, comparison.asset_b)]
        rank_b = ranks[(comparison.asset_b, comparison.asset_a)]
        selected_a = rank_a <= k
        selected_b = rank_b <= k
        records.append(
            NeighborRecord(
                scan_id=snapshot.scan_id,
                venue=snapshot.venue,
                horizon=snapshot.horizon.value,
                pair_id=pair_id,
                asset_a=comparison.asset_a,
                asset_b=comparison.asset_b,
                ssd_distance=comparison.distance,
                rank_from_a=rank_a,
                rank_from_b=rank_b,
                selected_by_a=selected_a,
                selected_by_b=selected_b,
                automatic_neighbor_selected=selected_a or selected_b,
                manual_pinned=pair_id in pinned_pairs,
            )
        )

    ordered_comparisons = tuple(sorted(comparisons, key=lambda item: item.pair_id))
    return SsdGraph(
        scan_id=snapshot.scan_id,
        venue=snapshot.venue,
        horizon=snapshot.horizon.value,
        universe_snapshot_id=snapshot.universe_snapshot_id,
        eligible_asset_count=len(eligible_assets),
        total_valid_pair_comparisons=len(comparisons),
        distance_digest=_distance_digest(
            venue=snapshot.venue,
            horizon=snapshot.horizon.value,
            comparisons=ordered_comparisons,
        ),
        records=tuple(records),
    )


def graph_metadata_record(
    graph: SsdGraph,
    *,
    series_by_asset: Mapping[str, EvaluatedSeries],
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> GraphMetadataRecord:
    """Freeze the reconstructible pre-neighbor SSD denominator for publication."""

    if not isinstance(cast(object, graph), SsdGraph):
        raise TypeError("graph must be an SsdGraph")
    if len(series_by_asset) != graph.eligible_asset_count:
        raise ValueError("graph metadata series must match eligible asset count")
    horizon = protocol.horizon(ScannerHorizon(graph.horizon))
    fingerprints: list[str] = []
    for asset, evaluated in sorted(series_by_asset.items()):
        if not isinstance(cast(object, evaluated), EvaluatedSeries):
            raise TypeError("graph metadata values must be EvaluatedSeries")
        if evaluated.instrument.venue != graph.venue:
            raise ValueError(f"graph metadata series venue mismatch: {asset}")
        if evaluated.interval != horizon.graph_interval:
            raise ValueError(f"graph metadata series interval mismatch: {asset}")
        fingerprints.append(evaluated.selection_slice_fingerprint)
    return GraphMetadataRecord(
        scan_id=graph.scan_id,
        venue=graph.venue,
        horizon=graph.horizon,
        universe_snapshot_id=graph.universe_snapshot_id,
        generator_version=protocol.candidate_generator_version,
        graph_interval=horizon.graph_interval.label,
        graph_window_seconds=int(horizon.graph_window.total_seconds()),
        neighbors_per_asset=protocol.neighbors_per_asset,
        minimum_pair_coverage=protocol.minimum_pair_coverage,
        maximum_missing_generator_bars=protocol.maximum_missing_generator_bars,
        eligible_asset_count=graph.eligible_asset_count,
        total_valid_pair_comparisons=graph.total_valid_pair_comparisons,
        input_selection_slice_fingerprints=tuple(sorted(fingerprints)),
        distance_digest=graph.distance_digest,
    )


__all__ = [
    "GraphMetadataRecord",
    "ManualPairPin",
    "NeighborRecord",
    "SsdGraph",
    "build_ssd_graph",
    "graph_metadata_record",
    "normalized_log_ssd",
]
