# pyright: reportUnknownVariableType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownArgumentType=false

from pathlib import Path

from fastapi.testclient import TestClient


def test_health_is_read_only_and_cors_is_limited_to_configured_origin(
    tmp_path: Path,
) -> None:
    from qap.api import ApiSettings, create_app

    app = create_app(
        ApiSettings(
            run_root=tmp_path / "runs",
            allowed_origins=("http://localhost:5173",),
        )
    )
    client = TestClient(app)

    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "schema_version": "qap.api.health.v1",
        "status": "ok",
    }

    allowed = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"

    rejected = client.options(
        "/api/health",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in rejected.headers
