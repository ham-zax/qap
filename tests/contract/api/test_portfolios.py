# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import json
from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).parents[3]
BASE_MANIFEST = REPOSITORY_ROOT / "tests/fixtures/experiments/two_asset_dummy.json"


def test_portfolio_snapshot_uses_persisted_inventory_and_exact_cost_strings(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/portfolios/{run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.portfolio_snapshot.v1"
    assert payload["run_id"] == run_id
    assert payload["starting"]["timestamp"] == "2024-01-01T01:00:00Z"
    assert payload["starting"]["role"] == "strategy"
    assert payload["starting"]["holdings"] == [
        {
            "asset": "BTC",
            "quantity": "1",
            "value": "4.205E+4",
            "weight": "0.97677119628339140534262485481997677119628339140534",
        },
        {
            "asset": "USDT",
            "quantity": "1E+3",
            "value": "1E+3",
            "weight": "0.023228803716608594657375145180023228803716608594657",
        },
    ]
    assert payload["terminal"]["holdings"][0]["quantity"] == (
        "0.25593119810201660735468564650059311981020166073547"
    )
    assert payload["hodl_terminal"]["holdings"][-1]["quantity"] == "1.1E+3"
    assert payload["strategy_costs"] == {
        "fill_count": 1,
        "fees_value": "31.34681874999999999999999999999999999999999999999993953025",
        "slippage_value": "15.68124999999999999999999999999999999999999999999996975",
        "turnover_value": "31346.81874999999999999999999999999999999999999999993953025",
    }
    selected = [item for item in payload["rebalance_audit"] if item["selected"]]
    assert len(selected) == 1
    assert selected[0]["decision_id"].endswith("2024-01-01T02:00:00+00:00")
    assert selected[0]["target_weights"] == {"BTC": "0.25", "USDT": "0.75"}
    assert selected[0]["evidence_ids"] == []
    assert selected[0]["fills"][0]["side"] == "sell"
    assert selected[0]["fills"][0]["fee_amount"] == (
        "31.34681874999999999999999999999999999999999999999993953025"
    )


def test_portfolio_starting_snapshot_is_pre_flow_and_pre_fill(tmp_path: Path) -> None:
    from qap.api import ApiSettings, create_app
    from qap.experiment import ExperimentManifest, run_experiment_to_artifacts

    raw = json.loads(BASE_MANIFEST.read_text(encoding="utf-8"))
    raw["experiment_name"] = "first decision starting snapshot"
    raw["external_flows"] = []
    raw["policy"]["config"] = {
        "schedule": [
            {
                "as_of": "2024-01-01T01:00:00Z",
                "weights": {"BTC": "0.25", "USDT": "0.75"},
            }
        ]
    }
    manifest = ExperimentManifest.model_validate(raw)
    run_root = tmp_path / "runs"
    paths = run_experiment_to_artifacts(
        manifest,
        data_root=REPOSITORY_ROOT,
        repository_root=REPOSITORY_ROOT,
        run_root=run_root,
    )
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/portfolios/{paths.run_id}")

    assert response.status_code == 200
    payload = response.json()
    starting_quantities = {
        item["asset"]: item["quantity"] for item in payload["starting"]["holdings"]
    }
    assert starting_quantities == {"BTC": "1", "USDT": "1E+3"}
    first_decision = payload["rebalance_audit"][0]
    assert first_decision["decision_time"] == "2024-01-01T01:00:00Z"
    assert first_decision["fills"]


def test_portfolio_exposes_all_roles_allocation_history_and_concentration(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/portfolios/{run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert [item["role"] for item in payload["role_terminals"]] == [
        "strategy",
        "hodl",
        "matched_contribution",
        "control:periodic-2",
        "control:band-5pct-half",
        "strategy:adverse_cost",
        "control:periodic-2:adverse_cost",
    ]
    assert len(payload["allocation_history"]) == 12
    assert payload["allocation_history"][0] == payload["starting"]
    assert payload["allocation_history"][-1] == payload["terminal"]
    concentration = payload["concentration"]
    assert (
        concentration["start_max_weight"]
        == payload["starting"]["holdings"][0]["weight"]
    )
    assert (
        concentration["terminal_max_weight"]
        == payload["terminal"]["holdings"][1]["weight"]
    )
    assert Decimal(concentration["start_herfindahl"]) > Decimal("0.9")
    assert Decimal(concentration["terminal_herfindahl"]) > Decimal("0.6")

    hodl_deltas = {
        item["asset"]: item for item in payload["strategy_vs_hodl_terminal_deltas"]
    }
    assert hodl_deltas["BTC"]["quantity_delta"] == (
        "-0.74406880189798339264531435349940688018979833926453"
    )
    assert hodl_deltas["USDT"]["quantity_delta"] == (
        "31315.47193124999999999999999999999999999999999999993959071975"
    )
    assert payload["strategy_vs_matched_contribution_terminal_deltas"] is not None


def test_rebalance_audit_exposes_decision_and_primary_control_context(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/portfolios/{run_id}")

    assert response.status_code == 200
    audits = response.json()["rebalance_audit"]
    selected = next(item for item in audits if item["selected"])
    assert selected["current_weights"] == {
        "BTC": "0.97682502896871378910776361529548088064889918887601",
        "USDT": "0.023174971031286210892236384704519119351100811123986",
    }
    assert selected["baseline_target_weights"] is None
    assert selected["modeled_fee_bps"] == "10"
    assert selected["modeled_slippage_bps"] == "5"

    control_target = next(
        item for item in audits if item["decision_time"] == "2024-01-01T03:00:00Z"
    )
    assert control_target["baseline_target_weights"] == {
        "BTC": "0.97677119628339140534262485481997677119628339140534",
        "USDT": "0.02322880371660859465737514518002322880371660859466",
    }


def test_portfolio_performance_projects_authoritative_exact_series(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/portfolios/{run_id}/performance")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.portfolio_performance.v1"
    assert payload["run_id"] == run_id
    assert payload["primary_incremental_benchmark"] == "periodic-2"
    assert payload["maximum_relative_drawdown_vs_hodl"] == (
        "0.01787789538187533090723874245196399729242482122632"
    )
    assert payload["time_below_hodl_seconds"] == 36_000
    assert payload["time_below_primary_control_seconds"] == 36_000
    series = {item["name"]: item["points"] for item in payload["series"]}
    assert series["value::strategy"][-1]["value"] == (
        "43458.90312935201660735468564650059311981020166073547009071975"
    )
    assert series["value::hodl"][-1]["value"] == "4.425E+4"
    assert series["relative::strategy_vs_hodl"][-1]["value"] == (
        "-0.01787789538187533090723874245196399729242482122632"
    )
    assert series["relative::strategy_vs_primary_control"][-1]["value"] == (
        "-0.017914217800326623022828241313706705883140291947"
    )
    assert series["log_relative::strategy_vs_hodl"][0]["value"] == "0"
    assert series["log_relative::strategy_vs_primary_control"][0]["value"] == "0"
