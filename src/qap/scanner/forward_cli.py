"""Bounded operator CLI for scanner prospective evidence and qualification."""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

from qap.market.public_capture import CaptureKind, capture_public_spot
from qap.portfolio import AssetId
from qap.scanner.catalog import load_scanner_catalog
from qap.scanner.prospective_run import cohort_scoreboard
from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import (
    advance_forward_with_qap,
    freeze_scan_with_qap,
    qualify_forward_with_qap,
)


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("timestamp must be ISO-8601 UTC") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise argparse.ArgumentTypeError("timestamp must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _capital(value: str) -> Decimal:
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("capital must be a Decimal") from exc
    if not parsed.is_finite() or parsed <= 0:
        raise argparse.ArgumentTypeError("capital must be positive finite")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m qap.scanner.forward_cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    freeze = subcommands.add_parser("freeze")
    freeze.add_argument("--scan-id", required=True)
    freeze.add_argument(
        "--horizon",
        choices=("short", "medium", "swing"),
        required=True,
    )
    freeze.add_argument("--freeze-at", type=_utc, required=True)
    freeze.add_argument("--data-root", type=Path, required=True)
    freeze.add_argument("--run-root", type=Path, required=True)
    freeze.add_argument("--prospective-root", type=Path, required=True)

    advance = subcommands.add_parser("advance")
    advance.add_argument("--cohort-root", type=Path, required=True)
    advance.add_argument("--through", type=_utc, required=True)
    advance.add_argument("--data-root", type=Path, required=True)
    advance.add_argument("--run-root", type=Path, required=True)
    advance.add_argument("--repository-root", type=Path, required=True)

    capture = subcommands.add_parser("capture")
    capture.add_argument("--venue", choices=("binance", "gate"), required=True)
    capture.add_argument("--symbol", required=True)
    capture.add_argument("--base", required=True)
    capture.add_argument("--quote", required=True)
    capture.add_argument(
        "--kind",
        choices=tuple(item.value for item in CaptureKind),
        required=True,
    )
    capture.add_argument("--capture-root", type=Path, required=True)
    capture.add_argument("--observed-at", type=_utc, default=None)

    qualify = subcommands.add_parser("qualify")
    qualify.add_argument("--cohort-root", type=Path, required=True)
    qualify.add_argument("--checkpoint-id", required=True)
    qualify.add_argument("--requested-capital", type=_capital, required=True)
    qualify.add_argument("--data-root", type=Path, required=True)
    qualify.add_argument("--capture-root", type=Path, required=True)
    qualify.add_argument("--run-root", type=Path, required=True)
    qualify.add_argument("--repository-root", type=Path, required=True)

    show = subcommands.add_parser("show")
    show.add_argument("--cohort-root", type=Path, required=True)
    return parser


def _run(arguments: argparse.Namespace) -> dict[str, object]:
    if arguments.command == "freeze":
        path = freeze_scan_with_qap(
            run_root=arguments.run_root,
            data_root=arguments.data_root,
            prospective_root=arguments.prospective_root,
            scan_id=arguments.scan_id,
            horizon=ScannerHorizon(arguments.horizon),
            freeze_at=arguments.freeze_at,
        )
        return {"cohort_root": str(path)}
    if arguments.command == "advance":
        paths = advance_forward_with_qap(
            cohort_root=arguments.cohort_root,
            catalog=load_scanner_catalog(arguments.data_root),
            data_root=arguments.data_root,
            repository_root=arguments.repository_root,
            run_root=arguments.run_root,
            through=arguments.through,
        )
        return {"checkpoint_directories": [str(path) for path in paths]}
    if arguments.command == "capture":
        path = capture_public_spot(
            venue=arguments.venue,
            venue_symbol=arguments.symbol,
            base=AssetId(arguments.base),
            quote_asset=AssetId(arguments.quote),
            capture_root=arguments.capture_root,
            kind=CaptureKind(arguments.kind),
            observed_at=arguments.observed_at,
        )
        return {"capture_file": str(path)}
    if arguments.command == "qualify":
        path = qualify_forward_with_qap(
            cohort_root=arguments.cohort_root,
            checkpoint_id=arguments.checkpoint_id,
            requested_capital=arguments.requested_capital,
            catalog=load_scanner_catalog(arguments.data_root),
            data_root=arguments.data_root,
            capture_root=arguments.capture_root,
            repository_root=arguments.repository_root,
            run_root=arguments.run_root,
        )
        return {"qualification_directory": str(path)}
    if arguments.command == "show":
        return cohort_scoreboard(arguments.cohort_root)
    raise ValueError(f"unsupported command: {arguments.command}")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        payload = _run(arguments)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"qap scanner prospective failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
