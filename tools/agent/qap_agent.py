#!/usr/bin/env python3
"""Small CLI for QAP sequential-agent plan, progress, Git, and verification helpers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.agent.git_guard import (  # noqa: E402
    GitGuardError,
    WriterOwnershipError,
    acquire_writer,
    inspect_writer,
    release_writer,
    snapshot_git,
)
from tools.agent.plan import PlanParseError, parse_plan  # noqa: E402
from tools.agent.state import (  # noqa: E402
    ProgressStateError,
    checkpoint_section,
    load_progress,
)
from tools.agent.verify import run_verification  # noqa: E402


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qap_agent.py",
        description="Sequential QAP implementation support helpers.",
    )
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    status = subparsers.add_parser("status", help="read plan/progress without mutation")
    status.add_argument("plan", type=Path)

    section = subparsers.add_parser("section", help="print one approved plan section")
    section.add_argument("plan", type=Path)
    section.add_argument("--section", required=True)

    checkpoint = subparsers.add_parser(
        "checkpoint", help="record one explicit local progress transition"
    )
    checkpoint.add_argument("plan", type=Path)
    checkpoint.add_argument("--section", required=True)
    checkpoint.add_argument(
        "--status",
        required=True,
        choices=("pending", "in_progress", "complete", "blocked"),
    )
    checkpoint.add_argument("--writer-id")
    checkpoint.add_argument("--writer-note")
    checkpoint.add_argument("--commit")
    checkpoint.add_argument("--note")
    checkpoint.add_argument("--next-action")

    verify = subparsers.add_parser(
        "verify", help="run one explicit bounded verification command"
    )
    verify.add_argument("plan", type=Path)
    verify.add_argument("--section", required=True)
    verify.add_argument("--timeout", type=float, required=True)
    verify.add_argument("--command", required=True)

    writer_status = subparsers.add_parser(
        "writer-status", help="inspect cooperative worktree ownership"
    )
    writer_status.add_argument("repository", type=Path, nargs="?", default=Path.cwd())

    writer_acquire = subparsers.add_parser(
        "writer-acquire", help="acquire cooperative worktree ownership"
    )
    writer_acquire.add_argument("repository", type=Path, nargs="?", default=Path.cwd())
    writer_acquire.add_argument("--writer-id", required=True)
    writer_acquire.add_argument("--owner-pid", type=int, required=True)
    writer_acquire.add_argument("--note")

    writer_release = subparsers.add_parser(
        "writer-release", help="release cooperative worktree ownership"
    )
    writer_release.add_argument("repository", type=Path, nargs="?", default=Path.cwd())
    writer_release.add_argument("--writer-id", required=True)
    return parser


def _status(plan_path: Path) -> int:
    plan = parse_plan(plan_path)
    progress = load_progress(repository_root=plan.repository_root, plan=plan)
    print(f"Plan: {plan.path.relative_to(plan.repository_root)}")
    print(f"Title: {plan.title}")
    for section in plan.sections:
        status = (
            "pending"
            if progress is None
            else progress.sections[section.section_id].status
        )
        print(f"{section.section_id}\t{status}\t{section.title}")
    return 0


def _section(plan_path: Path, section_id: str) -> int:
    plan = parse_plan(plan_path)
    section = plan.section(section_id)
    print(f"## Section {section.section_id} — {section.title}\n")
    print(section.body)
    return 0


def _checkpoint(arguments: argparse.Namespace) -> int:
    plan = parse_plan(arguments.plan)
    progress = load_progress(repository_root=plan.repository_root, plan=plan)
    current = None if progress is None else progress.sections[arguments.section]
    snapshot = None
    if arguments.status == "in_progress" and (
        current is None or current.baseline_head is None
    ):
        if not arguments.writer_id:
            raise ProgressStateError("in_progress checkpoint requires --writer-id")
        snapshot = snapshot_git(plan.repository_root)
    checkpoint_section(
        repository_root=plan.repository_root,
        plan=plan,
        section_id=arguments.section,
        status=arguments.status,
        baseline_head=None if snapshot is None else snapshot.head,
        baseline_status_fingerprint=(
            None if snapshot is None else snapshot.status_fingerprint
        ),
        worktree_path=None if snapshot is None else str(snapshot.worktree_path),
        branch=None if snapshot is None else snapshot.branch,
        writer_id=arguments.writer_id,
        writer_note=arguments.writer_note,
        commit_hash=arguments.commit,
        note=arguments.note,
        next_action=arguments.next_action,
    )
    print(f"{arguments.section}\t{arguments.status}")
    return 0


def _verify(arguments: argparse.Namespace) -> int:
    plan = parse_plan(arguments.plan)
    command = arguments.command
    state_root = plan.repository_root / ".qap-agent" / plan.path.stem
    result = run_verification(
        command,
        cwd=plan.repository_root,
        timeout_seconds=arguments.timeout,
        log_dir=state_root / "logs",
    )
    progress = load_progress(repository_root=plan.repository_root, plan=plan)
    status = (
        "pending" if progress is None else progress.sections[arguments.section].status
    )
    existing = (
        () if progress is None else progress.sections[arguments.section].verifications
    )
    checkpoint_section(
        repository_root=plan.repository_root,
        plan=plan,
        section_id=arguments.section,
        status=status,
        verifications=(*existing, result.evidence()),
    )
    print(
        json.dumps(
            {
                "command": result.command,
                "exit_code": result.exit_code,
                "duration_seconds": result.duration_seconds,
                "output_tail": result.output_tail,
                "timed_out": result.timed_out,
                "log_path": result.log_path,
            },
            sort_keys=True,
        )
    )
    return result.exit_code


def _writer_status(repository: Path) -> int:
    lease = inspect_writer(repository)
    if lease is None:
        print("unowned")
    else:
        print(
            json.dumps(
                {
                    "writer_id": lease.writer_id,
                    "owner_pid": lease.owner_pid,
                    "worktree_path": lease.worktree_path,
                    "branch": lease.branch,
                    "head": lease.head,
                    "acquired_at": lease.acquired_at,
                    "note": lease.note,
                },
                sort_keys=True,
            )
        )
    return 0


def _writer_acquire(arguments: argparse.Namespace) -> int:
    lease = acquire_writer(
        repository_root=arguments.repository,
        writer_id=arguments.writer_id,
        owner_pid=arguments.owner_pid,
        note=arguments.note,
    )
    print(f"{lease.writer_id}\t{lease.owner_pid}\t{lease.worktree_path}")
    return 0


def _writer_release(arguments: argparse.Namespace) -> int:
    release_writer(
        repository_root=arguments.repository,
        writer_id=arguments.writer_id,
    )
    print("released")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command_name == "status":
            return _status(arguments.plan)
        if arguments.command_name == "section":
            return _section(arguments.plan, arguments.section)
        if arguments.command_name == "checkpoint":
            return _checkpoint(arguments)
        if arguments.command_name == "verify":
            return _verify(arguments)
        if arguments.command_name == "writer-status":
            return _writer_status(arguments.repository)
        if arguments.command_name == "writer-acquire":
            return _writer_acquire(arguments)
        if arguments.command_name == "writer-release":
            return _writer_release(arguments)
        raise RuntimeError(f"unsupported command: {arguments.command_name}")
    except (
        GitGuardError,
        OSError,
        PlanParseError,
        ProgressStateError,
        ValueError,
        WriterOwnershipError,
    ) as exc:
        print(f"qap-agent: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
