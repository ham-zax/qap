# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

import json
from pathlib import Path

from fastapi.testclient import TestClient

_PRIMARY_INCREMENT = "-0.017914217800326623022828241313706705883140291947"
_MATCHED_CONTRIBUTION_INCREMENT = (
    "-0.01792075695329660828265582124373519119375441572932"
)


def test_experiment_list_preserves_research_and_benchmark_context(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get("/api/experiments")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["items"][0]["git_dirty"], bool)
    payload["items"][0]["git_dirty"] = None
    assert payload == {
        "schema_version": "qap.api.experiment_list.v1",
        "items": [
            {
                "artifact_status": "valid",
                "run_id": run_id,
                "experiment_name": "two-asset dummy",
                "research_family_id": "family-two-asset-v1",
                "parent_run_id": None,
                "universe_mode": "declared_fixed_basket",
                "basket": ["BTC", "USDT"],
                "analysis_anchor": "USDT",
                "relationship_id": "none",
                "policy_id": "scheduled_target",
                "data_role": "development",
                "final_oos_consumed": False,
                "status": "negative",
                "primary_metric": "primary_control_relative_terminal_wealth",
                "primary_metric_value": _PRIMARY_INCREMENT,
                "primary_incremental_benchmark": "periodic-2",
                "incremental_vs_primary_control": _PRIMARY_INCREMENT,
                "incremental_vs_matched_contribution": _MATCHED_CONTRIBUTION_INCREMENT,
                "created_timestamp": "2026-08-17T06:00:00Z",
                "git_dirty": None,
                "family_attempt_count": 1,
                "error": None,
            }
        ],
    }


def test_experiment_list_surfaces_corrupt_artifact_without_hiding_valid_runs(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, valid_run_id = populated_run_root
    corrupt_run_id = "run-222222222222222222222222"
    corrupt = run_root / corrupt_run_id
    corrupt.mkdir()
    (corrupt / "result.json").write_text("{broken", encoding="utf-8")

    client = TestClient(create_app(ApiSettings(run_root=run_root)))
    response = client.get("/api/experiments")

    assert response.status_code == 200
    items = {item["run_id"]: item for item in response.json()["items"]}
    assert set(items) == {valid_run_id, corrupt_run_id}
    assert items[valid_run_id]["artifact_status"] == "valid"
    assert items[corrupt_run_id] == {
        "artifact_status": "invalid",
        "run_id": corrupt_run_id,
        "experiment_name": None,
        "research_family_id": None,
        "parent_run_id": None,
        "universe_mode": None,
        "basket": None,
        "analysis_anchor": None,
        "relationship_id": None,
        "policy_id": None,
        "data_role": None,
        "final_oos_consumed": None,
        "status": None,
        "primary_metric": None,
        "primary_metric_value": None,
        "primary_incremental_benchmark": None,
        "incremental_vs_primary_control": None,
        "incremental_vs_matched_contribution": None,
        "created_timestamp": None,
        "git_dirty": None,
        "family_attempt_count": None,
        "error": {
            "code": "corrupt_artifact",
            "message": "Run artifacts are invalid.",
            "context": {"run_id": corrupt_run_id},
        },
    }


def test_family_attempt_count_includes_failed_attempts_with_recoverable_lineage(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, valid_run_id = populated_run_root
    failed_run_id = "run-222222222222222222222222"
    failed = run_root / failed_run_id
    failed.mkdir()
    manifest = json.loads(
        (run_root / valid_run_id / "manifest.json").read_text(encoding="utf-8")
    )
    manifest["experiment_name"] = "failed sibling attempt"
    manifest["parent_run_id"] = valid_run_id
    (failed / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    (failed / "failure.json").write_text(
        json.dumps({"error_type": "RuntimeError", "message": "deliberate"}) + "\n",
        encoding="utf-8",
    )

    client = TestClient(create_app(ApiSettings(run_root=run_root)))
    listing = client.get("/api/experiments")
    detail = client.get(f"/api/experiments/{valid_run_id}")

    assert listing.status_code == 200
    items = {item["run_id"]: item for item in listing.json()["items"]}
    assert items[valid_run_id]["family_attempt_count"] == 2
    assert items[failed_run_id]["artifact_status"] == "invalid"
    assert items[failed_run_id]["experiment_name"] == "failed sibling attempt"
    assert items[failed_run_id]["research_family_id"] == "family-two-asset-v1"
    assert items[failed_run_id]["parent_run_id"] == valid_run_id
    assert items[failed_run_id]["family_attempt_count"] == 2
    assert detail.status_code == 200
    assert detail.json()["family_attempt_count"] == 2


def test_experiment_detail_exposes_manifest_provenance_result_and_family_attempt_count(
    populated_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = populated_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/experiments/{run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "qap.api.experiment_detail.v1"
    assert payload["run_id"] == run_id
    assert payload["family_attempt_count"] == 1
    assert payload["available_pairs"] == [["BTC", "USDT"]]
    assert payload["manifest"]["experiment_name"] == "two-asset dummy"
    assert payload["manifest"]["universe_mode"] == "declared_fixed_basket"
    assert (
        payload["manifest"]["benchmarks"]["primary_incremental_benchmark"]
        == "periodic-2"
    )
    assert payload["provenance"]["run_id"] == run_id
    assert isinstance(payload["provenance"]["git_dirty"], bool)
    assert payload["result"]["data_role"] == "development"
    assert payload["result"]["final_oos_consumed"] is False
    assert payload["final_oos_commitment"] is None
    series = {item["name"]: item for item in payload["available_series"]}
    assert series["performance"]["schema_version"] == "qap.experiment.performance.v1"
    assert "relative::strategy_vs_primary_control" in series["performance"]["columns"]
    assert series["inventory"]["schema_version"] == "qap.experiment.inventory.v1"
    assert series["inventory"]["columns"] == [
        "timestamp",
        "role",
        "asset",
        "quantity",
        "value",
        "weight",
    ]
    assert payload["result"]["strategy_vs_primary_control"] == _PRIMARY_INCREMENT


def test_final_oos_detail_exposes_consumed_commitment(
    final_oos_run_root: tuple[Path, str],
) -> None:
    from qap.api import ApiSettings, create_app

    run_root, run_id = final_oos_run_root
    client = TestClient(create_app(ApiSettings(run_root=run_root)))

    response = client.get(f"/api/experiments/{run_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["data_role"] == "final_oos"
    assert payload["result"]["final_oos_consumed"] is True
    commitment = payload["final_oos_commitment"]
    assert commitment["run_id"] == run_id
    assert commitment["research_family_id"] == "family-api-final-oos-v1"
    assert commitment["consumed"] is True
    assert commitment["execution_status"] == "completed"
    assert commitment["consumed_at"] is not None
