#!/usr/bin/env python3
"""Run one deterministic forward-paper operation from recorded public inputs."""

from argparse import ArgumentParser
from pathlib import Path

from qap.experiment.paper_operation import run_paper_operation_to_artifact


def _parser() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="paper-operation spec JSON")
    parser.add_argument(
        "--repository-root",
        type=Path,
        default=Path.cwd(),
        help="repository root used to resolve recorded fixture paths",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="directory that will receive the immutable operation directory",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    artifact = run_paper_operation_to_artifact(
        args.spec,
        repository_root=args.repository_root,
        output_root=args.output_root,
    )
    print(artifact.operation_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
