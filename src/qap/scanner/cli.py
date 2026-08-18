"""Deterministic command-line entrypoint for Scanner-V1 Slice 1."""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

from qap.scanner.models import ScannerPinSpec, ScannerPinsFile
from qap.scanner.protocol import ScannerHorizon


def _utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("as-of must be an ISO-8601 UTC value") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise argparse.ArgumentTypeError("as-of must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _requested_horizons(value: str) -> tuple[ScannerHorizon, ...]:
    if value == "all":
        return (
            ScannerHorizon.SHORT,
            ScannerHorizon.MEDIUM,
            ScannerHorizon.SWING,
        )
    try:
        return (ScannerHorizon(value),)
    except ValueError as exc:
        raise ValueError(f"unsupported scanner horizon: {value}") from exc


def load_pins_file(path: Path | None) -> tuple[ScannerPinSpec, ...]:
    if path is None:
        return ()
    try:
        raw = path.read_text(encoding="utf-8")
        document = ScannerPinsFile.model_validate_json(raw)
    except (OSError, ValidationError) as exc:
        raise ValueError(f"invalid scanner pins file: {exc}") from exc
    return document.pins


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m qap.scanner.cli",
        description="Run one deterministic QAP Scanner-V1 Slice-1 generation.",
    )
    parser.add_argument("--as-of", type=_utc_timestamp, required=True)
    parser.add_argument(
        "--horizon",
        choices=("short", "medium", "swing", "all"),
        required=True,
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--pins-file", type=Path, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        pins = load_pins_file(arguments.pins_file)
        from qap.scanner_entry import run_scan_with_qap

        result = run_scan_with_qap(
            as_of=arguments.as_of,
            horizons=_requested_horizons(arguments.horizon),
            data_root=arguments.data_root,
            run_root=arguments.run_root,
            pins=pins,
        )
    except (
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        ValidationError,
    ) as exc:
        print(f"qap scanner failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            result.summary_payload(),
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess
    raise SystemExit(main())
