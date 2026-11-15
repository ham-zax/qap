"""HTTP and CLI contracts for forward L2 paper sessions (mock book provider)."""

import json
import time
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from fastapi.testclient import TestClient

from qap.api.app import create_app
from qap.api.live_paper_schemas import LivePaperSessionDto, LivePaperSessionListDto
from qap.api.settings import ApiSettings
from qap.experiment.live_paper_runner import LivePaperSessionManager
from qap.lab_cli import main
from qap.market import VenueInstrument
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


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


@pytest.fixture
def client(tmp_path: Path, provider: MockProvider) -> TestClient:
    app = create_app(ApiSettings(run_root=tmp_path / "runs"))
    app.state.paper_book_provider = provider
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


def test_session_lifecycle_over_http(
    client: TestClient, provider: MockProvider
) -> None:
    created = client.post(BASE, json=BODY)
    assert created.status_code == 200
    session = LivePaperSessionDto.model_validate(created.json())
    sid = session.session_id
    assert session.status == "active" and session.actor_id == "local"
    assert (session.coin_a, session.coin_b, session.bar) == (
        "binance:BTC",
        "binance:ETH",
        "1h",
    )
    assert provider.calls == [("BTCUSDT", "ETHUSDT")]

    listed = LivePaperSessionListDto.model_validate(client.get(BASE).json())
    assert [row.session_id for row in listed.sessions] == [sid]
    assert listed.next_offset is None

    stepped = client.post(f"{BASE}/{sid}/step", json={"duration_seconds": 1.5})
    assert stepped.status_code == 200
    after = LivePaperSessionDto.model_validate(stepped.json())
    assert after.decisions_count == 1 and after.trades == []
    (audit,) = after.latency_audit
    assert (
        audit.t_recv_ns
        <= audit.t_decide_ns
        < audit.t_fill_leg1_ns
        < audit.t_fill_leg2_ns
    )
    assert audit.action == "hold"

    # Step body is optional.
    assert client.post(f"{BASE}/{sid}/step").json()["decisions_count"] == 2
    got = LivePaperSessionDto.model_validate(client.get(f"{BASE}/{sid}").json())
    assert got.decisions_count == 2

    stopped = client.post(f"{BASE}/{sid}/stop")
    assert LivePaperSessionDto.model_validate(stopped.json()).status == "stopped"
    again = client.post(f"{BASE}/{sid}/step")
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "live_paper_unavailable"


def test_session_with_a_real_swap_validates_against_the_response_contract(
    client: TestClient, tmp_path: Path
) -> None:
    """The DTO must accept trades, fills, and four-clock audits from the engine."""
    btc, eth = (
        VenueInstrument("binance", s, AssetId(s[:3]), AssetId("USDT"))
        for s in ("BTCUSDT", "ETHUSDT")
    )

    def books(a: float, b: float, received: int) -> dict[str, TimedL2Book]:
        return {
            "BTCUSDT": timed_book(btc, a, received_ns=received),
            "ETHUSDT": timed_book(eth, b, received_ns=received),
        }

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
        historical_closes={
            "BTCUSDT": 100.0 + 0.1 * np.sin(np.arange(40, dtype=np.float64)),
            "ETHUSDT": np.full(40, 50.0),
        },
        session_id="swap1",
    )
    manager.step_session(
        "swap1",
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
    assert dto.latency_audit[0].decide_to_fill_leg2_ms == 150.0
    row = client.get(BASE).json()["sessions"][0]
    assert row["trades_count"] == 1 and row["status"] == "active"


def test_actor_header_scopes_every_endpoint(client: TestClient) -> None:
    sid = client.post(BASE, json=BODY, headers=actor("alice")).json()["session_id"]
    assert (
        client.get(BASE, headers=actor("alice")).json()["sessions"][0]["actor_id"]
        == "alice"
    )
    assert client.get(BASE).json()["sessions"] == []
    assert client.get(BASE, headers=actor("bob")).json()["sessions"] == []
    for method, path in (("get", ""), ("post", "/step"), ("post", "/stop")):
        denied = client.request(method, f"{BASE}/{sid}{path}", headers=actor("bob"))
        assert denied.status_code == 404
        assert denied.json()["error"]["code"] == "live_paper_session_not_found"
    assert client.get(f"{BASE}/{sid}", headers=actor("alice")).status_code == 200


def test_invalid_input_is_rejected_at_the_boundary(client: TestClient) -> None:
    same = client.post(BASE, json={**BODY, "coin_b": "binance:BTC"})
    assert same.status_code == 422
    assert client.post(BASE, json={**BODY, "anchor": "kraken:BTC"}).status_code == 422
    assert client.post(BASE, json={**BODY, "order_rtt_ms": 0}).status_code == 422
    assert client.post(BASE, json={**BODY, "surprise": 1}).status_code == 422
    assert client.post(BASE, json={**BODY, "bar": "2h"}).status_code == 422
    assert client.get(BASE, params={"limit": 0}).status_code == 422
    bad_actor = client.get(BASE, headers=actor("../x"))
    assert bad_actor.status_code == 409
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
    root: Path,
    *argv: str,
) -> tuple[int, Any]:
    code = main([*argv, "--run-root", str(root)], book_provider=provider)
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
    code, started = run_cli(
        capsys, provider, root, "paper-start",
        "--coin-a", "binance:BTC", "--coin-b", "binance:ETH",
        "--bar", "4h", "--order-rtt-ms", "1",
        "--settings", '{"lookback": 40, "auto_tune": false}',
        "--actor-id", "agent7",
    )  # fmt: skip
    assert code == 0
    sid = started["session_id"]
    assert started["status"] == "active" and started["actor_id"] == "agent7"
    assert started["bar"] == "4h" and started["last_latency"] is None

    code, stepped = run_cli(
        capsys, provider, root, "paper-step", "--session-id", sid,
        "--duration-seconds", "1", "--actor-id", "agent7",
    )  # fmt: skip
    assert code == 0 and stepped["decisions_count"] == 1
    assert stepped["last_latency"]["action"] == "hold"
    assert set(stepped["portfolios"]) == {"strategy", "hodl", "drift_control"}

    code, status = run_cli(
        capsys,
        provider,
        root,
        "paper-status",
        "--session-id",
        sid,
        "--actor-id",
        "agent7",
    )
    assert code == 0 and status["simple_status"].startswith("Active (1 check(s))")
    code, listing = run_cli(
        capsys, provider, root, "paper-list", "--actor-id", "agent7"
    )
    assert code == 0 and [r["session_id"] for r in listing["sessions"]] == [sid]
    code, other = run_cli(capsys, provider, root, "paper-list", "--actor-id", "agent8")
    assert code == 0 and other == {"sessions": []}

    app = create_app(ApiSettings(run_root=root))
    http = TestClient(app).get(f"{BASE}/{sid}", headers=actor("agent7"))
    assert http.status_code == 200 and http.json()["decisions_count"] == 1

    code, stopped = run_cli(
        capsys,
        provider,
        root,
        "paper-stop",
        "--session-id",
        sid,
        "--actor-id",
        "agent7",
    )
    assert code == 0 and stopped["status"] == "stopped"


def test_cli_markdown_format_and_errors(
    tmp_path: Path, provider: MockProvider, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "runs"
    args = ("--coin-a", "binance:BTC", "--coin-b", "binance:ETH", "--order-rtt-ms", "1")
    assert (
        main(
            ["paper-start", *args, "--format", "md", "--run-root", str(root)],
            book_provider=provider,
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

    code, err = run_cli(capsys, provider, root, "paper-status", "--session-id", "nope")
    assert code == 3 and "not found" in err["error"]
    code, err = run_cli(
        capsys, provider, root, "paper-start", *args, "--settings", "{nope"
    )
    assert code == 2 and "error" in err
    code, err = run_cli(
        capsys, provider, root, "paper-start", *args, "--settings", '{"lookback": 1}'
    )
    assert code == 2
    code, err = run_cli(
        capsys,
        provider,
        root,
        "paper-start",
        "--coin-a",
        "binance:BTC",
        "--coin-b",
        "binance:BTC",
    )
    assert code == 3 and "distinct" in err["error"]
