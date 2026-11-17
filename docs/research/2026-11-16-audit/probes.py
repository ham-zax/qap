"""Reproduce audit findings offline without changing strategy or saved runs.

Run from the repository root:
    uv run python docs/research/2026-11-16-audit/probes.py

Fixtures come from the existing test suite. Temporary sessions are discarded.
These probes describe current behavior. They are not acceptance tests.
"""

import hashlib
import json
import runpy
import subprocess
import tempfile
from decimal import Decimal
from pathlib import Path

import numpy as np

from qap.execution.fills import FillSide
from qap.execution.l2_book_fill import sweep_l2_taker_order
from qap.experiment.live_paper_state import append_mid_closes
from qap.market import MarketMetadata
from qap.relationship.lab_copula import rolling_spread_copula
from qap.relationship.pair_measurements import cointegration


def main() -> None:
    paper = runpy.run_path("tests/unit/experiment/test_live_paper_runner.py")
    book_fixture = runpy.run_path("tests/unit/execution/test_l2_book_fill.py")
    ms = paper["MS"]
    received = paper["RECV_NS"]
    report = {
        "head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "scope": "offline diagnostic fixtures, not investment performance",
    }
    source_paths = [
        "src/qap/experiment/lab_proof.py",
        "src/qap/experiment/lab_replay.py",
        "src/qap/experiment/live_paper_runner.py",
        "src/qap/experiment/live_paper_state.py",
        "src/qap/experiment/live_paper_execution.py",
        "src/qap/execution/l2_book_fill.py",
        "src/qap/relationship/lab_copula.py",
        "src/qap/policy/lab_signals.py",
        "src/qap/policy/lab_strategy_registry.py",
    ]
    report["source_sha256"] = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for name in source_paths
        if (path := Path(name)).exists()
    }

    book = book_fixture["make_book"]()
    common = {
        "fill_id": "audit-fill",
        "decision_id": "audit-decision",
        "execution_timestamp": book_fixture["AT"],
        "side": FillSide.SELL,
        "book": book,
        "book_received_ns": 850 * ms,
        "target_fill_ns": 75 * ms,
        "fee_bps": Decimal("10"),
        "base_quantity": Decimal("1"),
    }
    future = sweep_l2_taker_order(**common)
    report["late_book"] = {
        "target_fill_ms": 75,
        "book_receipt_ms": 850,
        "reported_book_age_ms": future.book_age_ms,
        "filled": future.fill is not None,
    }

    tiny = {
        **common,
        "book_received_ns": 0,
        "target_fill_ns": ms,
        "base_quantity": Decimal("0.0000001"),
    }
    unchecked = sweep_l2_taker_order(**tiny)
    metadata = MarketMetadata(
        instrument=book.instrument,
        status="TRADING",
        price_tick=Decimal("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=Decimal("0.001"),
        minimum_quantity=Decimal("0.001"),
        maximum_quantity=None,
        minimum_notional=Decimal("5"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=0,
    )
    checked = sweep_l2_taker_order(**tiny, market_metadata=metadata)
    report["optional_metadata"] = {
        "without_metadata_filled": unchecked.fill is not None,
        "with_metadata_filled": checked.fill is not None,
        "with_metadata_rejection": checked.rejected_reason,
    }

    history = {"BTCUSDT": [100.0], "ETHUSDT": [50.0]}
    mids = {paper["BTC"].base: Decimal("100"), paper["ETH"].base: Decimal("50")}
    for _ in range(3):
        append_mid_closes(history, [paper["BTC"], paper["ETH"]], mids, None)
    report["step_cadence"] = {
        "initial_observations": 1,
        "calls_without_candle_timestamps": 3,
        "final_observations": len(history["BTCUSDT"]),
    }

    with tempfile.TemporaryDirectory(prefix="qap-audit-") as directory:
        manager = paper["make_manager"](Path(directory))
        paper["start"](manager)
        first = manager.step_session(
            "sess1",
            books=paper["books"](130.0, 50.0, received_ns=received),
            decide_ns=received + 2 * ms,
            fill_books_leg1=paper["books"](130.0, 50.0, received_ns=received + 70 * ms),
            fill_books_leg2=paper["books"](
                128.0, 50.5, received_ns=received - 1000 * ms
            ),
        )
        second = manager.step_session(
            "sess1",
            books=paper["books"](130.0, 50.0, received_ns=received),
            decide_ns=received + 2 * ms,
            fill_books_leg1=paper["books"](130.0, 50.0, received_ns=received + 70 * ms),
            fill_books_leg2=paper["books"](
                128.0, 50.5, received_ns=received + 145 * ms
            ),
        )
        report["partial_rotation"] = {
            "first_rejections": first["latency_audit"][-1]["rejected_reasons"],
            "first_fills": len(first["trades"][0]["fills"]),
            "first_strategy_holdings": first["portfolios"]["strategy"]["holdings"],
            "second_strategy_holdings": second["portfolios"]["strategy"]["holdings"],
            "second_action": second["latency_audit"][-1]["action"],
            "second_signal_preference": second["latency_audit"][-1][
                "signal_preference"
            ],
            "strategy_trade_count_before": len(first["trades"]),
            "strategy_trade_count_after": len(second["trades"]),
        }

    rng = np.random.default_rng(20261116)
    logs = np.cumsum(rng.normal(0, 0.01, (3, 600)), axis=1)
    prices = np.exp(logs)
    probabilities = rolling_spread_copula(
        prices[0], prices[1], window=96, anchor=prices[2]
    )
    anchor_tests = [cointegration(logs[i], logs[2]) for i in (0, 1)]
    report["independent_walks"] = {
        "seed": 20261116,
        "anchor_cointegration_p_values": [
            None if result is None else result.p_value for result in anchor_tests
        ],
        "finite_copula_outputs": (
            0 if probabilities is None else int(np.isfinite(probabilities).sum())
        ),
    }

    rows = [
        json.loads(line)
        for line in Path("docs/research/2026-11-15-stage-s4-trials.jsonl")
        .read_text()
        .splitlines()
    ]
    counts = sorted({row["study"]["proof"]["settings_tried"] for row in rows})
    report["bootstrap_resolution"] = {
        "replicates": 499,
        "raw_p_floor": 1 / 500,
        "family_size": len(rows),
        "holm_first_threshold": 0.05 / len(rows),
        "recorded_trial_counts": counts,
        "smallest_possible_corrected_p": min(counts) / 500,
        "any_s4_row_can_start_holm_stepdown": min(counts) / 500 <= 0.05 / len(rows),
    }
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
