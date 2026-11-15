# Analysis speed baseline — 2026-10-27

## Load
 03:48:54 up 1 day, 11:36,  1 user,  load average: 3.84, 3.32, 1.83 | running operations: 0

## HTTP timings (seconds)
| run | kind | seconds |
|-----|------|---------|
| 1 | cold | 20.855314 |
| 2 | warm | 18.891583 |
| 3 | warm | 18.800041 |
| 4 | warm | 41.890932 |

## Profile (one warm in-process call, top 15 by cumulative time)
| cumulative s | calls | function (file:line) |
|--------------|-------|----------------------|
| 35.881 | 1 | `analyze_pair_rotation` (`src/qap/api/routes/pair_rotation.py:39`) |
| 35.865 | 1 | `analyze` (`src/qap/product_pair_rotation_analysis.py:86`) |
| 22.901 | 18 | `read_parquet_bar_series` (`src/qap/market/storage.py:293`) |
| 22.218 | 1 | `projection` (`src/qap/product_market_data.py:422`) |
| 22.156 | 14 | `resolve_catalog_source` (`src/qap/scanner/catalog.py:222`) |
| 10.212 | 36 | `fingerprint_bar_series` (`src/qap/market/fingerprint.py:59`) |
| 9.382 | 6 | `load` (`src/qap/product_pair_rotation_analysis.py:117`) |
| 7.264 | 633304 | `__post_init__` (`src/qap/market/bars.py:105`) |
| 5.897 | 4 | `resolve_immutable_generation` (`src/qap/product_market_data_generation.py:39`) |
| 4.327 | 5 | `research_scope` (`src/qap/product_universe.py:181`) |
| 2.382 | 6 | `coins` (`src/qap/product_coin_search.py:48`) |
| 1.740 | 1 | `cointegration` (`src/qap/relationship/pair_measurements.py:137`) |
| 1.468 | 29621 | `public_payload_fingerprint` (`src/qap/market/microstructure.py:50`) |
| 1.456 | 6 | `registry_snapshot` (`src/qap/product_universe.py:145`) |
| 1.332 | 6 | `resolve` (`src/qap/asset_resolver.py:125`) |

## Notes
- `copula_tails` (`src/qap/relationship/dependence_measurements.py:133`) took 0.197 s in this profile (1 call).
- `read_parquet_bar_series` was called 18 times (22.901 s, 633,304 `MarketBar.__post_init__` calls) and `fingerprint_bar_series` was called 36 times (10.212 s).
- `resolve_catalog_source` was called 14 times inside `projection` (22.156 s).
- `research_scope` was called 5 times (4.327 s) and `coins` 6 times (2.382 s).
