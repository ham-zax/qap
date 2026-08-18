"""Immutable current-schema scanner identity records."""

import json
import re
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from qap.portfolio import AssetId
from qap.scanner.protocol import SCANNER_V1_SLICE1, ScannerHorizon

_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


def _non_empty(value: str, *, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _fingerprint(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if _FINGERPRINT.fullmatch(normalized) is None:
        raise ValueError(f"{field} must be a 64-character SHA-256 hex fingerprint")
    return normalized


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError(f"{field} must be timezone-aware UTC")
    return value.astimezone(UTC)


class _FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)


class ScannerPinSpec(_FrozenModel):
    venue: str
    asset_a: str
    asset_b: str
    horizons: tuple[ScannerHorizon, ...]
    forensic: bool

    @field_validator("venue")
    @classmethod
    def validate_venue(cls, value: str) -> str:
        normalized = _non_empty(value, field="venue").lower()
        if normalized not in SCANNER_V1_SLICE1.venues:
            raise ValueError("venue is not admitted by scanner-v1-s1")
        return normalized

    @field_validator("asset_a", "asset_b")
    @classmethod
    def validate_asset(cls, value: str) -> str:
        return AssetId(value).key

    @field_validator("horizons")
    @classmethod
    def validate_pin_horizons(
        cls, values: tuple[ScannerHorizon, ...]
    ) -> tuple[ScannerHorizon, ...]:
        if not values:
            raise ValueError("horizons must not be empty")
        if len(set(values)) != len(values):
            raise ValueError("horizons must not contain duplicates")
        order = {
            ScannerHorizon.SHORT: 0,
            ScannerHorizon.MEDIUM: 1,
            ScannerHorizon.SWING: 2,
        }
        return tuple(sorted(values, key=order.__getitem__))

    @model_validator(mode="after")
    def canonicalize_pair(self) -> Self:
        if self.asset_a == self.asset_b:
            raise ValueError("pin assets must be distinct")
        first, second = sorted((self.asset_a, self.asset_b))
        object.__setattr__(self, "asset_a", first)
        object.__setattr__(self, "asset_b", second)
        return self

    def semantic_tokens(self) -> tuple[str, ...]:
        mode = "forensic" if self.forensic else "official"
        return tuple(
            f"{self.venue}:{self.asset_a}/{self.asset_b}:{horizon.value}:{mode}"
            for horizon in self.horizons
        )


class ScannerPinsFile(_FrozenModel):
    schema_version: Literal["qap.scanner.pins.v1"]
    pins: tuple[ScannerPinSpec, ...]

    @model_validator(mode="after")
    def validate_duplicates(self) -> Self:
        seen: set[tuple[str, str, str, ScannerHorizon]] = set()
        for pin in self.pins:
            for horizon in pin.horizons:
                identity = (pin.venue, pin.asset_a, pin.asset_b, horizon)
                if identity in seen:
                    raise ValueError("duplicate normalized pin for venue/pair/horizon")
                seen.add(identity)
        return self


class ScanInputIdentity(_FrozenModel):
    dataset_id: str
    source_artifact_fingerprint: str
    selection_slice_fingerprint: str

    @field_validator("dataset_id")
    @classmethod
    def validate_dataset_id(cls, value: str) -> str:
        return _non_empty(value, field="dataset_id")

    @field_validator("source_artifact_fingerprint", "selection_slice_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "fingerprint")
        return _fingerprint(value, field=field_name)


class ScanDefinition(_FrozenModel):
    schema_version: Literal["qap.scanner.definition.v1"] = "qap.scanner.definition.v1"
    scanner_protocol_version: str
    protocol_identity: str
    catalog_identity: str
    as_of: datetime
    eligible_information_end: datetime
    venues: tuple[str, ...]
    horizons: tuple[ScannerHorizon, ...]
    input_slices: tuple[ScanInputIdentity, ...]
    manual_inputs: tuple[str, ...] = ()
    created_at: datetime

    @field_validator("scanner_protocol_version")
    @classmethod
    def validate_protocol_version(cls, value: str) -> str:
        return _non_empty(value, field="scanner_protocol_version")

    @field_validator("protocol_identity", "catalog_identity")
    @classmethod
    def validate_identity_fingerprint(cls, value: str, info: object) -> str:
        field_name = getattr(info, "field_name", "identity")
        return _fingerprint(value, field=field_name)

    @field_validator("as_of", "eligible_information_end", "created_at")
    @classmethod
    def validate_utc(cls, value: datetime, info: object) -> datetime:
        field_name = getattr(info, "field_name", "timestamp")
        return _utc(value, field=field_name)

    @field_validator("venues")
    @classmethod
    def validate_venues(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(_non_empty(value, field="venue").lower() for value in values)
        if not normalized:
            raise ValueError("venues must not be empty")
        if len(set(normalized)) != len(normalized):
            raise ValueError("venues must be unique")
        return normalized

    @field_validator("horizons")
    @classmethod
    def validate_horizons(
        cls, values: tuple[ScannerHorizon, ...]
    ) -> tuple[ScannerHorizon, ...]:
        if not values:
            raise ValueError("horizons must not be empty")
        if len(set(values)) != len(values):
            raise ValueError("horizons must be unique")
        return values

    @field_validator("manual_inputs")
    @classmethod
    def validate_manual_inputs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_non_empty(value, field="manual input") for value in values)

    @model_validator(mode="after")
    def validate_cutoff(self) -> Self:
        if self.eligible_information_end > self.as_of:
            raise ValueError("eligible_information_end must not exceed as_of")
        slice_identities = tuple(
            (
                item.dataset_id,
                item.source_artifact_fingerprint,
                item.selection_slice_fingerprint,
            )
            for item in self.input_slices
        )
        if len(set(slice_identities)) != len(slice_identities):
            raise ValueError("input_slices must be unique exact slice identities")
        return self

    @property
    def scan_id(self) -> str:
        payload = {
            "schema_version": self.schema_version,
            "scanner_protocol_version": self.scanner_protocol_version,
            "protocol_identity": self.protocol_identity,
            "catalog_identity": self.catalog_identity,
            "as_of": self.as_of.isoformat(),
            "eligible_information_end": self.eligible_information_end.isoformat(),
            "venues": sorted(self.venues),
            "horizons": sorted(item.value for item in self.horizons),
            "input_slices": [
                item.model_dump(mode="json")
                for item in sorted(
                    self.input_slices,
                    key=lambda value: (
                        value.dataset_id,
                        value.source_artifact_fingerprint,
                        value.selection_slice_fingerprint,
                    ),
                )
            ],
            "manual_inputs": sorted(self.manual_inputs),
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


__all__ = [
    "ScanDefinition",
    "ScanInputIdentity",
    "ScannerPinSpec",
    "ScannerPinsFile",
]
