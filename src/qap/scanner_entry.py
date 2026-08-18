"""Outer composition root for scanner research and authoritative QAP replay."""

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from qap.experiment.artifacts import read_run_artifacts
from qap.experiment.scanner_adapter import run_scanner_candidate_replay
from qap.scanner.artifacts import (
    ReplayAttemptRecord,
    ReplayAttemptStatus,
    ScanArtifactGeneration,
)
from qap.scanner.catalog import ScannerCatalog
from qap.scanner.models import ScannerPinSpec
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon, ScannerProtocol
from qap.scanner.run import ReplayReference, ScanRunResult, run_scan
from qap.scanner.trials import ScannerTrial


def _direct_execution_instrument_id(
    catalog: ScannerCatalog,
    trial: ScannerTrial,
) -> str:
    candidate_assets = {trial.asset_a.key, trial.asset_b.key}
    matches = tuple(
        source.dataset_id
        for source in catalog.sources
        if source.venue == trial.venue
        and source.interval == trial.resolution.label
        and {source.base_asset, source.quote_asset} == candidate_assets
    )
    if len(matches) != 1:
        raise RuntimeError("terminal replay cannot resolve its frozen direct market")
    return matches[0]


def _economic_gate(run_root: Path, run_id: str) -> str:
    loaded = read_run_artifacts(run_root / run_id)
    primary = loaded.result.strategy_vs_primary_control
    survivor = (
        loaded.result.strategy_vs_hodl > Decimal("0")
        and primary is not None
        and primary > Decimal("0")
    )
    return "deep_replay_survivor" if survivor else "deep_replay_rejected"


class _QapReplayService:
    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root

    def execute(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt_id: str,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference:
        outcome = run_scanner_candidate_replay(
            generation=generation,
            attempt_id=attempt_id,
            trial=trial,
            catalog=catalog,
            data_root=data_root,
            repository_root=self._repository_root,
            run_root=run_root,
        )
        return ReplayReference(
            status=outcome.status.value,
            direct_execution_instrument_id=(outcome.direct_execution_instrument_id),
            deep_replay_run_id=outcome.deep_replay_run_id,
            economic_gate_status=(
                None
                if outcome.economic_gate_status is None
                else outcome.economic_gate_status.value
            ),
            failure_stage=outcome.failure_stage,
            failure_reason=outcome.failure_reason,
        )

    def recover(
        self,
        *,
        generation: ScanArtifactGeneration,
        attempt: ReplayAttemptRecord,
        trial: ScannerTrial,
        catalog: ScannerCatalog,
        data_root: Path,
        run_root: Path,
    ) -> ReplayReference:
        del generation, data_root
        if attempt.attempt_status is ReplayAttemptStatus.ENUMERATED:
            raise RuntimeError("enumerated replay attempt must execute, not recover")
        if attempt.attempt_status is ReplayAttemptStatus.COMPLETED:
            if attempt.deep_replay_run_id is None:
                raise RuntimeError("completed replay attempt is missing its run ID")
            direct_id = _direct_execution_instrument_id(catalog, trial)
            gate = _economic_gate(run_root, attempt.deep_replay_run_id)
        else:
            direct_id = (
                _direct_execution_instrument_id(catalog, trial)
                if attempt.attempt_status is ReplayAttemptStatus.REPLAY_FAILED
                else None
            )
            gate = None
        return ReplayReference(
            status=attempt.attempt_status.value,
            direct_execution_instrument_id=direct_id,
            deep_replay_run_id=attempt.deep_replay_run_id,
            economic_gate_status=gate,
            failure_stage=attempt.failure_stage,
            failure_reason=attempt.failure_reason,
        )


def run_scan_with_qap(
    *,
    as_of: datetime,
    horizons: tuple[ScannerHorizon, ...],
    data_root: str | Path,
    run_root: str | Path,
    pins: Sequence[ScannerPinSpec] = (),
    repository_root: str | Path | None = None,
    protocol: ScannerProtocol = SCANNER_V1_SLICE1,
) -> ScanRunResult:
    """Compose scanner discovery with the ordinary experiment replay adapter."""

    repository = (
        Path.cwd().resolve()
        if repository_root is None
        else Path(repository_root).resolve()
    )
    return run_scan(
        as_of=as_of,
        horizons=horizons,
        data_root=data_root,
        run_root=run_root,
        pins=pins,
        replay_service=_QapReplayService(repository),
        protocol=protocol,
    )


__all__ = ["run_scan_with_qap"]
