from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qap.experiment import RoleRun, execute_experiment, load_manifest

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/experiments/two_asset_dummy.json"


def _flow_schedule(role: RoleRun) -> tuple[tuple[str, str, str, Decimal], ...]:
    return tuple(
        (
            flow.flow_id,
            flow.effective_time.isoformat(),
            flow.asset.key,
            flow.quantity_delta,
        )
        for flow in role.trace.declared_flows
    )


def test_every_experiment_role_receives_byte_equivalent_external_flows() -> None:
    manifest = load_manifest(MANIFEST)
    run = execute_experiment(
        manifest,
        data_root=ROOT,
        repository_root=ROOT,
        run_timestamp=datetime(2026, 8, 17, 6, tzinfo=UTC),
    )
    expected = _flow_schedule(run.role("strategy"))

    assert expected == (
        ("deposit-1", "2024-01-01T03:00:00+00:00", "USDT", Decimal("100")),
    )
    for role in run.roles:
        assert _flow_schedule(role) == expected
        assert tuple(flow.flow_id for flow in role.trace.applied_flows) == (
            "deposit-1",
        )
        assert role.trace.starting_state == manifest.starting_state()
