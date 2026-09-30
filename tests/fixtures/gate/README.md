# Gate directory evidence fixtures

Captured 2026-09-30 from the unauthenticated Gate v4 API:

- `currency_pairs_identity_subset.json`: `/spot/currency_pairs`, W/BTC/ETH USDT listings.
- `currencies_identity_subset.json`: `/spot/currencies`, W/BTC/ETH/USDT records.

Rows are preserved as returned; the full responses are filtered to these assets.
Addresses preserve case. BTC/ETH wrapped-chain evidence is descriptive and does
not establish canonical identity. Gate model contracts:
[Currency](https://github.com/gateio/gateapi-python/blob/master/docs/Currency.md),
[CurrencyPair](https://github.com/gateio/gateapi-python/blob/master/docs/CurrencyPair.md),
[SpotCurrencyChain](https://github.com/gateio/gateapi-python/blob/master/docs/SpotCurrencyChain.md).

These JSON subsets are the raw test artifacts. Khiip capture was unavailable in
this runtime; no Markdown archive of the upstream API documentation is claimed.
