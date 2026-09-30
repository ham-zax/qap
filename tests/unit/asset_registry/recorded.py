"""Loaders for the recorded registry fixtures in tests/fixtures/registry."""

import gzip
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

from qap.asset_registry import RegistrySnapshot
from qap.asset_registry_coingecko import CoinGeckoRegistry
from qap.market.adapters.spot_directory import (
    binance_directory_from_payload,
    gate_directory_from_payload,
)
from qap.product_directory_models import ProductMarketDirectory

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "registry"
OBSERVED = datetime(2026, 9, 30, 13, 57, 35, tzinfo=UTC)


def load(name: str) -> Any:
    path = FIXTURES / name
    if name.endswith(".gz"):
        return json.loads(gzip.decompress(path.read_bytes()))
    return json.loads(path.read_text(encoding="utf-8"))


def case_transport(requests: list[httpx.Request] | None = None) -> httpx.MockTransport:
    """Replay recorded CoinGecko responses; the path and query select the payload."""

    responses = cast(dict[str, object], load("coingecko_case_responses.json"))

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        key = request.url.raw_path.decode().removeprefix("/api/v3/")
        return httpx.Response(200, json=responses[key])

    return httpx.MockTransport(handler)


def case_snapshot(cache_path: Path) -> RegistrySnapshot:
    registry = CoinGeckoRegistry(
        cache_path,
        transport=case_transport(),
        pacing_seconds=0,
        now=lambda: OBSERVED,
    )
    snapshot = registry.refresh().snapshot
    assert snapshot is not None
    return snapshot


def directory(prefix: str) -> ProductMarketDirectory:
    """Binance and Gate directories from `case` or `coverage` recordings."""

    binance = "binance_case_exchange_info.json"
    gate = "gate_case_currency_pairs.json"
    currencies = "gate_case_currencies.json"
    if prefix == "coverage":
        binance = "coverage_binance_exchange_info.json.gz"
        gate = "coverage_gate_currency_pairs.json.gz"
        currencies = "coverage_gate_currencies.json.gz"
    return ProductMarketDirectory.from_observations(
        (
            binance_directory_from_payload(load(binance), observed_at=OBSERVED),
            gate_directory_from_payload(
                load(gate), currencies_payload=load(currencies), observed_at=OBSERVED
            ),
        )
    )
