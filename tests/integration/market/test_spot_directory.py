"""Recorded directory evidence survives parsing, publication and persistence."""

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from qap.market.adapters.binance_public import BinancePublicAdapter
from qap.market.adapters.gate_public import GatePublicAdapter, GatePublicDataError
from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import ProductMarketDirectory

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures" / "gate"
OBSERVED = datetime(2026, 9, 30, tzinfo=UTC)


def _recorded(name: str) -> object:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def test_gate_keeps_names_listing_time_and_exact_chain_evidence(tmp_path: Path) -> None:
    pairs = _recorded("currency_pairs_identity_subset")
    currencies = _recorded("currencies_identity_subset")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        assert request.method == "GET"
        assert "KEY" not in request.headers and "SIGN" not in request.headers
        if request.url.path == "/api/v4/spot/currency_pairs":
            return httpx.Response(200, json=pairs)
        assert request.url.path == "/api/v4/spot/currencies"
        return httpx.Response(200, json=currencies)

    with GatePublicAdapter(transport=httpx.MockTransport(handler)) as adapter:
        observation = adapter.fetch_spot_directory(observed_at=OBSERVED)

    assert len(requests) == 2
    assert observation.observed_at == OBSERVED
    assert observation.source_fingerprint == public_payload_fingerprint(
        {"currency_pairs": pairs, "currencies": currencies}
    )
    directory = ProductMarketDirectory.from_observations((observation,))
    path = tmp_path / "directory.json"
    path.write_text(directory.model_dump_json())
    loaded = ProductMarketDirectory.model_validate_json(path.read_text())
    assert loaded.directory_id == directory.directory_id
    market = next(m for m in loaded.markets if m.venue_base_asset == "W")
    assert market.base_name == "WormHole"
    assert market.quote_name == "Tether"
    assert market.pair_type == "normal"
    assert market.buy_start == datetime(2024, 4, 3, 12, tzinfo=UTC)
    assert market.trading and market.status == "tradable"
    assert market.base_currency is not None
    assert market.base_currency.name == "WormHole"
    assert market.base_currency.delisted is False
    assert market.base_currency.trade_disabled is False
    assert market.base_currency.chain == "SOL"
    assert market.base_currency.chains[0].contract_address == (
        "85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ"
    )
    btc = next(m for m in loaded.markets if m.venue_base_asset == "BTC")
    assert btc.base_currency is not None
    assert btc.base_currency.chains[0].chain == "BTC"
    assert btc.base_currency.chains[0].contract_address is None
    assert any(chain.chain == "BSC" for chain in btc.base_currency.chains)


def _pair(**overrides: object) -> dict[str, object]:
    return {
        "id": "W_USDT",
        "base": "W",
        "quote": "USDT",
        "trade_status": "tradable",
        "type": "normal",
        **overrides,
    }


def test_gate_falls_back_to_currency_name_and_preserves_categories() -> None:
    observation = GatePublicAdapter.spot_directory_from_payload(
        [_pair()],
        currencies_payload=[
            {
                "currency": "W",
                "name": "WormHole",
                "category": ["Stock"],
                "delisted": True,
                "trade_disabled": True,
            }
        ],
        observed_at=OBSERVED,
    )
    market = observation.markets[0]
    assert market.base_name == "WormHole"
    assert market.base_currency is not None
    assert market.base_currency.categories == ("Stock",)
    assert market.base_currency.delisted is True
    assert market.base_currency.trade_disabled is True
    # Missing listing and chain data stay unknown, never inferred from observation.
    assert market.buy_start is None and market.base_currency.chains == ()


def test_gate_optional_metadata_and_premarket_filter_remain_compatible() -> None:
    observation = GatePublicAdapter.spot_directory_from_payload(
        [_pair(buy_start=0), _pair(id="X_USDT", base="X", type="premarket")],
        observed_at=OBSERVED,
    )
    assert len(observation.markets) == 1
    assert observation.markets[0].buy_start is None
    assert observation.markets[0].base_name is None
    assert observation.markets[0].base_currency is None


@pytest.mark.parametrize("invalid", [True, -1, "123", 1.5])
def test_gate_malformed_listing_time_is_an_explicit_source_failure(
    invalid: object,
) -> None:
    with pytest.raises(GatePublicDataError, match="buy_start"):
        GatePublicAdapter.spot_directory_from_payload([_pair(buy_start=invalid)])


@pytest.mark.parametrize(
    "invalid",
    [
        [{"currency": "W", "delisted": "false"}],
        [{"currency": "W", "chains": [{"name": "SOL", "addr": 123}]}],
        [{"currency": "W"}, {"currency": "W"}],
    ],
)
def test_gate_malformed_currency_evidence_is_rejected(invalid: object) -> None:
    with pytest.raises(GatePublicDataError):
        GatePublicAdapter.spot_currencies_from_payload(invalid)


def test_gate_currency_request_failure_is_typed() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("currency_pairs"):
            return httpx.Response(200, json=[_pair()])
        return httpx.Response(503)

    with GatePublicAdapter(transport=httpx.MockTransport(handler)) as adapter:
        with pytest.raises(GatePublicDataError, match="503"):
            adapter.fetch_spot_directory()


def test_binance_keeps_spot_permissions_without_inventing_a_name() -> None:
    payload = {
        "symbols": [
            {
                "symbol": "WUSDT",
                "baseAsset": "W",
                "quoteAsset": "USDT",
                "status": "TRADING",
                "isSpotTradingAllowed": False,
                "permissions": ["SPOT"],
                "permissionSets": [["SPOT", "TRD_GRP_004"]],
            }
        ]
    }
    observation = BinancePublicAdapter.spot_directory_from_payload(
        payload, observed_at=OBSERVED
    )
    directory = ProductMarketDirectory.from_observations((observation,))
    loaded = ProductMarketDirectory.model_validate_json(directory.model_dump_json())
    market = loaded.markets[0]
    assert not market.trading and market.spot_trading_allowed is False
    assert market.status == "TRADING"
    assert market.permissions == ("SPOT",)
    assert market.permission_sets == (("SPOT", "TRD_GRP_004"),)
    assert market.base_name is None and market.buy_start is None
    assert loaded.sources[0].source_fingerprint == public_payload_fingerprint(payload)
