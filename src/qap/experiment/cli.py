"""Minimal command-line entrypoint for one frozen experiment manifest."""

import argparse
import json
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import ValidationError

from qap.experiment.artifacts import ArtifactError, run_experiment_to_artifacts
from qap.experiment.manifest import load_manifest


def _utc_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "run timestamp must be an ISO-8601 UTC value"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise argparse.ArgumentTypeError("run timestamp must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m qap.experiment.cli",
        description="Execute one frozen QAP experiment manifest.",
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--data-root", type=Path, default=Path.cwd())
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--run-root", type=Path, default=Path.cwd() / "runs")
    parser.add_argument("--run-timestamp", type=_utc_timestamp, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        manifest = load_manifest(arguments.manifest)
        paths = run_experiment_to_artifacts(
            manifest,
            data_root=arguments.data_root,
            repository_root=arguments.repository_root,
            run_root=arguments.run_root,
            run_timestamp=arguments.run_timestamp,
        )
        from qap.experiment.artifacts import read_run_artifacts

        result = read_run_artifacts(paths.run_directory).result
    except (
        ArtifactError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
        ValidationError,
    ) as exc:
        print(f"qap experiment failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "run_id": paths.run_id,
                "status": result.status.value,
                "primary_metric": result.primary_metric.value,
                "primary_metric_value": str(result.primary_metric_value),
                "run_directory": str(paths.run_directory),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through subprocess
    raise SystemExit(main())
