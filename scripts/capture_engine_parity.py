"""Explicit, read-only public capture for the frozen Phase 19 parity inputs."""

import argparse
import gzip
import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

from qap.market import (
    BarInterval,
    MarketBar,
    VenueInstrument,
    validate_bar_series,
    write_parquet_bar_series,
)
from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.portfolio import AssetId

START = datetime(2026, 4, 1, tzinfo=UTC)
END = datetime(2026, 10, 1, tzinfo=UTC)
INTERVAL = BarInterval("15m")
ASSETS = ("BTC", "ETH", "SOL")


def capture(destination: Path) -> None:
    """Freeze full source responses and semantic fingerprints; never touch a catalog."""

    destination.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(UTC)
    records: list[dict[str, object]] = []
    for asset in ASSETS:
        symbol = f"{asset}USDT"
        parquet_path = destination / f"{symbol}.parquet"
        raw_path = destination / f"{symbol}.jsonl.gz"
        if parquet_path.exists() or raw_path.exists():
            raise FileExistsError(f"Refusing to replace recorded input for {symbol}")
        instrument = VenueInstrument(
            venue="binance",
            venue_symbol=symbol,
            base=AssetId(asset),
            quote=AssetId("USDT"),
        )
        bars: list[MarketBar] = []
        requests: list[dict[str, str]] = []
        # This hook preserves the exact bytes used by the ordinary public adapter.
        with gzip.open(raw_path, "wt", encoding="utf-8") as raw_file:

            def record(response: httpx.Response) -> None:
                response.read()
                response.raise_for_status()
                metadata = {
                    "url": str(response.request.url),
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "payload_sha256": hashlib.sha256(response.content).hexdigest(),
                }
                requests.append(metadata)
                raw_file.write(json.dumps({**metadata, "body": response.text}) + "\n")

            with httpx.Client(timeout=30, event_hooks={"response": [record]}) as client:
                with BinancePublicAdapter(client=client) as adapter:
                    cursor = START
                    while cursor < END:
                        page_end = min(cursor + 1000 * INTERVAL.duration, END)
                        page = adapter.fetch_klines(
                            instrument=instrument,
                            interval=INTERVAL,
                            start=cursor,
                            end_exclusive=page_end,
                        )
                        bars.extend(page.bars)
                        cursor = page_end
                        time.sleep(0.15)
        series = validate_bar_series(bars)
        expected_count = int((END - START) / INTERVAL.duration)
        if len(series) != expected_count:
            raise ValueError(
                f"{symbol}: expected {expected_count} bars, got {len(series)}"
            )
        fingerprint = write_parquet_bar_series(parquet_path, series)
        records.append(
            {
                "venue_symbol": symbol,
                "base_asset": asset,
                "quote_asset": "USDT",
                "bars": len(series),
                "semantic_fingerprint": fingerprint,
                "parquet_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
                "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
                "requests": requests,
            }
        )
        print(f"Recorded {symbol}: {len(series)} completed bars", flush=True)
    manifest = {
        "schema_version": "qap.engine-parity.inputs.v1",
        "captured_at": captured_at.isoformat(),
        "interval": INTERVAL.label,
        "start": START.isoformat(),
        "end_exclusive": END.isoformat(),
        "purpose": "Accounting parity only; no strategy selection or holdout use",
        "sources": records,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("tests/fixtures/engine_parity")
    )
    capture(parser.parse_args().output)
