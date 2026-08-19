"""Product preflight for an exact current-capital qualification boundary."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from qap.experiment import read_run_artifacts
from qap.experiment.artifacts import ArtifactError
from qap.market import (
    MarketDataStorageError,
    ValidatedBarSeries,
    fingerprint_bar_series,
    read_parquet_bar_series,
)
from qap.scanner.catalog import ScannerCatalogError, load_scanner_catalog
from qap.scanner.prospective_artifacts import read_forward_cohort

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class ProductCurrentAssessmentError(RuntimeError):
    """Raised when current OHLCV cannot support a truthful Product assessment."""


def _latest_completed_boundary(now: datetime, duration: timedelta) -> datetime:
    elapsed = now - _EPOCH
    return _EPOCH + (elapsed // duration) * duration


def current_assessment_as_of(
    *,
    run_root: Path,
    data_root: Path,
    active_cohort_id: str,
    active_freeze_id: str,
    now: datetime | None = None,
) -> datetime:
    """Return the latest exact common current bar boundary or fail as stale."""

    current = datetime.now(UTC) if now is None else now.astimezone(UTC)
    try:
        cohort = read_forward_cohort(
            run_root.resolve() / "scanner-forward" / active_cohort_id
        )
    except (OSError, ValueError) as exc:
        raise ProductCurrentAssessmentError(
            "Follow-up evidence is invalid; repair the Research Idea evidence first."
        ) from exc
    freeze = next(
        (
            item
            for item in cohort.candidate_freezes
            if item.freeze_id == active_freeze_id
        ),
        None,
    )
    if freeze is None:
        raise ProductCurrentAssessmentError("Active follow-up freeze is unavailable.")
    try:
        historical = read_run_artifacts(
            run_root.resolve() / freeze.candidate_deep_replay_run_id
        ).manifest
    except (OSError, ArtifactError, ValueError) as exc:
        raise ProductCurrentAssessmentError(
            "Frozen historical replay evidence is unavailable."
        ) from exc
    try:
        catalog = load_scanner_catalog(data_root)
    except ScannerCatalogError as exc:
        raise ProductCurrentAssessmentError(
            "Current market data is invalid; refresh or repair market data."
        ) from exc
    instruments = {item.instrument_id: item for item in historical.instruments}
    series_by_dataset: dict[str, ValidatedBarSeries] = {}
    for source in historical.data_sources:
        try:
            current_source = catalog.source(source.dataset_id)
        except KeyError as exc:
            raise ProductCurrentAssessmentError(
                "Current market data no longer contains the frozen research source."
            ) from exc
        try:
            series = read_parquet_bar_series(data_root / current_source.relative_path)
        except (OSError, MarketDataStorageError) as exc:
            raise ProductCurrentAssessmentError(
                "Current market data is invalid; refresh or repair market data."
            ) from exc
        if (
            fingerprint_bar_series(series)
            != current_source.expected_semantic_fingerprint
        ):
            raise ProductCurrentAssessmentError(
                "Current market-data fingerprint does not match the catalog."
            )
        spec = instruments.get(source.instrument_id)
        if spec is None or series.instrument != spec.to_domain():
            raise ProductCurrentAssessmentError(
                "Current market data disagrees with the frozen instrument identity."
            )
        expected = _latest_completed_boundary(current, series.interval.duration)
        if not series.bars or series.bars[-1].bar_end_exclusive != expected:
            raise ProductCurrentAssessmentError(
                "Current market data is stale; refresh market data before assessing "
                "an amount."
            )
        series_by_dataset[source.dataset_id] = series
    if not series_by_dataset:
        raise ProductCurrentAssessmentError(
            "Frozen research has no current data sources."
        )
    cutoff = min(
        series.bars[-1].bar_end_exclusive for series in series_by_dataset.values()
    )
    if any(
        not any(bar.bar_end_exclusive == cutoff for bar in series.bars)
        for series in series_by_dataset.values()
    ):
        raise ProductCurrentAssessmentError(
            "Current market data has no common exact assessment boundary."
        )
    return cutoff


__all__ = ["ProductCurrentAssessmentError", "current_assessment_as_of"]
