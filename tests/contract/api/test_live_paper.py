"""HTTP and CLI contracts for forward L2 paper sessions."""

import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from qap.api.app import create_app
from qap.api.live_paper_schemas import LivePaperSessionDto, LivePaperSessionListDto
from qap.api.settings import ApiSettings
from qap.artifact_integrity import build_integrity_record
from qap.experiment.live_paper_candles import (
    LEGACY_SCHEMA_VERSION,
    CandleInputs,
    candle_inputs_from_close_map,
)
from qap.experiment.live_paper_runner import LivePaperSessionManager
from qap.lab_cli import main
from qap.market import MarketMetadata, VenueInstrument
from qap.market.binance_ws_stream import TimedL2Book
from qap.market.microstructure import public_book_snapshot_from_rows
from qap.policy.lab_settings import LabSettings
from qap.portfolio import AssetId

BASE = "/api/pair-rotation/paper-sessions"
MIDS = {"BTCUSDT": 100.0, "ETHUSDT": 50.0, "SOLUSDT": 20.0}
NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)
MS = 1_000_000
RECV_NS = 1_000_000_000_000
BODY = {"coin_a": "binance:BTC", "coin_b": "binance:ETH", "order_rtt_ms": 1.0}
D = Decimal


def _meta(inst: VenueInstrument) -> MarketMetadata:
    return MarketMetadata(
        instrument=inst,
        status="TRADING",
        price_tick=D("0.01"),
        minimum_price=None,
        maximum_price=None,
        quantity_step=D("0.001"),
        minimum_quantity=D("0.001"),
        maximum_quantity=None,
        minimum_notional=D("5"),
        maximum_notional=None,
        minimum_notional_applies_to_market=True,
        maximum_notional_applies_to_market=False,
        notional_average_price_minutes=5,
    )


def timed_book(inst: VenueInstrument, mid: float, *, received_ns: int) -> TimedL2Book:
    half = mid * 0.001
    bids = [[f"{mid - half * (i + 1):.4f}", "1000"] for i in range(5)]
    asks = [[f"{mid + half * (i + 1):.4f}", "1000"] for i in range(5)]
    book = public_book_snapshot_from_rows(
        instrument=inst,
        observed_at=NOW,
        source_id="fixture",
        source_payload={"bids": bids, "asks": asks},
        bids=bids,
        asks=asks,
    )
    return TimedL2Book(inst, book, 1, 1_700_000_000_000_000, received_ns)


class MockProvider:
    """Flat live books stamped at call time; records every request."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(
        self, instruments: Sequence[VenueInstrument]
    ) -> Mapping[str, TimedL2Book]:
        self.calls.append(tuple(i.venue_symbol for i in instruments))
        now = time.time_ns()
        return {
            i.venue_symbol: timed_book(i, MIDS[i.venue_symbol], received_ns=now)
            for i in instruments
        }


class MockInputsProvider:
    """Mutable candle & metadata provider for deterministic HTTP/CLI tests."""

    def __init__(self, extra_steps: int = 0) -> None:
        self.extra_steps = extra_steps

    def __call__(
        self,
        *,
        coin_a: str,
        coin_b: str,
        anchor: str | None,
        anchor_mode: str,
        bar: str,
    ) -> CandleInputs:
        del coin_a, coin_b, anchor_mode
        btc = VenueInstrument("binance", "BTCUSDT", AssetId("BTC"), AssetId("USDT"))
        eth = VenueInstrument("binance", "ETHUSDT", AssetId("ETH"), AssetId("USDT"))
        sol = VenueInstrument("binance", "SOLUSDT", AssetId("SOL"), AssetId("USDT"))
        n = 40 + self.extra_steps
        closes: dict[str, Sequence[float]] = {
            "BTCUSDT": list(100.0 + 0.1 * np.sin(np.arange(n, dtype=np.float64))),
            "ETHUSDT": [50.0] * n,
        }
        meta = {"BTCUSDT": _meta(btc), "ETHUSDT": _meta(eth)}
        if anchor == "binance:SOL":
            closes["SOLUSDT"] = [20.0] * n
            meta["SOLUSDT"] = _meta(sol)
        return candle_inputs_from_close_map(
            bar, closes, metadata=meta, resolved_anchor=anchor
        )


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def inputs_provider() -> MockInputsProvider:
    return MockInputsProvider()


@pytest.fixture
def client(
    tmp_path: Path, provider: MockProvider, inputs_provider: MockInputsProvider
) -> TestClient:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    app.state.paper_book_provider = provider
    app.state.paper_inputs_provider = inputs_provider
    return TestClient(app)


def actor(name: str) -> dict[str, str]:
    return {"X-QAP-Actor-Id": name}


def test_all_five_operations_are_in_the_openapi_contract(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    ops = {
        (path, method): spec["operationId"]
        for path, item in paths.items()
        for method, spec in item.items()
        if path.startswith(BASE)
    }
    assert ops == {
        (BASE, "post"): "createLivePaperSession",
        (BASE, "get"): "listLivePaperSessions",
        (f"{BASE}/{{session_id}}", "get"): "getLivePaperSession",
        (f"{BASE}/{{session_id}}/step", "post"): "stepLivePaperSession",
        (f"{BASE}/{{session_id}}/stop", "post"): "stopLivePaperSession",
    }


def test_session_lifecycle_and_candle_gating_over_http(
    client: TestClient, provider: MockProvider, inputs_provider: MockInputsProvider
) -> None:
    created = client.post(BASE, json=BODY)
    assert created.status_code == 200
    session = LivePaperSessionDto.model_validate(created.json())
    sid = session.session_id
    assert session.status == "active" and session.actor_id == "local"
    assert (
        session.can_step is True
        and session.schema_version == "qap.lab.paper_session.v2"
    )
    assert sorted(session.market_metadata_provenance) == ["BTCUSDT", "ETHUSDT"]
    assert provider.calls == [("BTCUSDT", "ETHUSDT")]

    listed = LivePaperSessionListDto.model_validate(client.get(BASE).json())
    assert [row.session_id for row in listed.sessions] == [sid]

    # Step inside the same candle: zero signal observations, nullable actual fill times.
    same_candle = LivePaperSessionDto.model_validate(
        client.post(f"{BASE}/{sid}/step", json={"duration_seconds": 1.5}).json()
    )
    assert same_candle.decisions_count == 0
    assert same_candle.book_observations_count == 1
    assert same_candle.latency_audit[0].actual_fill_leg1_ns is None
    assert same_candle.latency_audit[0].actual_fill_leg2_ns is None

    # Advance one completed candle -> decisions_count == 1.
    inputs_provider.extra_steps = 1
    next_candle = LivePaperSessionDto.model_validate(
        client.post(f"{BASE}/{sid}/step").json()
    )
    assert next_candle.decisions_count == 1
    assert next_candle.book_observations_count == 2

    stopped = client.post(f"{BASE}/{sid}/stop")
    assert LivePaperSessionDto.model_validate(stopped.json()).status == "stopped"
    again = client.post(f"{BASE}/{sid}/step")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "live_paper_unavailable"


def test_session_with_a_real_swap_validates_against_the_response_contract(
    client: TestClient, tmp_path: Path
) -> None:
    btc, eth = (
        VenueInstrument("binance", s, AssetId(s[:3]), AssetId("USDT"))
        for s in ("BTCUSDT", "ETHUSDT")
    )

    def books(a: float, b: float, received: int) -> dict[str, TimedL2Book]:
        return {
            "BTCUSDT": timed_book(btc, a, received_ns=received),
            "ETHUSDT": timed_book(eth, b, received_ns=received),
        }

    meta = {"BTCUSDT": _meta(btc), "ETHUSDT": _meta(eth)}
    base_wave = list(100.0 + 0.1 * np.sin(np.arange(40, dtype=np.float64)))
    init_c = candle_inputs_from_close_map(
        "1h", {"BTCUSDT": base_wave, "ETHUSDT": [50.0] * 40}, metadata=meta
    )
    step_c = candle_inputs_from_close_map(
        "1h", {"BTCUSDT": base_wave + [130.0], "ETHUSDT": [50.0] * 41}, metadata=meta
    )

    manager = LivePaperSessionManager(tmp_path / "runs", actor_id="local")
    manager.create_session(
        "binance:BTC",
        "binance:ETH",
        settings=LabSettings(
            auto_tune=False,
            lookback=20,
            entry=1.0,
            exit=0.5,
            minimum_hold=0,
            cooldown=0,
        ),
        initial_books=books(100.0, 50.0, RECV_NS),
        candle_inputs=init_c,
        session_id="swap1",
    )
    manager.step_session(
        "swap1",
        candle_inputs=step_c,
        books=books(130.0, 50.0, RECV_NS),
        decide_ns=RECV_NS + 2 * MS,
        fill_books_leg1=books(130.0, 50.0, RECV_NS + 70 * MS),
        fill_books_leg2=books(128.0, 50.5, RECV_NS + 145 * MS),
    )
    response = client.get(f"{BASE}/swap1")
    assert response.status_code == 200
    dto = LivePaperSessionDto.model_validate(response.json())
    (trade,) = dto.trades
    assert [f.side for f in trade.fills] == ["sell", "buy"]
    assert dto.portfolios.strategy.rotations == 1
    assert dto.latency_audit[0].actual_fill_leg1_ns == RECV_NS + 77 * MS
    assert dto.latency_audit[0].actual_fill_leg2_ns == RECV_NS + 152 * MS


def test_missing_prepared_data_or_legacy_session_returns_409(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    unprepared = TestClient(app)
    resp = unprepared.post(BASE, json=BODY)
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "live_paper_unavailable"

    # Legacy v1 session reads cleanly with can_step=False and refuses /step with 409.
    sdir = (
        tmp_path / "runs" / "product" / "pair-rotation-lab" / "paper-sessions" / "legv1"
    )
    sdir.mkdir(parents=True)
    legacy: dict[str, Any] = {
        "schema_version": LEGACY_SCHEMA_VERSION,
        "session_id": "legv1",
        "actor_id": "local",
        "status": "active",
        "created_at": NOW.isoformat(),
        "updated_at": NOW.isoformat(),
        "stopped_at": None,
        "coin_a": "binance:BTC",
        "coin_b": "binance:ETH",
        "anchor": None,
        "bar": "1h",
        "order_rtt_ms": 75.0,
        "max_staleness_ms": 500.0,
        "starting_value": "10000",
        "settings": LabSettings().model_dump(mode="json"),
        "instruments": {
            "a": {
                "venue": "binance",
                "venue_symbol": "BTCUSDT",
                "base": "BTC",
                "quote": "USDT",
            },
            "b": {
                "venue": "binance",
                "venue_symbol": "ETHUSDT",
                "base": "ETH",
                "quote": "USDT",
            },
            "anchor": None,
        },
        "close_history": {"BTCUSDT": [100.0], "ETHUSDT": [50.0]},
        "decisions_count": 0,
        "last_preference": 0.0,
        "last_rotation_step": None,
        "peak_value": 10000.0,
        "parked": False,
        "portfolios": {
            k: {
                "holdings": {"BTC": "50", "ETH": "100"},
                "value_usdt": "10000",
                "fees_usdt": "0",
                "slippage_usdt": "0",
                "rotations": 0,
            }
            for k in ("strategy", "hodl", "drift_control")
        },
        "trades": [],
        "latency_audit": [],
    }
    (sdir / "session.json").write_text(json.dumps(legacy), encoding="utf-8")
    (sdir / "integrity.json").write_text(
        build_integrity_record(
            sdir, artifact_id="legv1", file_names=("session.json",)
        ).model_dump_json(),
        encoding="utf-8",
    )
    got = LivePaperSessionDto.model_validate(unprepared.get(f"{BASE}/legv1").json())
    assert got.can_step is False and "Legacy v1" in (got.step_block_reason or "")
    step_legacy = unprepared.post(f"{BASE}/legv1/step")
    assert step_legacy.status_code == 409


def test_actor_header_scopes_every_endpoint(client: TestClient) -> None:
    sid = client.post(BASE, json=BODY, headers=actor("alice")).json()["session_id"]
    assert (
        client.get(BASE, headers=actor("alice")).json()["sessions"][0]["actor_id"]
        == "alice"
    )
    assert client.get(BASE).json()["sessions"] == []
    for method, path in (("get", ""), ("post", "/step"), ("post", "/stop")):
        denied = client.request(method, f"{BASE}/{sid}{path}", headers=actor("bob"))
        assert denied.status_code == 404
        assert denied.json()["error"]["code"] == "live_paper_session_not_found"
    assert client.get(f"{BASE}/{sid}", headers=actor("alice")).status_code == 200


def test_invalid_input_is_rejected_at_the_boundary(client: TestClient) -> None:
    assert client.post(BASE, json={**BODY, "coin_b": "binance:BTC"}).status_code == 422
    assert client.post(BASE, json={**BODY, "anchor": "kraken:BTC"}).status_code == 422
    assert client.post(BASE, json={**BODY, "order_rtt_ms": 0}).status_code == 422
    assert client.post(BASE, json={**BODY, "surprise": 1}).status_code == 422
    assert client.post(BASE, json={**BODY, "bar": "2h"}).status_code == 422
    assert client.get(BASE, params={"limit": 0}).status_code == 422
    assert client.get(BASE, headers=actor("../x")).status_code == 409
    assert client.get(f"{BASE}/missing").status_code == 404


def test_writes_require_a_local_market_workspace(tmp_path: Path) -> None:
    app = create_app(ApiSettings(run_root=tmp_path / "r", workspace_mode="sample"))
    sample = TestClient(app)
    assert sample.post(BASE, json=BODY).status_code == 409
    assert sample.post(f"{BASE}/x/step").status_code == 409
    assert sample.post(f"{BASE}/x/stop").status_code == 409
    assert sample.get(BASE).status_code == 200


def run_cli(
    capsys: pytest.CaptureFixture[str],
    provider: MockProvider,
    inputs_provider: MockInputsProvider | None,
    root: Path,
    *argv: str,
) -> tuple[int, Any]:
    code = main(
        [*argv, "--run-root", str(root)],
        book_provider=provider,
        paper_inputs_provider=inputs_provider,
    )
    captured = capsys.readouterr()
    text = captured.out if code == 0 else captured.err
    try:
        return code, json.loads(text)
    except ValueError:
        return code, text


def test_cli_paper_commands_share_sessions_with_the_http_surface(
    tmp_path: Path, provider: MockProvider, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "runs"
    inp = MockInputsProvider()
    code, started = run_cli(
        capsys,
        provider,
        inp,
        root,
        "paper-start",
        "--coin-a",
        "binance:BTC",
        "--coin-b",
        "binance:ETH",
        "--bar",
        "4h",
        "--order-rtt-ms",
        "1",
        "--settings",
        '{"lookback": 40, "auto_tune": false}',
        "--actor-id",
        "agent7",
    )
    assert code == 0
    sid = started["session_id"]
    assert started["status"] == "active" and started["actor_id"] == "agent7"

    # Stepping on the same candle increments book_observations_count only.
    code, stepped_same = run_cli(
        capsys,
        provider,
        inp,
        root,
        "paper-step",
        "--session-id",
        sid,
        "--duration-seconds",
        "1",
        "--actor-id",
        "agent7",
    )
    assert code == 0 and stepped_same["decisions_count"] == 0
    assert stepped_same["book_observations_count"] == 1

    # Advancing 1 completed candle increments decisions_count to 1.
    inp.extra_steps = 1
    code, stepped_next = run_cli(
        capsys,
        provider,
        inp,
        root,
        "paper-step",
        "--session-id",
        sid,
        "--duration-seconds",
        "1",
        "--actor-id",
        "agent7",
    )
    assert code == 0 and stepped_next["decisions_count"] == 1

    code, status = run_cli(
        capsys,
        provider,
        inp,
        root,
        "paper-status",
        "--session-id",
        sid,
        "--actor-id",
        "agent7",
    )
    assert code == 0 and status["decisions_count"] == 1

    app = create_app(ApiSettings(run_root=root))
    http = TestClient(app).get(f"{BASE}/{sid}", headers=actor("agent7"))
    assert http.status_code == 200 and http.json()["decisions_count"] == 1

    code, stopped = run_cli(
        capsys,
        provider,
        inp,
        root,
        "paper-stop",
        "--session-id",
        sid,
        "--actor-id",
        "agent7",
    )
    assert code == 0 and stopped["status"] == "stopped"


def test_cli_errors_without_prepared_data_and_formats_markdown(
    tmp_path: Path, provider: MockProvider, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "runs"
    # Real path without inputs provider rejects missing prepared data.
    code, err = run_cli(
        capsys,
        provider,
        None,
        root,
        "paper-start",
        "--coin-a",
        "binance:BTC",
        "--coin-b",
        "binance:ETH",
    )
    assert code == 3 and (
        "refreshed" in err["error"]
        or "Prepare" in err["error"]
        or "Market data root" in err["error"]
    )

    inp = MockInputsProvider()
    args = ("--coin-a", "binance:BTC", "--coin-b", "binance:ETH", "--order-rtt-ms", "1")
    assert (
        main(
            ["paper-start", *args, "--format", "md", "--run-root", str(root)],
            book_provider=provider,
            paper_inputs_provider=inp,
        )
        == 0
    )
    out = capsys.readouterr().out
    assert out.startswith("## Paper ") and "vs_hodl=+0.00%" in out
    assert (
        main(
            ["paper-list", "--format", "md", "--run-root", str(root)],
            book_provider=provider,
        )
        == 0
    )
    assert capsys.readouterr().out.startswith("## Paper sessions (1)")
