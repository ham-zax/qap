"""Authoritative QAP replay adapter for one frozen scanner prospective checkpoint."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast

from qap.experiment.artifacts import read_run_artifacts, run_experiment_to_artifacts
from qap.experiment.data import DatasetFingerprintMismatchError, ExperimentSetupError
from qap.experiment.dataset_seals import validate_expected_fingerprints_for_role
from qap.experiment.manifest import DataRole, ExperimentManifest
from qap.market import fingerprint_bar_series, read_parquet_bar_series
from qap.portfolio._decimal import divide
from qap.scanner.catalog import ScannerCatalog
from qap.scanner.prospective import (
    CandidateFreeze,
    ForwardCheckpoint,
    ForwardOutcome,
    ForwardOutcomeStatus,
)
from qap.scanner.prospective_protocol import (
    PROSPECTIVE_V1,
    prospective_protocol_identity,
)
from qap.scanner.protocol import SCANNER_V1_SLICE1


class ProspectiveReplayError(ValueError):
    """Raised when frozen prospective lineage cannot be replayed faithfully."""


def _historical_run(run_root: Path, freeze: CandidateFreeze):
    directory = run_root.resolve() / freeze.candidate_deep_replay_run_id
    try:
        loaded = read_run_artifacts(directory)
    except Exception as exc:
        raise ProspectiveReplayError(
            "historical deep replay artifact is unavailable"
        ) from exc
    if loaded.result.run_id != freeze.candidate_deep_replay_run_id:
        raise ProspectiveReplayError("historical deep replay identity mismatch")
    if loaded.manifest.data_role is not DataRole.DEVELOPMENT:
        raise ProspectiveReplayError(
            "historical scanner replay must be development role"
        )
    if loaded.manifest.research_family_id != f"scanner-{freeze.candidate_id}":
        raise ProspectiveReplayError("historical scanner candidate lineage mismatch")
    return loaded


def _validate_frozen_contract(
    freeze: CandidateFreeze,
    historical: ExperimentManifest,
) -> None:
    if freeze.prospective_protocol_version != PROSPECTIVE_V1.protocol_id or (
        freeze.prospective_protocol_identity
        != prospective_protocol_identity(PROSPECTIVE_V1)
    ):
        raise ProspectiveReplayError("prospective protocol identity mismatch")
    if freeze.primary_control_reference != PROSPECTIVE_V1.primary_control_reference:
        raise ProspectiveReplayError("primary control reference mismatch")
    if freeze.cost_policy_reference != PROSPECTIVE_V1.adverse_cost_reference:
        raise ProspectiveReplayError("cost policy reference mismatch")
    if (
        historical.benchmarks.primary_incremental_benchmark
        != SCANNER_V1_SLICE1.primary_control.control_id
    ):
        raise ProspectiveReplayError("historical primary control does not match freeze")
    costs = SCANNER_V1_SLICE1.cost_policy
    adverse = historical.execution.adverse_cost_scenario
    if (
        historical.execution.fee_bps != costs.fee_bps
        or historical.execution.slippage_bps != costs.slippage_bps
        or adverse is None
        or adverse.fee_bps != costs.adverse_fee_bps
        or adverse.slippage_bps != costs.adverse_slippage_bps
    ):
        raise ProspectiveReplayError("historical cost policy does not match freeze")


def _forward_sources(
    historical: ExperimentManifest,
    checkpoint: ForwardCheckpoint,
    catalog: ScannerCatalog,
) -> list[dict[str, object]]:
    by_dataset = {item.dataset_id: item for item in checkpoint.forward_slices}
    historical_ids = {source.dataset_id for source in historical.data_sources}
    if set(by_dataset) != historical_ids:
        raise ProspectiveReplayError(
            "forward checkpoint must identify every frozen replay data source"
        )
    validate_expected_fingerprints_for_role(
        (item.source_artifact_fingerprint for item in checkpoint.forward_slices),
        data_role=DataRole.DEVELOPMENT,
    )
    resolved: list[dict[str, object]] = []
    for source in historical.data_sources:
        current = catalog.source(source.dataset_id)
        expected = by_dataset[source.dataset_id]
        if (
            current.expected_semantic_fingerprint
            != expected.source_artifact_fingerprint
        ):
            raise ProspectiveReplayError("forward catalog fingerprint mismatch")
        resolved.append(
            {
                **source.model_dump(mode="json"),
                "relative_path": current.relative_path,
                "expected_semantic_fingerprint": expected.source_artifact_fingerprint,
            }
        )
    return resolved


def _starting_quantities(
    historical: ExperimentManifest,
    checkpoint: ForwardCheckpoint,
    *,
    data_root: Path,
    catalog: ScannerCatalog,
) -> dict[str, str]:
    direct_instrument_id = historical.execution.execution_instrument_id
    direct_source = next(
        (
            source
            for source in historical.data_sources
            if source.instrument_id == direct_instrument_id
        ),
        None,
    )
    direct_instrument = next(
        (
            instrument
            for instrument in historical.instruments
            if instrument.instrument_id == direct_instrument_id
        ),
        None,
    )
    if direct_source is None or direct_instrument is None:
        raise ProspectiveReplayError("frozen replay direct market is unavailable")
    current_direct = catalog.source(direct_source.dataset_id)
    forward_identity = next(
        (
            item
            for item in checkpoint.forward_slices
            if item.dataset_id == direct_source.dataset_id
        ),
        None,
    )
    if forward_identity is None:
        raise ProspectiveReplayError("forward direct-market identity is unavailable")
    if (
        current_direct.expected_semantic_fingerprint
        != forward_identity.source_artifact_fingerprint
    ):
        raise ProspectiveReplayError("forward direct-market catalog mismatch")
    series = read_parquet_bar_series(data_root / current_direct.relative_path)
    if fingerprint_bar_series(series) != forward_identity.source_artifact_fingerprint:
        raise ProspectiveReplayError("forward direct-market fingerprint mismatch")
    matches = tuple(
        bar for bar in series.bars if bar.bar_end_exclusive == checkpoint.forward_start
    )
    if len(matches) != 1:
        raise ProspectiveReplayError("forward starting price is unavailable")
    price = Decimal(str(matches[0].close))
    if not price.is_finite() or price <= 0:
        raise ProspectiveReplayError("forward starting price is invalid")
    total = SCANNER_V1_SLICE1.normalization.total_direct_quote_value
    half = total / Decimal("2")
    return {
        direct_instrument.base_asset: str(divide(half, price)),
        direct_instrument.quote_asset: str(half),
    }


def prepare_prospective_manifest(
    freeze: CandidateFreeze,
    checkpoint: ForwardCheckpoint,
    *,
    data_root: str | Path,
    run_root: str | Path,
    catalog: ScannerCatalog,
) -> ExperimentManifest:
    """Clone frozen historical QAP semantics onto one strict forward window."""

    if (
        checkpoint.freeze_id != freeze.freeze_id
        or checkpoint.candidate_id != freeze.candidate_id
    ):
        raise ProspectiveReplayError("checkpoint does not belong to candidate freeze")
    if (
        checkpoint.prospective_protocol_version != freeze.prospective_protocol_version
        or checkpoint.prospective_protocol_identity
        != freeze.prospective_protocol_identity
    ):
        raise ProspectiveReplayError("checkpoint prospective protocol mismatch")
    if checkpoint.forward_start != freeze.forward_start:
        raise ProspectiveReplayError("checkpoint forward boundary changed after freeze")
    if checkpoint.information_end > freeze.forward_end:
        raise ProspectiveReplayError("checkpoint extends beyond frozen forward horizon")

    loaded = _historical_run(Path(run_root), freeze)
    historical = loaded.manifest
    _validate_frozen_contract(freeze, historical)
    data_sources = _forward_sources(historical, checkpoint, catalog)
    warmup = (
        historical.effective_evaluation_window().start - historical.data_window.start
    )
    data_start = freeze.forward_start - warmup
    payload = historical.model_dump(mode="json")
    payload.update(
        {
            "experiment_name": (
                f"prospective-{freeze.freeze_id[:12]}-{checkpoint.checkpoint_index}"
            ),
            "description": (
                "Frozen scanner prospective replay; "
                f"freeze={freeze.freeze_id}; checkpoint={checkpoint.checkpoint_id}."
            ),
            "research_family_id": f"scanner-forward-{freeze.freeze_id}",
            "parent_run_id": freeze.candidate_deep_replay_run_id,
            "starting_quantities": _starting_quantities(
                historical,
                checkpoint,
                data_root=Path(data_root).resolve(),
                catalog=catalog,
            ),
            "data_window": {
                "start": data_start.isoformat(),
                "end": checkpoint.information_end.isoformat(),
            },
            "evaluation_window": {
                "start": freeze.forward_start.isoformat(),
                "end": checkpoint.information_end.isoformat(),
            },
            "data_sources": data_sources,
            "data_role": DataRole.DEVELOPMENT.value,
        }
    )
    return ExperimentManifest.model_validate(payload)


def _economic_gates(result: object) -> tuple[bool, bool, Decimal, Decimal]:
    from qap.experiment.result import ExperimentResult

    if not isinstance(result, ExperimentResult):
        raise ProspectiveReplayError("QAP result type is invalid")
    primary = result.strategy_vs_primary_control
    if primary is None:
        raise ProspectiveReplayError("QAP result is missing primary control economics")
    baseline = result.strategy_vs_hodl > 0 and primary > 0
    adverse_strategy = result.role("strategy:adverse_cost")
    adverse_controls = tuple(
        role
        for role in result.roles
        if role.role.endswith(":adverse_cost") and role.role != "strategy:adverse_cost"
    )
    if len(adverse_controls) != 1:
        raise ProspectiveReplayError(
            "QAP result is missing adverse primary-control role"
        )
    hodl = result.role("hodl")
    adverse = (
        adverse_strategy.terminal_value > hodl.terminal_value
        and adverse_strategy.terminal_value > adverse_controls[0].terminal_value
    )
    return baseline, adverse, result.strategy_vs_hodl, primary


def prepare_prospective_qualification_manifest(
    freeze: CandidateFreeze,
    checkpoint: ForwardCheckpoint,
    *,
    requested_capital: Decimal,
    empirical_slippage_bps: Decimal,
    data_root: str | Path,
    run_root: str | Path,
    catalog: ScannerCatalog,
) -> ExperimentManifest:
    """Scale the frozen replay and apply measured baseline book impact."""

    if not requested_capital.is_finite() or requested_capital <= 0:
        raise ProspectiveReplayError("requested capital must be positive finite")
    costs = SCANNER_V1_SLICE1.cost_policy
    if (
        not empirical_slippage_bps.is_finite()
        or empirical_slippage_bps < 0
        or empirical_slippage_bps > costs.adverse_slippage_bps
    ):
        raise ProspectiveReplayError(
            "empirical slippage must fit the frozen adverse slippage budget"
        )
    base = prepare_prospective_manifest(
        freeze,
        checkpoint,
        data_root=data_root,
        run_root=run_root,
        catalog=catalog,
    )
    payload = base.model_dump(mode="json")
    payload["experiment_name"] = (
        f"qualification-{freeze.freeze_id[:12]}-{checkpoint.checkpoint_index}"
    )
    payload["description"] = (
        "Frozen scanner explicit-capital qualification replay; "
        f"freeze={freeze.freeze_id}; checkpoint={checkpoint.checkpoint_id}; "
        f"capital={requested_capital}."
    )
    payload["research_family_id"] = f"scanner-qualification-{freeze.freeze_id}"
    starting = cast(dict[str, object], payload["starting_quantities"])
    payload["starting_quantities"] = {
        asset: str(Decimal(str(quantity)) * requested_capital)
        for asset, quantity in starting.items()
    }
    execution = cast(dict[str, object], payload["execution"])
    execution["fee_bps"] = str(costs.adverse_fee_bps)
    execution["slippage_bps"] = str(empirical_slippage_bps)
    payload["execution"] = execution
    return ExperimentManifest.model_validate(payload)


def run_prospective_qualification(
    freeze: CandidateFreeze,
    checkpoint: ForwardCheckpoint,
    *,
    requested_capital: Decimal,
    empirical_slippage_bps: Decimal,
    data_root: str | Path,
    repository_root: str | Path,
    run_root: str | Path,
    catalog: ScannerCatalog,
    run_timestamp: datetime | None = None,
) -> tuple[str, bool, bool]:
    """Run one explicit-capital qualification through ordinary QAP artifacts."""

    manifest = prepare_prospective_qualification_manifest(
        freeze,
        checkpoint,
        requested_capital=requested_capital,
        empirical_slippage_bps=empirical_slippage_bps,
        data_root=data_root,
        run_root=run_root,
        catalog=catalog,
    )
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=data_root,
        repository_root=repository_root,
        run_root=run_root,
        run_timestamp=datetime.now(UTC) if run_timestamp is None else run_timestamp,
    )
    loaded = read_run_artifacts(paths.run_directory)
    baseline, adverse, _vs_hodl, _vs_primary = _economic_gates(loaded.result)
    return paths.run_id, baseline, adverse


def run_prospective_checkpoint(
    freeze: CandidateFreeze,
    checkpoint: ForwardCheckpoint,
    *,
    data_root: str | Path,
    repository_root: str | Path,
    run_root: str | Path,
    catalog: ScannerCatalog,
    run_timestamp: datetime | None = None,
) -> ForwardOutcome:
    """Run one prospective checkpoint through ordinary immutable QAP artifacts."""

    manifest = prepare_prospective_manifest(
        freeze,
        checkpoint,
        data_root=data_root,
        run_root=run_root,
        catalog=catalog,
    )
    try:
        paths = run_experiment_to_artifacts(
            manifest,
            data_root=data_root,
            repository_root=repository_root,
            run_root=run_root,
            run_timestamp=datetime.now(UTC) if run_timestamp is None else run_timestamp,
        )
    except DatasetFingerprintMismatchError:
        raise
    except ExperimentSetupError as exc:
        return ForwardOutcome(
            freeze_id=freeze.freeze_id,
            candidate_id=freeze.candidate_id,
            checkpoint_id=checkpoint.checkpoint_id,
            prospective_protocol_version=freeze.prospective_protocol_version,
            prospective_protocol_identity=freeze.prospective_protocol_identity,
            status=ForwardOutcomeStatus.INVALID,
            through=checkpoint.information_end,
            primary_control_reference=freeze.primary_control_reference,
            cost_policy_reference=freeze.cost_policy_reference,
            failure_reason=f"{type(exc).__name__}: {exc}",
        )
    loaded = read_run_artifacts(paths.run_directory)
    baseline, adverse, vs_hodl, vs_primary = _economic_gates(loaded.result)

    matured = checkpoint.information_end == freeze.forward_end
    return ForwardOutcome(
        freeze_id=freeze.freeze_id,
        candidate_id=freeze.candidate_id,
        checkpoint_id=checkpoint.checkpoint_id,
        prospective_protocol_version=freeze.prospective_protocol_version,
        prospective_protocol_identity=freeze.prospective_protocol_identity,
        status=(
            ForwardOutcomeStatus.MATURED if matured else ForwardOutcomeStatus.PARTIAL
        ),
        through=checkpoint.information_end,
        matured_at=(freeze.forward_end if matured else None),
        qap_run_id=paths.run_id,
        primary_control_reference=freeze.primary_control_reference,
        cost_policy_reference=freeze.cost_policy_reference,
        strategy_vs_hodl=vs_hodl,
        strategy_vs_primary_control=vs_primary,
        baseline_economic_gates_passed=baseline,
        adverse_economic_gates_passed=adverse,
    )


__all__ = [
    "ProspectiveReplayError",
    "prepare_prospective_manifest",
    "prepare_prospective_qualification_manifest",
    "run_prospective_checkpoint",
    "run_prospective_qualification",
]
