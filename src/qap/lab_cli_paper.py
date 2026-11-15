"""AI-agent CLI subcommands for forward Binance L2 paper sessions."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, cast

import numpy as np

from qap.experiment.live_paper_execution import (
    BookProvider,
    default_instrument,
    window_book_provider,
)
from qap.experiment.live_paper_runner import LivePaperSessionManager
from qap.policy.lab_settings import LabSettings
from qap.product_market_data import ProductMarketData
from qap.product_pair_rotation_analysis import PairRotationAnalysis
from qap.product_universe import ProductUniverse
from qap.relationship.pair_measurements import Floats

PAPER_COMMANDS = frozenset(
    {"paper-start", "paper-step", "paper-status", "paper-list", "paper-stop"}
)
_BARS = ("1m", "15m", "1h", "4h", "1d")
_DEFAULT_WINDOW_SECONDS = 3.0


def add_paper_parsers(
    add_parser: Callable[..., argparse.ArgumentParser],
    common: argparse.ArgumentParser,
) -> None:
    """Register the five `paper-*` subcommands next to the research commands."""

    start = add_parser("paper-start", parents=[common])
    start.add_argument("--coin-a", required=True)
    start.add_argument("--coin-b", required=True)
    start.add_argument("--anchor", default=None)
    start.add_argument("--bar", choices=_BARS, default="1h")
    start.add_argument("--settings", default="{}")
    start.add_argument("--order-rtt-ms", type=float, default=75.0)
    start.add_argument(
        "--duration-seconds", type=float, default=_DEFAULT_WINDOW_SECONDS
    )

    step = add_parser("paper-step", parents=[common])
    step.add_argument("--session-id", required=True)
    step.add_argument("--duration-seconds", type=float, default=_DEFAULT_WINDOW_SECONDS)

    status = add_parser("paper-status", parents=[common])
    status.add_argument("--session-id", required=True)

    listing = add_parser("paper-list", parents=[common])
    listing.add_argument("--limit", type=int, default=25)

    stop = add_parser("paper-stop", parents=[common])
    stop.add_argument("--session-id", required=True)


def compact_paper_session(view: Mapping[str, Any]) -> dict[str, Any]:
    """Token-efficient session summary for AI agents."""

    audit = view["latency_audit"]
    return {
        "session_id": view["session_id"],
        "actor_id": view["actor_id"],
        "status": view["status"],
        "coin_a": view["coin_a"],
        "coin_b": view["coin_b"],
        "anchor": view["anchor"],
        "bar": view["bar"],
        "simple_status": view["simple_status"],
        "decisions_count": view["decisions_count"],
        "trades_count": len(view["trades"]),
        "vs_hodl_pct": view["vs_hodl_pct"],
        "vs_control_pct": view["vs_control_pct"],
        "portfolios": {
            key: {
                "value_usdt": item["value_usdt"],
                "return_pct": item["return_pct"],
                "rotations": item["rotations"],
            }
            for key, item in view["portfolios"].items()
        },
        "last_latency": audit[-1] if audit else None,
    }


def format_paper_md(payload: Mapping[str, Any]) -> str:
    """Render a paper CLI payload as short markdown."""

    if "sessions" in payload:
        lines = [f"## Paper sessions ({len(payload['sessions'])})"]
        lines.extend(
            f"- {row['session_id'][:12]} {row['status']} "
            f"{row['coin_a']}/{row['coin_b']} {row['bar']} "
            f"vs_hodl={row['vs_hodl_pct']:+.2f}% vs_ctrl={row['vs_control_pct']:+.2f}%"
            for row in payload["sessions"]
        )
        return "\n".join(lines)
    return (
        f"## Paper {payload['session_id'][:12]} ({payload['status']})\n"
        f"{payload['simple_status']}\n"
        f"vs_hodl={payload['vs_hodl_pct']:+.2f}% "
        f"vs_ctrl={payload['vs_control_pct']:+.2f}% "
        f"decisions={payload['decisions_count']} trades={payload['trades_count']}"
    )


def warm_historical_closes(
    run_root: Path,
    data_root: Path | None,
    *,
    coin_a: str,
    coin_b: str,
    anchor: str | None,
    bar: str,
) -> dict[str, Floats] | None:
    """Seed initial close history from prepared bars when available on disk."""
    if data_root is None or bar not in ("15m", "1h", "4h", "1d"):
        return None
    try:
        analysis = PairRotationAnalysis(
            ProductUniverse(run_root), ProductMarketData(run_root, data_root), data_root
        ).analyze(coin_a, coin_b, bar=bar, days=180, band_lookback=96, anchor=anchor)
    except Exception:
        return None
    raw_series = analysis.get("series")
    if not isinstance(raw_series, Mapping):
        return None
    series = cast(Mapping[str, Any], raw_series)
    close_a = cast(Sequence[float | None], series["close_a"])
    close_b = cast(Sequence[float | None], series["close_b"])
    out: dict[str, Floats] = {
        default_instrument(coin_a).venue_symbol: np.asarray(
            [float(x) for x in close_a if x is not None], dtype=np.float64
        ),
        default_instrument(coin_b).venue_symbol: np.asarray(
            [float(x) for x in close_b if x is not None], dtype=np.float64
        ),
    }
    anc_closes = series.get("anchor_close")
    if anchor is not None and isinstance(anc_closes, list):
        typed_anc = cast(Sequence[float | None], anc_closes)
        vals = [float(x) for x in typed_anc if x is not None]
        if vals:
            out[default_instrument(anchor).venue_symbol] = np.asarray(
                vals, dtype=np.float64
            )
    return out


def run_paper_command(
    args: argparse.Namespace, book_provider: BookProvider | None = None
) -> dict[str, Any]:
    """Execute one `paper-*` subcommand; `book_provider` injects test books."""

    window = float(getattr(args, "duration_seconds", _DEFAULT_WINDOW_SECONDS))
    manager = LivePaperSessionManager(
        args.run_root,
        actor_id=args.actor_id,
        book_provider=book_provider or window_book_provider(window),
    )
    if args.command == "paper-list":
        return {"sessions": manager.list_sessions(limit=args.limit)}
    if args.command == "paper-start":
        warm = warm_historical_closes(
            args.run_root,
            getattr(args, "data_root", None),
            coin_a=args.coin_a,
            coin_b=args.coin_b,
            anchor=args.anchor,
            bar=args.bar,
        )
        view = manager.create_session(
            args.coin_a,
            args.coin_b,
            anchor=args.anchor,
            bar=args.bar,
            settings=LabSettings.model_validate(json.loads(args.settings)),
            order_rtt_ms=args.order_rtt_ms,
            historical_closes=warm,
        )
    elif args.command == "paper-step":
        view = manager.step_session(args.session_id)
    elif args.command == "paper-stop":
        view = manager.stop_session(args.session_id)
    else:
        view = manager.read_session(args.session_id)
    return compact_paper_session(view)
