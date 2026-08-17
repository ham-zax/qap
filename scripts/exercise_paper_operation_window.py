"""Exercise larger-window paper artifacts and filesystem readers on recorded data."""

from __future__ import annotations

import argparse
import json
import resource
import time
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, cast

from qap.api.paper_operation_views import PaperOperationReader
from qap.api.readers import RunArtifactReader
from qap.experiment import (
    ExperimentManifest,
    load_manifest,
    run_experiment_to_artifacts,
)
from qap.experiment.paper_operation import (
    read_paper_operation_artifact,
    run_paper_operation_to_artifact,
)
from qap.market import fingerprint_bar_series, read_parquet_bar_series

_ROOT = Path(__file__).resolve().parents[1]
_EXCHANGE_INFO = (
    "tests/fixtures/binance/exchange_info_three_asset_snapshot_2026-08-17.json"
)
_SERIES_PATHS = {
    "BTCUSDT": Path("tests/fixtures/market/BTCUSDT_1d_2023.parquet"),
    "ETHUSDT": Path("tests/fixtures/market/ETHUSDT_1d_2023.parquet"),
    "SOLUSDT": Path("tests/fixtures/market/SOLUSDT_1d_2023.parquet"),
}
_TARGETS = (
    {"BTC": "0.4", "ETH": "0.2", "SOL": "0.1", "USDT": "0.3"},
    {"BTC": "0.2", "ETH": "0.3", "SOL": "0.2", "USDT": "0.3"},
)
_STARTING_HOLDINGS = {
    "BTC": "0.01",
    "ETH": "0.1",
    "SOL": "1",
    "USDT": "1000",
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-days", type=int, default=365)
    parser.add_argument("--experiment-runs", type=int, default=25)
    return parser


def _validated_count(value: int, *, field: str, maximum: int) -> int:
    if isinstance(value, bool) or value <= 0 or value > maximum:
        raise ValueError(f"{field} must be in [1, {maximum}]")
    return value


def _paper_window(output_root: Path, *, days: int) -> dict[str, object]:
    series = {
        symbol: read_parquet_bar_series(_ROOT / relative_path)
        for symbol, relative_path in _SERIES_PATHS.items()
    }
    timestamps = tuple(bar.candle_open_time for bar in series["BTCUSDT"].bars[:days])
    for symbol, item in series.items():
        candidate = tuple(bar.candle_open_time for bar in item.bars[:days])
        if candidate != timestamps:
            raise RuntimeError(f"{symbol} timestamps do not align with BTCUSDT")

    fingerprints = {
        symbol: fingerprint_bar_series(item) for symbol, item in series.items()
    }
    holdings = dict(_STARTING_HOLDINGS)
    spec_path = output_root.parent / "paper-operation-spec.json"
    fill_count = 0
    no_fill_order_count = 0
    artifact_bytes = 0
    largest_artifact_bytes = 0
    started = time.perf_counter()

    for index in range(days):
        closes = {
            symbol: str(item.bars[index].close) for symbol, item in series.items()
        }
        timestamp = series["BTCUSDT"].bars[index].bar_end_exclusive
        target = _TARGETS[(index // 30) % len(_TARGETS)]
        spec = {
            "schema_version": "qap.paper_operation_spec.v1",
            "operation_id": f"window-2023-{index + 1:03d}",
            "data_role": "forward_paper",
            "execution_timestamp": timestamp.isoformat(),
            "exchange_info_fixture": _EXCHANGE_INFO,
            "source_note": (
                "Phase-11 larger-window operational stress exercise on recorded 2023 "
                "daily bars; not research or prospective candidate evidence."
            ),
            "bridge": "USDT",
            "starting_holdings": holdings,
            "target_weights": target,
            "valuation_prices": {
                "BTC": closes["BTCUSDT"],
                "ETH": closes["ETHUSDT"],
                "SOL": closes["SOLUSDT"],
                "USDT": "1",
            },
            "instruments": [
                {
                    "venue_symbol": symbol,
                    "base": symbol.removesuffix("USDT"),
                    "quote": "USDT",
                    "venue_base_asset": symbol.removesuffix("USDT"),
                    "venue_quote_asset": "USDT",
                    "reference_price": closes[symbol],
                    "notional_reference_price": closes[symbol],
                }
                for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT")
            ],
            "fee_bps": "10",
            "slippage_bps": "10",
        }
        spec_path.write_text(
            json.dumps(spec, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        artifact = run_paper_operation_to_artifact(
            spec_path,
            repository_root=_ROOT,
            output_root=output_root,
        )
        record = read_paper_operation_artifact(artifact.operation_file)
        if record["reconciliation"]["matches"] is not True:
            raise RuntimeError(f"{artifact.operation_id} did not reconcile")
        holdings = cast(dict[str, str], record["ending_holdings"])
        fills = cast(list[dict[str, Any]], record["fills"])
        orders = cast(list[dict[str, Any]], record["orders"])
        fill_count += len(fills)
        no_fill_order_count += sum(order["leg_reason"] is not None for order in orders)
        size = artifact.operation_file.stat().st_size
        artifact_bytes += size
        largest_artifact_bytes = max(largest_artifact_bytes, size)

    execution_seconds = time.perf_counter() - started
    list_started = time.perf_counter()
    summaries = PaperOperationReader(output_root).list()
    list_seconds = time.perf_counter() - list_started
    if len(summaries) != days:
        raise RuntimeError("paper-operation list did not return the full window")

    return {
        "days": days,
        "market_series": len(series),
        "market_rows": days * len(series),
        "semantic_fingerprints": fingerprints,
        "fill_count": fill_count,
        "no_fill_order_count": no_fill_order_count,
        "execution_seconds": execution_seconds,
        "artifact_bytes": artifact_bytes,
        "average_artifact_bytes": artifact_bytes / days,
        "largest_artifact_bytes": largest_artifact_bytes,
        "list_seconds": list_seconds,
        "ending_holdings": holdings,
    }


def _experiment_scan(run_root: Path, *, run_count: int) -> dict[str, object]:
    base = load_manifest(_ROOT / "tests/fixtures/experiments/two_asset_dummy.json")
    raw_base = base.model_dump(mode="json")
    started = time.perf_counter()
    for index in range(run_count):
        raw = dict(raw_base)
        raw["experiment_name"] = f"Phase-11 filesystem scan {index + 1:03d}"
        raw["research_family_id"] = "phase11-filesystem-scan"
        manifest = ExperimentManifest.model_validate(raw)
        run_experiment_to_artifacts(
            manifest,
            data_root=_ROOT,
            repository_root=_ROOT,
            run_root=run_root,
            run_timestamp=datetime(2026, 8, 17, 13, 0, index, tzinfo=UTC),
        )
    generation_seconds = time.perf_counter() - started

    list_started = time.perf_counter()
    listing = RunArtifactReader(run_root, market_data_root=_ROOT).list_experiments()
    list_seconds = time.perf_counter() - list_started
    if len(listing.items) != run_count:
        raise RuntimeError("experiment list did not return every temporary run")
    return {
        "run_count": run_count,
        "generation_seconds": generation_seconds,
        "list_seconds": list_seconds,
    }


def main() -> int:
    arguments = _parser().parse_args()
    paper_days = _validated_count(
        arguments.paper_days,
        field="paper_days",
        maximum=365,
    )
    experiment_runs = _validated_count(
        arguments.experiment_runs,
        field="experiment_runs",
        maximum=59,
    )

    with TemporaryDirectory(prefix="qap-phase11-window-") as temporary:
        root = Path(temporary)
        paper = _paper_window(root / "paper-operations", days=paper_days)
        experiments = _experiment_scan(
            root / "experiment-runs",
            run_count=experiment_runs,
        )
        maximum_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    print(
        json.dumps(
            {
                "schema_version": "qap.phase11.window_exercise.v1",
                "paper": paper,
                "experiments": experiments,
                "maximum_rss_kib": maximum_rss_kib,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
