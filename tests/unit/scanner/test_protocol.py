from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from qap.market import BarInterval
from qap.scanner.protocol import (
    SCANNER_V1_SLICE1,
    ScannerHorizon,
    TemplateId,
    protocol_identity,
)


def test_scanner_v1_slice1_protocol_freezes_search_and_replay_references() -> None:
    protocol = SCANNER_V1_SLICE1

    assert protocol.protocol_id == "scanner-v1-s1"
    assert protocol.automatic_history == timedelta(days=365)
    assert protocol.maximum_discovery_history == timedelta(days=730)
    assert protocol.venues == ("binance", "gate")
    assert protocol.quote_asset == "USDT"
    assert protocol.neighbors_per_asset == 8
    assert protocol.automatic_replay_cap_per_horizon == 10
    assert protocol.max_promotions_per_asset_per_horizon == 2
    assert protocol.max_promotions_per_pair_family_per_horizon == 1
    assert protocol.minimum_asset_coverage == 0.95
    assert protocol.minimum_pair_coverage == 0.95
    assert protocol.maximum_missing_generator_bars == 2

    assert protocol.cost_policy.policy_id == "scanner-v1-historical-costs-v1"
    assert protocol.cost_policy.fee_bps == Decimal("10")
    assert protocol.cost_policy.slippage_bps == Decimal("5")
    assert protocol.cost_policy.adverse_fee_bps == Decimal("20")
    assert protocol.cost_policy.adverse_slippage_bps == Decimal("10")

    assert protocol.primary_control.control_id == "band-5pct-half"
    assert protocol.primary_control.policy_id == "scanner-v1-band-control-v1"
    assert protocol.primary_control.band_width == Decimal("0.05")
    assert protocol.primary_control.partial_correction_fraction == Decimal("0.5")

    assert protocol.normalization.policy_id == "scanner-v1-unit-value-normalization-v1"
    assert protocol.normalization.total_direct_quote_value == Decimal("1")
    assert protocol.normalization.minimum_rebalance_notional == Decimal("0")
    assert protocol.normalization.base_step is None


def test_horizon_and_template_mappings_are_frozen_and_deterministic() -> None:
    short = SCANNER_V1_SLICE1.horizon(ScannerHorizon.SHORT)
    medium = SCANNER_V1_SLICE1.horizon(ScannerHorizon.MEDIUM)
    swing = SCANNER_V1_SLICE1.horizon(ScannerHorizon.SWING)

    assert (short.graph_interval, short.graph_window) == (
        BarInterval("1h"),
        timedelta(days=30),
    )
    assert short.model_resolutions == (BarInterval("15m"), BarInterval("1h"))
    assert short.evaluation_window == timedelta(days=30)
    assert short.template_window(TemplateId.FAST) == timedelta(days=2)
    assert short.template_window(TemplateId.BASE) == timedelta(days=7)
    assert short.template_window(TemplateId.SLOW) == timedelta(days=14)

    assert (medium.graph_interval, medium.graph_window) == (
        BarInterval("4h"),
        timedelta(days=90),
    )
    assert medium.model_resolutions == (BarInterval("1h"), BarInterval("4h"))
    assert medium.template_window(TemplateId.SLOW) == timedelta(days=60)

    assert (swing.graph_interval, swing.graph_window) == (
        BarInterval("1d"),
        timedelta(days=180),
    )
    assert swing.model_resolutions == (BarInterval("4h"), BarInterval("1d"))
    assert swing.template_window(TemplateId.SLOW) == timedelta(days=180)

    assert short.window_bars(TemplateId.BASE, BarInterval("1h")) == 7 * 24
    assert medium.window_bars(TemplateId.FAST, BarInterval("4h")) == 14 * 6
    assert swing.window_bars(TemplateId.SLOW, BarInterval("1d")) == 180


def test_protocol_identity_changes_when_search_or_replay_policy_changes() -> None:
    baseline = protocol_identity(SCANNER_V1_SLICE1)
    changed_neighbors = protocol_identity(
        replace(SCANNER_V1_SLICE1, neighbors_per_asset=7)
    )
    changed_costs = protocol_identity(
        replace(
            SCANNER_V1_SLICE1,
            cost_policy=replace(SCANNER_V1_SLICE1.cost_policy, fee_bps=Decimal("11")),
        )
    )

    assert len(baseline) == 64
    assert baseline != changed_neighbors
    assert baseline != changed_costs
