"""Resolver coverage on the recorded 2026-09-30 snapshot versus the 2026-09-27 study.

The registry snapshot is the real full CoinGecko acquisition (coin list plus every
Binance and Gate ticker page), trimmed to coins that carry evidence for a listing.
Reference figures are Section 4.2 of the Phase 18 investigation findings; markets
and registry data moved between the two dates, so each figure has a stated tolerance.
"""

import pytest

from qap.asset_registry import RegistrySnapshot
from qap.asset_resolver import AssetResolutionProposal, AssetResolver

from .recorded import directory, load


@pytest.fixture(scope="module")
def usdt_proposals() -> dict[tuple[str, str], AssetResolutionProposal]:
    snapshot = RegistrySnapshot.model_validate(
        load("coverage_coingecko_snapshot.json.gz")
    )
    source = directory("coverage")
    tradable = {
        (m.venue, m.venue_base_asset)
        for m in source.markets
        if m.trading and m.venue_quote_asset == "USDT"
    }
    return {
        (p.venue, p.venue_asset_code): p
        for p in AssetResolver(snapshot).resolve(source)
        if (p.venue, p.venue_asset_code) in tradable
    }


def _venue(
    proposals: dict[tuple[str, str], AssetResolutionProposal], venue: str
) -> list[AssetResolutionProposal]:
    return [p for (v, _), p in proposals.items() if v == venue]


def test_binance_resolved_count_matches_the_study(
    usdt_proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Study: 413 of 414 crypto USDT bases resolved, no conflicts. Tolerance +-10."""

    binance = _venue(usdt_proposals, "binance")
    resolved = [p for p in binance if p.disposition == "resolved"]

    assert abs(len(resolved) - 413) <= 10  # measured 415
    assert not [p for p in binance if p.disposition == "review"]


def test_gate_resolved_share_matches_the_study(
    usdt_proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Study: 1,459 of 1,488 crypto bases (98.1%) resolved; 8 conflicts (0.5%).

    Tolerance +-1.5 percentage points on the resolved share; conflicts at most 1.0%.
    Measured 1,421 of 1,461 (97.3%) with 5 reviews (0.3%).
    """

    gate = [p for p in _venue(usdt_proposals, "gate") if p.disposition != "excluded"]
    resolved = sum(p.disposition == "resolved" for p in gate)
    review = sum(p.disposition == "review" for p in gate)

    assert abs(resolved / len(gate) - 1459 / 1488) <= 0.015
    assert review / len(gate) <= 0.010
    assert {p.venue_asset_code for p in gate if p.disposition == "review"} >= {
        "DYDX",
        "HOLDSTATION",
    }


def test_gate_exclusions_match_the_study_categories(
    usdt_proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Study: 420 leveraged and 163 stock/metal/forex tokens. Tolerance +-20 each."""

    gate = _venue(usdt_proposals, "gate")
    leveraged = sum(p.reason == "leveraged_token" for p in gate)
    tokenized = sum(p.reason in {"tokenized_stock", "synthetic_asset"} for p in gate)

    assert abs(leveraged - 420) <= 20  # measured 425
    assert abs(tokenized - 163) <= 20  # measured 165


def test_cross_venue_bases_never_resolve_to_different_coins(
    usdt_proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Study: 393 shared USDT bases; 389 agree; none disagree. Tolerance +-15 agree."""

    both = [
        (usdt_proposals["binance", code], usdt_proposals["gate", code])
        for venue, code in usdt_proposals
        if venue == "binance" and ("gate", code) in usdt_proposals
    ]
    resolved = [
        (b, g) for b, g in both if {b.disposition, g.disposition} == {"resolved"}
    ]

    assert abs(len(both) - 393) <= 15  # measured 393
    assert abs(len(resolved) - 389) <= 15  # measured 385
    assert all(b.registry_coin_id == g.registry_coin_id for b, g in resolved)
    for code, coin in (("W", "wormhole"), ("BTC", "bitcoin"), ("PIXEL", "pixels")):
        assert usdt_proposals["binance", code].registry_coin_id == coin
        assert usdt_proposals["gate", code].registry_coin_id == coin


def test_binance_tokenized_stocks_are_all_excluded(
    usdt_proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Stock tokens the registry does not name are excluded by permission group."""

    stock_tokens = [
        p
        for p in _venue(usdt_proposals, "binance")
        if p.venue_asset_code in {"ADBEB", "AMDB", "TSLAB"}
    ]

    assert stock_tokens
    assert {(p.disposition, p.reason) for p in stock_tokens} == {
        ("excluded", "tokenized_stock")
    }
    assert not [
        p for p in _venue(usdt_proposals, "binance") if p.disposition == "unresolved"
    ]
