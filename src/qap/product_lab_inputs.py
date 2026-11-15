"""Resolve observed pair/anchor/direct inputs through existing dataset owners."""

from pathlib import Path
from typing import Any

from qap.experiment.lab_replay import LabInputs
from qap.market import BarInterval, validate_bar_series
from qap.product_lab_metadata import read_lab_metadata
from qap.product_market_data import ProductMarketData
from qap.product_market_data_generation import resolve_immutable_generation
from qap.product_market_data_prepare import product_dataset_id
from qap.product_pair_rotation_analysis import PairAnalysisError
from qap.product_pair_rotation_markets import direct_instrument
from qap.product_universe import (
    ProductUniverse,
    ResolvedProductInstrument,
)


def load_lab_inputs(
    universe: ProductUniverse,
    data: ProductMarketData,
    data_root: Path,
    analysis: dict[str, Any],
) -> LabInputs:
    scope = universe.research_scope(
        (analysis["coin_a"]["id"], analysis["coin_b"]["id"]), refresh_bindings=False
    )
    interval = BarInterval(analysis["bar"])
    first, second = scope.instruments
    direct = direct_instrument(universe, scope)
    anchor = None
    if analysis["anchor"] is not None:
        key = analysis["anchor"]["id"]
        anchor = (
            first
            if key == analysis["coin_a"]["id"]
            else second
            if key == analysis["coin_b"]["id"]
            else universe.research_scope(
                (key, analysis["coin_a"]["id"]), refresh_bindings=False
            ).instruments[0]
        )
    instruments = tuple(
        dict.fromkeys(
            item for item in (first, second, direct, anchor) if item is not None
        )
    )
    ids = frozenset(product_dataset_id(item, interval) for item in instruments)
    generations = {
        item.dataset_id: item for item in data.projection(dataset_ids=ids).generations
    }
    exact = {
        row["dataset_id"]: row["semantic_fingerprint"] for row in analysis["datasets"]
    }
    selected_times = set(analysis["series"]["time"])

    def load(item: ResolvedProductInstrument):
        dataset_id = product_dataset_id(item, interval)
        current = generations.get(dataset_id)
        fingerprint = exact.get(dataset_id) or (
            None if current is None else current.semantic_fingerprint
        )
        if fingerprint is None:
            raise PairAnalysisError(
                f"Prepare observed {item.instrument.venue_symbol} execution data first."
            )
        provenance, series = resolve_immutable_generation(
            data_root, dataset_id=dataset_id, semantic_fingerprint=fingerprint
        )
        if series.instrument != item.instrument:
            raise PairAnalysisError("Dataset identity changed. Reopen the pair.")
        if dataset_id not in exact:
            analysis["datasets"].append(
                {
                    "dataset_id": dataset_id,
                    "semantic_fingerprint": fingerprint,
                    "interval": interval.label,
                    "venue_symbol": item.instrument.venue_symbol,
                    "coverage_start": provenance.coverage_start,
                    "cutoff": provenance.coverage_end_exclusive,
                }
            )
        bars = tuple(
            bar
            for bar in series.bars
            if int(bar.candle_open_time.timestamp()) in selected_times
        )
        if len(bars) != len(selected_times):
            raise PairAnalysisError(
                "Execution history does not cover the selected pair window."
            )
        return validate_bar_series(bars)

    return LabInputs(
        load(first),
        load(second),
        None if direct is None else load(direct),
        None if anchor is None else load(anchor),
        read_lab_metadata(
            data_root,
            tuple(
                item.instrument
                for item in instruments
                if item != anchor or item in (first, second, direct)
            ),
        ),
    )
