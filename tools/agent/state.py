"""Atomic local progress state for the sequential QAP implementation agent."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from tools.agent.plan import ParsedPlan

SectionStatus = Literal["pending", "in_progress", "complete", "blocked"]


class ProgressStateError(ValueError):
    """Raised when local progress state is corrupt or violates legal transitions."""


@dataclass(frozen=True, slots=True)
class VerificationEvidence:
    command: str
    exit_code: int
    duration_seconds: float
    output_tail: str
    log_path: str | None = None


@dataclass(slots=True)
class SectionProgress:
    section_id: str
    status: SectionStatus = "pending"
    baseline_head: str | None = None
    baseline_status_fingerprint: str | None = None
    worktree_path: str | None = None
    branch: str | None = None
    writer_id: str | None = None
    writer_note: str | None = None
    active_processes: tuple[str, ...] = ()
    started_at: str | None = None
    ended_at: str | None = None
    commit_hash: str | None = None
    verifications: tuple[VerificationEvidence, ...] = ()
    note: str | None = None
    next_action: str | None = None


@dataclass(slots=True)
class ProgressDocument:
    schema_version: str
    plan_path: str
    updated_at: str
    sections: dict[str, SectionProgress]


_ALLOWED_TRANSITIONS: dict[SectionStatus, frozenset[SectionStatus]] = {
    "pending": frozenset({"pending", "in_progress", "blocked"}),
    "in_progress": frozenset({"in_progress", "blocked", "complete"}),
    "blocked": frozenset({"blocked", "in_progress"}),
    "complete": frozenset({"complete"}),
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _state_root(repository_root: Path, plan: ParsedPlan) -> Path:
    slug = plan.path.stem
    return repository_root.resolve() / ".qap-agent" / slug


def _progress_path(repository_root: Path, plan: ParsedPlan) -> Path:
    return _state_root(repository_root, plan) / "progress.json"


def _markdown_path(repository_root: Path, plan: ParsedPlan) -> Path:
    return _state_root(repository_root, plan) / "progress.md"


def _new_document(repository_root: Path, plan: ParsedPlan) -> ProgressDocument:
    relative_plan = plan.path.relative_to(repository_root.resolve()).as_posix()
    return ProgressDocument(
        schema_version="qap.agent.progress.v1",
        plan_path=relative_plan,
        updated_at=_utc_now(),
        sections={
            section.section_id: SectionProgress(section_id=section.section_id)
            for section in plan.sections
        },
    )


def _verification_from_object(value: object) -> VerificationEvidence:
    if not isinstance(value, dict):
        raise ProgressStateError("corrupt verification evidence")
    raw = cast(dict[str, object], value)
    command = raw.get("command")
    exit_code = raw.get("exit_code")
    duration = raw.get("duration_seconds")
    output_tail = raw.get("output_tail")
    log_path = raw.get("log_path")
    if not isinstance(command, str) or not command:
        raise ProgressStateError("corrupt verification command")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise ProgressStateError("corrupt verification exit code")
    if not isinstance(duration, (int, float)) or isinstance(duration, bool):
        raise ProgressStateError("corrupt verification duration")
    if not isinstance(output_tail, str):
        raise ProgressStateError("corrupt verification output tail")
    if log_path is not None and not isinstance(log_path, str):
        raise ProgressStateError("corrupt verification log path")
    return VerificationEvidence(
        command=command,
        exit_code=exit_code,
        duration_seconds=float(duration),
        output_tail=output_tail,
        log_path=log_path,
    )


def _section_from_object(section_id: str, value: object) -> SectionProgress:
    if not isinstance(value, dict):
        raise ProgressStateError(f"corrupt section state: {section_id}")
    raw = cast(dict[str, object], value)
    status = raw.get("status")
    if status not in _ALLOWED_TRANSITIONS:
        raise ProgressStateError(f"corrupt section status: {section_id}")

    def optional_text(field_name: str) -> str | None:
        candidate = raw.get(field_name)
        if candidate is None:
            return None
        if not isinstance(candidate, str):
            raise ProgressStateError(
                f"corrupt section field {field_name}: {section_id}"
            )
        return candidate

    processes_value = raw.get("active_processes", [])
    if not isinstance(processes_value, list):
        raise ProgressStateError(f"corrupt active_processes: {section_id}")
    processes_raw = cast(list[object], processes_value)
    if any(not isinstance(item, str) for item in processes_raw):
        raise ProgressStateError(f"corrupt active_processes: {section_id}")
    verifications_value = raw.get("verifications", [])
    if not isinstance(verifications_value, list):
        raise ProgressStateError(f"corrupt verifications: {section_id}")
    verifications_raw = cast(list[object], verifications_value)
    return SectionProgress(
        section_id=section_id,
        status=status,
        baseline_head=optional_text("baseline_head"),
        baseline_status_fingerprint=optional_text("baseline_status_fingerprint"),
        worktree_path=optional_text("worktree_path"),
        branch=optional_text("branch"),
        writer_id=optional_text("writer_id"),
        writer_note=optional_text("writer_note"),
        active_processes=tuple(cast(str, item) for item in processes_raw),
        started_at=optional_text("started_at"),
        ended_at=optional_text("ended_at"),
        commit_hash=optional_text("commit_hash"),
        verifications=tuple(
            _verification_from_object(item) for item in verifications_raw
        ),
        note=optional_text("note"),
        next_action=optional_text("next_action"),
    )


def load_progress(
    *,
    repository_root: str | Path,
    plan: ParsedPlan,
) -> ProgressDocument | None:
    """Read progress without creating or modifying local state."""

    root = Path(repository_root).resolve()
    path = _progress_path(root, plan)
    if not path.is_file():
        return None
    try:
        raw_value: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProgressStateError("corrupt progress state") from exc
    if not isinstance(raw_value, dict):
        raise ProgressStateError("corrupt progress state")
    raw = cast(dict[str, object], raw_value)
    if raw.get("schema_version") != "qap.agent.progress.v1":
        raise ProgressStateError("corrupt or unsupported progress schema")
    plan_path = raw.get("plan_path")
    updated_at = raw.get("updated_at")
    sections_raw = raw.get("sections")
    if not isinstance(plan_path, str) or not isinstance(updated_at, str):
        raise ProgressStateError("corrupt progress metadata")
    if not isinstance(sections_raw, dict):
        raise ProgressStateError("corrupt progress sections")
    sections_mapping = cast(dict[str, object], sections_raw)
    expected_ids = {section.section_id for section in plan.sections}
    if set(sections_mapping) != expected_ids:
        raise ProgressStateError("corrupt progress section set")
    return ProgressDocument(
        schema_version="qap.agent.progress.v1",
        plan_path=plan_path,
        updated_at=updated_at,
        sections={
            section_id: _section_from_object(section_id, value)
            for section_id, value in sections_mapping.items()
        },
    )


def _document_dict(document: ProgressDocument) -> dict[str, object]:
    sections: dict[str, object] = {}
    for section_id, section in document.sections.items():
        raw = asdict(section)
        raw["verifications"] = [asdict(item) for item in section.verifications]
        raw["active_processes"] = list(section.active_processes)
        sections[section_id] = raw
    return {
        "schema_version": document.schema_version,
        "plan_path": document.plan_path,
        "updated_at": document.updated_at,
        "sections": sections,
    }


def _render_markdown(document: ProgressDocument, plan: ParsedPlan) -> str:
    title_by_id = {section.section_id: section.title for section in plan.sections}
    lines = [
        f"# Progress — {plan.title}",
        "",
        f"Plan: `{document.plan_path}`",
        f"Updated: `{document.updated_at}`",
        "",
        "| Section | Status | Commit | Next action |",
        "|---|---|---|---|",
    ]
    for section_id, section in document.sections.items():
        label = f"{section_id} {title_by_id.get(section_id, '')}".strip()
        lines.append(
            "| "
            + " | ".join(
                (
                    label.replace("|", "\\|"),
                    section.status,
                    section.commit_hash or "—",
                    (section.next_action or "—").replace("|", "\\|"),
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _write_progress(
    repository_root: Path,
    plan: ParsedPlan,
    document: ProgressDocument,
) -> None:
    encoded = json.dumps(
        _document_dict(document),
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
    )
    _atomic_write_text(_progress_path(repository_root, plan), encoded + "\n")
    _atomic_write_text(
        _markdown_path(repository_root, plan),
        _render_markdown(document, plan),
    )


def checkpoint_section(
    *,
    repository_root: str | Path,
    plan: ParsedPlan,
    section_id: str,
    status: SectionStatus,
    baseline_head: str | None = None,
    baseline_status_fingerprint: str | None = None,
    worktree_path: str | None = None,
    branch: str | None = None,
    writer_id: str | None = None,
    writer_note: str | None = None,
    active_processes: tuple[str, ...] | None = None,
    commit_hash: str | None = None,
    verifications: tuple[VerificationEvidence, ...] | None = None,
    note: str | None = None,
    next_action: str | None = None,
) -> ProgressDocument:
    """Persist one legal progress transition and regenerate its readable summary."""

    root = Path(repository_root).resolve()
    document = load_progress(repository_root=root, plan=plan) or _new_document(
        root, plan
    )
    try:
        current = document.sections[section_id]
    except KeyError as exc:
        raise ProgressStateError(f"unknown plan section: {section_id}") from exc
    if status not in _ALLOWED_TRANSITIONS[current.status]:
        raise ProgressStateError(
            f"illegal progress transition {current.status} -> {status} for {section_id}"
        )

    effective_verifications = (
        current.verifications if verifications is None else verifications
    )
    effective_commit = current.commit_hash if commit_hash is None else commit_hash
    if status == "in_progress":
        required = {
            "baseline_head": baseline_head or current.baseline_head,
            "baseline_status_fingerprint": (
                baseline_status_fingerprint or current.baseline_status_fingerprint
            ),
            "worktree_path": worktree_path or current.worktree_path,
            "branch": branch or current.branch,
            "writer_id": writer_id or current.writer_id,
        }
        missing = tuple(key for key, value in required.items() if not value)
        if missing:
            raise ProgressStateError(
                "in_progress checkpoint requires " + ", ".join(missing)
            )
    if status == "complete":
        latest_by_command = {item.command: item for item in effective_verifications}
        if not latest_by_command or any(
            item.exit_code != 0 for item in latest_by_command.values()
        ):
            raise ProgressStateError("complete requires passing verification evidence")
        if not effective_commit:
            raise ProgressStateError("complete requires a commit/reference")

    current.status = status
    current.baseline_head = baseline_head or current.baseline_head
    current.baseline_status_fingerprint = (
        baseline_status_fingerprint or current.baseline_status_fingerprint
    )
    current.worktree_path = worktree_path or current.worktree_path
    current.branch = branch or current.branch
    current.writer_id = writer_id or current.writer_id
    current.writer_note = (
        writer_note if writer_note is not None else current.writer_note
    )
    current.active_processes = (
        current.active_processes if active_processes is None else active_processes
    )
    current.commit_hash = effective_commit
    current.verifications = effective_verifications
    current.note = note if note is not None else current.note
    current.next_action = (
        next_action if next_action is not None else current.next_action
    )
    if status == "in_progress" and current.started_at is None:
        current.started_at = _utc_now()
    if status == "complete":
        current.ended_at = _utc_now()
    elif status in {"pending", "in_progress", "blocked"}:
        current.ended_at = None
    document.updated_at = _utc_now()
    _write_progress(root, plan, document)
    return document


__all__ = [
    "ProgressDocument",
    "ProgressStateError",
    "SectionProgress",
    "SectionStatus",
    "VerificationEvidence",
    "checkpoint_section",
    "load_progress",
]
