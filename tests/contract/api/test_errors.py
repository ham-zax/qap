# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

from pathlib import Path

from fastapi.testclient import TestClient


def test_missing_run_uses_stable_error_envelope(tmp_path: Path) -> None:
    from qap.api import ApiSettings, create_app

    client = TestClient(create_app(ApiSettings(run_root=tmp_path / "runs")))
    response = client.get("/api/experiments/run-000000000000000000000000")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "run_not_found",
            "message": "Run was not found.",
            "context": {"run_id": "run-000000000000000000000000"},
        }
    }


def test_corrupt_run_uses_distinct_error_without_path_leak(tmp_path: Path) -> None:
    from qap.api import ApiSettings, create_app

    run_id = "run-111111111111111111111111"
    run_root = tmp_path / "runs"
    directory = run_root / run_id
    directory.mkdir(parents=True)
    (directory / "result.json").write_text("{broken", encoding="utf-8")

    client = TestClient(create_app(ApiSettings(run_root=run_root)))
    response = client.get(f"/api/experiments/{run_id}")

    assert response.status_code == 409
    payload = response.json()
    assert payload["error"]["code"] == "corrupt_artifact"
    assert payload["error"]["message"] == "Run artifacts are invalid."
    assert payload["error"]["context"] == {"run_id": run_id}
    assert str(tmp_path) not in response.text
