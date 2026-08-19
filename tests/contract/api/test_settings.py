from pathlib import Path

import pytest
from pydantic import ValidationError


def test_api_settings_default_to_loopback_and_reject_business_configuration(
    tmp_path: Path,
) -> None:
    from qap.api.settings import ApiSettings

    settings = ApiSettings(run_root=tmp_path / "runs")

    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.run_root == (tmp_path / "runs").resolve()
    assert settings.market_data_root is None
    assert settings.repository_root is None
    assert settings.capture_root is None
    assert settings.allowed_origins == (
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    )

    with pytest.raises(ValidationError, match="policy_id"):
        ApiSettings(run_root=tmp_path / "runs", policy_id="forbidden")  # type: ignore[call-arg]


def test_api_settings_environment_loader_reads_operational_values_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qap.api.settings import ApiSettings

    monkeypatch.setenv("QAP_API_RUN_ROOT", str(tmp_path / "runs"))
    monkeypatch.setenv("QAP_API_MARKET_DATA_ROOT", str(tmp_path / "market"))
    monkeypatch.setenv("QAP_API_REPOSITORY_ROOT", str(tmp_path / "repository"))
    monkeypatch.setenv("QAP_API_CAPTURE_ROOT", str(tmp_path / "capture"))
    monkeypatch.setenv("QAP_API_ALLOWED_ORIGINS", "http://localhost:4173")
    monkeypatch.setenv("QAP_API_HOST", "127.0.0.1")
    monkeypatch.setenv("QAP_API_PORT", "8123")

    settings = ApiSettings.from_environment()

    assert settings.run_root == (tmp_path / "runs").resolve()
    assert settings.market_data_root == (tmp_path / "market").resolve()
    assert settings.repository_root == (tmp_path / "repository").resolve()
    assert settings.capture_root == (tmp_path / "capture").resolve()
    assert settings.allowed_origins == ("http://localhost:4173",)
    assert settings.host == "127.0.0.1"
    assert settings.port == 8123


def test_api_settings_reject_non_local_mutation_surface(tmp_path: Path) -> None:
    from qap.api.settings import ApiSettings

    with pytest.raises(ValidationError, match="host must be loopback/local"):
        ApiSettings(run_root=tmp_path / "runs", host="0.0.0.0")
    with pytest.raises(ValidationError, match="wildcard origins"):
        ApiSettings(run_root=tmp_path / "runs", allowed_origins=("*",))
    with pytest.raises(ValidationError, match="loopback/local"):
        ApiSettings(
            run_root=tmp_path / "runs",
            allowed_origins=("https://example.com",),
        )
