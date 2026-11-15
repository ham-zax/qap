"""Admission-free discovery must retain evidence and economic identity boundaries."""

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from qap.asset_registry import RegistryCoin, RegistrySnapshot, RegistryTicker
from qap.portfolio import AssetId
from qap.product_pair_rotation_analysis import PairAnalysisError
from qap.product_pair_rotation_markets import direct_instrument
from qap.product_universe import (
    AssetIdentityMapping,
    DirectoryMarket,
    DirectorySource,
    ProductMarketDirectory,
    ProductUniverse,
    ProductUniverseError,
    ProductUniverseState,
)

NOW = datetime(2026, 9, 30, tzinfo=UTC)


def setup_universe(root: Path, *, registry: bool = True) -> ProductUniverse:
    universe = ProductUniverse(root)
    universe.root.mkdir(parents=True, exist_ok=True)
    directory = ProductMarketDirectory(
        sources=(
            DirectorySource(
                venue="binance",
                observed_at=NOW,
                source_id="fixture-exchangeInfo",
                source_fingerprint="1" * 64,
            ),
        ),
        markets=tuple(
            DirectoryMarket(
                venue="binance",
                venue_symbol=f"{code}USDT",
                venue_base_asset=code,
                venue_quote_asset="USDT",
                status="TRADING",
                trading=True,
                base_name=name,
                permissions=permissions,
            )
            for code, name, permissions in (
                ("W", "Wormhole", ()),
                ("BTC", "Bitcoin", ()),
                ("ETH", "Ethereum", ()),
                ("NEW", "New coin", ()),
                ("BTCUP", "", ()),
                ("AAPLB", "", ("TRD_GRP_261",)),
            )
        ),
    )
    universe.directory_path.write_text(directory.model_dump_json())
    if registry:
        snapshot = RegistrySnapshot(
            observed_at=NOW,
            coins=tuple(
                RegistryCoin(coin_id=coin_id, symbol=code.lower(), name=name)
                for coin_id, code, name in (
                    ("wormhole", "W", "Wormhole"),
                    ("bitcoin", "BTC", "Bitcoin"),
                    ("ethereum", "ETH", "Ethereum"),
                )
            ),
            tickers=tuple(
                RegistryTicker(
                    venue="binance", base=code, target="USDT", coin_id=coin_id
                )
                for coin_id, code in (
                    ("wormhole", "W"),
                    ("bitcoin", "BTC"),
                    ("ethereum", "ETH"),
                )
            ),
        )
        (universe.root / "asset-registry.json").write_text(
            json.dumps(
                {
                    "snapshot": snapshot.model_dump(mode="json"),
                    "fingerprint": snapshot.fingerprint,
                }
            )
        )
    # Simulate the automatic acceptance performed after directory/registry refresh.
    universe.apply_policy_bindings()
    return universe


@pytest.mark.parametrize("query", ["Wormhole", "W", "W/USDT", "W_USDT", "WUSDT"])
def test_name_and_alias_search_resolves_without_admission(
    tmp_path: Path, query: str
) -> None:
    universe = setup_universe(tmp_path)
    rows = universe.search(query)
    assert rows[0].listing_id == "binance:W"
    assert rows[0].canonical_asset_id == "W"
    assert rows[0].identity_state == "resolved"
    state = universe.read_state()
    assert state.approved_asset_ids == ()
    assert any(
        m.venue_asset_code == "USDT" and m.accepted_by == "policy"
        for m in state.identity_mappings
    )
    assert not {"BTCUP", "AAPLB"} & {row.venue_asset_code for row in universe.search()}


def test_research_scope_is_separate_from_portfolio_admission(tmp_path: Path) -> None:
    universe = setup_universe(tmp_path)
    scope = universe.research_scope(("binance:W", "binance:BTC"))
    assert scope.approved_assets == ()
    assert scope.economic_identity_confirmed
    assert tuple(i.instrument.base.key for i in scope.instruments) == ("W", "BTC")
    assert all(
        i.quote_asset_identity_version == "usdt-policy-v1" for i in scope.instruments
    )
    with pytest.raises(ProductUniverseError, match="not approved"):
        universe.resolved_scope(
            asset_ids=tuple(i.instrument.base for i in scope.instruments)
        )


def test_unknown_coin_has_local_identity_and_no_economic_call(tmp_path: Path) -> None:
    universe = setup_universe(tmp_path, registry=False)
    rows = universe.search("NEW")
    assert len(rows) == 1 and rows[0].relationship_available
    assert rows[0].canonical_asset_id is None and not rows[0].call_available
    scope = universe.research_scope(("binance:NEW", "binance:W"))
    assert scope.instruments[0].instrument.base.key == "VENUE:BINANCE:NEW"
    assert not scope.economic_identity_confirmed
    assert universe.read_state().approved_asset_ids == ()


def test_legacy_w_to_btc_is_retired_and_cannot_be_reintroduced(tmp_path: Path) -> None:
    universe = setup_universe(tmp_path)
    bad = AssetIdentityMapping(
        venue="binance",
        venue_asset_code="W",
        canonical_asset_id="BTC",
        asset_identity_version="old",
        confirmed_at=NOW,
    )
    state = ProductUniverseState(
        schema_version="qap.product.research-universe.v1",
        approved_asset_ids=("BTC", "W"),
        identity_mappings=(
            bad,
            AssetIdentityMapping(
                venue="binance",
                venue_asset_code="USDT",
                canonical_asset_id="USDT",
                asset_identity_version="old",
                confirmed_at=NOW,
            ),
        ),
    )
    universe.state_path.write_text(state.model_dump_json())
    # Even an untouched legacy workspace must not use the contradicted identity.
    with pytest.raises(ProductUniverseError, match="identity is unresolved"):
        universe.resolved_scope(asset_ids=(AssetId("BTC"),))
    universe.apply_policy_bindings()
    updated = universe.read_state()
    assert updated.schema_version == "qap.product.research-universe.v2"
    assert updated.retired_identity_mappings == (bad,)
    assert updated.pending_admission_asset_ids == ("BTC",)
    assert updated.approved_asset_ids == ("W",)
    assert universe.search("W")[0].canonical_asset_id == "W"
    with pytest.raises(ProductUniverseError, match="cannot be bound"):
        universe.set_identity_mapping(
            venue="binance",
            venue_asset_code="W",
            canonical_asset_id="BTC",
            asset_identity_version="bad",
        )
    universe.set_asset_admission(canonical_asset_id="BTC", approved=True)
    assert universe.read_state().pending_admission_asset_ids == ()
    assert universe.read_state().retired_identity_mappings == (bad,)


def test_registry_conflict_stays_blocked_when_evidence_goes_missing(
    tmp_path: Path,
) -> None:
    universe = setup_universe(tmp_path)
    universe.set_identity_mapping(
        venue="binance",
        venue_asset_code="ETH",
        canonical_asset_id="OTHER",
        asset_identity_version="old",
    )
    universe.apply_policy_bindings()
    assert (
        universe.read_state().resolution_reviews[0].reason
        == "accepted_binding_conflict"
    )
    assert universe.search("ETH")[0].identity_state == "review"
    (universe.root / "asset-registry.json").unlink()
    universe.apply_policy_bindings()
    assert universe.read_state().resolution_reviews
    assert not universe.search("ETH")[0].call_available


def test_unchanged_evidence_does_not_rewrite_binding_timestamp(tmp_path: Path) -> None:
    universe = setup_universe(tmp_path)
    universe.apply_policy_bindings()
    before = universe.state_path.read_bytes()
    universe.apply_policy_bindings()
    assert universe.state_path.read_bytes() == before


@pytest.mark.parametrize(
    "ids",
    [
        ("binance:W", "binance:W"),
        ("binance:W", "binance:BTCUP"),
        ("binance:W", "binance:AAPLB"),
        ("binance:W", "binance:MISSING"),
    ],
)
def test_missing_duplicate_or_ineligible_selection_is_refused(
    tmp_path: Path, ids: tuple[str, str]
) -> None:
    with pytest.raises(ProductUniverseError):
        setup_universe(tmp_path).research_scope(ids)


def test_direct_instrument_raises_pair_analysis_error_when_listing_missing(
    tmp_path: Path,
) -> None:
    universe = setup_universe(tmp_path)
    scope = universe.research_scope(("binance:BTC", "binance:ETH"))
    directory = universe.read_directory()
    assert directory is not None
    trimmed = directory.model_copy(
        update={
            "markets": tuple(
                row for row in directory.markets if row.venue_symbol != "ETHUSDT"
            )
        }
    )
    universe.directory_path.write_text(trimmed.model_dump_json())
    with pytest.raises(PairAnalysisError, match="missing a selected listing"):
        direct_instrument(universe, scope)
