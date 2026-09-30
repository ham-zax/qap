# Registry, Gate and Binance identity-evidence fixtures

All data here is **recorded from the real public APIs on 2026-09-30** (UTC). Nothing
in these files is hand-made. Rows are preserved as returned; only whole rows or whole
top-level fields are dropped, as listed. Tests that need synthetic input (429
responses, paging, a constructed DAI market, altered snapshots) build it in the test
and say so in its docstring or name.

| Source | URL | Retrieved (UTC) |
| --- | --- | --- |
| CoinGecko coin list with platforms | `https://api.coingecko.com/api/v3/coins/list?include_platform=true` (21,731 coins) | 2026-09-30 13:57 |
| CoinGecko Binance tickers | `https://api.coingecko.com/api/v3/exchanges/binance/tickers?page=1..14&order=base_target` (1,360 tickers) | 2026-09-30 13:57-14:00 |
| CoinGecko Gate tickers | `https://api.coingecko.com/api/v3/exchanges/gate/tickers?page=1..17&order=base_target` (1,674 tickers) | 2026-09-30 14:00-14:05 |
| Gate currencies | `https://api.gateio.ws/api/v4/spot/currencies` | 2026-09-30 13:48 |
| Gate currency pairs | `https://api.gateio.ws/api/v4/spot/currency_pairs` | 2026-09-30 13:48 |
| Binance exchange info | `https://api.binance.com/api/v3/exchangeInfo` | 2026-09-30 13:48 |

The CoinGecko pages were acquired by `CoinGeckoRegistry` itself (keyless, pacing 4 s,
up to 6 retries with 8 s doubling backoff; 6 pages returned 429 and succeeded on
retry). A first attempt at default pacing (2.1 s, one retry) was rate limited on
Gate page 1, so its Binance-only result was discarded. Both venues' tickers are
therefore recorded; there is no Gate-ticker gap. Gate and Binance responses were
fetched with `curl` without keys. CoinGecko attribution: data provided by CoinGecko
(https://www.coingecko.com/).

## Case fixtures (small)

Used by the client, resolver and eligibility unit tests. Cases: W, BTC, ETH (wrapped
conflict), DAI (no ticker; bridged variants), DYDX (migration), leveraged tokens
(Gate `ARB3L`, Binance `BTCUP`), tokenized stocks (Gate `AAPLX`, Binance `AAPLB`),
Gate-only `GHO`; plus USDC (Gate `forex` tag), ONDO (`ondo-stocks` tag) and RON
(fiat-code collision).

- `coingecko_case_responses.json`: replay map keyed by request path and query.
  `coins/list...` holds the raw rows of the 23 coins that carry evidence for the
  cases (ticker-mapped or address-matched); each `exchanges/<venue>/tickers...` entry
  is one page holding every raw ticker row of that venue whose base is a case
  code (all recorded pages merged into page 1, all fields preserved).
- `gate_case_currencies.json`, `gate_case_currency_pairs.json`: raw Gate rows for
  the case codes (pairs: `USDT` quote, type `normal`).
- `binance_case_exchange_info.json`: Binance `symbols` rows for the case codes with
  a `USDT` quote, keeping only `symbol`, `status`, `baseAsset`, `quoteAsset`,
  `isSpotTradingAllowed`, `permissions`.

## Coverage fixtures (gzip, full venues)

Used by `test_asset_resolver_coverage.py`.

- `coverage_coingecko_snapshot.json.gz`: the `RegistrySnapshot` produced by the
  acquisition above, with `coins` trimmed to coins that appear in any ticker or
  match any Gate contract address (2,558 of 21,731). All 3,019 recorded tickers and
  all 32 successful-request provenance records are kept. The trim cannot change a proposal:
  every coin the resolver could look up is retained. The `sources` fingerprints
  describe the untrimmed responses.
- `coverage_gate_currencies.json.gz`, `coverage_gate_currency_pairs.json.gz`: full
  Gate currencies; pairs with a `USDT` quote.
- `coverage_binance_exchange_info.json.gz`: Binance symbols with a `USDT` quote,
  reduced to the same keys as the case file (the raw response is 17 MB).

## Measured coverage (2026-09-30 snapshot, tradable USDT bases)

| Venue | Result |
| --- | --- |
| Binance (503) | 415 resolved, 88 excluded (84 tokenized stock, 3 leveraged, 1 fiat), 0 unresolved, 0 review |
| Gate (2,052) | 1,421 resolved, 591 excluded, 5 review, 35 unresolved; 1,421 of 1,461 non-excluded (97.3%) |

Study figures (2026-09-27): Binance 413 of 414; Gate 1,459 of 1,488 (98.1%) with 8
conflicts. Binance tokenized stocks (`...B`) are excluded by their venue permission
group `TRD_GRP_261`, including those the registry does not name as stocks.
`coverage_binance_exchange_info.json.gz` keeps `permissionSets` trimmed to that
group only (87 USDT symbols carry it; all are stock tokens).

Known limits: stale or anomalous tickers are excluded as evidence (195 of 3,019);
the bridged-variant allowlist is narrow. It includes Binance-bridged USDC and the
Avalanche/Polygon bridged DAI, so Gate `USDC` and `DAI` resolve without review.
