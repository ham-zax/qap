"""Explicit scanner scope binding for Product current-approved research."""

from dataclasses import dataclass

from qap.portfolio import AssetId

CURRENT_APPROVED_UNIVERSE_POLICY_VERSION = (
    "product-current-approved-current-survivor-v1"
)


def _fingerprint(value: str, *, field: str) -> str:
    normalized = value.strip().lower()
    if len(normalized) != 64 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise ValueError(f"{field} must be a 64-character SHA-256 fingerprint")
    return normalized


@dataclass(frozen=True, slots=True)
class CurrentApprovedScanScope:
    """Freeze one Product-approved asset scope against one current catalog state."""

    research_claim_identity: str
    scope_identity: str
    expected_catalog_identity: str
    assets_by_venue: tuple[tuple[str, tuple[str, ...]], ...]
    dataset_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "research_claim_identity",
            _fingerprint(
                self.research_claim_identity,
                field="research_claim_identity",
            ),
        )
        object.__setattr__(
            self,
            "scope_identity",
            _fingerprint(self.scope_identity, field="scope_identity"),
        )
        object.__setattr__(
            self,
            "expected_catalog_identity",
            _fingerprint(
                self.expected_catalog_identity,
                field="expected_catalog_identity",
            ),
        )
        normalized_rows: list[tuple[str, tuple[str, ...]]] = []
        seen_venues: set[str] = set()
        for venue, assets in self.assets_by_venue:
            normalized_venue = venue.strip().lower()
            if not normalized_venue or normalized_venue in seen_venues:
                raise ValueError("assets_by_venue must use unique non-empty venues")
            seen_venues.add(normalized_venue)
            normalized_assets = tuple(sorted({AssetId(asset).key for asset in assets}))
            if not normalized_assets:
                raise ValueError("current-approved venue scope must contain assets")
            normalized_rows.append((normalized_venue, normalized_assets))
        if not normalized_rows:
            raise ValueError("current-approved scanner scope must contain a venue")
        object.__setattr__(
            self,
            "assets_by_venue",
            tuple(sorted(normalized_rows, key=lambda item: item[0])),
        )
        normalized_datasets = tuple(
            sorted({value.strip() for value in self.dataset_ids if value.strip()})
        )
        if not normalized_datasets:
            raise ValueError("current-approved scanner scope must contain dataset IDs")
        object.__setattr__(self, "dataset_ids", normalized_datasets)

    def assets_for(self, venue: str) -> frozenset[str]:
        normalized = venue.strip().lower()
        for candidate, assets in self.assets_by_venue:
            if candidate == normalized:
                return frozenset(assets)
        return frozenset()

    @property
    def datasets(self) -> frozenset[str]:
        return frozenset(self.dataset_ids)


__all__ = [
    "CURRENT_APPROVED_UNIVERSE_POLICY_VERSION",
    "CurrentApprovedScanScope",
]
