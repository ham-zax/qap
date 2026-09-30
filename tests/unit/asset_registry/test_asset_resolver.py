"""Resolver behaviour on the eight recorded cases; evidence in, proposals out."""

import pytest

from qap.asset_registry import RegistrySnapshot
from qap.asset_resolver import AssetResolutionProposal, AssetResolver
from qap.market.adapters.spot_directory import (
    gate_currencies_from_payload,
    gate_directory_from_payload,
)
from qap.product_directory_models import ProductMarketDirectory

from .recorded import OBSERVED, case_snapshot, directory, load


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory: pytest.TempPathFactory) -> RegistrySnapshot:
    return case_snapshot(tmp_path_factory.mktemp("registry") / "cache.json")


@pytest.fixture(scope="module")
def proposals(
    snapshot: RegistrySnapshot,
) -> dict[tuple[str, str], AssetResolutionProposal]:
    return {
        (p.venue, p.venue_asset_code): p
        for p in AssetResolver(snapshot).resolve(directory("case"))
    }


def _outcome(p: AssetResolutionProposal) -> tuple[str, str, str | None]:
    return p.disposition, p.reason, p.registry_coin_id


def test_w_resolves_to_wormhole_on_both_venues_and_never_to_bitcoin(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    assert _outcome(proposals["binance", "W"]) == (
        "resolved",
        "venue_ticker_mapping",
        "wormhole",
    )
    assert _outcome(proposals["gate", "W"]) == (
        "resolved",
        "venue_ticker_mapping",
        "wormhole",
    )
    assert proposals["gate", "W"].address_coin_ids == ("wormhole",)
    assert proposals["gate", "W"].canonical_asset_id == "W"


@pytest.mark.parametrize(
    ("code", "coin", "wrapped"),
    [("BTC", "bitcoin", "binance-bitcoin"), ("ETH", "ethereum", "binance-peg-weth")],
)
def test_ticker_mapping_beats_a_wrapped_address_match(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
    code: str,
    coin: str,
    wrapped: str,
) -> None:
    gate = proposals["gate", code]

    assert _outcome(gate) == ("resolved", "venue_ticker_over_representation", coin)
    assert gate.address_coin_ids == (wrapped,)
    assert gate.ticker_coin_ids == (coin,)
    assert _outcome(proposals["binance", code]) == (
        "resolved",
        "venue_ticker_mapping",
        coin,
    )
    assert gate.identity_version == proposals["binance", code].identity_version


def test_dai_without_ticker_or_address_evidence_stays_unresolved(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Recorded Binance DAI (BREAK) has no registry ticker: no identity is invented."""

    proposal = proposals["binance", "DAI"]

    assert _outcome(proposal) == ("unresolved", "no_strong_identity_evidence", None)
    assert proposal.identity_version is None


def test_dai_with_reviewed_bridged_variants_resolves_to_dai(
    snapshot: RegistrySnapshot,
) -> None:
    """CONSTRUCTED market over recorded Gate DAI currency (Gate lists no DAI pair).

    The Ethereum address names `dai`; the Avalanche and Polygon addresses name
    reviewed bridged representations of `dai`, so they identify DAI itself.
    """

    currencies = {
        c.venue_asset_code: c
        for c in gate_currencies_from_payload(load("gate_case_currencies.json"))
    }
    pair = {
        "id": "DAI_USDT",
        "base": "DAI",
        "base_name": "Dai",
        "quote": "USDT",
        "trade_status": "tradable",
        "type": "normal",
    }
    observation = gate_directory_from_payload(
        [pair],
        currencies_payload=load("gate_case_currencies.json"),
        observed_at=OBSERVED,
    )
    assert "DAI" in currencies
    (proposal,) = AssetResolver(snapshot).resolve(
        ProductMarketDirectory.from_observations((observation,))
    )

    assert _outcome(proposal) == ("resolved", "contract_over_representation", "dai")
    assert proposal.address_coin_ids == (
        "avalanche-bridged-dai-avalanche",
        "dai",
        "polygon-pos-bridged-dai-polygon-pos",
    )


def test_dydx_migration_goes_to_review_with_both_candidates_and_no_binding(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    gate = proposals["gate", "DYDX"]

    assert _outcome(gate) == ("review", "conflict_or_migration", None)
    assert (gate.ticker_coin_ids, gate.address_coin_ids) == (
        ("dydx-chain",),
        ("dydx",),
    )
    assert gate.canonical_asset_id is None and gate.identity_version is None
    assert _outcome(proposals["binance", "DYDX"])[2] == "dydx-chain"


def test_reviewed_bridged_usdc_resolves_without_manual_review(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    """Gate USDC: the BSC address matches the reviewed Binance-bridged USDC."""

    assert _outcome(proposals["gate", "USDC"]) == (
        "resolved",
        "venue_ticker_over_representation",
        "usd-coin",
    )
    assert _outcome(proposals["binance", "USDC"])[0] == "resolved"


@pytest.mark.parametrize(
    ("key", "reason"),
    [
        (("gate", "ARB3L"), "leveraged_token"),
        (("binance", "BTCUP"), "leveraged_token"),
        (("gate", "AAPLX"), "tokenized_stock"),
        (("binance", "AAPLB"), "tokenized_stock"),
    ],
)
def test_ineligible_listings_are_excluded_with_a_typed_reason(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
    key: tuple[str, str],
    reason: str,
) -> None:
    proposal = proposals[key]

    assert (proposal.disposition, proposal.reason) == ("excluded", reason)
    assert proposal.registry_coin_id is None and proposal.identity_version is None


def test_gate_only_asset_resolves_by_contract_without_a_binance_twin(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    assert ("binance", "GHO") not in proposals
    assert _outcome(proposals["gate", "GHO"]) == (
        "resolved",
        "unique_contract_match",
        "gho",
    )
    assert proposals["gate", "GHO"].ticker_coin_ids == ()


def test_ondo_and_ron_are_not_excluded_by_category_or_fiat_code(
    proposals: dict[tuple[str, str], AssetResolutionProposal],
) -> None:
    assert _outcome(proposals["gate", "ONDO"])[0] == "resolved"
    assert _outcome(proposals["gate", "RON"]) == (
        "resolved",
        "venue_ticker_mapping",
        "ronin",
    )


def test_same_code_on_two_venues_is_never_merged_by_ticker_equality(
    snapshot: RegistrySnapshot,
) -> None:
    """SYNTHETIC: venue tickers disagree, so each venue keeps its own identity."""

    tickers = tuple(
        t.model_copy(update={"coin_id": "wormhole"})
        if (t.venue, t.base) == ("gate", "W")
        else t.model_copy(update={"coin_id": "dai"})
        if (t.venue, t.base) == ("binance", "W")
        else t
        for t in snapshot.tickers
    )
    altered = snapshot.model_copy(update={"tickers": tickers})

    got = {
        (p.venue, p.venue_asset_code): p
        for p in AssetResolver(altered).resolve(directory("case"))
    }

    assert got["binance", "W"].registry_coin_id == "dai"
    assert got["gate", "W"].registry_coin_id == "wormhole"


def test_stale_and_anomalous_tickers_are_not_identity_evidence(
    snapshot: RegistrySnapshot,
) -> None:
    tickers = tuple(
        t.model_copy(update={"stale": True})
        if (t.venue, t.base) == ("binance", "W")
        else t
        for t in snapshot.tickers
    )
    altered = snapshot.model_copy(update={"tickers": tickers})

    got = {
        (p.venue, p.venue_asset_code): p
        for p in AssetResolver(altered).resolve(directory("case"))
    }

    assert _outcome(got["binance", "W"])[0] == "unresolved"


def test_resolution_is_deterministic_and_independent_of_input_order(
    snapshot: RegistrySnapshot,
) -> None:
    source = directory("case")
    reordered = source.model_copy(update={"markets": tuple(reversed(source.markets))})

    first = AssetResolver(snapshot).resolve(source)
    second = AssetResolver(snapshot).resolve(reordered)

    assert first == second
    assert [p.evidence_fingerprint for p in first] == [
        p.evidence_fingerprint for p in second
    ]


def test_evidence_fingerprint_ignores_time_but_tracks_evidence(
    snapshot: RegistrySnapshot,
) -> None:
    source = directory("case")
    later = snapshot.model_copy(
        update={"observed_at": snapshot.observed_at.replace(year=2027)}
    )
    other_address = tuple(
        c.model_copy(update={"platforms": (("solana", "MIGRATED"),)})
        if c.coin_id == "wormhole"
        else c
        for c in snapshot.coins
    )
    migrated = snapshot.model_copy(update={"coins": other_address})

    def w(snap: RegistrySnapshot) -> AssetResolutionProposal:
        return next(
            p
            for p in AssetResolver(snap).resolve(source)
            if (p.venue, p.venue_asset_code) == ("gate", "W")
        )

    assert w(later).evidence_fingerprint == w(snapshot).evidence_fingerprint
    assert w(migrated).evidence_fingerprint != w(snapshot).evidence_fingerprint
    assert w(migrated).identity_version != w(snapshot).identity_version


def test_without_a_registry_snapshot_nothing_is_resolved() -> None:
    proposals = AssetResolver(None).resolve(directory("case"))

    resolved = {p.disposition for p in proposals}
    assert resolved <= {"unresolved", "excluded"}
