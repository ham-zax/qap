"""Deterministic identity proposals from registry and venue evidence."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict
from typing import Literal

from qap.asset_eligibility import classify_asset
from qap.asset_registry import RegistryCoin, RegistryModel, RegistrySnapshot
from qap.market.microstructure import public_payload_fingerprint
from qap.product_directory_models import DirectoryMarket, ProductMarketDirectory, Venue

# Compatibility aliases are keyed by economic identity, never by venue symbol.
_CANONICAL = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "wormhole": "W",
    "pixels": "PIXEL",
    "tether": "USDT",
    "dai": "DAI",
    "solana": "SOL",
}
# Reviewed representations observed in the Phase 18 investigation. This narrow
# allowlist is evidence about identity, not a general name-based heuristic.
_REPRESENTATIONS = {
    "binance-bitcoin": "bitcoin",
    "binance-peg-weth": "ethereum",
    "wrapped-telos": "telos",
    "bridged-nxpc": "nexpace",
    "e-radix": "radix",
    "binance-bridged-usdc-bnb-smart-chain": "usd-coin",
    "avalanche-bridged-dai-avalanche": "dai",
    "polygon-pos-bridged-dai-polygon-pos": "dai",
}
_CHAIN = {
    "ETH": "ethereum",
    "ERC20": "ethereum",
    "ETHEREUM": "ethereum",
    "BSC": "binance-smart-chain",
    "BEP20": "binance-smart-chain",
    "SOL": "solana",
    "SOLANA": "solana",
    "POLYGON": "polygon-pos",
    "MATIC": "polygon-pos",
    "ARBITRUM": "arbitrum-one",
    "ARB": "arbitrum-one",
    "ARBEVM": "arbitrum-one",
    "OP": "optimistic-ethereum",
    "OPETH": "optimistic-ethereum",
    "OPTIMISM": "optimistic-ethereum",
    "AVAX": "avalanche",
    "AVAX_C": "avalanche",
    "BASE": "base",
    "BASEEVM": "base",
    "TRX": "tron",
    "TRON": "tron",
    "TON": "the-open-network",
    "SUI": "sui",
    "SUINEW": "sui",
    "APT": "aptos",
    "ADA": "cardano",
    "NEAR": "near-protocol",
    "KAIA": "klay-token",
    "CHZ2": "chiliz",
    "BTCRUNES": "ordinals",
    "ZKSERA": "zksync",
    "ROBINHOOD": "robinhood",
    "CRO": "cronos",
    "BLASTETH": "blast",
    "LINEAETH": "linea",
    "HBAR": "hedera-hashgraph",
    "ALGO": "algorand",
    "MNT": "mantle",
    "BERA": "berachain",
    "FTM": "fantom",
    "XRP": "xrp",
    "CELO": "celo",
    "EGLD": "elrond",
    "MERLBTC": "merlin-chain",
    "MANTAETH": "manta-pacific",
    "S": "sonic",
    "RON": "ronin",
    "WAVES": "waves",
    "LUNC": "terra",
}


Disposition = Literal["resolved", "review", "unresolved", "excluded"]


def _address(address: str) -> str:
    # EVM hexadecimal addresses are case-insensitive; Solana and other native
    # addresses remain byte-for-byte case-sensitive.
    return address.lower() if address.startswith("0x") else address


class AssetResolutionProposal(RegistryModel):
    venue: Venue
    venue_asset_code: str
    registry_coin_id: str | None = None
    canonical_asset_id: str | None = None
    name: str | None = None
    evidence_fingerprint: str
    identity_version: str | None = None
    disposition: Disposition
    reason: str
    source: str = "coingecko"
    ticker_coin_ids: tuple[str, ...] = ()
    address_coin_ids: tuple[str, ...] = ()


class AssetResolver:
    def __init__(self, snapshot: RegistrySnapshot | None) -> None:
        self.snapshot = snapshot
        self.coins = {} if snapshot is None else {c.coin_id: c for c in snapshot.coins}
        self._coin_payloads: dict[str, dict[str, object]] = {}
        self.tickers: dict[tuple[Venue, str], set[str]] = defaultdict(set)
        self.addresses: dict[tuple[str, str], set[str]] = defaultdict(set)
        if snapshot is not None:
            for ticker in snapshot.tickers:
                if not ticker.stale and not ticker.anomalous:
                    self.tickers[ticker.venue, ticker.base.upper()].add(ticker.coin_id)
            for coin in snapshot.coins:
                for chain, address in coin.platforms:
                    if address:
                        self.addresses[chain, _address(address)].add(coin.coin_id)

    def resolve(
        self, directory: ProductMarketDirectory
    ) -> tuple[AssetResolutionProposal, ...]:
        return self.resolve_markets(directory.markets)

    def resolve_markets(
        self, markets: Iterable[DirectoryMarket]
    ) -> tuple[AssetResolutionProposal, ...]:
        listings: dict[tuple[Venue, str], DirectoryMarket] = {}
        for market in sorted(markets, key=lambda m: (m.venue, m.venue_symbol)):
            listings.setdefault((market.venue, market.venue_base_asset), market)
        return tuple(self._resolve(market) for _, market in sorted(listings.items()))

    def _canonical(self, coin: RegistryCoin) -> str:
        # Reserved aliases cannot be assigned to another registry coin, even if
        # that other coin has the same symbol.
        return _CANONICAL.get(coin.coin_id, "CG_" + coin.coin_id.upper())

    def _coin_payload(self, coin_id: str) -> dict[str, object]:
        cached = self._coin_payloads.get(coin_id)
        if cached is None:
            cached = self.coins[coin_id].model_dump(mode="json")
            self._coin_payloads[coin_id] = cached
        return cached

    def _resolve(self, market: DirectoryMarket) -> AssetResolutionProposal:
        code = market.venue_base_asset
        ticker_ids = self.tickers.get((market.venue, code), set())
        address_ids: set[str] = set()
        currency = market.base_currency
        if currency is not None:
            for chain in currency.chains:
                if chain.contract_address:
                    platform = _CHAIN.get(chain.chain.upper(), chain.chain.lower())
                    address_ids.update(
                        self.addresses.get(
                            (platform, _address(chain.contract_address)), ()
                        )
                    )
        # Names and classes come from the coins that carry the identity evidence:
        # a wrapped-address match must not reclassify a ticker-mapped asset.
        evidence_ids = sorted(ticker_ids or address_ids)
        eligibility = classify_asset(
            code,
            currency=currency,
            registry_categories=tuple(
                cat for cid in evidence_ids for cat in self.coins[cid].categories
            ),
            names=tuple(self.coins[cid].name for cid in evidence_ids)
            or (() if market.base_name is None else (market.base_name,)),
            registry_evidence=bool(evidence_ids),
            venue_permissions=market.permissions
            + tuple(p for group in market.permission_sets for p in group),
        )
        fingerprint = public_payload_fingerprint(
            {
                "venue": market.venue,
                "code": code,
                "currency": None if currency is None else asdict(currency),
                "ticker_ids": sorted(ticker_ids),
                "address_ids": sorted(address_ids),
                "coins": [
                    self._coin_payload(cid) for cid in sorted(ticker_ids | address_ids)
                ],
            }
        )

        def proposal(
            disposition: Disposition,
            reason: str,
            chosen: str | None = None,
        ) -> AssetResolutionProposal:
            coin = None if chosen is None else self.coins[chosen]
            return AssetResolutionProposal(
                venue=market.venue,
                venue_asset_code=code,
                registry_coin_id=chosen,
                canonical_asset_id=None if coin is None else self._canonical(coin),
                name=market.base_name if coin is None else coin.name,
                evidence_fingerprint=fingerprint,
                identity_version=None if coin is None else coin.identity_version,
                disposition=disposition,
                reason=reason,
                ticker_coin_ids=tuple(sorted(ticker_ids)),
                address_coin_ids=tuple(sorted(address_ids)),
            )

        if not eligibility.eligible:
            return proposal("excluded", eligibility.reason)
        if not ticker_ids and len(address_ids) > 1:
            # Addresses that only point at reviewed bridged forms of one asset
            # identify that asset (Gate DAI on Ethereum, Avalanche and Polygon).
            roots = [
                cid
                for cid in address_ids
                if not any(
                    self._represents(cid, other) for other in address_ids - {cid}
                )
            ]
            if len(roots) == 1 and all(
                self._represents(cid, roots[0]) for cid in address_ids - {roots[0]}
            ):
                return proposal("resolved", "contract_over_representation", roots[0])
        if len(ticker_ids) > 1 or (not ticker_ids and len(address_ids) > 1):
            return proposal("review", "ambiguous_registry_evidence")
        if len(ticker_ids) == 1:
            chosen = next(iter(ticker_ids))
            differing = address_ids - {chosen}
            if not differing:
                return proposal("resolved", "venue_ticker_mapping", chosen)
            # The venue's own ticker mapping outranks an address that only points
            # at a wrapped or bridged form of the same asset; anything else is a
            # conflict or migration and is never bound automatically.
            if all(self._represents(cid, chosen) for cid in differing):
                return proposal("resolved", "venue_ticker_over_representation", chosen)
            return proposal("review", "conflict_or_migration")
        if len(address_ids) == 1:
            return proposal(
                "resolved", "unique_contract_match", next(iter(address_ids))
            )
        return proposal("unresolved", "no_strong_identity_evidence")

    def _represents(self, coin_id: str, target: str) -> bool:
        declared = self.coins[coin_id].representation_of or _REPRESENTATIONS.get(
            coin_id
        )
        return declared == target
