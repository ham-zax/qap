"""Scanner-neutral immutable Product market-data generation resolution."""

from pathlib import Path, PurePosixPath
from urllib.parse import quote

from pydantic import ValidationError

from qap.market import (
    MarketDataStorageError,
    ValidatedBarSeries,
    fingerprint_bar_series,
    read_parquet_bar_series,
)
from qap.product_market_data_cache import (
    GENERATION_CACHE,
    GenerationKey,
    stat_key,
)
from qap.product_market_data_models import (
    MarketDataGenerationProvenance,
    safe_relative_path,
    validated_text,
)

_GENERATION_ROOT = PurePosixPath("product-market-data/generations")


class ProductGenerationReadError(RuntimeError):
    """Raised when one sealed Product generation cannot be resolved exactly."""


def generation_relative_path(dataset_id: str, fingerprint: str) -> str:
    component = quote(validated_text(dataset_id, field="dataset_id"), safe="-_.~")
    if component in {".", ".."}:
        raise ValueError("dataset_id cannot resolve to a relative path marker")
    return (_GENERATION_ROOT / component / f"{fingerprint}.parquet").as_posix()


def provenance_relative_path(generation_path: str) -> str:
    path = PurePosixPath(safe_relative_path(generation_path))
    return path.with_suffix(".provenance.json").as_posix()


def resolve_immutable_generation(
    data_root: str | Path,
    *,
    dataset_id: str,
    semantic_fingerprint: str,
) -> tuple[MarketDataGenerationProvenance, ValidatedBarSeries]:
    """Resolve one exact published Product generation without catalog substitution."""

    root = Path(data_root).expanduser().resolve()
    relative_path = generation_relative_path(dataset_id, semantic_fingerprint)
    generation_path = root / relative_path
    provenance_path = root / provenance_relative_path(relative_path)
    try:
        resolved_generation = generation_path.resolve(strict=True)
        resolved_generation.relative_to(root)
        if not resolved_generation.is_file():
            raise OSError("generation path is not a file")
        cache_key: GenerationKey = (
            root,
            dataset_id,
            semantic_fingerprint,
            stat_key(resolved_generation),
            stat_key(provenance_path),
        )
        cached = GENERATION_CACHE.get(cache_key)
        if cached is not None:
            return cached
        provenance = MarketDataGenerationProvenance.model_validate_json(
            provenance_path.read_text(encoding="utf-8")
        )
        series = read_parquet_bar_series(resolved_generation)
    except (MarketDataStorageError, OSError, ValidationError, ValueError) as exc:
        raise ProductGenerationReadError(
            "Immutable market-data generation is unavailable or invalid."
        ) from exc
    fingerprint = fingerprint_bar_series(series)
    if (
        provenance.dataset_id != dataset_id
        or provenance.relative_path != relative_path
        or provenance.semantic_fingerprint != semantic_fingerprint
        or fingerprint != semantic_fingerprint
        or provenance.venue != series.instrument.venue
        or provenance.venue_symbol != series.instrument.venue_symbol
        or provenance.base_asset != series.instrument.base.key
        or provenance.quote_asset != series.instrument.quote.key
        or provenance.interval != series.interval.label
        or provenance.coverage_start != series.bars[0].candle_open_time
        or provenance.coverage_end_exclusive != series.bars[-1].bar_end_exclusive
    ):
        raise ProductGenerationReadError(
            "Immutable market-data generation does not match its provenance."
        )
    result = (provenance, series)
    GENERATION_CACHE.put(cache_key, result)
    return result


__all__ = [
    "ProductGenerationReadError",
    "generation_relative_path",
    "provenance_relative_path",
    "resolve_immutable_generation",
]
