"""Compose sealed data, authoritative research, trial counting and snapshots."""

import json
from collections.abc import Sequence
from decimal import Decimal
from math import isfinite
from pathlib import Path
from typing import Any

import numpy as np

from qap.experiment.lab_proof import LabProof, prove_lab_strategy, settings_candidates
from qap.experiment.lab_replay import LabInputs
from qap.experiment.provenance import code_fingerprint
from qap.policy.lab_settings import LabSettings
from qap.product_lab_advisor import advise_pair_strategies
from qap.product_lab_inputs import load_lab_inputs
from qap.product_lab_store import LabStudyStore, canonical_json
from qap.product_market_data import ProductMarketData
from qap.product_pair_rotation_analysis import PairRotationAnalysis
from qap.product_universe import ProductUniverse


def _sample_indices(
    size: int, *, offset: int = 0, extra: tuple[int, ...] = ()
) -> list[int]:
    stride = max(1, size // 1500)
    return sorted(
        set((*range(offset, offset + size, stride), offset + size - 1, *extra))
    )


def _wealth(inputs: LabInputs, result: LabProof) -> dict[str, Any] | None:
    paths = dict(result.benchmarks)
    if result.strategy is not None:
        paths["strategy"] = result.strategy
    if not paths:
        return None
    offset = result.split if result.strategy is not None else 0
    size = len(inputs.first.bars) - offset
    indices = _sample_indices(
        size,
        offset=offset,
        extra=()
        if result.strategy is None
        else tuple(trade.fill_index for trade in result.strategy.trades),
    )
    values = {
        name: [float(path.values[index - offset]) for index in indices]
        for name, path in paths.items()
    }
    return {
        "time": [
            int(inputs.first.bars[index].bar_end_exclusive.timestamp())
            for index in indices
        ],
        "value": values,
        "coins_a": {
            name: [
                value / inputs.first.bars[index].close
                for value, index in zip(curve, indices, strict=True)
            ]
            for name, curve in values.items()
        },
        "coins_b": {
            name: [
                value / inputs.second.bars[index].close
                for value, index in zip(curve, indices, strict=True)
            ]
            for name, curve in values.items()
        },
        "terminal_values": {
            name: str(path.terminal_value) for name, path in paths.items()
        },
        "window_kind": "validation" if result.strategy is not None else "context_only",
    }


def _statistics(result: LabProof) -> dict[str, dict[str, Any]]:
    paths = dict(result.benchmarks)
    if result.strategy is not None:
        paths["strategy"] = result.strategy
    statistics: dict[str, dict[str, Any]] = {}
    for name, replay in paths.items():
        peaks = np.maximum.accumulate(replay.values)
        drawdown = np.min(replay.values / peaks - 1) * 100
        statistics[name] = {
            "terminal_value_usdt": str(replay.terminal_value),
            "return_pct": float(replay.values[-1] / replay.values[0] - 1) * 100,
            "maximum_drawdown_pct": float(drawdown),
            "rotations": len(replay.trades),
            "executed_legs": sum(len(trade.fills) for trade in replay.trades),
            "fees_usdt": str(
                sum(
                    (Decimal(trade.fees_usdt) for trade in replay.trades),
                    Decimal(0),
                )
            ),
            "slippage_usdt": str(
                sum(
                    (Decimal(trade.slippage_usdt) for trade in replay.trades),
                    Decimal(0),
                )
            ),
            "terminal_holdings": {
                asset.key: str(quantity)
                for asset, quantity in replay.ending_state.holdings.items()
            },
        }
    return statistics


def _trades(result: LabProof) -> list[dict[str, Any]]:
    if result.strategy is None:
        return []
    return [
        {
            "decision_index": trade.decision_index,
            "fill_index": trade.fill_index,
            "time": trade.time,
            "direction": trade.direction,
            "route": trade.route,
            "fees_usdt": trade.fees_usdt,
            "slippage_usdt": trade.slippage_usdt,
            "fills": [
                {
                    "market": fill.venue_symbol,
                    "side": fill.side.value,
                    "base_quantity": str(fill.base_quantity),
                    "base_asset": fill.base.key,
                    "quote_asset": fill.quote.key,
                    "execution_price": str(fill.execution_price),
                    "reference_price": str(fill.reference_price),
                    "fee": str(fill.fee_amount),
                    "fee_asset": fill.fee_asset.key,
                }
                for fill in trade.fills
            ],
        }
        for trade in result.strategy.trades
    ]


def _execution_ready(inputs: LabInputs, settings: LabSettings) -> bool:
    metadata = {item.metadata.instrument for item in inputs.metadata}
    if settings.crash_defense_mode == "park_anchor":
        if inputs.anchor is None:
            return False
        needed: list[Any] = [inputs.first.instrument, inputs.second.instrument]
        if inputs.anchor.instrument.base not in (
            inputs.first.instrument.base,
            inputs.second.instrument.base,
        ):
            needed.append(inputs.anchor.instrument)
        return all(inst in metadata for inst in needed)
    if settings.crash_defense_mode == "park_usdt":
        return (
            inputs.first.instrument in metadata and inputs.second.instrument in metadata
        )
    required = (
        (inputs.direct.instrument,)
        if inputs.direct is not None
        else (inputs.first.instrument, inputs.second.instrument)
    )
    return all(instrument in metadata for instrument in required)


class LabStudyService:
    def __init__(
        self,
        universe: ProductUniverse,
        data: ProductMarketData,
        data_root: Path,
        run_root: Path,
        repository_root: Path,
        *,
        actor_id: str = "local",
    ) -> None:
        self.universe, self.data, self.data_root = universe, data, data_root
        self.store = LabStudyStore(run_root, actor_id=actor_id)
        self.repository_root = repository_root

    def _build_and_save(
        self,
        analysis: dict[str, Any],
        inputs: LabInputs,
        settings: LabSettings,
        *,
        count: int,
        reused: bool,
        fingerprint: str,
        execution_ready: bool,
    ) -> dict[str, Any]:
        result = prove_lab_strategy(
            inputs,
            settings,
            trial_count=count,
            identity_confirmed=analysis["identity_confirmed"],
            execution_ready=execution_ready,
            validation_reused=reused,
        )
        if result.call["status"] in ("into_a", "into_b"):
            a, b = analysis["coin_a"]["code"], analysis["coin_b"]["code"]
            result.call["headline"] = (
                f"Rotate {b} → {a}"
                if result.call["status"] == "into_a"
                else f"Rotate {a} → {b}"
            )
        samples = _sample_indices(len(inputs.first.bars))
        payload = {
            "schema_version": "qap.lab.study.v1",
            "analysis": analysis,
            "requested_settings": settings.model_dump(mode="json"),
            "applied_settings": result.applied_settings.model_dump(mode="json"),
            "call": result.call,
            "proof": result.proof,
            "signal": {
                "time": [
                    int(inputs.first.bars[index].bar_end_exclusive.timestamp())
                    for index in samples
                ],
                "values": [
                    float(result.signal.values[index])
                    if isfinite(result.signal.values[index])
                    else None
                    for index in samples
                ],
                "upper": result.signal.upper,
                "lower": result.signal.lower,
                "unit": result.signal.unit,
            },
            "wealth": _wealth(inputs, result),
            "trades": _trades(result),
            "folds": list(result.folds),
            "statistics": _statistics(result),
            "code_fingerprint": fingerprint,
            "execution_route": "direct"
            if inputs.direct is not None
            else "two legs via USDT",
            "execution_metadata": [
                {
                    "market": item.metadata.instrument.venue_symbol,
                    "fingerprint": item.source_fingerprint,
                    "observed_at": item.observed_at.isoformat(),
                }
                for item in inputs.metadata
            ],
        }
        return self.store.save(json.loads(canonical_json(payload)))

    def run(
        self,
        coin_a: str,
        coin_b: str,
        *,
        bar: str,
        days: int,
        band_lookback: int,
        anchor: str | None,
        settings: LabSettings,
    ) -> dict[str, Any]:
        family = self.store.family_id(coin_a, coin_b)
        with self.store.family_lock(family):
            analysis = PairRotationAnalysis(
                self.universe, self.data, self.data_root
            ).analyze(
                coin_a,
                coin_b,
                bar=bar,
                days=days,
                band_lookback=band_lookback,
                anchor=anchor,
            )
            inputs = load_lab_inputs(self.universe, self.data, self.data_root, analysis)
            split = int(len(inputs.first.bars) * (1 - settings.proof_fraction))
            fingerprint = code_fingerprint(self.repository_root)
            common = {
                "coin_a": coin_a,
                "coin_b": coin_b,
                "anchor": anchor,
                "bar": bar,
                "days": days,
                "protocol": "qap.lab.proof.v1",
                "code_fingerprint": fingerprint,
            }
            configurations = [
                {**common, "settings": candidate.model_dump(mode="json")}
                for candidate in settings_candidates(settings)
            ]
            count, reused = self.store.register_trials(
                family,
                configurations,
                validation_start=inputs.first.bars[split].candle_open_time.isoformat(),
                validation_end=inputs.first.bars[-1].bar_end_exclusive.isoformat(),
            )
            return self._build_and_save(
                analysis,
                inputs,
                settings,
                count=count,
                reused=reused,
                fingerprint=fingerprint,
                execution_ready=_execution_ready(inputs, settings),
            )

    def compare(
        self,
        coin_a: str,
        coin_b: str,
        *,
        bar: str,
        days: int,
        band_lookback: int,
        anchor: str | None,
        candidates: Sequence[LabSettings],
    ) -> dict[str, Any]:
        if not 1 <= len(candidates) <= 8:
            raise ValueError("Compare requires between 1 and 8 candidate settings.")
        family = self.store.family_id(coin_a, coin_b)
        with self.store.family_lock(family):
            analysis = PairRotationAnalysis(
                self.universe, self.data, self.data_root
            ).analyze(
                coin_a,
                coin_b,
                bar=bar,
                days=days,
                band_lookback=band_lookback,
                anchor=anchor,
            )
            advisor = advise_pair_strategies(analysis)
            inputs = load_lab_inputs(self.universe, self.data, self.data_root, analysis)
            split = int(len(inputs.first.bars) * (1 - candidates[0].proof_fraction))
            fingerprint = code_fingerprint(self.repository_root)
            common = {
                "coin_a": coin_a,
                "coin_b": coin_b,
                "anchor": anchor,
                "bar": bar,
                "days": days,
                "protocol": "qap.lab.proof.v1",
                "code_fingerprint": fingerprint,
            }
            configurations = [
                {**common, "settings": expanded.model_dump(mode="json")}
                for cand in candidates
                for expanded in settings_candidates(cand)
            ]
            count, reused = self.store.register_trials(
                family,
                configurations,
                validation_start=inputs.first.bars[split].candle_open_time.isoformat(),
                validation_end=inputs.first.bars[-1].bar_end_exclusive.isoformat(),
            )
            studies = [
                self._build_and_save(
                    analysis,
                    inputs,
                    cand,
                    count=count,
                    reused=reused,
                    fingerprint=fingerprint,
                    execution_ready=_execution_ready(inputs, cand),
                )
                for cand in candidates
            ]
        studies.sort(
            key=lambda s: (
                bool(s["result"]["proof"]["passes"]),
                s["result"]["proof"]["vs_hodl_pct"]
                if s["result"]["proof"]["vs_hodl_pct"] is not None
                else -1e9,
            ),
            reverse=True,
        )
        top = studies[0]
        best_study_id = (
            top["study_id"] if top["result"]["proof"]["passes"] is True else None
        )
        return {
            "advisor": advisor,
            "studies": studies,
            "best_study_id": best_study_id,
        }
