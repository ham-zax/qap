"""CoinGecko acquisition: recorded responses, pacing, provenance and outage fallback."""

import json
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest

from qap.asset_registry_coingecko import (
    DEMO_KEY_ENV,
    CoinGeckoRegistry,
    RegistryCacheError,
)

from .recorded import OBSERVED, case_snapshot, case_transport, load


def _registry(
    tmp_path: Path,
    transport: httpx.BaseTransport | None = None,
    *,
    pacing_seconds: float = 0.0,
    retries: int = 1,
    backoff_seconds: float = 5.0,
    budget_seconds: float = 300.0,
    min_age: timedelta = timedelta(hours=6),
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = lambda seconds: None,
    now: Callable[[], datetime] = lambda: OBSERVED,
) -> CoinGeckoRegistry:
    return CoinGeckoRegistry(
        tmp_path / "registry.json",
        transport=transport,
        pacing_seconds=pacing_seconds,
        retries=retries,
        backoff_seconds=backoff_seconds,
        budget_seconds=budget_seconds,
        min_age=min_age,
        clock=clock,
        sleep=sleep,
        now=now,
    )


def _failing(status: int | None = None, error: bool = False) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if error:
            raise httpx.ConnectError("offline", request=request)
        assert status is not None
        return httpx.Response(status, text="{}")

    return httpx.MockTransport(handler)


def test_refresh_builds_snapshot_from_recorded_responses_with_provenance(
    tmp_path: Path,
) -> None:
    requests: list[httpx.Request] = []
    result = _registry(tmp_path, case_transport(requests)).refresh()

    assert result.status == "refreshed"
    snapshot = result.snapshot
    assert snapshot is not None
    coins = {coin.coin_id: coin for coin in snapshot.coins}
    assert ("solana", "85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ") in (
        coins["wormhole"].platforms
    )
    assert {
        (t.venue, t.base, t.coin_id)
        for t in snapshot.tickers
        if t.coin_id == "wormhole"
    } >= {("binance", "W", "wormhole"), ("gate", "W", "wormhole")}
    assert [str(r.url.path) for r in requests] == [
        "/api/v3/coins/list",
        "/api/v3/exchanges/binance/tickers",
        "/api/v3/exchanges/gate/tickers",
    ]
    assert [s.retrieved_at for s in snapshot.sources] == [OBSERVED] * 3
    assert len({s.request_fingerprint for s in snapshot.sources}) == 3
    assert all(len(s.payload_fingerprint) == 64 for s in snapshot.sources)
    assert "CoinGecko" in snapshot.attribution


def test_stale_and_anomalous_ticker_flags_are_recorded(tmp_path: Path) -> None:
    snapshot = case_snapshot(tmp_path / "c.json")
    recorded = load("coingecko_case_responses.json")
    flagged = {
        (venue, row["base"], row["target"])
        for venue in ("binance", "gate")
        for row in recorded[f"exchanges/{venue}/tickers?page=1&order=base_target"][
            "tickers"
        ]
        if row["is_stale"] or row["is_anomaly"]
    }

    assert {
        (t.venue, t.base, t.target) for t in snapshot.tickers if t.stale or t.anomalous
    } <= flagged


def test_snapshot_fingerprint_is_deterministic_and_cache_round_trips(
    tmp_path: Path,
) -> None:
    first = _registry(tmp_path / "a", case_transport()).refresh().snapshot
    second = _registry(tmp_path / "b", case_transport()).refresh().snapshot
    cached = _registry(tmp_path / "a").snapshot()

    assert first is not None and second is not None
    assert first.fingerprint == second.fingerprint
    assert cached == first


def test_construction_and_import_make_no_request(tmp_path: Path) -> None:
    def forbidden(request: httpx.Request) -> httpx.Response:
        raise AssertionError("network used before refresh")

    registry = _registry(tmp_path, httpx.MockTransport(forbidden))

    assert registry.snapshot() is None


def test_demo_key_is_sent_as_header_and_never_stored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    secret = "CG-demo-secret-0123"
    seen: list[httpx.Request] = []
    monkeypatch.setenv(DEMO_KEY_ENV, secret)
    registry = _registry(tmp_path, case_transport(seen))

    registry.refresh()

    assert {r.headers["x-cg-demo-api-key"] for r in seen} == {secret}
    assert secret not in (tmp_path / "registry.json").read_text()


def test_keyless_requests_carry_no_key_header(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(DEMO_KEY_ENV, raising=False)
    seen: list[httpx.Request] = []

    _registry(tmp_path, case_transport(seen)).refresh()

    assert all("x-cg-demo-api-key" not in r.headers for r in seen)


def test_requests_are_paced_from_the_previous_request(tmp_path: Path) -> None:
    now = [100.0]
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    registry = _registry(
        tmp_path,
        case_transport(),
        pacing_seconds=2.1,
        clock=lambda: now[0],
        sleep=sleep,
    )
    registry.refresh()

    assert sleeps == pytest.approx([2.1, 2.1])
    # Pacing state survives across refreshes: the next call waits before its first.
    registry.refresh(force=True)
    assert len(sleeps) == 5


def test_rate_limit_retries_with_exponential_backoff(tmp_path: Path) -> None:
    """SYNTHETIC 429 responses in front of the recorded ones."""

    recorded = case_transport()
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] in (1, 2):
            return httpx.Response(429, text="{}")
        return recorded.handle_request(request)

    now = [0.0]
    sleeps: list[float] = []

    def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    registry = _registry(
        tmp_path,
        httpx.MockTransport(handler),
        retries=3,
        backoff_seconds=4.0,
        clock=lambda: now[0],
        sleep=sleep,
    )

    assert registry.refresh().status == "refreshed"
    assert sleeps == [4.0, 8.0]


@pytest.mark.parametrize(
    ("transport", "failure"),
    [
        (_failing(error=True), "network_error"),
        (_failing(429), "rate_limited"),
        (_failing(500), "http_error"),
        (_failing(404), "http_error"),
    ],
)
def test_outage_without_a_snapshot_is_unavailable_and_typed(
    tmp_path: Path, transport: httpx.MockTransport, failure: str
) -> None:
    result = _registry(tmp_path, transport).refresh()

    assert (result.status, result.snapshot, result.failure) == (
        "unavailable",
        None,
        failure,
    )
    assert not (tmp_path / "registry.json").exists()


def test_outage_falls_back_to_last_good_snapshot_as_a_stale_source(
    tmp_path: Path,
) -> None:
    good = _registry(tmp_path, case_transport()).refresh().snapshot
    later = _registry(tmp_path, _failing(error=True)).refresh(force=True)

    assert later.status == "stale"
    assert later.failure == "network_error"
    assert later.snapshot == good


def test_malformed_and_timeout_failures_never_replace_the_cache(
    tmp_path: Path,
) -> None:
    good = _registry(tmp_path, case_transport()).refresh().snapshot

    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    malformed = httpx.MockTransport(lambda request: httpx.Response(200, json={"a": 1}))
    outcomes = [
        _registry(tmp_path, transport).refresh(force=True)
        for transport in (httpx.MockTransport(timeout), malformed)
    ]

    assert [o.failure for o in outcomes] == ["timeout", "malformed_response"]
    assert all(o.snapshot == good for o in outcomes)
    assert _registry(tmp_path).snapshot() == good


def test_exhausted_budget_stops_before_issuing_requests(tmp_path: Path) -> None:
    now = [0.0]

    def sleep(seconds: float) -> None:
        now[0] += seconds

    result = _registry(
        tmp_path,
        case_transport(),
        pacing_seconds=50.0,
        budget_seconds=60.0,
        clock=lambda: now[0],
        sleep=sleep,
    ).refresh()

    assert (result.status, result.failure) == ("unavailable", "budget_exhausted")


def test_fresh_snapshot_is_reused_without_network_until_min_age(
    tmp_path: Path,
) -> None:
    clock = [OBSERVED]
    _registry(tmp_path, case_transport()).refresh()
    seen: list[httpx.Request] = []
    registry = _registry(
        tmp_path,
        case_transport(seen),
        now=lambda: clock[0],
        min_age=timedelta(hours=6),
    )

    assert registry.refresh().status == "cached"
    assert seen == []
    clock[0] = OBSERVED + timedelta(hours=7)
    assert registry.refresh().status == "refreshed"
    assert seen


def test_ticker_pagination_continues_until_a_short_page(tmp_path: Path) -> None:
    """SYNTHETIC paging: 100 rows on page 1, the recorded rows on page 2."""

    recorded = load("coingecko_case_responses.json")
    row = recorded["exchanges/binance/tickers?page=1&order=base_target"]["tickers"][0]
    pages: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.raw_path.decode().removeprefix("/api/v3/")
        if "tickers" in key:
            pages.append(key)
        if key.startswith("exchanges/binance/tickers?page=1"):
            return httpx.Response(200, json={"tickers": [row] * 100})
        if key.startswith("exchanges/binance/tickers?page=2"):
            return httpx.Response(200, json={"tickers": [row]})
        if key.startswith("exchanges/binance"):
            raise AssertionError(key)
        return httpx.Response(200, json=recorded[key])

    result = _registry(tmp_path, httpx.MockTransport(handler)).refresh()

    assert result.status == "refreshed"
    assert [p.split("&")[0] for p in pages[:2]] == [
        "exchanges/binance/tickers?page=1",
        "exchanges/binance/tickers?page=2",
    ]


def test_corrupt_cache_is_visible_but_does_not_block_refresh(tmp_path: Path) -> None:
    cache = tmp_path / "registry.json"
    _registry(tmp_path, case_transport()).refresh()
    envelope = json.loads(cache.read_text())
    envelope["snapshot"]["registry"] = "tampered"
    cache.write_text(json.dumps(envelope))
    registry = _registry(tmp_path, case_transport())

    with pytest.raises(RegistryCacheError):
        registry.snapshot()
    assert registry.refresh(force=True).status == "refreshed"
    assert registry.snapshot() is not None
