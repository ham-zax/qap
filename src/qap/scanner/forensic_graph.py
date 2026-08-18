"""Manual forensic-pin extension around the frozen official SSD generator."""

from dataclasses import dataclass, replace
from hashlib import sha256
from typing import Mapping

from qap.portfolio import AssetId
from qap.scanner.graph import ManualPairPin, NeighborRecord, SsdGraph, build_ssd_graph
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerProtocol
from qap.scanner.slices import EvaluatedSeries
from qap.scanner.universe import UniverseSnapshot


@dataclass(frozen=True, slots=True)
class ScopedManualPin:
    asset_a: AssetId
    asset_b: AssetId
    forensic: bool = False

    def __post_init__(self) -> None:
        if self.asset_a == self.asset_b:
            raise ValueError("manual pin assets must be distinct")

    @property
    def canonical_assets(self) -> tuple[AssetId, AssetId]:
        ordered = sorted((self.asset_a, self.asset_b))
        return ordered[0], ordered[1]


def _empty_official_graph(snapshot: UniverseSnapshot) -> SsdGraph:
    return SsdGraph(
        scan_id=snapshot.scan_id,
        venue=snapshot.venue,
        horizon=snapshot.horizon.value,
        universe_snapshot_id=snapshot.universe_snapshot_id,
        eligible_asset_count=len(snapshot.eligible_records),
        total_valid_pair_comparisons=0,
        distance_digest=sha256(b"").hexdigest(),
        records=(),
    )


def _forensic_record(
    snapshot: UniverseSnapshot,
    *,
    pin: ScopedManualPin,
    evaluated_by_asset: Mapping[str, EvaluatedSeries],
    protocol: ScannerProtocol,
) -> NeighborRecord:
    by_asset = {record.asset_id: record for record in snapshot.records}
    first, second = pin.canonical_assets
    try:
        records = (by_asset[first.key], by_asset[second.key])
    except KeyError as exc:
        raise ValueError(
            "forensic manual pin asset is absent from PIT universe"
        ) from exc
    if not all(
        record.automatic_eligible or record.forensic_research_allowed
        for record in records
    ):
        raise ValueError(
            "forensic manual pin asset is not admitted for forensic research"
        )

    synthetic_records = tuple(
        replace(record, automatic_eligible=True) for record in records
    )
    synthetic = replace(snapshot, records=synthetic_records)
    mini = build_ssd_graph(
        synthetic,
        series_by_asset={
            first.key: evaluated_by_asset[first.key],
            second.key: evaluated_by_asset[second.key],
        },
        manual_pins=(ManualPairPin(asset_a=first, asset_b=second),),
        protocol=protocol,
    )
    if len(mini.records) != 1:
        raise ValueError("forensic manual pin did not produce exactly one comparison")
    return replace(
        mini.records[0],
        selected_by_a=False,
        selected_by_b=False,
        automatic_neighbor_selected=False,
        manual_pinned=True,
    )


def build_scanner_graph(
    snapshot: UniverseSnapshot,
    *,
    evaluated_by_asset: Mapping[str, EvaluatedSeries],
    manual_pins: tuple[ScopedManualPin, ...] = (),
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> SsdGraph:
    """Build official SSD graph plus isolated forensic-only manual comparisons."""

    automatic_assets = {
        AssetId(record.asset_id) for record in snapshot.eligible_records
    }
    official_pins: list[ManualPairPin] = []
    forensic_pins: list[ScopedManualPin] = []
    for pin in manual_pins:
        first, second = pin.canonical_assets
        if first in automatic_assets and second in automatic_assets:
            official_pins.append(ManualPairPin(asset_a=first, asset_b=second))
        elif pin.forensic:
            forensic_pins.append(pin)
        else:
            raise ValueError(
                "manual pin with non-automatic asset requires forensic=true"
            )

    official = (
        build_ssd_graph(
            snapshot,
            series_by_asset=evaluated_by_asset,
            manual_pins=tuple(official_pins),
            protocol=protocol,
        )
        if len(automatic_assets) >= 2
        else _empty_official_graph(snapshot)
    )
    merged = {record.pair_id: record for record in official.records}
    for pin in forensic_pins:
        record = _forensic_record(
            snapshot,
            pin=pin,
            evaluated_by_asset=evaluated_by_asset,
            protocol=protocol,
        )
        if record.pair_id in merged:
            raise ValueError("forensic manual pin duplicates an official pair record")
        merged[record.pair_id] = record
    return replace(
        official,
        records=tuple(merged[key] for key in sorted(merged)),
    )


__all__ = ["ScopedManualPin", "build_scanner_graph"]
