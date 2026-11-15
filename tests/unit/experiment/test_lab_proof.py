"""Lab proof keeps chronological tuning and finite multiplicity correction."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import numpy as np
import pytest

from qap.execution import MultiAssetPreflightError
from qap.experiment.lab_proof import (
    corrected_spa,
    prove_lab_strategy,
    settings_candidates,
)
from qap.experiment.lab_replay import LabInputs, LabReplay, ReplayKind, run_lab_replay
from qap.market import (
    BarInterval,
    MarketBar,
    ValidatedBarSeries,
    VenueInstrument,
    validate_bar_series,
)
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import (
    PublicMarketMetadataSnapshot,
    public_market_metadata_snapshot_from_metadata,
)
from qap.policy.lab_settings import LabSettings
from qap.policy.lab_signals import LabSignal, signal_path
from qap.portfolio import AssetId
from qap.relationship.pair_measurements import Floats


def _instrument(code: str) -> VenueInstrument:
    return VenueInstrument("binance", f"{code}USDT", AssetId(code), AssetId("USDT"))


def market_inputs(*, changed_after: int | None = None) -> LabInputs:
    size = 600
    index = np.arange(size)
    a = np.exp(0.03 * np.sin(index * 0.3) + index * 0.0001)
    b = np.exp(index * 0.00005)
    if changed_after is not None:
        a[changed_after:] *= np.exp(np.linspace(0, 2, size - changed_after))
    series: list[ValidatedBarSeries] = []
    for code, prices in (("A", a), ("B", b)):
        instrument = _instrument(code)
        series.append(
            validate_bar_series(
                tuple(
                    MarketBar(
                        instrument=instrument,
                        interval=BarInterval("1h"),
                        candle_open_time=datetime(2026, 1, 1, tzinfo=UTC)
                        + timedelta(hours=int(offset)),
                        open=float(price),
                        high=float(price),
                        low=float(price),
                        close=float(price),
                        volume=1_000_000.0,
                    )
                    for offset, price in enumerate(prices)
                )
            )
        )
    return LabInputs(series[0], series[1])


def metadata_snapshots(*, legs: int = 2) -> tuple[PublicMarketMetadataSnapshot, ...]:
    """Canonical venue constraints for the first ``legs`` Lab instruments."""
    return tuple(
        public_market_metadata_snapshot_from_metadata(
            metadata=MarketMetadata(
                instrument=instrument,
                status="TRADING",
                price_tick=Decimal("0.000001"),
                minimum_price=None,
                maximum_price=None,
                quantity_step=Decimal("0.000001"),
                minimum_quantity=None,
                maximum_quantity=None,
                minimum_notional=None,
                maximum_notional=None,
                minimum_notional_applies_to_market=False,
                maximum_notional_applies_to_market=False,
                notional_average_price_minutes=5,
            ),
            observed_at=datetime(2026, 1, 1, tzinfo=UTC),
            source_id=f"binance-exchangeInfo:{instrument.venue_symbol}",
        )
        for instrument in (_instrument("A"), _instrument("B"))[:legs]
    )


def test_no_trade_strategy_never_claims_edge_and_keeps_matched_inventory() -> None:
    settings = LabSettings(lookback=40, entry=10, auto_tune=False)
    result = prove_lab_strategy(
        market_inputs(), settings, trial_count=1, identity_confirmed=True
    )
    assert result.call["status"] == "no_edge"
    assert result.proof["passes"] is False
    assert result.proof["corrected_p_value"] == 1.0
    assert result.proof["validation_trades"] == 0
    assert result.proof["final_oos_used"] is False
    assert result.strategy is not None
    assert result.strategy.terminal_value == result.benchmarks["hodl"].terminal_value
    assert result.strategy.ending_state == result.benchmarks["hodl"].ending_state
    assert len(result.folds) == settings.folds
    for fold in result.folds:
        assert fold["training_end"] <= fold["test_start"]
    assert all(
        first["end_index"] == second["start_index"]
        for first, second in zip(result.folds, result.folds[1:])
    )


def test_future_prices_cannot_change_control_or_first_fold_tuning() -> None:
    settings = LabSettings(lookback=40)
    first = prove_lab_strategy(
        market_inputs(), settings, trial_count=3, identity_confirmed=True
    )
    changed = prove_lab_strategy(
        market_inputs(changed_after=460),
        settings,
        trial_count=3,
        identity_confirmed=True,
    )
    assert first.proof["control"] == changed.proof["control"]
    assert first.folds[0] == changed.folds[0]
    assert first.strategy is not None and changed.strategy is not None
    np.testing.assert_array_equal(
        first.strategy.values[:40], changed.strategy.values[:40]
    )


@pytest.mark.parametrize(
    "identity,execution,status",
    [(False, True, "identity_unresolved"), (True, False, "execution_data_missing")],
)
def test_missing_authority_blocks_economic_calls(
    identity: bool, execution: bool, status: str
) -> None:
    result = prove_lab_strategy(
        market_inputs(),
        LabSettings(lookback=40, auto_tune=False),
        trial_count=1,
        identity_confirmed=identity,
        execution_ready=execution,
    )
    assert result.call["status"] == status
    assert result.call["target_weight_a"] is None


def test_bootstrap_floor_keeps_family_correction_effective() -> None:
    control = np.zeros(200)
    positive = np.full(200, 0.001)
    raw, corrected = corrected_spa(positive, control, 1000)
    assert raw == pytest.approx(1 / 500)
    assert corrected == 1.0
    assert corrected_spa(-positive, control, 1) == (1.0, 1.0)
    assert corrected_spa(positive[:10], control[:10], 1) == (1.0, 1.0)


def test_seeded_spa_is_repeatable_for_varying_advantage() -> None:
    control = np.random.default_rng(8).normal(0, 0.001, 200)
    strategy = control + np.random.default_rng(9).normal(0.0001, 0.001, 200)
    first = corrected_spa(strategy, control, 3)
    assert first == corrected_spa(strategy, control, 3)
    assert 0 < first[0] <= first[1] <= 1


@pytest.mark.parametrize("last_preference,status", [(0.0, "into_b"), (1.0, "hold")])
def test_current_call_matches_replay_transition_including_neutral_exit(
    monkeypatch: pytest.MonkeyPatch, last_preference: float, status: str
) -> None:
    def final_signal(
        a: Floats, b: Floats, settings: LabSettings, anchor: Floats | None = None
    ) -> LabSignal:
        signal = signal_path(a, b, settings, anchor)
        preference = signal.preference.copy()
        preference[-10:] = 1.0
        preference[-1] = last_preference
        return replace(signal, preference=preference)

    monkeypatch.setattr("qap.experiment.lab_proof.signal_path", final_signal)
    result = prove_lab_strategy(
        market_inputs(),
        LabSettings(
            lookback=40,
            entry=1,
            exit=0.2,
            minimum_hold=1,
            cooldown=1,
            minimum_passing_folds=1,
            minimum_trades=1,
            auto_tune=False,
            significance=0.1,
        ),
        trial_count=1,
        identity_confirmed=True,
    )
    assert result.proof["passes"] is True
    assert result.strategy is not None
    assert result.strategy.last_preference == 1.0
    assert result.call["status"] == status
    if last_preference == 0:
        assert Decimal(result.call["target_weight_a"]) == Decimal("0.5")


def test_partial_execution_metadata_blocks_every_trading_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = LabSettings(lookback=40, auto_tune=False)
    inputs = replace(market_inputs(), metadata=metadata_snapshots(legs=1))
    replayed: list[ReplayKind] = []
    perform_replay = run_lab_replay

    def recording_replay(
        inputs: LabInputs,
        settings: LabSettings,
        signal: LabSignal,
        *,
        kind: ReplayKind = "strategy",
        start: int = 0,
        end: int | None = None,
        preferences: Floats | None = None,
    ) -> LabReplay:
        replayed.append(kind)
        return perform_replay(
            inputs,
            settings,
            signal,
            kind=kind,
            start=start,
            end=end,
            preferences=preferences,
        )

    monkeypatch.setattr("qap.experiment.lab_proof.run_lab_replay", recording_replay)
    result = prove_lab_strategy(
        inputs,
        settings,
        trial_count=1,
        identity_confirmed=True,
        execution_ready=False,
    )
    assert replayed == ["hodl", "hold_a", "hold_b"]
    assert set(result.benchmarks) == {"hodl", "hold_a", "hold_b"}
    assert result.strategy is None
    assert result.folds == ()
    assert result.proof["control"] is None
    assert result.proof["passes"] is False
    assert result.proof["raw_p_value"] is None
    assert result.proof["corrected_p_value"] is None
    assert result.proof["validation_trades"] == 0
    assert result.call["status"] == "execution_data_missing"
    assert result.call["target_weight_a"] is None
    # The same partial inputs would fail strict canonical preflight if traded.
    with pytest.raises(MultiAssetPreflightError):
        perform_replay(inputs, settings, result.signal, kind="daily")


def test_full_direct_metadata_with_market_filter_reaches_the_proof() -> None:
    data = market_inputs()
    instrument = VenueInstrument(
        "binance", "AB", data.first.instrument.base, data.second.instrument.base
    )
    direct = validate_bar_series(
        tuple(
            replace(
                first,
                instrument=instrument,
                open=first.close / second.close,
                high=first.close / second.close,
                low=first.close / second.close,
                close=first.close / second.close,
            )
            for first, second in zip(data.first.bars, data.second.bars, strict=True)
        )
    )
    snapshot = public_market_metadata_snapshot_from_metadata(
        metadata=replace(
            metadata_snapshots()[0].metadata,
            instrument=instrument,
            minimum_notional=Decimal("5"),
            minimum_notional_applies_to_market=True,
        ),
        observed_at=data.first.bars[0].candle_open_time,
        source_id="offline-direct-metadata",
    )
    result = prove_lab_strategy(
        replace(data, direct=direct, metadata=(snapshot,)),
        LabSettings(lookback=40, entry=1, auto_tune=False),
        trial_count=1,
        identity_confirmed=True,
        execution_ready=True,
    )
    assert result.strategy is not None
    assert len(result.folds) == 8
    assert result.strategy.trades


def test_proof_reports_cost_paid_pct_and_gross_vs_hodl_pct() -> None:
    data = market_inputs()
    instrument = VenueInstrument(
        "binance", "AB", data.first.instrument.base, data.second.instrument.base
    )
    direct = validate_bar_series(
        tuple(
            replace(
                first,
                instrument=instrument,
                open=first.close / second.close,
                high=first.close / second.close,
                low=first.close / second.close,
                close=first.close / second.close,
            )
            for first, second in zip(data.first.bars, data.second.bars, strict=True)
        )
    )
    snapshot = public_market_metadata_snapshot_from_metadata(
        metadata=replace(
            metadata_snapshots()[0].metadata,
            instrument=instrument,
            minimum_notional=Decimal("5"),
            minimum_notional_applies_to_market=True,
        ),
        observed_at=data.first.bars[0].candle_open_time,
        source_id="offline-direct-metadata",
    )
    result = prove_lab_strategy(
        replace(data, direct=direct, metadata=(snapshot,)),
        LabSettings(lookback=40, entry=1, auto_tune=False),
        trial_count=1,
        identity_confirmed=True,
        execution_ready=True,
    )
    assert result.strategy is not None
    assert result.proof["cost_paid_pct"] is not None
    assert result.proof["cost_paid_pct"] >= 0
    if result.proof["vs_hodl_pct"] is not None:
        assert result.proof["gross_vs_hodl_pct"] >= result.proof["vs_hodl_pct"]
    assert result.strategy is not None
    assert all(
        len(trade.fills) == 1 and trade.fills[0].venue_symbol == "AB"
        for trade in result.strategy.trades
    )


def test_cost_budget_gate_rejects_high_fee_tuning() -> None:
    result = prove_lab_strategy(
        market_inputs(),
        LabSettings(lookback=40, entry=1, auto_tune=False, fee_bps=Decimal("100")),
        trial_count=1,
        identity_confirmed=True,
        execution_ready=True,
    )
    assert result.proof["cost_gate_passed"] is False
    assert result.proof["passes"] is False
    assert result.call["status"] == "cost_budget_failed"


def test_auto_tune_copula_clamps_candidates_within_exit_band() -> None:
    settings = LabSettings(
        method="copula",
        lookback=80,
        copula_probability=0.32,
        copula_exit_band=0.15,
        auto_tune=True,
    )
    candidates = settings_candidates(settings)
    assert len(candidates) >= 2
    assert all(
        candidate.copula_probability < 0.5 - candidate.copula_exit_band
        for candidate in candidates
    )

    base = market_inputs()
    rng = np.random.default_rng(123)
    b_prices = 100.0 * np.exp(np.cumsum(rng.normal(0.0, 0.01, len(base.second.bars))))
    b_series = validate_bar_series(
        tuple(
            replace(
                bar,
                open=float(price),
                high=float(price),
                low=float(price),
                close=float(price),
            )
            for bar, price in zip(base.second.bars, b_prices, strict=True)
        )
    )
    result = prove_lab_strategy(
        replace(base, second=b_series),
        settings,
        trial_count=1,
        identity_confirmed=True,
        execution_ready=True,
    )
    assert result.applied_settings.copula_probability < 0.35
    assert result.signal.available is True
