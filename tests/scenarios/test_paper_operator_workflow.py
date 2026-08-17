import json
from pathlib import Path

import pytest

from qap.experiment.paper_operation import (
    read_paper_operation_artifact,
    run_paper_operation_to_artifact,
)

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "tests/fixtures/paper/four_asset_forward_paper.json"
NO_FILL_SPEC = (
    ROOT / "tests/fixtures/paper/four_asset_forward_paper_precision_no_fill.json"
)


def test_forward_paper_operator_writes_reconciled_replayable_artifact(
    tmp_path: Path,
) -> None:
    artifact = run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=tmp_path / "paper-operations",
    )
    loaded = read_paper_operation_artifact(artifact.operation_file)

    assert loaded["schema_version"] == "qap.paper_operation.v1"
    assert loaded["operation_id"] == "forward-paper-three-asset-20260817"
    assert loaded["data_role"] == "forward_paper"
    assert loaded["reconciliation"]["matches"] is True
    assert loaded["bridge"] == "USDT"
    assert DecimalString(loaded["bridge_residual"]) >= 0
    assert len(loaded["orders"]) == 3
    assert [order["phase"] for order in loaded["orders"]] == [
        "sell_to_bridge",
        "sell_to_bridge",
        "buy_from_bridge",
    ]
    assert [order["asset"] for order in loaded["orders"]] == ["ETH", "SOL", "BTC"]
    assert all(order["route_id"].startswith("direct:") for order in loaded["orders"])
    assert len(loaded["fills"]) == 3
    assert all(DecimalString(fill["fee_quote"]) > 0 for fill in loaded["fills"])
    assert all(DecimalString(fill["slippage_quote"]) > 0 for fill in loaded["fills"])
    assert set(loaded["market_metadata"]) == {"BTCUSDT", "ETHUSDT", "SOLUSDT"}
    assert all(
        DecimalString(item["quantity_step"]) > 0
        for item in loaded["market_metadata"].values()
    )
    assert loaded["research_boundary"] == {
        "eligible_for_parameter_selection": False,
        "eligible_for_model_promotion": False,
        "eligible_for_deployment_evidence": False,
        "rule": (
            "Observed forward-paper outcomes are prospective operational evidence "
            "only; "
            "they cannot be retuned into or reused as deployment evidence."
        ),
    }


def test_forward_paper_operator_preserves_explicit_precision_no_fill(
    tmp_path: Path,
) -> None:
    artifact = run_paper_operation_to_artifact(
        NO_FILL_SPEC,
        repository_root=ROOT,
        output_root=tmp_path / "paper-operations",
    )
    loaded = read_paper_operation_artifact(artifact.operation_file)

    sol_order = next(item for item in loaded["orders"] if item["asset"] == "SOL")
    assert sol_order["phase"] == "sell_to_bridge"
    assert sol_order["leg_reason"] == "below_minimum_notional"
    assert sol_order["fill_ids"] == []
    assert loaded["reconciliation"]["matches"] is True
    assert DecimalString(loaded["bridge_residual"]) >= 0


def test_same_forward_paper_input_is_byte_reproducible_across_output_roots(
    tmp_path: Path,
) -> None:
    first = run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=tmp_path / "first",
    )
    second = run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=tmp_path / "second",
    )

    assert first.operation_file.read_bytes() == second.operation_file.read_bytes()


def test_operator_refuses_to_overwrite_existing_operation(tmp_path: Path) -> None:
    output_root = tmp_path / "paper-operations"
    run_paper_operation_to_artifact(
        SPEC,
        repository_root=ROOT,
        output_root=output_root,
    )

    with pytest.raises(FileExistsError, match="already exists"):
        run_paper_operation_to_artifact(
            SPEC,
            repository_root=ROOT,
            output_root=output_root,
        )


def test_forward_paper_spec_rejects_non_forward_role(tmp_path: Path) -> None:
    payload = json.loads(SPEC.read_text(encoding="utf-8"))
    payload["data_role"] = "development"
    spec = tmp_path / "invalid-role.json"
    spec.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="data_role must be forward_paper"):
        run_paper_operation_to_artifact(
            spec,
            repository_root=ROOT,
            output_root=tmp_path / "paper-operations",
        )


class DecimalString:
    def __init__(self, value: object) -> None:
        from decimal import Decimal

        if not isinstance(value, str):
            raise TypeError("expected exact decimal string")
        self.value = Decimal(value)

    def __gt__(self, other: int) -> bool:
        return self.value > other

    def __ge__(self, other: int) -> bool:
        return self.value >= other
