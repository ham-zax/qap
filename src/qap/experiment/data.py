"""Experiment dataset resolution, fingerprint admission, and exact windowing."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

from qap.experiment.dataset_seals import validate_dataset_seals
from qap.experiment.manifest import DataSourceSpec, ExperimentManifest
from qap.experiment.provenance import DatasetFingerprint
from qap.market import (
    AlignedBarSeries,
    BarInterval,
    ValidatedBarSeries,
    VenueInstrument,
    align_bar_series,
    fingerprint_bar_series,
    load_csv_bar_series,
    read_parquet_bar_series,
    validate_bar_series,
)


class ExperimentSetupError(ValueError):
    """Raised when frozen experiment inputs cannot compose one valid run."""


class DatasetFingerprintMismatchError(ExperimentSetupError):
    """Raised before replay when located data differs from its commitment."""


@dataclass(frozen=True, slots=True)
class LoadedExperimentData:
    aligned: AlignedBarSeries
    data_fingerprints: tuple[DatasetFingerprint, ...]
    series_by_instrument_id: Mapping[str, ValidatedBarSeries]
    fingerprint_by_instrument_id: Mapping[str, str]

    def __post_init__(self) -> None:
        series = dict(self.series_by_instrument_id)
        fingerprints = dict(self.fingerprint_by_instrument_id)
        if set(series) != set(fingerprints):
            raise ValueError(
                "loaded experiment instrument series/fingerprint keys must match"
            )
        object.__setattr__(self, "series_by_instrument_id", MappingProxyType(series))
        object.__setattr__(
            self,
            "fingerprint_by_instrument_id",
            MappingProxyType(fingerprints),
        )

    def aligned_for_instrument_ids(
        self,
        instrument_ids: Sequence[str],
    ) -> AlignedBarSeries:
        copied = tuple(instrument_ids)
        if not copied or len(set(copied)) != len(copied):
            raise ExperimentSetupError(
                "evidence instrument IDs must be non-empty and unique"
            )
        try:
            series = tuple(self.series_by_instrument_id[item] for item in copied)
        except KeyError as exc:
            raise ExperimentSetupError(
                f"unknown loaded instrument ID: {exc.args[0]}"
            ) from exc
        return align_bar_series(series)

    def fingerprint_for_instrument_id(self, instrument_id: str) -> str:
        try:
            return self.fingerprint_by_instrument_id[instrument_id]
        except KeyError as exc:
            raise ExperimentSetupError(
                f"unknown loaded instrument ID: {instrument_id}"
            ) from exc


def _safe_dataset_path(data_root: Path, relative_path: str) -> Path:
    root = data_root.resolve()
    candidate = (root / relative_path).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ExperimentSetupError(
            f"dataset path escapes configured data root: {relative_path}"
        ) from exc
    if not candidate.is_file():
        raise ExperimentSetupError(f"dataset path is not a file: {relative_path}")
    return candidate


def _load_dataset(
    *,
    source: DataSourceSpec,
    instrument: VenueInstrument,
    interval: BarInterval,
    data_root: Path,
) -> ValidatedBarSeries:
    path = _safe_dataset_path(data_root, source.relative_path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        series = load_csv_bar_series(
            path,
            instrument=instrument,
            interval=interval,
        )
    elif suffix in {".parquet", ".pq"}:
        series = read_parquet_bar_series(path)
        if series.instrument != instrument:
            raise ExperimentSetupError(
                f"dataset {source.dataset_id} instrument metadata does not "
                "match manifest"
            )
        if series.interval != interval:
            raise ExperimentSetupError(
                f"dataset {source.dataset_id} interval metadata does not match manifest"
            )
    else:
        raise ExperimentSetupError(
            f"unsupported dataset suffix for {source.dataset_id}: {suffix or '<none>'}"
        )

    actual = fingerprint_bar_series(series)
    if actual != source.expected_semantic_fingerprint:
        raise DatasetFingerprintMismatchError(
            f"dataset {source.dataset_id} fingerprint mismatch: "
            f"expected {source.expected_semantic_fingerprint}, got {actual}"
        )
    return series


def _slice_exact_window(
    series: ValidatedBarSeries,
    *,
    manifest: ExperimentManifest,
    dataset_id: str,
) -> ValidatedBarSeries:
    start = manifest.data_window.start
    end = manifest.data_window.end
    bars = tuple(bar for bar in series.bars if start <= bar.candle_open_time < end)
    if not bars:
        raise ExperimentSetupError(
            f"dataset {dataset_id} has no bars in the declared data window"
        )
    if bars[0].candle_open_time != start:
        raise ExperimentSetupError(
            f"dataset {dataset_id} does not start exactly at the declared window"
        )
    if bars[-1].bar_end_exclusive != end:
        raise ExperimentSetupError(
            f"dataset {dataset_id} does not end exactly at the declared window"
        )
    return validate_bar_series(bars)


def load_experiment_data(
    manifest: ExperimentManifest,
    *,
    data_root: str | Path,
) -> LoadedExperimentData:
    """Resolve, fingerprint-check, window, and align every declared dataset."""

    if not isinstance(cast(object, manifest), ExperimentManifest):
        raise TypeError("manifest must be an ExperimentManifest")
    try:
        validate_dataset_seals(manifest)
    except ValueError as exc:
        raise ExperimentSetupError(str(exc)) from exc
    root = Path(data_root)
    instruments = manifest.instruments_by_id()
    interval = manifest.interval_domain()
    series: list[ValidatedBarSeries] = []
    fingerprints: list[DatasetFingerprint] = []
    series_by_instrument_id: dict[str, ValidatedBarSeries] = {}
    fingerprint_by_instrument_id: dict[str, str] = {}
    for source in manifest.data_sources:
        loaded = _load_dataset(
            source=source,
            instrument=instruments[source.instrument_id],
            interval=interval,
            data_root=root,
        )
        actual = fingerprint_bar_series(loaded)
        fingerprints.append(
            DatasetFingerprint(
                dataset_id=source.dataset_id,
                fingerprint=actual,
            )
        )
        windowed = _slice_exact_window(
            loaded,
            manifest=manifest,
            dataset_id=source.dataset_id,
        )
        series.append(windowed)
        series_by_instrument_id[source.instrument_id] = windowed
        fingerprint_by_instrument_id[source.instrument_id] = actual
    return LoadedExperimentData(
        aligned=align_bar_series(series),
        data_fingerprints=tuple(fingerprints),
        series_by_instrument_id=series_by_instrument_id,
        fingerprint_by_instrument_id=fingerprint_by_instrument_id,
    )


__all__ = [
    "DatasetFingerprintMismatchError",
    "ExperimentSetupError",
    "LoadedExperimentData",
    "load_experiment_data",
]
