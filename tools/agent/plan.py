"""Parse explicitly approved QAP implementation plans into bounded sections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SECTION = re.compile(
    r"^## Section (?P<section_id>\d+\.\d+)\s+(?:—|-)\s+(?P<title>.+?)\s*$",
    re.MULTILINE,
)
_TITLE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)


class PlanParseError(ValueError):
    """Raised when an explicit plan does not match the supported QAP grammar."""


@dataclass(frozen=True, slots=True)
class PlanSection:
    """One bounded section from an approved repository plan."""

    section_id: str
    title: str
    body: str


@dataclass(frozen=True, slots=True)
class ParsedPlan:
    """Parsed approved plan plus its repository ownership boundary."""

    path: Path
    repository_root: Path
    title: str
    sections: tuple[PlanSection, ...]

    def section(self, section_id: str) -> PlanSection:
        for section in self.sections:
            if section.section_id == section_id:
                return section
        raise PlanParseError(f"plan has no section {section_id}")


def _repository_root(path: Path) -> Path:
    for candidate in (path.parent, *path.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    raise PlanParseError(f"plan is not inside a Git repository: {path}")


def _assert_approved_path(path: Path, repository_root: Path) -> None:
    try:
        relative = path.relative_to(repository_root)
    except ValueError as exc:
        raise PlanParseError("plan is outside its repository") from exc
    parts = relative.parts
    approved = parts[:2] == ("docs", "plans") or parts[:3] == (
        "docs",
        "superpowers",
        "plans",
    )
    if not approved:
        raise PlanParseError(
            "plan must be an approved plan path under docs/plans or "
            "docs/superpowers/plans"
        )


def parse_plan(path: str | Path) -> ParsedPlan:
    """Parse one explicitly supplied plan without discovering alternatives."""

    plan_path = Path(path).resolve()
    if not plan_path.is_file():
        raise PlanParseError(f"plan does not exist: {plan_path}")
    repository_root = _repository_root(plan_path)
    _assert_approved_path(plan_path, repository_root)
    text = plan_path.read_text(encoding="utf-8")
    title_match = _TITLE.search(text)
    if title_match is None:
        raise PlanParseError("plan must have one top-level title")

    matches = tuple(_SECTION.finditer(text))
    if not matches:
        raise PlanParseError("plan contains no supported Section headings")

    sections: list[PlanSection] = []
    seen: set[str] = set()
    for index, match in enumerate(matches):
        section_id = match.group("section_id")
        if section_id in seen:
            raise PlanParseError(f"duplicate section id: {section_id}")
        seen.add(section_id)
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append(
            PlanSection(
                section_id=section_id,
                title=match.group("title").strip(),
                body=text[body_start:body_end].strip(),
            )
        )

    return ParsedPlan(
        path=plan_path,
        repository_root=repository_root,
        title=title_match.group("title").strip(),
        sections=tuple(sections),
    )


__all__ = ["ParsedPlan", "PlanParseError", "PlanSection", "parse_plan"]
