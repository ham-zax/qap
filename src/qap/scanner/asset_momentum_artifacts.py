# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Immutable artifacts for asset-native scanner momentum generations."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from qap.artifact_integrity import (
    INTEGRITY_FILE,
    build_integrity_record,
    read_and_validate_integrity,
)
from qap.scanner.artifact_schemas import ELIGIBLE_SCHEMA
from qap.scanner.artifact_tables import eligible_table
from qap.scanner.asset_momentum import (
    AssetMomentumGeneration,
    AssetMomentumObservation,
    MomentumObservationStatus,
)
from qap.scanner.protocol import ScannerHorizon
from qap.scanner.universe import (
    EligibleAssetRecord,
    HistoricalEligibilityState,
    UniverseSnapshot,
)

DEFINITION = "definition.json"
ELIGIBLE_ASSETS = "eligible_assets.parquet"
OBSERVATIONS = "observations.parquet"
MANIFEST = "manifest.json"
AUTHORITATIVE_FILES = frozenset({DEFINITION, ELIGIBLE_ASSETS, OBSERVATIONS, MANIFEST})

OBSERVATION_SCHEMA = pa.schema(
    [
        ("asset_id", pa.string()),
        ("venue_symbol", pa.string()),
        ("status", pa.string()),
        ("reason", pa.string()),
        ("source_artifact_fingerprint", pa.string()),
        ("selection_slice_fingerprint", pa.string()),
        ("bar_coverage", pa.float64()),
        ("longest_missing_run", pa.int64()),
        ("own_momentum", pa.float64()),
        ("common_mode", pa.float64()),
        ("relative_momentum", pa.float64()),
        ("common_mode_member_count", pa.int64()),
        ("rank", pa.int64()),
    ]
)


class AssetMomentumArtifactError(ValueError):
    """Raised when an asset-momentum artifact is malformed or inconsistent."""


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _write_bytes(path: Path, payload: bytes) -> None:
    path.write_bytes(payload)


def _write_table(path: Path, table: Any) -> None:
    try:
        pq.write_table(table, path)
    except (OSError, pa.ArrowException) as exc:
        raise AssetMomentumArtifactError(f"failed to write {path.name}") from exc


def _read_table(path: Path, schema: Any) -> Any:
    try:
        table = pq.read_table(path)
    except (OSError, pa.ArrowException) as exc:
        raise AssetMomentumArtifactError(f"table is malformed: {path.name}") from exc
    if not table.schema.equals(schema):
        raise AssetMomentumArtifactError(f"table schema mismatch: {path.name}")
    return table


def _definition(generation: AssetMomentumGeneration) -> dict[str, object]:
    return {
        "schema_version": "qap.scanner.asset-momentum.definition.v1",
        "momentum_scan_id": generation.momentum_scan_id,
        "protocol_id": generation.protocol_id,
        "protocol_identity": generation.protocol_identity,
        "source_scan_id": generation.source_scan_id,
        "venue": generation.venue,
        "horizon": generation.horizon.value,
        "as_of": generation.as_of.isoformat(),
        "universe_snapshot_id": generation.universe_snapshot_id,
        "resolution": generation.resolution,
        "formation_seconds": generation.formation_seconds,
    }


def _observation_table(generation: AssetMomentumGeneration) -> Any:
    rows = [
        {
            "asset_id": item.asset_id,
            "venue_symbol": item.venue_symbol,
            "status": item.status.value,
            "reason": item.reason,
            "source_artifact_fingerprint": item.source_artifact_fingerprint,
            "selection_slice_fingerprint": item.selection_slice_fingerprint,
            "bar_coverage": item.bar_coverage,
            "longest_missing_run": item.longest_missing_run,
            "own_momentum": item.own_momentum,
            "common_mode": item.common_mode,
            "relative_momentum": item.relative_momentum,
            "common_mode_member_count": item.common_mode_member_count,
            "rank": item.rank,
        }
        for item in generation.observations
    ]
    return pa.Table.from_pylist(rows, schema=OBSERVATION_SCHEMA)


def _manifest(
    generation: AssetMomentumGeneration,
    snapshot: UniverseSnapshot,
) -> dict[str, object]:
    valid_count = sum(
        item.status is MomentumObservationStatus.VALID
        for item in generation.observations
    )
    return {
        "schema_version": "qap.scanner.asset-momentum.manifest.v1",
        "momentum_scan_id": generation.momentum_scan_id,
        "universe_snapshot_id": snapshot.universe_snapshot_id,
        "eligible_asset_count": len(snapshot.records),
        "observation_count": len(generation.observations),
        "valid_observation_count": valid_count,
        "invalid_observation_count": len(generation.observations) - valid_count,
    }


def _validate_generation_snapshot(
    generation: AssetMomentumGeneration,
    snapshot: UniverseSnapshot,
) -> None:
    if generation.source_scan_id != snapshot.scan_id:
        raise AssetMomentumArtifactError("generation source scan mismatch")
    if generation.venue != snapshot.venue or generation.horizon is not snapshot.horizon:
        raise AssetMomentumArtifactError("generation universe scope mismatch")
    if generation.universe_snapshot_id != snapshot.universe_snapshot_id:
        raise AssetMomentumArtifactError("generation universe identity mismatch")
    if {item.asset_id for item in generation.observations} != {
        item.asset_id for item in snapshot.records
    }:
        raise AssetMomentumArtifactError(
            "generation observations do not match universe"
        )


def publish_asset_momentum_generation(
    run_root: str | Path,
    generation: AssetMomentumGeneration,
    snapshot: UniverseSnapshot,
) -> Path:
    """Atomically publish one immutable asset-momentum generation."""

    _validate_generation_snapshot(generation, snapshot)
    root = Path(run_root).resolve() / "asset-momentum"
    final = root / generation.momentum_scan_id
    staging = root / f"{generation.momentum_scan_id}.partial"
    if final.is_dir():
        read_asset_momentum_generation(final)
        return final
    root.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir()
    try:
        _write_bytes(staging / DEFINITION, _json_bytes(_definition(generation)))
        _write_table(staging / ELIGIBLE_ASSETS, eligible_table(snapshot.records))
        _write_table(staging / OBSERVATIONS, _observation_table(generation))
        _write_bytes(staging / MANIFEST, _json_bytes(_manifest(generation, snapshot)))
        integrity = build_integrity_record(
            staging,
            artifact_id=generation.momentum_scan_id,
            file_names=tuple(sorted(AUTHORITATIVE_FILES)),
        )
        _write_bytes(
            staging / INTEGRITY_FILE,
            integrity.model_dump_json().encode("utf-8"),
        )
        os.replace(staging, final)
    except (OSError, ValueError) as exc:
        raise AssetMomentumArtifactError(
            "failed to publish momentum generation"
        ) from exc
    return final


def _read_json(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AssetMomentumArtifactError(f"malformed JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise AssetMomentumArtifactError(f"JSON object required: {path.name}")
    return value


def _snapshot_from_table(definition: dict[str, object], table: Any) -> UniverseSnapshot:
    records = tuple(
        EligibleAssetRecord(
            scan_id=str(row["scan_id"]),
            venue=str(row["venue"]),
            horizon=ScannerHorizon(str(row["horizon"])),
            asset_id=str(row["asset_id"]),
            venue_symbol=str(row["venue_symbol"]),
            eligibility_state=HistoricalEligibilityState(str(row["eligibility_state"])),
            eligibility_reason=str(row["eligibility_reason"]),
            lifecycle_evidence_refs=tuple(row["lifecycle_evidence_refs"] or ()),
            source_artifact_fingerprint=str(row["source_artifact_fingerprint"]),
            selection_slice_fingerprint=str(row["selection_slice_fingerprint"]),
            bar_coverage=float(row["bar_coverage"]),
            longest_missing_run=int(row["longest_missing_run"]),
            automatic_eligible=bool(row["automatic_eligible"]),
            forensic_research_allowed=bool(row["forensic_research_allowed"]),
        )
        for row in table.to_pylist()
    )
    return UniverseSnapshot(
        scan_id=str(definition["source_scan_id"]),
        venue=str(definition["venue"]),
        horizon=ScannerHorizon(str(definition["horizon"])),
        records=records,
        universe_snapshot_id=str(definition["universe_snapshot_id"]),
    )


def _generation_from_table(
    definition: dict[str, object],
    table: Any,
) -> AssetMomentumGeneration:
    observations = tuple(
        AssetMomentumObservation(
            asset_id=str(row["asset_id"]),
            venue_symbol=str(row["venue_symbol"]),
            status=MomentumObservationStatus(str(row["status"])),
            reason=str(row["reason"]),
            source_artifact_fingerprint=str(row["source_artifact_fingerprint"]),
            selection_slice_fingerprint=str(row["selection_slice_fingerprint"]),
            bar_coverage=float(row["bar_coverage"]),
            longest_missing_run=int(row["longest_missing_run"]),
            own_momentum=(
                None if row["own_momentum"] is None else float(row["own_momentum"])
            ),
            common_mode=(
                None if row["common_mode"] is None else float(row["common_mode"])
            ),
            relative_momentum=(
                None
                if row["relative_momentum"] is None
                else float(row["relative_momentum"])
            ),
            common_mode_member_count=int(row["common_mode_member_count"]),
            rank=None if row["rank"] is None else int(row["rank"]),
        )
        for row in table.to_pylist()
    )
    return AssetMomentumGeneration(
        protocol_id=str(definition["protocol_id"]),
        protocol_identity=str(definition["protocol_identity"]),
        source_scan_id=str(definition["source_scan_id"]),
        venue=str(definition["venue"]),
        horizon=ScannerHorizon(str(definition["horizon"])),
        as_of=datetime.fromisoformat(str(definition["as_of"])),
        universe_snapshot_id=str(definition["universe_snapshot_id"]),
        resolution=str(definition["resolution"]),
        formation_seconds=int(str(definition["formation_seconds"])),
        observations=observations,
    )


def read_asset_momentum_generation(
    directory: str | Path,
) -> tuple[AssetMomentumGeneration, UniverseSnapshot]:
    """Read and reconcile one completed immutable momentum generation."""

    root = Path(directory).resolve()
    artifact_id = root.name
    try:
        read_and_validate_integrity(
            root,
            artifact_id=artifact_id,
            required_files=AUTHORITATIVE_FILES,
            allowed_files=AUTHORITATIVE_FILES,
        )
    except ValueError as exc:
        raise AssetMomentumArtifactError(str(exc)) from exc
    definition = _read_json(root / DEFINITION)
    manifest = _read_json(root / MANIFEST)
    eligible = _read_table(root / ELIGIBLE_ASSETS, ELIGIBLE_SCHEMA)
    observations = _read_table(root / OBSERVATIONS, OBSERVATION_SCHEMA)
    generation = _generation_from_table(definition, observations)
    snapshot = _snapshot_from_table(definition, eligible)
    _validate_generation_snapshot(generation, snapshot)
    if generation.momentum_scan_id != artifact_id:
        raise AssetMomentumArtifactError("momentum semantic identity mismatch")
    if definition.get("momentum_scan_id") != artifact_id:
        raise AssetMomentumArtifactError("definition identity mismatch")
    if manifest.get("momentum_scan_id") != artifact_id:
        raise AssetMomentumArtifactError("manifest identity mismatch")
    if manifest.get("universe_snapshot_id") != snapshot.universe_snapshot_id:
        raise AssetMomentumArtifactError("manifest universe identity mismatch")
    if manifest.get("eligible_asset_count") != len(snapshot.records):
        raise AssetMomentumArtifactError("manifest eligible count mismatch")
    if manifest.get("observation_count") != len(generation.observations):
        raise AssetMomentumArtifactError("manifest observation count mismatch")
    valid_count = sum(
        item.status is MomentumObservationStatus.VALID
        for item in generation.observations
    )
    if manifest.get("valid_observation_count") != valid_count:
        raise AssetMomentumArtifactError("manifest valid count mismatch")
    if (
        manifest.get("invalid_observation_count")
        != len(generation.observations) - valid_count
    ):
        raise AssetMomentumArtifactError("manifest invalid count mismatch")
    return generation, snapshot


__all__ = [
    "AssetMomentumArtifactError",
    "OBSERVATION_SCHEMA",
    "publish_asset_momentum_generation",
    "read_asset_momentum_generation",
]
