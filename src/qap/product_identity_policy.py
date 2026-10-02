"""Pure evidence acceptance; ProductUniverse remains the only binding writer."""

from datetime import datetime

from qap.asset_registry import RegistrySnapshot
from qap.asset_resolver import AssetResolutionProposal, AssetResolver
from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import ProductMarketDirectory
from qap.product_universe_models import AssetIdentityMapping, ProductUniverseState


def accept_evidence(
    state: ProductUniverseState,
    directory: ProductMarketDirectory,
    snapshot: RegistrySnapshot | None,
    *,
    now: datetime,
) -> ProductUniverseState:
    proposals = AssetResolver(snapshot).resolve(directory)
    mappings = {
        (item.venue, item.venue_asset_code): item for item in state.identity_mappings
    }
    retired = list(state.retired_identity_mappings)
    pending = set(state.pending_admission_asset_ids)
    approved = set(state.approved_asset_ids)
    # D6: a known contradicted binding cannot remain an economic input while
    # supplemental evidence is unavailable. Keep its exact history for audit.
    bad = mappings.get(("binance", "W"))
    if bad is not None and bad.canonical_asset_id == "BTC":
        retired.append(bad)
        del mappings["binance", "W"]
        approved.discard("BTC")
        pending.add("BTC")
    for source in directory.sources:
        if any(
            m.venue == source.venue and m.venue_quote_asset == "USDT"
            for m in directory.markets
        ):
            mappings[source.venue, "USDT"] = AssetIdentityMapping(
                venue=source.venue,
                venue_asset_code="USDT",
                canonical_asset_id="USDT",
                asset_identity_version="usdt-policy-v1",
                confirmed_at=now,
                accepted_by="policy",
                source="policy",
                evidence_fingerprint=public_payload_fingerprint(
                    {"policy": "USDT-quote-v1"}
                ),
            )
    reviews: dict[tuple[str, str], AssetResolutionProposal] = {
        (item.venue, item.venue_asset_code): item for item in state.resolution_reviews
    }
    for proposal in proposals:
        if proposal.venue_asset_code == "USDT":
            continue
        key = (proposal.venue, proposal.venue_asset_code)
        old = mappings.get(key)
        if key == ("binance", "W") and proposal.canonical_asset_id == "BTC":
            reviews[key] = proposal.model_copy(
                update={"disposition": "review", "reason": "contradicted_w_to_btc"}
            )
            continue
        if proposal.disposition != "resolved":
            if proposal.disposition == "review":
                reviews[key] = proposal
            continue
        assert (
            proposal.canonical_asset_id is not None
            and proposal.identity_version is not None
        )
        if old is not None and old.canonical_asset_id != proposal.canonical_asset_id:
            reviews[key] = proposal.model_copy(
                update={
                    "disposition": "review",
                    "reason": "accepted_binding_conflict",
                }
            )
            continue
        reviews.pop(key, None)
        mappings[key] = AssetIdentityMapping(
            venue=proposal.venue,
            venue_asset_code=proposal.venue_asset_code,
            canonical_asset_id=proposal.canonical_asset_id,
            asset_identity_version=proposal.identity_version,
            confirmed_at=now,
            accepted_by="policy",
            source=proposal.source,
            registry_coin_id=proposal.registry_coin_id,
            evidence_fingerprint=proposal.evidence_fingerprint,
        )
    # Keep a stable accepted_at for evidence that has not changed.
    previous = {
        (item.venue, item.venue_asset_code): item for item in state.identity_mappings
    }
    for key, mapping in tuple(mappings.items()):
        old = previous.get(key)
        if (
            old is not None
            and mapping.model_copy(update={"confirmed_at": old.confirmed_at}) == old
        ):
            mappings[key] = old
    next_state = ProductUniverseState(
        updated_at=now,
        approved_asset_ids=tuple(sorted(approved)),
        identity_mappings=tuple(mappings[key] for key in sorted(mappings)),
        resolution_reviews=tuple(reviews[key] for key in sorted(reviews)),
        retired_identity_mappings=tuple(retired),
        pending_admission_asset_ids=tuple(sorted(pending)),
    )
    if next_state.model_copy(update={"updated_at": state.updated_at}) == state:
        return state
    return next_state
