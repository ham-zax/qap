"""Offline, fixed-basket Phase 19 parity report; fails closed on disagreement."""

import argparse
import hashlib
import json
import sys
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path

if str(Path(__file__).resolve().parents[1]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from qap.market import fingerprint_bar_series, read_parquet_bar_series
from scripts.engine_parity_support.bt_reference import run_reference
from scripts.engine_parity_support.contracts import STRATEGIES, PairInputs, Settings
from scripts.engine_parity_support.hand_cases import (
    verify_bt_arithmetic,
    verify_hand_cases,
)
from scripts.engine_parity_support.qap_replay import run_qap


def report(fixtures: Path, *, max_bars: int | None = None) -> dict[str, object]:
    manifest = json.loads((fixtures / "manifest.json").read_text(encoding="utf-8"))
    settings = Settings()
    outcomes: list[dict[str, object]] = []
    all_series = {
        asset: read_parquet_bar_series(fixtures / f"{asset}USDT.parquet")
        for asset in ("BTC", "ETH", "SOL")
    }
    for source in manifest["sources"]:
        series = all_series[source["base_asset"]]
        if fingerprint_bar_series(series) != source["semantic_fingerprint"]:
            raise ValueError("Recorded source fingerprint mismatch")
        path = fixtures / f"{source['venue_symbol']}.parquet"
        if hashlib.sha256(path.read_bytes()).hexdigest() != source["parquet_sha256"]:
            raise ValueError("Recorded artifact hash mismatch")
    for first, second in (("BTC", "ETH"), ("BTC", "SOL"), ("ETH", "SOL")):
        series = (all_series[first], all_series[second])
        bars = tuple(item.bars[:max_bars] for item in series)
        dates = tuple(bar.candle_open_time for bar in bars[0])
        if dates != tuple(bar.candle_open_time for bar in bars[1]):
            raise ValueError("Pair inputs must align exactly")
        inputs = PairInputs(
            (first, second),
            dates,
            tuple((a.open, b.open) for a, b in zip(*bars, strict=True)),
            tuple((a.close, b.close) for a, b in zip(*bars, strict=True)),
        )
        for strategy in STRATEGIES:
            qap = run_qap(inputs, series, strategy, settings)
            reference = run_reference(inputs, strategy, settings)
            relative_error = abs(qap.terminal_value / reference.terminal_value - 1)
            balance_error = max(
                *(
                    abs(q - r) * price
                    for q, r, price in zip(
                        qap.holdings,
                        reference.holdings,
                        inputs.closes[-1],
                        strict=True,
                    )
                ),
                abs(qap.settlement - reference.settlement),
            )
            passed = (
                relative_error <= 0.0001
                and qap.legs == reference.legs
                and balance_error <= settings.starting_value * 1e-8
            )
            row: dict[str, object] = {
                "pair": f"{first}/{second}",
                "strategy": strategy,
                "bars": len(dates),
                "qap": asdict(qap),
                "bt": asdict(reference),
                "relative_terminal_error": relative_error,
                "maximum_inventory_value_error": balance_error,
                "passed": passed,
            }
            outcomes.append(row)
            print(
                f"{first}/{second} {strategy}: error={relative_error:.12g}, "
                f"legs={qap.legs}/{reference.legs}, passed={passed}",
                flush=True,
            )
    hands = verify_hand_cases()
    verify_bt_arithmetic()
    return {
        "schema_version": "qap.engine-parity.report.v1",
        "bt_version": version("bt"),
        "settings": asdict(settings),
        "window": {
            "start": manifest["start"],
            "end_exclusive": manifest["end_exclusive"],
        },
        "full_recorded_window": max_bars is None,
        "input_manifest_sha256": hashlib.sha256(
            (fixtures / "manifest.json").read_bytes()
        ).hexdigest(),
        "results": outcomes,
        "hand_cases": hands,
        "passed": all(row["passed"] for row in outcomes)
        and all(row["passed"] for row in hands),
        "scope": [
            "Fixed-basket accounting verification; no edge/discovery evidence",
            "Real-data runs: USDT settlement; direct conversion checked by hand",
            "Historical unconstrained metadata; 10bp fees, 5bp slippage per leg",
            "QAP replay: bounded two-bar windows, continuous authoritative ledger",
            "bt owns holdings, cash, commissions and trades from raw input prices",
            "Hand inventory: exact Decimal; bt arithmetic tolerance: 1e-10",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures", type=Path, default=Path("tests/fixtures/engine_parity")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/qap-engine-parity.json")
    )
    parser.add_argument(
        "--max-bars", type=int, help="Smoke check only; never full M1 acceptance"
    )
    args = parser.parse_args()
    result = report(args.fixtures, max_bars=args.max_bars)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not result["passed"]:
        raise SystemExit("Engine parity failed; see report before continuing")


if __name__ == "__main__":
    main()
