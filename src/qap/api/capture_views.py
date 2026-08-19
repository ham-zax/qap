"""Read-only current-evidence readiness over authoritative forward lineage."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal, cast

from qap.api.errors import ApiBoundaryError
from qap.api.scanner_schemas import CaptureReadinessDto, ForwardCohortDetailDto
from qap.experiment import read_run_artifacts
from qap.market import MicrostructureStorageError, read_public_book_snapshots
from qap.market.microstructure_storage import read_public_market_metadata_snapshots
from qap.market.public_capture import CaptureKind, capture_file
from qap.scanner.liquidity_policy import evaluate_capture_contract
from qap.scanner.prospective_protocol import (
    DAILY_COVERAGE_MINIMUM,
    OVERALL_COVERAGE_MINIMUM,
)


def _unavailable(message: str, *, cohort_id: str) -> ApiBoundaryError:
    return ApiBoundaryError(
        code="capture_readiness_unavailable",
        message=message,
        status_code=409,
        context={"forward_cohort_id": cohort_id},
    )


def _capture_times(
    root: Path,
    *,
    venue: str,
    venue_symbol: str,
    kind: CaptureKind,
) -> tuple[datetime, ...]:
    path = capture_file(root, venue=venue, venue_symbol=venue_symbol, kind=kind)
    if not path.is_file():
        return ()
    return tuple(item.observed_at for item in read_public_book_snapshots(path))


def forward_capture_readiness(
    *,
    detail: ForwardCohortDetailDto,
    run_root: Path,
    capture_root: Path,
    checkpoint_id: str,
    as_of: datetime,
) -> CaptureReadinessDto:
    """Project finite capture work without moving capture policy into the API/UI."""

    cohort_id = detail.summary.cohort_id
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise ApiBoundaryError(
            code="capture_readiness_invalid",
            message="Current evidence as-of must be timezone-aware UTC.",
            status_code=422,
            context={"forward_cohort_id": cohort_id},
        )
    current_as_of = as_of.astimezone(UTC)
    checkpoint = next(
        (item for item in detail.checkpoints if item.checkpoint_id == checkpoint_id),
        None,
    )
    if checkpoint is None:
        raise ApiBoundaryError(
            code="forward_checkpoint_not_found",
            message="Forward checkpoint was not found in this validation.",
            status_code=404,
            context={"checkpoint_id": checkpoint_id},
        )
    if current_as_of < checkpoint.information_end:
        raise ApiBoundaryError(
            code="capture_readiness_invalid",
            message="Current evidence as-of must not precede the selected checkpoint.",
            status_code=422,
            context={"checkpoint_id": checkpoint_id},
        )
    freeze = next(
        (item for item in detail.freezes if item.freeze_id == checkpoint.freeze_id),
        None,
    )
    if freeze is None:
        raise _unavailable(
            "Selected checkpoint is missing its frozen research lineage.",
            cohort_id=cohort_id,
        )

    try:
        historical = read_run_artifacts(
            run_root.resolve() / freeze.candidate_deep_replay_run_id
        ).manifest
        execution_instrument_id = historical.execution.execution_instrument_id
        instrument_spec = next(
            (
                item
                for item in historical.instruments
                if item.instrument_id == execution_instrument_id
            ),
            None,
        )
        if instrument_spec is None:
            raise ValueError("execution instrument is missing")
        instrument = instrument_spec.to_domain()
        if instrument.venue != freeze.venue:
            raise ValueError("frozen venue does not match execution instrument")
        if instrument.venue not in {"binance", "gate"}:
            raise ValueError("execution venue is not capture-supported")
        venue = cast(Literal["binance", "gate"], instrument.venue)

        l1_observations = _capture_times(
            capture_root.resolve(),
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.L1,
        )
        depth_observations = _capture_times(
            capture_root.resolve(),
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.DEPTH,
        )
        metadata_path = capture_file(
            capture_root.resolve(),
            venue=instrument.venue,
            venue_symbol=instrument.venue_symbol,
            kind=CaptureKind.METADATA,
        )
        metadata_rows = (
            read_public_market_metadata_snapshots(metadata_path)
            if metadata_path.is_file()
            else ()
        )
        coverage = evaluate_capture_contract(
            l1_observations,
            depth_observations,
            window_end=current_as_of,
        )
    except (
        OSError,
        MicrostructureStorageError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        raise _unavailable(
            "Current market evidence could not be read from authoritative lineage.",
            cohort_id=cohort_id,
        ) from exc

    metadata_available = any(
        item.observed_at <= current_as_of for item in metadata_rows
    )
    l1_ready = (
        coverage.l1_overall_coverage >= OVERALL_COVERAGE_MINIMUM
        and coverage.minimum_l1_daily_coverage >= DAILY_COVERAGE_MINIMUM
    )
    depth_ready = (
        coverage.depth_overall_coverage >= OVERALL_COVERAGE_MINIMUM
        and coverage.minimum_depth_daily_coverage >= DAILY_COVERAGE_MINIMUM
    )
    missing: list[Literal["l1", "depth", "metadata"]] = []
    if not l1_ready:
        missing.append("l1")
    if not depth_ready:
        missing.append("depth")
    if not metadata_available:
        missing.append("metadata")

    return CaptureReadinessDto(
        cohort_id=cohort_id,
        checkpoint_id=checkpoint.checkpoint_id,
        as_of=current_as_of,
        window_start=coverage.window_start,
        window_end=coverage.window_end,
        venue=venue,
        venue_symbol=instrument.venue_symbol,
        base_asset=instrument.base.key,
        quote_asset=instrument.quote.key,
        l1_expected_slots=coverage.l1_expected_slots,
        l1_captured_slots=coverage.l1_captured_slots,
        l1_overall_coverage=str(coverage.l1_overall_coverage),
        depth_expected_slots=coverage.depth_expected_slots,
        depth_captured_slots=coverage.depth_captured_slots,
        depth_overall_coverage=str(coverage.depth_overall_coverage),
        metadata_available=metadata_available,
        ready=coverage.satisfied and metadata_available,
        missing_capture_kinds=tuple(missing),
    )


__all__ = ["forward_capture_readiness"]
