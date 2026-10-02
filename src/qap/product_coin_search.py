"""Read-only discovery from venue listings and supplemental identity evidence."""

import re
from dataclasses import asdict
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from qap.asset_registry import RegistrySnapshot
from qap.asset_resolver import AssetResolutionProposal, AssetResolver
from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import DirectoryMarket, ProductMarketDirectory, Venue
from qap.product_universe_models import ProductUniverseState


class ResearchCoin(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    listing_id: str
    venue: Venue
    venue_symbol: str
    venue_asset_code: str
    name: str
    canonical_asset_id: str | None
    identity_version: str
    identity_state: Literal["resolved", "review", "unresolved"]
    identity_reason: str
    trading: bool
    listing_time: datetime | None
    relationship_available: bool
    call_available: bool
    source: str


def local_identity_version(market: DirectoryMarket) -> str:
    return "venue-local-v1-" + public_payload_fingerprint(
        {
            "venue": market.venue,
            "code": market.venue_base_asset,
            "name": market.base_name,
            "currency": None
            if market.base_currency is None
            else asdict(market.base_currency),
        }
    )


def coins(
    directory: ProductMarketDirectory | None,
    snapshot: RegistrySnapshot | None,
    state: ProductUniverseState,
) -> tuple[ResearchCoin, ...]:
    if directory is None:
        return ()
    proposals = {
        (item.venue, item.venue_asset_code): item
        for item in AssetResolver(snapshot).resolve(directory)
    }
    reviews = {
        (item.venue, item.venue_asset_code): item for item in state.resolution_reviews
    }
    bindings = {
        (item.venue, item.venue_asset_code): item for item in state.identity_mappings
    }
    rows: list[ResearchCoin] = []
    for market in directory.markets:
        if market.venue_quote_asset != "USDT" or market.venue_base_asset == "USDT":
            continue
        key = (market.venue, market.venue_base_asset)
        proposal: AssetResolutionProposal = proposals[key]
        if proposal.disposition == "excluded":
            continue
        proposal = reviews.get(key, proposal)
        binding = bindings.get(key)
        resolved = (
            proposal.disposition == "resolved"
            and binding is not None
            and binding.canonical_asset_id == proposal.canonical_asset_id
        )
        rows.append(
            ResearchCoin(
                listing_id=f"{market.venue}:{market.venue_base_asset}",
                venue=market.venue,
                venue_symbol=market.venue_symbol,
                venue_asset_code=market.venue_base_asset,
                name=proposal.name or market.base_name or market.venue_base_asset,
                canonical_asset_id=(
                    binding.canonical_asset_id
                    if resolved and binding is not None
                    else None
                ),
                identity_version=binding.asset_identity_version
                if resolved and binding is not None
                else local_identity_version(market),
                identity_state="resolved"
                if resolved
                else ("review" if proposal.disposition == "review" else "unresolved"),
                identity_reason=proposal.reason,
                trading=market.trading,
                listing_time=market.buy_start,
                relationship_available=market.trading,
                call_available=market.trading and resolved,
                source=proposal.source if resolved else "venue",
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.venue_asset_code, row.venue)))


def search_coins(
    rows: tuple[ResearchCoin, ...], query: str, limit: int
) -> tuple[ResearchCoin, ...]:
    needle = re.sub(r"[\s/_-]", "", query).casefold()
    matches: list[tuple[int, ResearchCoin]] = []
    for row in rows:
        aliases = (
            row.venue_asset_code,
            row.venue_symbol,
            row.name,
            row.canonical_asset_id or "",
        )
        normalized = tuple(
            re.sub(r"[\s/_-]", "", alias).casefold() for alias in aliases
        )
        if not needle or any(needle in alias for alias in normalized):
            rank = 0 if needle in normalized else 1
            matches.append((rank, row))
    return tuple(
        row
        for _rank, row in sorted(
            matches,
            key=lambda value: (
                value[0],
                not value[1].trading,
                value[1].venue_asset_code,
                value[1].venue,
            ),
        )[:limit]
    )
