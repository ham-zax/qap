"""Bounded persisted Product authority for transient research-replay bridges."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from threading import Lock
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from qap.portfolio import AssetId
from qap.product_universe import ProductUniverse

_TRANSIENT_BRIDGE = AssetId("USDT")


class ProductResearchAuthorityError(RuntimeError):
    """Raised when transient research authority cannot be represented safely."""


class ProductResearchAuthorityState(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["qap.product.research-authority.v1"] = (
        "qap.product.research-authority.v1"
    )
    transient_bridge_asset: str | None = None
    transient_bridge_identity_version: str | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_bridge_identity(self) -> "ProductResearchAuthorityState":
        paired = (
            self.transient_bridge_asset is None,
            self.transient_bridge_identity_version is None,
        )
        if paired[0] != paired[1]:
            raise ValueError(
                "transient bridge asset and identity version must be paired"
            )
        if self.transient_bridge_asset is not None:
            if AssetId(self.transient_bridge_asset) != _TRANSIENT_BRIDGE:
                raise ValueError(
                    "only canonical USDT may be admitted as research bridge"
                )
        return self


class ProductResearchAuthority:
    """Own one explicit research-only permission without changing asset admission."""

    def __init__(self, universe: ProductUniverse) -> None:
        self._universe = universe
        self._path = universe.root / "research-authority.json"
        self._lock = Lock()

    def _read(self) -> ProductResearchAuthorityState:
        if not self._path.is_file():
            return ProductResearchAuthorityState()
        try:
            return ProductResearchAuthorityState.model_validate_json(
                self._path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise ProductResearchAuthorityError(
                "Product research authority state is invalid."
            ) from exc

    def _current_bridge_identity_version(self) -> str:
        state = self._universe.read_state()
        versions = {
            mapping.asset_identity_version
            for mapping in state.identity_mappings
            if AssetId(mapping.canonical_asset_id) == _TRANSIENT_BRIDGE
        }
        if len(versions) != 1:
            raise ProductResearchAuthorityError(
                "Canonical USDT identity must be explicitly resolved before "
                "bridge authority."
            )
        return next(iter(versions))

    def allows_transient_bridge(self, asset: AssetId = _TRANSIENT_BRIDGE) -> bool:
        if asset != _TRANSIENT_BRIDGE:
            return False
        try:
            current_version = self._current_bridge_identity_version()
        except ProductResearchAuthorityError:
            return False
        state = self._read()
        return (
            state.transient_bridge_asset == _TRANSIENT_BRIDGE.key
            and state.transient_bridge_identity_version == current_version
        )

    def grant_transient_usdt_bridge(self) -> ProductResearchAuthorityState:
        """Persist research-replay-only USDT bridge authority for current identity."""

        version = self._current_bridge_identity_version()
        next_state = ProductResearchAuthorityState(
            transient_bridge_asset=_TRANSIENT_BRIDGE.key,
            transient_bridge_identity_version=version,
            updated_at=datetime.now(UTC),
        )
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._path.with_name(f".{self._path.name}.tmp-{os.getpid()}")
            payload = (next_state.model_dump_json(indent=2) + "\n").encode("utf-8")
            with temporary.open("wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self._path)
        return next_state


__all__ = [
    "ProductResearchAuthority",
    "ProductResearchAuthorityError",
    "ProductResearchAuthorityState",
]
