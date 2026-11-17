"""Shared product-level input and venue-metadata resolver for forward L2 paper."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from qap.experiment.live_paper_candles import (
    CandleInputs,
    LivePaperCandleError,
    candle_inputs_from_lab_inputs,
)
from qap.product_lab_inputs import load_lab_inputs
from qap.product_market_data import ProductMarketData, ProductMarketDataError
from qap.product_market_data_generation import ProductGenerationReadError
from qap.product_pair_rotation_analysis import (
    PairAnalysisError,
    PairRotationAnalysis,
)
from qap.product_universe import ProductUniverse, ProductUniverseError


class PaperInputError(RuntimeError):
    """Raised when prepared market candles or venue constraints are missing."""


def resolve_paper_inputs(
    run_root: Path,
    data_root: Path | None,
    *,
    coin_a: str,
    coin_b: str,
    anchor: str | None,
    anchor_mode: Literal["auto", "none", "explicit"],
    bar: str,
    days: int | None = None,
    band_lookback: int = 96,
    require_metadata: bool = True,
) -> CandleInputs:
    """Resolve aligned timestamped candles and observed venue metadata."""

    if data_root is None:
        raise PaperInputError(
            "Market data root is not configured. Prepare pair data first."
        )
    window_days = days if days is not None else (30 if bar == "1m" else 180)
    query_anchor = "none" if anchor_mode == "none" else anchor
    universe = ProductUniverse(run_root)
    market_data = ProductMarketData(run_root, data_root)
    try:
        analysis = PairRotationAnalysis(universe, market_data, data_root).analyze(
            coin_a,
            coin_b,
            bar=bar,
            days=window_days,
            band_lookback=band_lookback,
            anchor=query_anchor,
        )
        lab_inputs = load_lab_inputs(universe, market_data, data_root, analysis)
    except (
        PairAnalysisError,
        ProductUniverseError,
        ProductMarketDataError,
        ProductGenerationReadError,
        LivePaperCandleError,
        ValueError,
    ) as exc:
        raise PaperInputError(str(exc)) from exc

    resolved_anchor: str | None = (
        None if analysis["anchor"] is None else str(analysis["anchor"]["id"])
    )
    if anchor_mode == "explicit" and anchor is not None and resolved_anchor != anchor:
        raise PaperInputError(f"Prepared window does not cover pinned anchor {anchor}.")

    candle_inputs = candle_inputs_from_lab_inputs(
        lab_inputs,
        bar,
        datasets=analysis.get("datasets", []),
        resolved_anchor=resolved_anchor,
    )
    if require_metadata:
        required = [lab_inputs.first.instrument, lab_inputs.second.instrument]
        seen_syms = {
            lab_inputs.first.instrument.venue_symbol,
            lab_inputs.second.instrument.venue_symbol,
        }
        if (
            lab_inputs.anchor is not None
            and lab_inputs.anchor.instrument.venue_symbol not in seen_syms
        ):
            required.append(lab_inputs.anchor.instrument)
        missing = [
            inst.venue_symbol
            for inst in required
            if inst.venue_symbol not in candle_inputs.metadata
        ]
        if missing:
            raise PaperInputError(
                f"Prepare observed venue metadata for {', '.join(missing)} first."
            )
    return candle_inputs
