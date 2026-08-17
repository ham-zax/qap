import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qap.execution import Fill
from qap.experiment import ExperimentManifest, execute_experiment

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"
RUN_AT = datetime(2026, 8, 17, 6, tzinfo=UTC)


def _data() -> dict[str, object]:
    value: object = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("manifest fixture must be an object")
    return cast(dict[str, object], value)


def _fill_economics(fill: Fill) -> tuple[object, ...]:
    return (
        fill.decision_id,
        fill.execution_timestamp,
        fill.instrument,
        fill.side,
        fill.reference_price,
        fill.execution_price,
        fill.base_quantity,
        fill.gross_quote_notional,
        fill.fee_amount,
        fill.fee_asset,
        fill.slippage_value,
        dict(fill.balance_deltas),
    )


def test_data_role_changes_provenance_but_not_financial_calculation() -> None:
    development_data = _data()
    exploratory_data = _data()
    exploratory_data["data_role"] = "exploratory"
    exploratory_data["experiment_name"] = "exploratory role invariant"
    development = execute_experiment(
        ExperimentManifest.model_validate(development_data),
        data_root=ROOT,
        repository_root=ROOT,
        run_timestamp=RUN_AT,
    )
    exploratory = execute_experiment(
        ExperimentManifest.model_validate(exploratory_data),
        data_root=ROOT,
        repository_root=ROOT,
        run_timestamp=RUN_AT,
    )

    assert development.provenance.run_id != exploratory.provenance.run_id
    assert (
        development.provenance.manifest_sha256 != exploratory.provenance.manifest_sha256
    )
    assert (
        development.provenance.code_fingerprint
        == exploratory.provenance.code_fingerprint
    )
    assert (
        development.provenance.data_fingerprints
        == exploratory.provenance.data_fingerprints
    )
    assert (
        development.result.primary_metric_value
        == exploratory.result.primary_metric_value
    )
    assert development.result.status == exploratory.result.status
    for left in development.roles:
        right = exploratory.role(left.role)
        assert left.values == right.values
        assert left.unitized_nav == right.unitized_nav
        assert left.trace.ending_state == right.trace.ending_state
        assert tuple(_fill_economics(fill) for fill in left.trace.fills) == tuple(
            _fill_economics(fill) for fill in right.trace.fills
        )
        if left.trace.fills:
            assert tuple(fill.fill_id for fill in left.trace.fills) != tuple(
                fill.fill_id for fill in right.trace.fills
            )
