# Phase-10 Predeclared Daily Momentum Family Result

**Date:** 2026-08-17

**Research family:** `phase10-btcusdt-daily-momentum-2023-v1`

**Precommit:** `docs/research/2026-08-17-phase10-momentum-family-precommit.json`, committed before any family economics were inspected in `9dbabe2`.

**Execution provenance:** all nine runs were executed from clean commit `7cef139a0feaaeefcc3eed50aba32b3fe087576c` with `git_dirty=false` and the same run timestamp, `2026-08-17T13:27:03+00:00`.

## Data boundary

Development used the recorded public Binance BTCUSDT daily 2023 artifact:

- path: `tests/fixtures/market/BTCUSDT_1d_2023.parquet`
- bars: `365`
- semantic fingerprint: `0cff5a7068c2d3e7957b481f826ce8ca80956191873671035a08353cfdb4d5fc`
- window: `[2023-01-01T00:00:00Z, 2024-01-01T00:00:00Z)`

The recorded 2024 daily artifact remains reserved as possible final OOS and was not referenced by any development manifest:

- path: `tests/fixtures/market/BTCUSDT_1d_2024.parquet`
- bars: `366`
- semantic fingerprint: `b3069c70fb61f1e7fb6a8b1d338194817ba8896dfd2618b96091c8c46686f2a5`
- window: `[2024-01-01T00:00:00Z, 2025-01-01T00:00:00Z)`
- final-OOS commitment status: **unconsumed**

## Frozen family

The predeclared development denominator was nine attempts:

- six core members: `30/90/180` day lookbacks crossed with narrow and wide entry bands;
- two nearby-parameter diagnostics: `60` and `120` day lookbacks under the narrow band;
- one causal-delay diagnostic: `90` day narrow-band evidence delayed by one completed daily bar.

Every member used the same starting inventory, 50/50 neutral target, no external flows, next-open execution semantics, baseline costs (`10` bps fee + `5` bps slippage), adverse costs (`20` bps fee + `10` bps slippage), strict HODL, periodic-30 primary control, and 5%-band partial secondary control.

The frozen development survivor rule required a **core** member to satisfy all three:

1. positive terminal wealth relative to strict HODL;
2. positive terminal wealth relative to periodic-30 under baseline costs;
3. positive terminal wealth relative to periodic-30 when both strategy and control are rerun under the same adverse-cost scenario.

If multiple core members survived, the predeclared selection rule was maximum primary-control-relative terminal wealth with lexicographic member ID as tie-breaker.

## Development results

| Member | Core | vs HODL | vs periodic-30 | adverse vs periodic-30 | Fills | Survivor |
|---|---:|---:|---:|---:|---:|---|
| `l30-narrow` | yes | -0.9975% | 6.6465% | 6.2511% | 258 | no |
| `l30-wide` | yes | -4.6526% | 2.7092% | 2.4189% | 249 | no |
| `l90-narrow` | yes | -8.6574% | -1.6048% | -1.8864% | 228 | no |
| `l90-wide` | yes | -4.9859% | 2.3501% | 2.1956% | 209 | no |
| `l180-narrow` | yes | -3.8821% | 3.5392% | 3.3859% | 161 | no |
| `l180-wide` | yes | -4.7277% | 2.6283% | 2.5158% | 158 | no |
| `nearby-l60-narrow` | no | -5.7916% | 1.4822% | 1.2195% | 260 | no |
| `nearby-l120-narrow` | no | -3.5758% | 3.8691% | 3.6128% | 197 | no |
| `delay-l90-narrow-1bar` | no | -8.1911% | -1.1025% | -1.4046% | 228 | no |

The percentages above are presentation summaries of exact persisted Decimal results. The immutable run artifacts under the local ignored research run root retain the exact values, role economics, costs, fills, and provenance.

## Interpretation

The small family provides a stronger falsification result than the earlier 12-bar protocol fixture:

- **No core member beats HODL.** This alone prevents development survival under the predeclared rule.
- Several members beat periodic-30, including under symmetric adverse costs, but that does not rescue a strategy that destroys wealth relative to the stricter passive counterfactual.
- The best core primary-control increment is `l30-narrow` at approximately `+6.65%` versus periodic-30, yet it remains approximately `-1.00%` versus HODL.
- Nearby lookbacks do not reveal a hidden robust HODL-beating region. The 60- and 120-day diagnostics remain negative versus HODL.
- A one-bar causal delay does not rescue the 90-day narrow member; it remains negative versus both HODL and periodic-30.
- High fill counts and explicit modeled costs remain material, so the result does not support stronger trend-alpha language.

## Holdout decision

**No 2024 final-OOS evaluation is consumed.** The predeclared rule says the reserved holdout is used only if at least one core development member survives. The development survivor count is zero, so consuming final OOS would spend information without a candidate justified for promotion.

This is a negative research result, not a protocol failure. The 2024 artifact remains available for a future research generation only if a new candidate family is independently motivated and predeclared without using that holdout for tuning.

## Phase-10 conclusion

The simple-first momentum gate is now empirically exercised on a real recorded daily market window with an explicit family denominator, nearby-parameter diagnostic, symmetric adverse-cost comparison, and causal-delay diagnostic. It does **not** establish slow-momentum alpha for this BTCUSDT setup. Richer relationship models therefore cannot cite momentum as a successful predictive prior here, and no deployment or final-OOS authority follows from this family.
