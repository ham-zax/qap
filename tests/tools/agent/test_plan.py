from pathlib import Path

import pytest

from tools.agent.plan import PlanParseError, parse_plan

ROOT = Path(__file__).resolve().parents[3]
PHASE13 = ROOT / "docs/plans/13-autonomous-development-harness.md"


def test_parser_reads_actual_qap_sections_in_order() -> None:
    plan = parse_plan(PHASE13)

    assert plan.path == PHASE13.resolve()
    assert (
        plan.title
        == "Phase 13 — Sequential Autonomous Development Harness Implementation Plan"
    )
    assert tuple(section.section_id for section in plan.sections[:3]) == (
        "13.1",
        "13.2",
        "13.3",
    )
    assert plan.sections[-1].section_id == "13.11"
    assert plan.sections[-1].title == "Dry Run"
    assert "## Phase Verification" in plan.sections[-1].body
    assert "## Phase Exit Criteria" in plan.sections[-1].body
    assert "## Stop Conditions" in plan.sections[-1].body


def test_parser_returns_one_requested_bounded_section() -> None:
    plan = parse_plan(PHASE13)

    section = plan.section("13.6")

    assert section.title == "Verification Runner"
    assert "subprocess execution with timeout" in section.body
    assert "Section 13.7" not in section.body


def test_parser_rejects_duplicate_section_ids(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    plan_path = repository / "docs/plans/bad.md"
    plan_path.parent.mkdir(parents=True)
    (repository / ".git").mkdir()
    plan_path.write_text(
        "# Bad plan\n\n## Section 13.1 — One\nA\n\n## Section 13.1 — Two\nB\n",
        encoding="utf-8",
    )

    with pytest.raises(PlanParseError, match="duplicate section"):
        parse_plan(plan_path)


def test_parser_rejects_document_outside_approved_plan_roots(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    document = repository / "docs/research/not-a-plan.md"
    document.parent.mkdir(parents=True)
    (repository / ".git").mkdir()
    document.write_text("# Not a plan\n\n## Section 13.1 — Nope\n", encoding="utf-8")

    with pytest.raises(PlanParseError, match="approved plan path"):
        parse_plan(document)
