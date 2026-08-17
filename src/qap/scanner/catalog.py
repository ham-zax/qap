"""Scanner-local catalog for admitted immutable market-data artifacts."""

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
    model_validator,
)

from qap.market import (
    BarInterval,
    MarketDataStorageError,
    ValidatedBarSeries,
    fingerprint_bar_series,
    read_parquet_bar_series,
)
from qap.portfolio import AssetId


class ScannerCatalogError(ValueError):
    """Raised when a scanner catalog cannot be admitted safely."""


def _text(value: str, *, field: str, lower: bool = False) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized.lower() if lower else normalized


def _safe_relative_posix(value: str) -> str:
    normalized = value.strip()
    if not normalized or "\\" in normalized:
        raise ValueError("path must be a safe relative POSIX path")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("path must be a safe relative POSIX path")
    return path.as_posix()


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class ScannerSourceSpec(_FrozenModel):
    dataset_id: str
    relative_path: str
    venue: str
    venue_symbol: str
    base_asset: str
    quote_asset: str
    interval: str
    expected_semantic_fingerprint: str
    lifecycle_evidence_ids: tuple[str, ...] = ()
    direct_pair_dataset_ids: tuple[str, ...] = ()

    @field_validator("dataset_id", "venue_symbol")
    @classmethod
    def validate_text(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "value")
        return _text(value, field=field_name)

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, value: str) -> str:
        return _text(value, field="venue", lower=True)

    @field_validator("base_asset", "quote_asset")
    @classmethod
    def validate_asset(cls, value: str) -> str:
        return AssetId(value).key

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, value: str) -> str:
        return BarInterval(value).label

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, value: str) -> str:
        return _safe_relative_posix(value)

    @field_validator("expected_semantic_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) != 64 or any(
            character not in "0123456789abcdef" for character in normalized
        ):
            raise ValueError(
                "expected_semantic_fingerprint must be a 64-character SHA-256 hex"
            )
        return normalized

    @field_validator("lifecycle_evidence_ids", "direct_pair_dataset_ids")
    @classmethod
    def validate_ids(cls, values: tuple[str, ...], info: object) -> tuple[str, ...]:
        field_name = getattr(info, "field_name", "ids")
        normalized = tuple(_text(value, field=field_name) for value in values)
        if len(set(normalized)) != len(normalized):
            raise ValueError(f"{field_name} must not contain duplicates")
        return normalized


class ScannerCatalog(_FrozenModel):
    schema_version: Literal["qap.scanner.catalog.v1"]
    lifecycle_evidence_relative_path: str
    sources: tuple[ScannerSourceSpec, ...]

    @field_validator("lifecycle_evidence_relative_path")
    @classmethod
    def validate_lifecycle_path(cls, value: str) -> str:
        return _safe_relative_posix(value)

    @model_validator(mode="after")
    def validate_sources(self) -> Self:
        dataset_ids = tuple(source.dataset_id for source in self.sources)
        if not dataset_ids:
            raise ValueError("catalog sources must not be empty")
        if len(set(dataset_ids)) != len(dataset_ids):
            raise ValueError("catalog dataset_id values must be unique")
        known = set(dataset_ids)
        for source in self.sources:
            missing = set(source.direct_pair_dataset_ids) - known
            if missing:
                raise ValueError(
                    "direct_pair_dataset_ids must reference catalog sources; "
                    f"missing={sorted(missing)}"
                )
        return self

    def source(self, dataset_id: str) -> ScannerSourceSpec:
        normalized = _text(dataset_id, field="dataset_id")
        for source in self.sources:
            if source.dataset_id == normalized:
                return source
        raise KeyError(normalized)


@dataclass(frozen=True, slots=True)
class ResolvedCatalogSource:
    spec: ScannerSourceSpec
    series: ValidatedBarSeries
    source_artifact_fingerprint: str


def _safe_existing_file(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    candidate = (resolved_root / relative_path).resolve(strict=True)
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ScannerCatalogError(
            f"catalog path escapes configured data root: {relative_path}"
        ) from exc
    if not candidate.is_file():
        raise ScannerCatalogError(f"catalog path is not a file: {relative_path}")
    return candidate


def load_scanner_catalog(data_root: str | Path) -> ScannerCatalog:
    root = Path(data_root)
    catalog_path = root / "catalog.json"
    try:
        raw = catalog_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ScannerCatalogError(
            f"cannot read scanner catalog: {catalog_path}"
        ) from exc
    try:
        catalog = ScannerCatalog.model_validate_json(raw)
    except ValidationError as exc:
        raise ScannerCatalogError(f"scanner catalog is invalid: {exc}") from exc

    try:
        _safe_existing_file(root, catalog.lifecycle_evidence_relative_path)
    except (OSError, ScannerCatalogError) as exc:
        raise ScannerCatalogError("scanner lifecycle evidence path is invalid") from exc
    return catalog


def resolve_catalog_source(
    catalog: ScannerCatalog,
    *,
    dataset_id: str,
    data_root: str | Path,
) -> ResolvedCatalogSource:
    if not isinstance(cast(object, catalog), ScannerCatalog):
        raise TypeError("catalog must be a ScannerCatalog")
    try:
        spec = catalog.source(dataset_id)
    except KeyError as exc:
        raise ScannerCatalogError(f"unknown scanner dataset_id: {dataset_id}") from exc

    try:
        path = _safe_existing_file(Path(data_root), spec.relative_path)
        series = read_parquet_bar_series(path)
    except (OSError, MarketDataStorageError, ScannerCatalogError) as exc:
        if isinstance(exc, ScannerCatalogError):
            raise
        raise ScannerCatalogError(
            f"cannot admit scanner dataset {spec.dataset_id}"
        ) from exc

    instrument = series.instrument
    if (
        instrument.venue != spec.venue
        or instrument.venue_symbol != spec.venue_symbol
        or instrument.base != AssetId(spec.base_asset)
        or instrument.quote != AssetId(spec.quote_asset)
        or series.interval != BarInterval(spec.interval)
    ):
        raise ScannerCatalogError(
            f"scanner dataset {spec.dataset_id} metadata does not match catalog"
        )

    actual = fingerprint_bar_series(series)
    if actual != spec.expected_semantic_fingerprint:
        raise ScannerCatalogError(
            f"scanner dataset {spec.dataset_id} fingerprint mismatch: "
            f"expected {spec.expected_semantic_fingerprint}, got {actual}"
        )
    return ResolvedCatalogSource(
        spec=spec,
        series=series,
        source_artifact_fingerprint=actual,
    )


__all__ = [
    "ResolvedCatalogSource",
    "ScannerCatalog",
    "ScannerCatalogError",
    "ScannerSourceSpec",
    "load_scanner_catalog",
    "resolve_catalog_source",
]
