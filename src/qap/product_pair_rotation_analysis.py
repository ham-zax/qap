"""Read-only Pair Rotation Lab composition over exact immutable generations."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from math import isfinite
from pathlib import Path
from threading import Lock
from typing import Any

import numpy as np

from qap.market import BarInterval, ValidatedBarSeries
from qap.product_coin_search import ResearchCoin, coins_for_listings
from qap.product_market_data import ProductMarketData
from qap.product_market_data_generation import (
    resolve_immutable_generation,
)
from qap.product_market_data_models import CurrentMarketDataGeneration
from qap.product_market_data_prepare import product_dataset_id
from qap.product_universe import (
    ProductUniverse,
    ProductUniverseError,
    ResolvedProductInstrument,
)
from qap.relationship.anchor_measurements import anchor_beta, lead_lag, rank_anchors
from qap.relationship.dependence_measurements import (
    copula_tails,
    granger,
    kalman_reading,
    rolling_dependence,
)
from qap.relationship.pair_measurements import (
    Floats,
    cointegration,
    correlation,
    half_life,
    hedge_ratio,
    hurst,
    log_returns,
    percentile_of_last,
    ratio_bands,
    regime,
)

DEFAULT_ANCHORS = ("binance:BTC", "binance:ETH", "binance:BNB", "binance:SOL")
_ANALYSIS_LOCK = Lock()
_ANALYSIS_CACHE: OrderedDict[tuple[object, ...], dict[str, Any]] = OrderedDict()


class PairAnalysisError(ValueError):
    """Required sealed data is not ready for descriptive analysis."""


def _coin(row: ResearchCoin) -> dict[str, str]:
    return {
        "id": row.listing_id,
        "code": row.venue_asset_code,
        "name": row.name,
        "identity_state": row.identity_state,
    }


def _measurement(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    result = asdict(value)
    # Degenerate statistical fits are unavailable, never infinite JSON numbers.
    if any(isinstance(item, float) and not isfinite(item) for item in result.values()):
        return None
    return result


def _anchor_link(coin: Floats, anchor: Floats) -> dict[str, Any] | None:
    beta = _measurement(anchor_beta(coin, anchor))
    if beta is None:
        return None
    beta["lead_lag"] = _measurement(lead_lag(coin, anchor, max_lag=8))
    return beta


class PairRotationAnalysis:
    """Compose existing owners without acquisition or economic state changes."""

    def __init__(
        self, universe: ProductUniverse, market_data: ProductMarketData, data_root: Path
    ) -> None:
        self.universe = universe
        self.market_data = market_data
        self.data_root = data_root

    def analyze(
        self,
        coin_a: str,
        coin_b: str,
        *,
        bar: str,
        days: int,
        band_lookback: int,
        anchor: str | None = None,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        directory = self.universe.read_directory()
        if directory is None:
            raise ProductUniverseError(
                "Current market directory has not been refreshed."
            )
        state = self.universe.read_state()
        no_anchor = anchor == "none"
        explicit_anchor = None if anchor in (None, "none") else anchor
        needed_ids = {coin_a, coin_b, *DEFAULT_ANCHORS}
        if explicit_anchor is not None:
            needed_ids.add(explicit_anchor)
        rows = {
            row.listing_id: row
            for row in coins_for_listings(
                directory,
                self.universe.registry_snapshot(),
                state,
                needed_ids,
            )
        }
        scope = self.universe.research_scope_from_snapshot(
            directory, state, rows, (coin_a, coin_b)
        )
        if explicit_anchor is not None and (
            explicit_anchor not in rows or not rows[explicit_anchor].trading
        ):
            raise PairAnalysisError("Choose an eligible anchor listing.")
        interval = BarInterval(bar)
        wanted = dict.fromkeys(
            (
                *DEFAULT_ANCHORS,
                *((explicit_anchor,) if explicit_anchor else ()),
            )
        )
        instruments: dict[str, ResolvedProductInstrument] = {
            coin_a: scope.instruments[0],
            coin_b: scope.instruments[1],
        }
        for key in wanted:
            if key not in instruments and key in rows and rows[key].trading:
                try:
                    instruments[key] = self.universe.research_scope_from_snapshot(
                        directory, state, rows, (key, coin_a)
                    ).instruments[0]
                except ProductUniverseError:
                    continue
        generations = {
            item.dataset_id: item
            for item in self.market_data.projection(
                intervals=frozenset({bar}),
                dataset_ids=frozenset(
                    product_dataset_id(inst, interval) for inst in instruments.values()
                ),
            ).generations
        }
        loaded: dict[str, tuple[CurrentMarketDataGeneration, ValidatedBarSeries]] = {}

        def load(key: str) -> tuple[CurrentMarketDataGeneration, ValidatedBarSeries]:
            if key in loaded:
                return loaded[key]
            instrument = instruments.get(key)
            if instrument is None:
                partner = coin_b if key == coin_a else coin_a
                instrument = self.universe.research_scope_from_snapshot(
                    directory, state, rows, (key, partner)
                ).instruments[0]
            dataset_id = product_dataset_id(instrument, interval)
            generation = generations.get(dataset_id)
            if generation is None or generation.provenance_status != "complete":
                raise PairAnalysisError(
                    f"Prepare {rows[key].venue_asset_code} data first."
                )
            _, series = resolve_immutable_generation(
                self.data_root,
                dataset_id=dataset_id,
                semantic_fingerprint=generation.semantic_fingerprint,
            )
            if (
                series.instrument != instrument.instrument
                or series.interval != interval
            ):
                raise PairAnalysisError("Prepared data does not match this listing.")
            loaded[key] = generation, series
            return loaded[key]

        _, first = load(coin_a)
        _, second = load(coin_b)
        cutoff = now or datetime.now(UTC)
        a_bars = {
            item.candle_open_time: item
            for item in first.bars
            if item.bar_end_exclusive <= cutoff
        }
        b_bars = {
            item.candle_open_time: item
            for item in second.bars
            if item.bar_end_exclusive <= cutoff
        }
        shared = sorted(a_bars.keys() & b_bars.keys())
        if not shared:
            raise PairAnalysisError("The coins have no shared completed bars.")
        data_through = shared[-1] + interval.duration
        start = data_through - timedelta(days=days)
        times = [time for time in shared if time >= start]
        if len(times) < 2:
            raise PairAnalysisError("At least two shared completed bars are required.")
        if any(
            right - left != interval.duration for left, right in zip(times, times[1:])
        ):
            raise PairAnalysisError("Shared history contains missing bars.")
        for key in wanted:
            if key in rows and rows[key].trading:
                try:
                    load(key)
                except PairAnalysisError, ProductUniverseError:
                    continue
        cache_key = (
            coin_a,
            coin_b,
            bar,
            days,
            band_lookback,
            "none" if no_anchor else explicit_anchor,
            scope.directory_id,
            scope.economic_identity_confirmed,
            data_through,
            tuple(
                (
                    key,
                    rows[key].venue_asset_code,
                    rows[key].name,
                    rows[key].identity_state,
                    gen.dataset_id,
                    gen.semantic_fingerprint,
                    gen.coverage_start,
                    gen.coverage_end_exclusive,
                )
                for key, (gen, _) in loaded.items()
            ),
        )
        with _ANALYSIS_LOCK:
            cached_analysis = _ANALYSIS_CACHE.get(cache_key)
            if cached_analysis is not None:
                _ANALYSIS_CACHE.move_to_end(cache_key)
                return deepcopy(cached_analysis)
        close_a = np.array([a_bars[time].close for time in times], dtype=np.float64)
        close_b = np.array([b_bars[time].close for time in times], dtype=np.float64)
        ratio = close_a / close_b
        if not np.isfinite(ratio).all() or not np.greater(ratio, 0).all():
            raise PairAnalysisError("The price ratio cannot be represented safely.")
        bands = ratio_bands(ratio, lookback=band_lookback)
        returns_a, returns_b = log_returns(close_a), log_returns(close_b)
        candidates: dict[str, tuple[Floats, Floats, Floats]] = {}
        anchor_prices: dict[str, Floats] = {}
        for key in wanted:
            if key not in loaded:
                continue
            _, series = loaded[key]
            prices = {
                item.candle_open_time: item.close
                for item in series.bars
                if item.bar_end_exclusive <= cutoff
            }
            if not all(time in prices for time in times):
                continue
            closes = np.array([prices[time] for time in times], dtype=np.float64)
            anchor_prices[key] = closes
            # Every candidate uses the same pair window, so scores are comparable.
            if key not in (coin_a, coin_b):
                candidates[key] = returns_a, returns_b, log_returns(closes)
        ranking = rank_anchors(candidates)
        selected = (
            None
            if no_anchor
            else explicit_anchor
            if explicit_anchor is not None
            else (ranking[0].anchor if ranking else None)
        )
        selected_prices = anchor_prices.get(selected) if selected else None
        anchor_returns = (
            log_returns(selected_prices) if selected_prices is not None else None
        )
        log_ratio = np.log(ratio)
        measurements = {
            "correlation": _measurement(correlation(returns_a, returns_b)),
            "cointegration": _measurement(
                cointegration(np.log(close_a), np.log(close_b))
            ),
            "hedge_ratio": _measurement(hedge_ratio(np.log(close_a), np.log(close_b))),
            "half_life": _measurement(half_life(log_ratio)),
            "hurst": _measurement(hurst(log_ratio)),
            "ratio_percentile": percentile_of_last(ratio),
            "regime": _measurement(regime(log_ratio, window=min(band_lookback, 40))),
            "anchor_a": None
            if anchor_returns is None
            else _anchor_link(returns_a, anchor_returns),
            "anchor_b": None
            if anchor_returns is None
            else _anchor_link(returns_b, anchor_returns),
            "kalman": _measurement(kalman_reading(np.log(close_a), np.log(close_b))),
            "granger": _measurement(granger(returns_a, returns_b)),
            "copula": _measurement(copula_tails(close_a, close_b)),
            "rolling_dependence": _measurement(
                rolling_dependence(returns_a, returns_b, window=band_lookback)
            ),
        }
        result = {
            "schema_version": "qap.api.pair-rotation-analysis.v1",
            "coin_a": _coin(rows[coin_a]),
            "coin_b": _coin(rows[coin_b]),
            "bar": bar,
            "window_days": days,
            "band_lookback": band_lookback,
            "data_through": data_through,
            "bars_used": len(times),
            "identity_confirmed": scope.economic_identity_confirmed,
            "series": {
                "time": [int(time.timestamp()) for time in times],
                "close_a": close_a.tolist(),
                "close_b": close_b.tolist(),
                "ratio": ratio.tolist(),
                "mean": [
                    float(value) if isfinite(value) else None for value in bands.mean
                ],
                "std": [
                    float(value) if isfinite(value) else None for value in bands.std
                ],
                "anchor_close": None
                if selected_prices is None
                else selected_prices.tolist(),
            },
            "anchor": None
            if selected is None or selected_prices is None
            else _coin(rows[selected]),
            "anchor_ranking": [
                {
                    "anchor": _coin(rows[fit.anchor]),
                    "beta_a": fit.beta_a,
                    "beta_b": fit.beta_b,
                    "joint_explained": fit.joint_explained,
                }
                for fit in ranking
            ],
            "measurements": measurements,
            "datasets": [
                {
                    "dataset_id": item.dataset_id,
                    "interval": item.interval,
                    "venue_symbol": item.venue_symbol,
                    "semantic_fingerprint": item.semantic_fingerprint,
                    "coverage_start": item.coverage_start,
                    "cutoff": item.coverage_end_exclusive,
                }
                for item, _ in loaded.values()
            ],
        }
        with _ANALYSIS_LOCK:
            _ANALYSIS_CACHE[cache_key] = deepcopy(result)
            _ANALYSIS_CACHE.move_to_end(cache_key)
            while len(_ANALYSIS_CACHE) > 32:
                _ANALYSIS_CACHE.popitem(last=False)
        return result
