"""Tests for the token-efficient AI-Agent CLI (qap.lab_cli)."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import exp, sin
from pathlib import Path

import pytest

from qap.lab_cli import main
from qap.market import BarInterval, MarketBar, validate_bar_series
from qap.market.metadata import MarketMetadata
from qap.market.microstructure import public_market_metadata_snapshot_from_metadata
from qap.market.microstructure_storage import append_public_market_metadata_snapshot
from qap.product_lab_metadata import (
    _path as lab_metadata_path,  # pyright: ignore[reportPrivateUsage]
)
from qap.product_market_data import ProductMarketData
from qap.product_market_data_models import (
    MarketDataGenerationInput,
    MarketDataUpstreamSource,
)
from qap.product_market_data_prepare import product_dataset_id
from qap.product_universe import (
    DirectoryMarket,
    DirectorySource,
    ProductMarketDirectory,
    ProductUniverse,
)


def _publish_directory(owner: ProductUniverse) -> None:
    observed = datetime(2026, 10, 2, 14, 7, tzinfo=UTC)
    directory = ProductMarketDirectory(
        sources=(
            DirectorySource(
                venue="binance",
                observed_at=observed,
                source_id="offline-exchangeInfo",
                source_fingerprint="1" * 64,
            ),
        ),
        markets=tuple(
            DirectoryMarket(
                venue="binance",
                venue_symbol=f"{code}USDT",
                venue_base_asset=code,
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
                base_name=name,
                permissions=(),
            )
            for code, name in (("W", "Wormhole"), ("BTC", "Bitcoin"))
        ),
    )
    owner.root.mkdir(parents=True, exist_ok=True)
    owner.directory_path.write_text(directory.model_dump_json())


def _seed_offline_pair(root: Path) -> tuple[Path, Path]:
    run_root = root / "runs"
    data_root = root / "data"
    uni = ProductUniverse(run_root)
    _publish_directory(uni)
    scope = uni.research_scope(("binance:W", "binance:BTC"))
    data = ProductMarketData(run_root, data_root)
    interval = BarInterval("1h")
    observed_at = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
    end = observed_at.replace(minute=0, second=0, microsecond=0)
    for leg, instrument in enumerate(scope.instruments):
        bars: list[MarketBar] = []
        for index in range(720):
            movement = (
                0.04 * sin(index * 0.3) if leg == 0 else 0.003 * sin(index * 0.17)
            )
            price = exp(index * 0.0001 + movement)
            bars.append(
                MarketBar(
                    instrument=instrument.instrument,
                    interval=interval,
                    candle_open_time=end - timedelta(hours=720 - index),
                    open=price,
                    high=price,
                    low=price,
                    close=price,
                    volume=1_000_000.0,
                )
            )
        data.publish_generation(
            scope,
            MarketDataGenerationInput(
                dataset_id=product_dataset_id(instrument, interval),
                resolved_instrument=instrument,
                series=validate_bar_series(tuple(bars)),
                acquisition_implementation="offline-lab-cli-test",
                upstream_sources=(
                    MarketDataUpstreamSource(
                        provider="binance",
                        source_family="offline-contract",
                        source_id=instrument.instrument.venue_symbol,
                        retrieved_at=observed_at,
                        source_fingerprint="1" * 64,
                    ),
                ),
            ),
        )
        append_public_market_metadata_snapshot(
            lab_metadata_path(data_root, instrument.instrument),
            public_market_metadata_snapshot_from_metadata(
                metadata=MarketMetadata(
                    instrument=instrument.instrument,
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
                observed_at=observed_at,
                source_id=f"binance-exchangeInfo:{instrument.instrument.venue_symbol}",
            ),
        )
    return run_root, data_root


def test_lab_cli_analyze_study_compare_and_saved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_root, data_root = _seed_offline_pair(tmp_path)
    base_flags = [
        "--run-root",
        str(run_root),
        "--data-root",
        str(data_root),
        "--actor-id",
        "agent_1",
    ]

    assert (
        main(
            [
                "analyze",
                *base_flags,
                "--coin-a",
                "binance:W",
                "--coin-b",
                "binance:BTC",
                "--bar",
                "1h",
                "--days",
                "30",
                "--band-lookback",
                "20",
            ]
        )
        == 0
    )
    ana = json.loads(capsys.readouterr().out)
    assert "series" not in ana
    assert "advisor" in ana
    assert len(ana["advisor"]["suggestions"]) == 3

    assert (
        main(
            [
                "study",
                *base_flags,
                "--coin-a",
                "binance:W",
                "--coin-b",
                "binance:BTC",
                "--bar",
                "1h",
                "--days",
                "30",
                "--band-lookback",
                "20",
                "--settings",
                '{"lookback":40,"auto_tune":false}',
            ]
        )
        == 0
    )
    st = json.loads(capsys.readouterr().out)
    assert len(st["study_id"]) == 64
    assert "proof" in st and "call" in st and "trade_count" in st

    assert (
        main(
            [
                "compare",
                *base_flags,
                "--coin-a",
                "binance:W",
                "--coin-b",
                "binance:BTC",
                "--bar",
                "1h",
                "--days",
                "30",
                "--band-lookback",
                "20",
                "--format",
                "md",
            ]
        )
        == 0
    )
    md_out = capsys.readouterr().out
    assert "## Compare" in md_out

    assert main(["saved", *base_flags, "--limit", "10"]) == 0
    saved = json.loads(capsys.readouterr().out)
    assert len(saved["studies"]) == 4

    assert (
        main(
            [
                "saved",
                "--run-root",
                str(run_root),
                "--data-root",
                str(data_root),
                "--actor-id",
                "other",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["studies"] == []
