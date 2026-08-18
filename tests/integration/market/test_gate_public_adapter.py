from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import httpx

from qap.market import VenueInstrument
from qap.market.adapters.gate_public import GatePublicAdapter
from qap.portfolio import AssetId


def _transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _pair_payload(*, status: str = "tradable") -> dict[str, object]:
    return {
        "id": "BTC_USDT",
        "base": "BTC",
        "quote": "USDT",
        "min_base_amount": "0.0001",
        "min_quote_amount": "1",
        "max_base_amount": "100",
        "max_quote_amount": "1000000",
        "amount_precision": 4,
        "precision": 2,
        "trade_status": status,
        "type": "normal",
        "market_order_max_stock": "50",
        "market_order_max_money": "500000",
    }


def test_gate_public_metadata_preserves_current_status_and_constraints() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_pair_payload(status="buyable"))

    with GatePublicAdapter(transport=_transport(handler)) as adapter:
        metadata = adapter.fetch_market_metadata(
            venue_symbol="BTC_USDT",
            base=AssetId("BTC"),
            quote=AssetId("USDT"),
            venue_base_asset="BTC",
            venue_quote_asset="USDT",
        )

    assert metadata.instrument.venue == "gate"
    assert metadata.status == "BUYABLE"
    assert metadata.price_tick == Decimal("0.01")
    assert metadata.quantity_step == Decimal("0.0001")
    assert metadata.minimum_notional == Decimal("1")
    assert metadata.maximum_notional == Decimal("500000")
    assert metadata.market_maximum_quantity == Decimal("50")
    assert len(requests) == 1
    assert requests[0].url.path == "/api/v4/spot/currency_pairs/BTC_USDT"
    assert "KEY" not in requests[0].headers
    assert "SIGN" not in requests[0].headers


def test_gate_public_l1_and_shallow_depth_use_bounded_order_book() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        limit = int(request.url.params["limit"])
        bids = [["100.0", "2.0"], ["99.0", "4.0"]][:limit]
        asks = [["101.0", "3.0"], ["102.0", "5.0"]][:limit]
        return httpx.Response(
            200,
            json={"id": 77, "current": 1_700_000_000_000, "bids": bids, "asks": asks},
        )

    instrument = VenueInstrument(
        venue="gate",
        venue_symbol="BTC_USDT",
        base=AssetId("BTC"),
        quote=AssetId("USDT"),
    )
    observed = datetime(2026, 8, 18, tzinfo=UTC)
    with GatePublicAdapter(transport=_transport(handler)) as adapter:
        l1 = adapter.fetch_l1_book(instrument=instrument, observed_at=observed)
        depth = adapter.fetch_shallow_depth(
            instrument=instrument,
            limit=20,
            observed_at=observed,
        )

    assert len(l1.bids) == len(l1.asks) == 1
    assert l1.best_bid == 100.0
    assert l1.best_ask == 101.0
    assert tuple(level.price for level in depth.bids) == (100.0, 99.0)
    assert tuple(level.price for level in depth.asks) == (101.0, 102.0)
    assert [request.url.path for request in requests] == [
        "/api/v4/spot/order_book",
        "/api/v4/spot/order_book",
    ]
    assert [request.url.params["limit"] for request in requests] == ["1", "20"]
    assert all("KEY" not in request.headers for request in requests)
    assert all("SIGN" not in request.headers for request in requests)
