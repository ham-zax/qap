"""Normalized public-market evidence bundle shared by capture consumers."""

from dataclasses import dataclass

from qap.market.microstructure import PublicBookSnapshot, PublicMarketMetadataSnapshot


@dataclass(frozen=True, slots=True)
class PublicEvidenceBundle:
    """Normalized public evidence with no storage or scientific-policy semantics."""

    l1: tuple[PublicBookSnapshot, ...] = ()
    depth: tuple[PublicBookSnapshot, ...] = ()
    metadata: tuple[PublicMarketMetadataSnapshot, ...] = ()


__all__ = ["PublicEvidenceBundle"]
