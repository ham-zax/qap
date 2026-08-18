# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import ast
from pathlib import Path

from qap.scanner.artifact_schemas import PROMOTION_SCHEMA, SCOUT_SCHEMA

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "qap"


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            found.append(node.module)
    return tuple(found)


def test_scanner_core_has_no_outer_financial_imports() -> None:
    forbidden = ("qap.policy", "qap.execution", "qap.evaluation", "qap.experiment")
    violations: list[str] = []
    for path in sorted((SOURCE_ROOT / "scanner").glob("*.py")):
        if path.name == "cli.py":
            continue
        for imported in _imports(path):
            if imported.startswith(forbidden):
                violations.append(f"{path.name}: {imported}")
    assert violations == []


def test_financial_core_never_imports_scanner() -> None:
    violations: list[str] = []
    for package in (
        "policy",
        "execution",
        "evaluation",
        "relationship",
        "market",
        "portfolio",
    ):
        for path in sorted((SOURCE_ROOT / package).rglob("*.py")):
            for imported in _imports(path):
                if imported.startswith("qap.scanner"):
                    violations.append(f"{path.relative_to(SOURCE_ROOT)}: {imported}")
    assert violations == []


def test_experiment_scanner_dependency_is_limited_to_scanner_adapter() -> None:
    consumers: set[str] = set()
    for path in sorted((SOURCE_ROOT / "experiment").rglob("*.py")):
        if any(imported.startswith("qap.scanner") for imported in _imports(path)):
            consumers.add(path.name)
    assert consumers == {"scanner_adapter.py"}


def test_scanner_entry_is_the_outer_composition_root() -> None:
    entry_imports = _imports(SOURCE_ROOT / "scanner_entry.py")
    assert any(item.startswith("qap.experiment") for item in entry_imports)
    assert any(item.startswith("qap.scanner") for item in entry_imports)

    cli_imports = _imports(SOURCE_ROOT / "scanner" / "cli.py")
    assert not any(item.startswith("qap.experiment") for item in cli_imports)
    assert "qap.scanner_entry" in cli_imports


def test_scanner_adapter_never_imports_phase11_bridge_routing() -> None:
    path = SOURCE_ROOT / "experiment" / "scanner_adapter.py"
    imported = _imports(path)
    assert not any(
        item.startswith("qap.execution.multi_asset")
        or item.startswith("qap.execution.routing")
        for item in imported
    )
    source = path.read_text(encoding="utf-8")
    assert "build_rebalance_plan" not in source
    assert "execute_multi_asset_rebalance" not in source


def test_scanner_tables_do_not_copy_authoritative_financial_truth() -> None:
    forbidden = {
        "terminal_wealth",
        "starting_wealth",
        "hodl_wealth",
        "control_wealth",
        "terminal_quantities",
        "holdings",
        "fills",
        "fees_paid",
        "slippage_paid",
    }
    promotion_fields = set(PROMOTION_SCHEMA.names)
    scout_fields = set(SCOUT_SCHEMA.names)
    assert promotion_fields.isdisjoint(forbidden)
    assert scout_fields.isdisjoint(forbidden)
