"""Accounting oracles and causal replay checks for the independent M1 harness."""

import ast
import gzip
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from qap.market import BarInterval, MarketBar, VenueInstrument, validate_bar_series
from qap.portfolio import AssetId
from scripts.engine_parity_support import bt_reference
from scripts.engine_parity_support.contracts import PairInputs, Settings
from scripts.engine_parity_support.hand_cases import (
    verify_bt_arithmetic,
    verify_hand_cases,
)
from scripts.engine_parity_support.qap_replay import run_qap

START = datetime(2026, 1, 1, tzinfo=UTC)
INTERVAL = BarInterval("15m")


def fixture_inputs(
    opens: tuple[tuple[float, float], ...],
    closes: tuple[tuple[float, float], ...],
):
    dates = tuple(START + i * INTERVAL.duration for i in range(len(opens)))
    inputs = PairInputs(("AAA", "BBB"), dates, opens, closes)
    instruments = tuple(
        VenueInstrument(
            venue="fixture",
            venue_symbol=f"{asset}USDT",
            base=AssetId(asset),
            quote=AssetId("USDT"),
        )
        for asset in inputs.assets
    )
    series = tuple(
        validate_bar_series(
            tuple(
                MarketBar(
                    instrument=instrument,
                    interval=INTERVAL,
                    candle_open_time=date,
                    open=float(op[i]),
                    close=float(cl[i]),
                    high=float(max(op[i], cl[i])),
                    low=float(min(op[i], cl[i])),
                    volume=100.0,
                )
                for date, op, cl in zip(dates, opens, closes, strict=True)
            )
        )
        for i, instrument in enumerate(instruments)
    )
    return inputs, (series[0], series[1])


def test_five_hand_computed_inventory_oracles_and_bt_arithmetic() -> None:
    cases = verify_hand_cases()
    assert len(cases) == 5
    assert all(case["passed"] for case in cases), cases
    verify_bt_arithmetic()


@pytest.mark.parametrize("strategy", ["periodic", "threshold"])
def test_orders_use_closed_decision_quantities_and_next_open_prices(
    strategy: str,
) -> None:
    from typing import cast

    from scripts.engine_parity_support.contracts import Strategy

    inputs, series = fixture_inputs(
        ((10, 2), (20, 2), (30, 2)),
        ((10, 2), (20, 2), (30, 2)),
    )
    settings = Settings(starting_value=100, fee_rate=0, slippage_rate=0, period_bars=1)
    qap = run_qap(inputs, series, cast(Strategy, strategy), settings)
    reference = bt_reference.run_reference(inputs, cast(Strategy, strategy), settings)
    # At the second close, sell 1.25 A at the NEXT open of 30.
    # Desired B budget was25; spend25 at2, preserving12.5 settlement cash.
    assert qap.terminal_value == 200
    assert qap.holdings == (3.75, 37.5)
    assert qap.settlement == 12.5
    assert qap.legs == 2
    assert reference == qap


def test_last_bar_target_cannot_execute() -> None:
    inputs, series = fixture_inputs(((10, 2), (200, 2)), ((10, 2), (200, 2)))
    settings = Settings(starting_value=100, fee_rate=0, slippage_rate=0, period_bars=1)
    qap = run_qap(inputs, series, "threshold", settings)
    reference = bt_reference.run_reference(inputs, "threshold", settings)
    assert qap.holdings == (5, 25)
    assert qap.legs == reference.legs == 0
    assert qap.terminal_value == reference.terminal_value == 1050


def test_both_legs_pay_fees_and_adverse_slippage() -> None:
    inputs, series = fixture_inputs(
        ((10, 2), (20, 2), (30, 2)), ((10, 2), (20, 2), (30, 2))
    )
    settings = Settings(starting_value=100, period_bars=1)
    qap = run_qap(inputs, series, "periodic", settings)
    reference = bt_reference.run_reference(inputs, "periodic", settings)
    sell_proceeds = 1.25 * 30 * 0.9995 * 0.999
    buy_quantity = 25 / (2 * 1.0005 * 1.001)
    expected = 3.75 * 30 + (25 + buy_quantity) * 2 + sell_proceeds - 25
    assert qap.legs == reference.legs == 2
    assert qap.terminal_value == pytest.approx(expected, abs=1e-10)
    assert reference.terminal_value == pytest.approx(expected, abs=1e-10)
    assert 0 < qap.terminal_value < 200
    assert qap.settlement >= 0


def test_reference_has_no_qap_accounting_imports() -> None:
    tree = ast.parse(Path(bt_reference.__file__).read_text(encoding="utf-8"))
    imports = [
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    ]
    assert not any(module == "qap" or module.startswith("qap.") for module in imports)
    direct = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert not any(module == "qap" or module.startswith("qap.") for module in direct)


def test_recorded_source_bytes_match_provenance_and_cover_six_months() -> None:
    root = Path(__file__).resolve().parents[1] / "fixtures" / "engine_parity"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["start"] == "2026-04-01T00:00:00+00:00"
    assert manifest["end_exclusive"] == "2026-10-01T00:00:00+00:00"
    assert {row["base_asset"] for row in manifest["sources"]} == {"BTC", "ETH", "SOL"}
    for source in manifest["sources"]:
        assert source["bars"] == 17568
        raw = root / f"{source['venue_symbol']}.jsonl.gz"
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == source["raw_sha256"]
        with gzip.open(raw, "rt", encoding="utf-8") as handle:
            records = [json.loads(line) for line in handle]
        assert len(records) == len(source["requests"]) == 18
        for record, request in zip(records, source["requests"], strict=True):
            assert record["url"] == request["url"]
            assert (
                hashlib.sha256(record["body"].encode()).hexdigest()
                == request["payload_sha256"]
            )
            assert "interval=15m" in record["url"]
