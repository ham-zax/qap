"""Chronological Lab validation, control selection and multiplicity correction."""

from dataclasses import dataclass
from decimal import Decimal
from math import isfinite
from typing import Any, cast

import numpy as np
from arch.bootstrap import SPA

from qap.experiment.lab_replay import LabInputs, LabReplay, ReplayKind, run_lab_replay
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import LabSignal, signal_path
from qap.relationship.pair_measurements import Floats

CONTROL_KINDS: tuple[ReplayKind, ...] = ("daily", "weekly", "drift")


@dataclass(frozen=True, slots=True)
class LabProof:
    split: int
    signal: LabSignal
    applied_settings: LabSettings
    strategy: LabReplay | None
    benchmarks: dict[str, LabReplay]
    proof: dict[str, Any]
    call: dict[str, Any]
    folds: tuple[dict[str, Any], ...]


def settings_candidates(settings: LabSettings) -> tuple[LabSettings, ...]:
    if not settings.auto_tune:
        return (settings,)
    candidates: list[LabSettings] = []
    for factor in (0.8, 1.0, 1.2):
        values = settings.model_dump()
        if settings.method == "zscore":
            values["entry"] = max(
                settings.exit + 0.01, min(10.0, settings.entry * factor)
            )
        elif settings.method == "lead_lag":
            values["anchor_threshold"] = min(0.5, settings.anchor_threshold * factor)
        elif settings.method == "copula":
            values["copula_probability"] = min(
                0.49, settings.copula_probability * factor
            )
        else:
            values["fast_window"] = max(
                2, min(settings.slow_window - 1, round(settings.fast_window * factor))
            )
        candidate = LabSettings.model_validate(values)
        if candidate not in candidates:
            candidates.append(candidate)
    return tuple(candidates)


def _returns(values: Floats) -> Floats:
    return np.diff(np.log(np.maximum(values, 1e-300)))


def corrected_spa(
    strategy: Floats, control: Floats, trials: int
) -> tuple[float, float]:
    """Stationary block bootstrap SPA, then conservative across-family correction."""
    if strategy.size < 20 or strategy.shape != control.shape:
        return 1.0, 1.0
    advantage = strategy - control
    if not np.isfinite(advantage).all() or float(np.mean(advantage)) <= 0:
        return 1.0, 1.0
    if float(np.std(advantage)) < 1e-15:
        raw = 0.0
    else:
        test = SPA(
            -control,
            -strategy[:, None],
            block_size=max(2, int(np.sqrt(strategy.size))),
            reps=499,
            seed=20260930,
        )
        test.compute()
        raw = float(cast(Any, test.pvalues)["consistent"])
    # A finite bootstrap cannot establish p=0; keep multiplicity effective.
    raw = max(1.0 / 500, raw) if isfinite(raw) else 1.0
    return raw, min(1.0, raw * max(1, trials))


def _call(status: str, headline: str, reason: str) -> dict[str, Any]:
    return {
        "status": status,
        "headline": headline,
        "reason": reason,
        "target_weight_a": None,
        "rotation_fraction": None,
    }


def prove_lab_strategy(
    inputs: LabInputs,
    settings: LabSettings,
    *,
    trial_count: int,
    identity_confirmed: bool,
    execution_ready: bool = True,
    validation_reused: bool = False,
) -> LabProof:
    a = np.array([bar.close for bar in inputs.first.bars])
    b = np.array([bar.close for bar in inputs.second.bars])
    anchor = (
        None
        if inputs.anchor is None
        else np.array([bar.close for bar in inputs.anchor.bars])
    )
    size = a.size
    split = int(size * (1 - settings.proof_fraction))
    base_signal = signal_path(a, b, settings, anchor)
    minimum_training = max(
        settings.lookback + 2,
        settings.slow_window + 2 if settings.method == "trend" else 60,
    )
    proof: dict[str, Any] = {
        "passes": False,
        "data_role": "validation",
        "final_oos_used": False,
        "validation_reused": validation_reused,
        "settings_tried": trial_count,
        "control": None,
        "raw_p_value": None,
        "corrected_p_value": None,
        "significance": settings.significance,
        "folds_passing": 0,
        "folds_total": settings.folds,
        "minimum_passing_folds": settings.minimum_passing_folds,
        "validation_trades": 0,
        "minimum_trades": settings.minimum_trades,
        "vs_hodl_pct": None,
        "vs_control_pct": None,
        "cost_paid_pct": None,
        "gross_vs_hodl_pct": None,
        "cost_gate_passed": None,
        "tuning_cost_pct": None,
        "tuning_gross_vs_hodl_pct": None,
        "tuning_start": inputs.first.bars[0].candle_open_time.isoformat(),
        "tuning_end": inputs.first.bars[
            max(0, split - 1)
        ].bar_end_exclusive.isoformat(),
        "proof_start": inputs.first.bars[
            min(split, size - 1)
        ].candle_open_time.isoformat(),
        "proof_end": inputs.first.bars[-1].bar_end_exclusive.isoformat(),
        "correction": (
            "Stationary-bootstrap SPA (499 replicates), "
            "Bonferroni across all recorded settings"
        ),
        "limitations": [
            "Fixed-pair validation, not point-in-time universe discovery.",
            "Current-data research does not authorize live orders.",
            "Volume impact is an estimate, not calibrated execution evidence.",
            "Observed venue constraints are held fixed in historical simulation.",
            "Market notional filters use execution opens, not venue average prices.",
        ],
    }
    if not execution_ready:
        # Missing execution evidence outranks identity and history here: a
        # candidate, control or rebalancing replay would trade without observed
        # venue constraints or fail strict canonical preflight.
        context = {
            name: run_lab_replay(inputs, settings, base_signal, kind=name)
            for name in ("hodl", "hold_a", "hold_b")
        }
        return LabProof(
            split,
            base_signal,
            settings,
            None,
            context,
            proof,
            _call(
                "execution_data_missing",
                "Execution data is incomplete",
                "Prepare observed market history and venue constraints before "
                "using proof.",
            ),
            (),
        )
    if (
        split < minimum_training
        or size - split < max(40, settings.folds * 3)
        or not base_signal.available
    ):
        reason = base_signal.reason or (
            "Need older training history and at least "
            f"{max(40, settings.folds * 3)} validation bars."
        )
        context = {
            name: run_lab_replay(inputs, settings, base_signal, kind=name)
            for name in ("hodl", "daily", "hold_a", "hold_b")
        }
        return LabProof(
            split,
            base_signal,
            settings,
            None,
            context,
            proof,
            _call("insufficient_history", "Not enough history", reason),
            (),
        )
    candidates = settings_candidates(settings)
    signals = tuple(signal_path(a, b, candidate, anchor) for candidate in candidates)
    # Candidate paths are causal. Selection below reads their older returns only.
    paths = tuple(
        run_lab_replay(inputs, candidate, signal)
        for candidate, signal in zip(candidates, signals, strict=True)
    )
    tuning_index = max(
        range(len(candidates)),
        key=lambda i: float(paths[i].values[split - 1] / paths[i].values[0]),
    )
    tuning = run_lab_replay(
        inputs, candidates[tuning_index], signals[tuning_index], end=split
    )
    tuning_hodl = run_lab_replay(inputs, settings, base_signal, kind="hodl", end=split)
    tuning_cost = sum(
        (Decimal(t.fees_usdt) + Decimal(t.slippage_usdt) for t in tuning.trades),
        Decimal(0),
    )
    tuning_gross = tuning.terminal_value + tuning_cost - tuning_hodl.terminal_value
    cost_gate = tuning_gross >= settings.cost_budget_multiple * tuning_cost
    tuning_start_value = Decimal(str(tuning.values[0]))
    proof["cost_gate_passed"] = cost_gate
    proof["tuning_cost_pct"] = (
        float(tuning_cost / tuning_start_value) * 100
        if tuning_start_value > 0
        else None
    )
    proof["tuning_gross_vs_hodl_pct"] = (
        float(tuning_gross / tuning_start_value) * 100
        if tuning_start_value > 0
        else None
    )
    controls = {
        kind: run_lab_replay(inputs, settings, base_signal, kind=kind, end=split)
        for kind in CONTROL_KINDS
    }
    control = max(CONTROL_KINDS, key=lambda kind: controls[kind].terminal_value)
    proof["control"] = control
    edges = np.linspace(split, size, settings.folds + 1, dtype=int)
    chosen = np.full(size, np.nan)
    folds: list[dict[str, Any]] = []
    selected_index = 0
    for fold_index in range(settings.folds):
        start, end = int(edges[fold_index]), int(edges[fold_index + 1])
        train_start = max(0, start - split)

        def older_score(index: int) -> float:
            values = paths[index].values
            return float(values[start - 1] / values[int(train_start)] - 1)

        selected_index = max(range(len(candidates)), key=older_score)
        chosen[start:end] = signals[selected_index].preference[start:end]
        folds.append(
            {
                "fold": fold_index + 1,
                "start_index": start,
                "end_index": end,
                "training_start": inputs.first.bars[
                    train_start
                ].candle_open_time.isoformat(),
                "training_end": inputs.first.bars[
                    start - 1
                ].bar_end_exclusive.isoformat(),
                "test_start": inputs.first.bars[start].candle_open_time.isoformat(),
                "test_end": inputs.first.bars[end - 1].bar_end_exclusive.isoformat(),
                "settings": candidates[selected_index].model_dump(mode="json"),
                "passes": False,
            }
        )
    strategy = run_lab_replay(
        inputs, settings, base_signal, start=split, preferences=chosen
    )
    benchmarks = {
        name: run_lab_replay(inputs, settings, base_signal, kind=name, start=split)
        for name in ("hodl", control, "hold_a", "hold_b")
    }
    comparator = benchmarks[control]
    for fold in folds:
        left, right = fold["start_index"] - split, fold["end_index"] - split - 1
        previous = max(0, left - 1)
        gain = float(strategy.values[right] / strategy.values[previous] - 1)
        control_gain = float(comparator.values[right] / comparator.values[previous] - 1)
        fold["strategy_return_pct"], fold["control_return_pct"] = (
            gain * 100,
            control_gain * 100,
        )
        fold["passes"] = gain > control_gain + 1e-12
    raw_p, adjusted_p = corrected_spa(
        _returns(strategy.values), _returns(comparator.values), trial_count
    )
    passing = sum(bool(fold["passes"]) for fold in folds)
    above_hodl = strategy.terminal_value > benchmarks["hodl"].terminal_value
    above_control = strategy.terminal_value > comparator.terminal_value
    cost_paid = sum(
        (Decimal(t.fees_usdt) + Decimal(t.slippage_usdt) for t in strategy.trades),
        Decimal(0),
    )
    start_value = Decimal(str(strategy.values[0]))
    hodl_end = benchmarks["hodl"].terminal_value
    cost_paid_pct = float(cost_paid / start_value) * 100 if start_value > 0 else None
    gross_vs_hodl_pct = (
        float((strategy.terminal_value + cost_paid) / hodl_end - 1) * 100
        if hodl_end > 0
        else None
    )
    proof.update(
        {
            "raw_p_value": raw_p,
            "corrected_p_value": adjusted_p,
            "folds_passing": passing,
            "validation_trades": len(strategy.trades),
            "vs_hodl_pct": float(
                strategy.terminal_value / benchmarks["hodl"].terminal_value - 1
            )
            * 100,
            "vs_control_pct": float(
                strategy.terminal_value / comparator.terminal_value - 1
            )
            * 100,
            "cost_paid_pct": cost_paid_pct,
            "gross_vs_hodl_pct": gross_vs_hodl_pct,
        }
    )
    passed = (
        above_hodl
        and above_control
        and adjusted_p < settings.significance
        and passing >= settings.minimum_passing_folds
        and len(strategy.trades) >= settings.minimum_trades
        and strategy.costs_supported
        and execution_ready
        and cost_gate
    )
    proof["passes"] = passed
    applied, signal = candidates[selected_index], signals[selected_index]
    if not identity_confirmed:
        call = _call(
            "identity_unresolved",
            "Coin identity is unresolved",
            "Charts remain available. An economic call needs resolved identity.",
        )
    elif not strategy.costs_supported:
        call = _call(
            "cost_data_missing",
            "Trading costs cannot be measured",
            "Some candles had no trades when the test wanted to swap, so the cost "
            "of that swap is unknown. Try a larger candle size, such as 1h or 4h, "
            "or another pair.",
        )
    elif not cost_gate:
        call = _call(
            "cost_budget_failed",
            "Costs eat the edge",
            "On the tuning period, the gain before costs was less than "
            "twice the costs paid.",
        )
    elif not passed:
        call = _call(
            "no_edge",
            "No reliable edge right now",
            "The test found no reliable advantage after costs.",
        )
    else:
        if not np.isfinite(signal.preference[-1]):
            return LabProof(
                split,
                signal,
                applied,
                strategy,
                benchmarks,
                proof,
                _call(
                    "hold",
                    "Hold. No rotation signal right now.",
                    "Validation passes. The current signal is unavailable.",
                ),
                tuple(folds),
            )
        preference = float(signal.preference[-1])
        target = applied.initial_weight + applied.rotation_size * Decimal(
            str(preference)
        )
        asset = inputs.first.instrument.base
        current_weight = (
            float(strategy.ending_state.quantity(asset))
            * float(a[-1])
            / float(strategy.terminal_value)
        )
        can_rotate = size - 1 - strategy.last_rotation_index >= max(
            applied.minimum_hold, applied.cooldown
        )
        difference = float(target) - current_weight
        below_minimum = (
            abs(Decimal(str(difference))) * strategy.terminal_value
            < applied.minimum_notional
        )
        if preference == strategy.last_preference or below_minimum or not can_rotate:
            call = _call(
                "hold",
                "Hold. No rotation signal right now.",
                "Validation passes. The signal or hold period calls for holding.",
            )
        else:
            direction = "into_a" if difference > 0 else "into_b"
            call = _call(
                direction,
                "Rotate toward coin A" if difference > 0 else "Rotate toward coin B",
                "The current causal signal fires and its after-cost validation passes.",
            )
            call["target_weight_a"], call["rotation_fraction"] = (
                str(target),
                str(applied.rotation_size),
            )
    return LabProof(
        split, signal, applied, strategy, benchmarks, proof, call, tuple(folds)
    )
