"""Bounded operator CLI for Scanner-V1 asset momentum and manual basket replay."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from qap.scanner.protocol import ScannerHorizon
from qap.scanner_entry import generate_asset_momentum, run_basket_with_qap


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m qap.scanner.basket_cli")
    subcommands = parser.add_subparsers(dest="command", required=True)

    momentum = subcommands.add_parser("momentum")
    momentum.add_argument("--scan-id", required=True)
    momentum.add_argument("--venue", choices=("binance", "gate"), required=True)
    momentum.add_argument(
        "--horizon", choices=("short", "medium", "swing"), required=True
    )
    momentum.add_argument("--data-root", type=Path, required=True)
    momentum.add_argument("--run-root", type=Path, required=True)

    basket = subcommands.add_parser("run")
    basket.add_argument("--scan-id", required=True)
    basket.add_argument("--venue", choices=("binance", "gate"), required=True)
    basket.add_argument(
        "--horizon", choices=("short", "medium", "swing"), required=True
    )
    basket.add_argument("--decision-resolution", required=True)
    basket.add_argument("--asset", action="append", required=True, dest="assets")
    basket.add_argument(
        "--candidate-id", action="append", required=True, dest="candidate_ids"
    )
    basket.add_argument("--momentum-scan-id", default=None)
    basket.add_argument("--data-root", type=Path, required=True)
    basket.add_argument("--run-root", type=Path, required=True)
    basket.add_argument("--repository-root", type=Path, required=True)
    return parser


def _run(arguments: argparse.Namespace) -> dict[str, object]:
    if arguments.command == "momentum":
        path = generate_asset_momentum(
            scan_id=arguments.scan_id,
            venue=arguments.venue,
            horizon=ScannerHorizon(arguments.horizon),
            data_root=arguments.data_root,
            run_root=arguments.run_root,
        )
        return {"momentum_directory": str(path)}
    if arguments.command == "run":
        path = run_basket_with_qap(
            scan_id=arguments.scan_id,
            venue=arguments.venue,
            horizon=ScannerHorizon(arguments.horizon),
            decision_resolution=arguments.decision_resolution,
            economic_assets=tuple(arguments.assets),
            candidate_ids=tuple(arguments.candidate_ids),
            momentum_scan_id=arguments.momentum_scan_id,
            data_root=arguments.data_root,
            run_root=arguments.run_root,
            repository_root=arguments.repository_root,
        )
        return {"basket_directory": str(path)}
    raise ValueError(f"unsupported command: {arguments.command}")


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        payload = _run(arguments)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f"qap scanner basket failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
