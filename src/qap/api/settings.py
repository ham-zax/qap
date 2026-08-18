"""Operational-only settings for the local read-only API boundary."""

import os
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DEFAULT_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)


class ApiSettings(BaseModel):
    """Local API process settings; business/research configuration is excluded."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_root: Path
    market_data_root: Path | None = None
    repository_root: Path | None = None
    capture_root: Path | None = None
    allowed_origins: tuple[str, ...] = _DEFAULT_ORIGINS
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    @field_validator(
        "run_root",
        "market_data_root",
        "repository_root",
        "capture_root",
    )
    @classmethod
    def resolve_paths(cls, value: Path | None) -> Path | None:
        return None if value is None else value.expanduser().resolve()

    @field_validator("allowed_origins")
    @classmethod
    def validate_origins(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(origin.strip() for origin in value if origin.strip())
        if not normalized:
            raise ValueError("allowed_origins must contain at least one origin")
        for origin in normalized:
            if origin == "*":
                raise ValueError("wildcard origins are not allowed")
            parsed = urlparse(origin)
            host = parsed.hostname
            if parsed.scheme not in {"http", "https"} or host is None:
                raise ValueError("allowed origins must be HTTP(S) loopback URLs")
            if host == "localhost":
                continue
            try:
                loopback = ip_address(host).is_loopback
            except ValueError as exc:
                raise ValueError("allowed origins must be loopback/local") from exc
            if not loopback:
                raise ValueError("allowed origins must be loopback/local")
        return normalized

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("host must not be empty")
        if normalized == "localhost":
            return normalized
        try:
            loopback = ip_address(normalized).is_loopback
        except ValueError as exc:
            raise ValueError("host must be loopback/local") from exc
        if not loopback:
            raise ValueError("host must be loopback/local")
        return normalized

    @classmethod
    def from_environment(cls) -> "ApiSettings":
        """Load launch-only path/network overrides from dedicated environment keys."""

        run_root = os.environ.get("QAP_API_RUN_ROOT", "runs")
        market_data_root = os.environ.get("QAP_API_MARKET_DATA_ROOT")
        repository_root = os.environ.get("QAP_API_REPOSITORY_ROOT", ".")
        capture_root = os.environ.get("QAP_API_CAPTURE_ROOT")
        raw_origins = os.environ.get("QAP_API_ALLOWED_ORIGINS")
        allowed_origins = (
            tuple(item.strip() for item in raw_origins.split(",") if item.strip())
            if raw_origins is not None
            else _DEFAULT_ORIGINS
        )
        return cls(
            run_root=Path(run_root),
            market_data_root=(
                None if market_data_root is None else Path(market_data_root)
            ),
            repository_root=Path(repository_root),
            capture_root=(None if capture_root is None else Path(capture_root)),
            allowed_origins=allowed_origins,
            host=os.environ.get("QAP_API_HOST", "127.0.0.1"),
            port=int(os.environ.get("QAP_API_PORT", "8000")),
        )


__all__ = ["ApiSettings"]
