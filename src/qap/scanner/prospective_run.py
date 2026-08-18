# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Thin orchestration for scanner prospective freezes and forward checkpoints."""

import json
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from qap.market import BarInterval, fingerprint_bar_series, read_parquet_bar_series
from qap.scanner.artifact_schemas import (
    GRAPH_METADATA_SCHEMA,
    PROMOTION_SCHEMA,
    SCOUT_SCHEMA,
)
from qap.scanner.artifacts import discover_completed_scans
from qap.scanner.catalog import ScannerCatalog, load_scanner_catalog
from qap.scanner.models import ScanDefinition, ScanInputIdentity
from qap.scanner.prospective import (
    CandidateFreeze,
    ForwardCheckpoint,
    ForwardOutcome,
    enroll_forward_cohort,
)
from qap.scanner.prospective_artifacts import (
    publish_checkpoint,
    read_forward_cohort,
    start_checkpoint,
    start_forward_cohort,
    write_checkpoint_evidence,
)
from qap.scanner.prospective_integrity import (
    completed_generation_dirs,
    read_manifest,
    read_outcome,
    validate_completed_generation,
)
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon
from qap.scanner.qualification_artifacts import read_qualifications
from qap.scanner.slices import evaluate_series, selection_slice_fingerprint


class ProspectiveRunError(ValueError):
    """Raised when prospective orchestration cannot preserve frozen lineage."""


@dataclass(frozen=True, slots=True)
class HistoricalReplayTemplate:
    """Scanner-owned immutable view of one historical QAP replay template."""

    evidence_sources: tuple[tuple[str, str], ...]
    data_source_dataset_ids: tuple[str, ...]
    model_parameters: tuple[tuple[str, str], ...]


HistoricalTemplateLoader = Callable[[str, Path], HistoricalReplayTemplate]
CheckpointRunner = Callable[
    [CandidateFreeze, ForwardCheckpoint, ScannerCatalog, Path, Path, datetime | None],
    ForwardOutcome,
]


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ProspectiveRunError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


def _read_table(path: Path, schema: Any) -> Any:
    try:
        table = pq.read_table(path)
    except (OSError, pa.ArrowException) as exc:
        raise ProspectiveRunError(f"scanner table is unreadable: {path.name}") from exc
    if not table.schema.equals(schema):
        raise ProspectiveRunError(f"scanner table schema mismatch: {path.name}")
    return table


def _scan_directory(run_root: Path, scan_id: str) -> Path:
    for directory in discover_completed_scans(run_root):
        if directory.name == scan_id:
            return directory
    raise ProspectiveRunError(f"completed Slice-1 scan not found: {scan_id}")


def _scan_definition(scan_directory: Path) -> ScanDefinition:
    path = scan_directory / "definition.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProspectiveRunError("Slice-1 definition is malformed") from exc
    if not isinstance(payload, dict):
        raise ProspectiveRunError("Slice-1 definition is malformed")
    document = cast(dict[str, object], payload)
    expected_scan_id = document.pop("scan_id", None)
    try:
        definition = ScanDefinition.model_validate(document)
    except ValueError as exc:
        raise ProspectiveRunError("Slice-1 definition is malformed") from exc
    if expected_scan_id != definition.scan_id:
        raise ProspectiveRunError("Slice-1 definition identity mismatch")
    return definition


def _next_boundary(after: datetime, interval: BarInterval) -> datetime:
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    elapsed = after - epoch
    elapsed_microseconds = (
        elapsed.days * 86_400_000_000
        + elapsed.seconds * 1_000_000
        + elapsed.microseconds
    )
    step_microseconds = int(interval.duration.total_seconds() * 1_000_000)
    boundary = (elapsed_microseconds // step_microseconds + 1) * step_microseconds
    return epoch + timedelta(microseconds=boundary)


def _active_freezes(
    prospective_root: Path, as_of: datetime
) -> tuple[CandidateFreeze, ...]:
    active: dict[str, CandidateFreeze] = {}
    if not prospective_root.is_dir():
        return ()
    for cohort_directory in prospective_root.iterdir():
        if (
            not cohort_directory.is_dir()
            or not (cohort_directory / "cohort.json").is_file()
        ):
            continue
        try:
            cohort = read_forward_cohort(cohort_directory)
        except (OSError, ValueError) as exc:
            raise ProspectiveRunError("existing forward cohort is malformed") from exc
        for freeze in cohort.candidate_freezes:
            if freeze.forward_end > as_of:
                existing = active.get(freeze.semantic_rule_id)
                if existing is not None and existing.freeze_id != freeze.freeze_id:
                    raise ProspectiveRunError(
                        "multiple active freezes share one semantic rule"
                    )
                active[freeze.semantic_rule_id] = freeze
    return tuple(sorted(active.values(), key=lambda item: item.freeze_id))


def _historical_selection_lineage(
    *,
    data_root: Path,
    catalog: ScannerCatalog,
    template: HistoricalReplayTemplate,
    definition: ScanDefinition,
    horizon: ScannerHorizon,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if len(template.evidence_sources) != 2:
        raise ProspectiveRunError(
            "historical survivor must have exactly two evidence legs"
        )
    horizon_rule = SCANNER_V1_SLICE1.horizon(horizon)
    model_lookback = horizon_rule.evaluation_window + max(
        duration for _template, duration in horizon_rule.template_windows
    )
    admitted = set(definition.input_slices)
    source_fingerprints: list[str] = []
    slice_fingerprints: list[str] = []
    for dataset_id, expected_fingerprint in template.evidence_sources:
        source = catalog.source(dataset_id)
        series = read_parquet_bar_series(data_root / source.relative_path)
        evaluated = evaluate_series(
            series,
            dataset_id=dataset_id,
            eligible_information_end=definition.as_of,
            lookback=model_lookback,
        )
        identity = ScanInputIdentity(
            dataset_id=dataset_id,
            source_artifact_fingerprint=evaluated.source_artifact_fingerprint,
            selection_slice_fingerprint=evaluated.selection_slice_fingerprint,
        )
        if identity not in admitted:
            raise ProspectiveRunError(
                "historical survivor slice is not sealed by scan definition"
            )
        if evaluated.source_artifact_fingerprint != expected_fingerprint:
            raise ProspectiveRunError("historical survivor source fingerprint mismatch")
        source_fingerprints.append(evaluated.source_artifact_fingerprint)
        slice_fingerprints.append(evaluated.selection_slice_fingerprint)
    if len(source_fingerprints) != 2:
        raise ProspectiveRunError("historical survivor evidence sources are incomplete")
    return tuple(source_fingerprints), tuple(slice_fingerprints)


def freeze_completed_scan(
    *,
    run_root: str | Path,
    data_root: str | Path,
    prospective_root: str | Path,
    scan_id: str,
    horizon: ScannerHorizon,
    freeze_at: datetime,
    load_historical_template: HistoricalTemplateLoader,
) -> Path:
    """Freeze every surviving automatic/manual selection from one scan/horizon."""

    root = Path(run_root).resolve()
    data = Path(data_root).resolve()
    prospective_run_root = Path(prospective_root).resolve()
    forward = prospective_run_root / "scanner-forward"
    frozen_at = _utc(freeze_at, field="freeze_at")
    scan_directory = _scan_directory(root, scan_id)
    definition = _scan_definition(scan_directory)
    catalog = load_scanner_catalog(data)
    if definition.scan_id != scan_id:
        raise ProspectiveRunError("requested scan identity mismatch")
    if definition.eligible_information_end > frozen_at:
        raise ProspectiveRunError("freeze time precedes eligible Slice-1 information")

    promotions = _read_table(scan_directory / "promotions.parquet", PROMOTION_SCHEMA)
    scouts = _read_table(scan_directory / "scout_trials.parquet", SCOUT_SCHEMA)
    graphs = _read_table(
        scan_directory / "graph_metadata.parquet", GRAPH_METADATA_SCHEMA
    )
    scout_by_candidate = {row["candidate_id"]: row for row in scouts.to_pylist()}
    graph_by_scope = {(row["venue"], row["horizon"]): row for row in graphs.to_pylist()}
    selected: list[CandidateFreeze] = []
    protocol_id = prospective_protocol_identity(PROSPECTIVE_V1)
    for promotion in promotions.to_pylist():
        scout = scout_by_candidate.get(promotion["candidate_id"])
        if scout is None:
            raise ProspectiveRunError("promotion is missing scout lineage")
        if scout["horizon"] != horizon.value:
            continue
        if promotion["economic_gate_status"] != "deep_replay_survivor":
            continue
        if not promotion["automatic_selected"] and not promotion["manual_selected"]:
            continue
        run_id = promotion["deep_replay_run_id"]
        if not isinstance(run_id, str) or not run_id:
            raise ProspectiveRunError("surviving promotion is missing deep replay run")
        scope = graph_by_scope.get((scout["venue"], scout["horizon"]))
        if scope is None:
            raise ProspectiveRunError("surviving promotion is missing graph lineage")
        resolution = BarInterval(scout["resolution"])
        template = load_historical_template(run_id, root)
        source_fingerprints, slice_fingerprints = _historical_selection_lineage(
            data_root=data,
            catalog=catalog,
            template=template,
            definition=definition,
            horizon=horizon,
        )
        forward_start = _next_boundary(frozen_at, resolution)
        selected.append(
            CandidateFreeze(
                candidate_id=promotion["candidate_id"],
                scan_id=definition.scan_id,
                scanner_protocol_version=definition.scanner_protocol_version,
                scanner_protocol_identity=definition.protocol_identity,
                prospective_protocol_version=PROSPECTIVE_V1.protocol_id,
                prospective_protocol_identity=protocol_id,
                automatic_selected=promotion["automatic_selected"],
                manual_selected=promotion["manual_selected"],
                frozen_at=frozen_at,
                eligible_information_end=definition.eligible_information_end,
                forward_start=forward_start,
                forward_end=forward_start + PROSPECTIVE_V1.forward_window(horizon),
                horizon=horizon,
                venue=scout["venue"],
                pair_id=scout["pair_id"],
                orientation=scout["orientation"],
                resolution=resolution.label,
                model_family=scout["model_family"],
                template_id=scout["template_id"],
                model_parameters=template.model_parameters,
                source_artifact_fingerprints=source_fingerprints,
                selection_slice_fingerprints=slice_fingerprints,
                universe_snapshot_id=scope["universe_snapshot_id"],
                cost_policy_reference=PROSPECTIVE_V1.adverse_cost_reference,
                primary_control_reference=PROSPECTIVE_V1.primary_control_reference,
                candidate_deep_replay_run_id=run_id,
                candidate_deep_replay_gate_status=promotion["economic_gate_status"],
            )
        )

    cohort = enroll_forward_cohort(
        source_scan_id=definition.scan_id,
        horizon=horizon,
        freeze_at=frozen_at,
        selected_freezes=tuple(selected),
        active_freezes=_active_freezes(forward, frozen_at),
    )
    return start_forward_cohort(prospective_run_root, cohort)


def _forward_slices(
    freeze: CandidateFreeze,
    *,
    catalog: ScannerCatalog,
    data_root: Path,
    run_root: Path,
    through: datetime,
    load_historical_template: HistoricalTemplateLoader,
) -> tuple[tuple[ScanInputIdentity, ...], datetime, datetime]:
    template = load_historical_template(freeze.candidate_deep_replay_run_id, run_root)
    identities: list[ScanInputIdentity] = []
    first_completions: list[datetime] = []
    for dataset_id in template.data_source_dataset_ids:
        current = catalog.source(dataset_id)
        series = read_parquet_bar_series(data_root / current.relative_path)
        fingerprint = fingerprint_bar_series(series)
        if fingerprint != current.expected_semantic_fingerprint:
            raise ProspectiveRunError("forward catalog/source fingerprint mismatch")
        bars = tuple(
            bar
            for bar in series.bars
            if freeze.forward_start < bar.bar_end_exclusive <= through
        )
        if not bars:
            raise ProspectiveRunError(
                "forward source has no completed post-freeze bars"
            )
        identities.append(
            ScanInputIdentity(
                dataset_id=dataset_id,
                source_artifact_fingerprint=fingerprint,
                selection_slice_fingerprint=selection_slice_fingerprint(
                    instrument=series.instrument,
                    interval=series.interval,
                    bars=bars,
                ),
            )
        )
        first_completions.append(bars[0].bar_end_exclusive)
    return tuple(identities), max(first_completions), through


def _next_checkpoint_index(cohort_root: Path, freeze_id: str) -> int:
    indexes = [
        manifest["checkpoint_index"]
        for directory in completed_generation_dirs(cohort_root)
        for manifest in [read_manifest(directory)]
        if manifest.get("freeze_id") == freeze_id
        and isinstance(manifest.get("checkpoint_index"), int)
        and not isinstance(manifest.get("checkpoint_index"), bool)
    ]
    return max(cast(list[int], indexes), default=0) + 1


def _existing_checkpoint(
    cohort_root: Path,
    *,
    freeze_id: str,
    information_end: datetime,
) -> Path | None:
    for directory in completed_generation_dirs(cohort_root):
        manifest, tables = validate_completed_generation(directory)
        if manifest.get("freeze_id") != freeze_id:
            continue
        checkpoint = tables["checkpoint.parquet"].to_pylist()[0]
        if checkpoint["information_end"] == information_end:
            return directory
    return None


def cohort_scoreboard(cohort_root: str | Path) -> dict[str, object]:
    """Summarize prospective policy evidence without aggregating candidate wealth."""

    root = Path(cohort_root).resolve()
    try:
        cohort = read_forward_cohort(root)
    except (OSError, ValueError) as exc:
        raise ProspectiveRunError("forward cohort definition is malformed") from exc
    outcomes = tuple(
        read_outcome(directory) for directory in completed_generation_dirs(root)
    )
    outcome_states = Counter(item.status.value for item in outcomes)
    matured = tuple(item for item in outcomes if item.status.value == "matured")
    matured_passes = sum(
        item.baseline_economic_gates_passed is True
        and item.adverse_economic_gates_passed is True
        for item in matured
    )
    model_families = Counter(item.model_family for item in cohort.candidate_freezes)
    qualifications = read_qualifications(root)
    qualification_states = Counter(
        str(item.get("state", "unknown")) for item in qualifications
    )
    return {
        "cohort_id": cohort.cohort_id,
        "source_scan_id": cohort.source_scan_id,
        "horizon": cohort.horizon.value,
        "freeze_at": cohort.freeze_at.isoformat(),
        "automatic_selected_count": cohort.automatic_member_count,
        "manual_selected_count": cohort.manual_member_count,
        "new_freeze_count": len(cohort.candidate_freezes),
        "reselection_count": len(cohort.reselections),
        "outcome_state_counts": dict(sorted(outcome_states.items())),
        "matured_pass_count": matured_passes,
        "matured_pass_fraction": (
            None
            if not matured
            else str(Decimal(matured_passes) / Decimal(len(matured)))
        ),
        "strategy_vs_hodl": sorted(
            str(item.strategy_vs_hodl)
            for item in outcomes
            if item.strategy_vs_hodl is not None
        ),
        "strategy_vs_primary_control": sorted(
            str(item.strategy_vs_primary_control)
            for item in outcomes
            if item.strategy_vs_primary_control is not None
        ),
        "model_family_counts": dict(sorted(model_families.items())),
        "qualification_state_counts": dict(sorted(qualification_states.items())),
        "qualification_count": len(qualifications),
    }


def advance_forward_cohort(
    *,
    cohort_root: str | Path,
    catalog: ScannerCatalog,
    data_root: str | Path,
    run_root: str | Path,
    through: datetime,
    load_historical_template: HistoricalTemplateLoader,
    run_checkpoint: CheckpointRunner,
    run_timestamp: datetime | None = None,
) -> tuple[Path, ...]:
    """Advance every newly frozen member in one cohort through ordinary QAP."""

    root = Path(cohort_root).resolve()
    data = Path(data_root).resolve()
    runs = Path(run_root).resolve()
    requested_through = _utc(through, field="through")
    try:
        cohort = read_forward_cohort(root)
    except (OSError, ValueError) as exc:
        raise ProspectiveRunError("forward cohort definition is malformed") from exc
    completed: list[Path] = []
    for freeze in cohort.candidate_freezes:
        if requested_through > freeze.forward_end:
            raise ProspectiveRunError("through exceeds frozen prospective horizon")
        if requested_through <= freeze.forward_start:
            raise ProspectiveRunError("through must extend beyond forward_start")
        slices, first_complete, information_end = _forward_slices(
            freeze,
            catalog=catalog,
            data_root=data,
            run_root=runs,
            through=requested_through,
            load_historical_template=load_historical_template,
        )
        existing = _existing_checkpoint(
            root,
            freeze_id=freeze.freeze_id,
            information_end=information_end,
        )
        if existing is not None:
            completed.append(existing)
            continue
        checkpoint = ForwardCheckpoint(
            cohort_id=cohort.cohort_id,
            candidate_id=freeze.candidate_id,
            freeze_id=freeze.freeze_id,
            checkpoint_index=_next_checkpoint_index(root, freeze.freeze_id),
            freeze_at=freeze.frozen_at,
            eligible_information_end=freeze.eligible_information_end,
            forward_start=freeze.forward_start,
            first_outcome_complete_at=first_complete,
            evidence_window_start=freeze.forward_start,
            evidence_window_end=information_end,
            information_end=information_end,
            forward_slices=slices,
            evidence_role="prospective",
            prospective_protocol_version=freeze.prospective_protocol_version,
            prospective_protocol_identity=freeze.prospective_protocol_identity,
            created_at=(
                datetime.now(UTC)
                if run_timestamp is None
                else _utc(run_timestamp, field="run_timestamp")
            ),
        )
        outcome = run_checkpoint(
            freeze,
            checkpoint,
            catalog,
            data,
            runs,
            run_timestamp,
        )
        generation = start_checkpoint(root, checkpoint)
        write_checkpoint_evidence(
            generation,
            outcome=outcome,
            liquidity=(),
        )
        completed.append(publish_checkpoint(generation))
    return tuple(completed)


__all__ = [
    "ProspectiveRunError",
    "advance_forward_cohort",
    "cohort_scoreboard",
    "freeze_completed_scan",
]
