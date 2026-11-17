# Stage S4-B — Low-Turnover Tail Copula & Crash-Defense Discovery Results (2026-11-15)

Update context — 2026-11-16
Trigger: Audit repair AR-7 ([Plan 25](../plans/25-audit-repairs-and-evidence-integrity.md), [2026-11-16 audit](2026-11-16-audit/README.md)).
Purpose: Correct the turnover-ratio generalization, document percentage denominators and add-back gross semantics, and qualify the post-fix `park_anchor` evidence while keeping all 12 preregistered rows and raw JSONL immutable.
Impact: Clarifies interpretation only; original `0/12` Holm result and blocked rows `S4B-07`..`S4B-10` remain unchanged.
Evidence: [2026-11-15-stage-s4b-trial-plan.json](2026-11-15-stage-s4b-trial-plan.json), [2026-11-15-stage-s4b-trials.jsonl](2026-11-15-stage-s4b-trials.jsonl), commit `7f0f7e3`.

**Dated Corrections (2026-11-16):**
- **Turnover & 2× Cost Gate (correcting Finding #2 below):** Lower turnover is *not* mathematically incapable of improving net economics or the tuning gross-to-cost ratio. Eliminating trades whose expected gross spread is below `2 × cost` raises both net return and the gross-to-cost ratio. On S4-B's specific sample, the 1d and 2%-tail rules compressed gross gain alongside cost, so those configurations failed the gate without proving scale-invariance in general.
- **Add-Back Gross & Denominators:** `gross_vs_hodl_pct` and `tuning_gross_vs_hodl_pct` are cost add-back approximations `((terminal + paid_costs) / HODL_end - 1) * 100`, not zero-cost counterfactual replays. `cost_paid_pct` and `tuning_cost_pct` divide by starting capital, while `vs_hodl_pct` divides by ending HODL wealth; the monetary `cost_budget_multiple` gate compares USDT dollars directly (`tuning_gross >= 2 * tuning_cost`).
- **Post-Fix `park_anchor` Qualification:** Commit `7f0f7e3` resolved third-asset `park_anchor` metadata loading in `src/qap/product_lab_inputs.py` and `src/qap/product_lab_study.py`, and [TASKS.md](../../TASKS.md) notes an ad-hoc `AVAX/SOL` `-4.67%` observation after that fix. No saved rerun JSONL or immutable study artifact is archived alongside [2026-11-15-stage-s4b-trials.jsonl](2026-11-15-stage-s4b-trials.jsonl), so `S4B-07`..`S4B-10` remain recorded as `blocked` in the preregistered S4-B record.

- **Actor ID:** `stage-s4b-20261115`
- **Preregistration:** [2026-11-15-stage-s4b-trial-plan.json](2026-11-15-stage-s4b-trial-plan.json) (written before any trial ran)
- **Raw trials:** [2026-11-15-stage-s4b-trials.jsonl](2026-11-15-stage-s4b-trials.jsonl) (12 lines, one per preregistered trial)
- **Trials:** 12 preregistered single-shot (`auto_tune: false`) trials — 5 × 4h `2%`-tail BTC-anchored copula (`coins_only`), 1 × 4h `2%`-tail ETH-anchored copula (`LTC/BTC`, `coins_only`), 4 × 4h BTC-anchored copula with `park_anchor` crash defense, 2 × 1d Kalman z-score
- **Family Correction:** Holm-Bonferroni step-down at `alpha = 0.05` across all 12 trials (family size held at the preregistered 12; blocked trials enter at `p = 1.0` and cannot pass)
- **Holm Survivors:** 0 / 12
- **Executed:** 8 / 12 — the 4 `park_anchor` trials are **blocked by a code defect**, not by the market (see [Blocked arm](#blocked-arm-park_anchor-cannot-execute-in-this-worktree))

## Trial Table

| trial_id | pair | bar | method/defense | call | passes | vs_hodl_pct | vs_control_pct | gross_vs_hodl_pct | cost_paid_pct | tuning_gross_vs_hodl_pct | tuning_cost_pct | cost_gate_passed | folds_passing | validation_trades | settings_tried | raw_p_value | corrected_p_value | holm_survives |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S4B-01 | SOL/ETH | 4h | copula(BTC) coins_only | cost_budget_failed | False | -2.86 | -2.86 | 0.22 | 3.01 | -6.28 | 3.03 | False | 2/8 | 24 | 1 | 1.0000 | 1.0000 | False |
| S4B-02 | BNB/ETH | 4h | copula(BTC) coins_only | cost_budget_failed | False | -2.01 | -2.01 | 0.05 | 2.08 | 3.51 | 3.48 | False | 3/8 | 19 | 1 | 1.0000 | 1.0000 | False |
| S4B-03 | LINK/ETH | 4h | copula(BTC) coins_only | cost_budget_failed | False | 4.28 | 3.81 | 7.00 | 2.82 | 6.01 | 4.60 | False | 4/8 | 19 | 1 | 0.3066 | 0.3066 | False |
| S4B-04 | AVAX/SOL | 4h | copula(BTC) coins_only | cost_budget_failed | False | -6.77 | -7.61 | -1.91 | 5.13 | 10.22 | 5.87 | False | 4/8 | 22 | 1 | 1.0000 | 1.0000 | False |
| S4B-05 | DOGE/XRP | 4h | copula(BTC) coins_only | cost_budget_failed | False | 16.50 | 16.22 | 22.90 | 5.57 | 5.08 | 6.24 | False | 5/8 | 27 | 1 | 0.0220 | 0.0220 | False |
| S4B-06 | LTC/BTC | 4h | copula(ETH) coins_only | cost_budget_failed | False | -5.07 | -6.09 | -1.71 | 3.40 | 6.81 | 4.64 | False | 3/8 | 25 | 1 | 1.0000 | 1.0000 | False |
| S4B-07 | AVAX/SOL | 4h | copula(BTC) park_anchor | blocked | False | – | – | – | – | – | – | – | – | – | – | – | 1.0000 | False |
| S4B-08 | SOL/ETH | 4h | copula(BTC) park_anchor | blocked | False | – | – | – | – | – | – | – | – | – | – | – | 1.0000 | False |
| S4B-09 | LINK/ETH | 4h | copula(BTC) park_anchor | blocked | False | – | – | – | – | – | – | – | – | – | – | – | 1.0000 | False |
| S4B-10 | DOGE/XRP | 4h | copula(BTC) park_anchor | blocked | False | – | – | – | – | – | – | – | – | – | – | – | 1.0000 | False |
| S4B-11 | DOGE/XRP | 1d | zscore(kalman) coins_only | cost_budget_failed | False | 0.31 | 0.06 | 1.90 | 1.32 | 0.57 | 0.47 | False | 5/8 | 7 | 3 | 0.5030 | 1.0000 | False |
| S4B-12 | LINK/ETH | 1d | zscore(kalman) coins_only | cost_budget_failed | False | 10.92 | 9.88 | 11.84 | 0.91 | 0.30 | 0.62 | False | 5/8 | 7 | 3 | 0.1323 | 0.3968 | False |

`blocked` = the study command exited non-zero before producing a proof; no economics exist for those rows. `settings_tried` is the cumulative per-family configuration count in the actor's trial registry, not a per-trial count.

## Holm-Bonferroni Step-Down (alpha = 0.05, n = 12)

Sorted by `study.proof.corrected_p_value`; rank `k` is 0-indexed and the threshold is `0.05 / (12 - k)`. A trial survives only if `corrected_p_value <= threshold` **and** `study.proof.passes is True`.

| k | trial_id | corrected_p_value | threshold 0.05/(12-k) | proof.passes | survives |
|---|---|---|---|---|---|
| 0 | S4B-05 | 0.0220 | 0.0042 | False | False |
| 1 | S4B-03 | 0.3066 | 0.0045 | False | False |
| 2 | S4B-12 | 0.3968 | 0.0050 | False | False |
| 3 | S4B-01 | 1.0000 | 0.0056 | False | False |
| 4 | S4B-02 | 1.0000 | 0.0063 | False | False |
| 5 | S4B-04 | 1.0000 | 0.0071 | False | False |
| 6 | S4B-06 | 1.0000 | 0.0083 | False | False |
| 7 | S4B-07 | 1.0000 | 0.0100 | False | False |
| 8 | S4B-08 | 1.0000 | 0.0125 | False | False |
| 9 | S4B-09 | 1.0000 | 0.0167 | False | False |
| 10 | S4B-10 | 1.0000 | 0.0250 | False | False |
| 11 | S4B-11 | 1.0000 | 0.0500 | False | False |

The step-down stops at `k = 0`: the smallest p-value in the family (`S4B-05`, `0.0220`) already exceeds its threshold (`0.0042`) by a factor of 5.2, and its `proof.passes` is `False` regardless. No trial is promoted.

## Before-vs-After Against S4-A

S4-A ran the same three pairs at 4h with `copula(BTC)`, `copula_probability = 0.05`, default `minimum_hold`/`cooldown` (4/4), and the default `crash_defense_mode = "coins_only"`. S4-B tightens the tail to `2%`, sets `minimum_hold = 12` / `cooldown = 8`, and sets `band_lookback = 180` (S4-A used the CLI default 672).

`band_lookback` only feeds `ratio_bands` in the analysis; the copula signal is `rolling_spread_copula(a, b, window=settings.lookback, anchor=anchor)` (`src/qap/policy/lab_signals.py:46`), so the band change does not enter the traded signal and the comparison below is like-for-like on the signal path.

| pair | S4-A trial | S4-B trial | validation trades | cost_paid_pct | vs_hodl_pct | folds_passing | tuning gross/cost ratio |
|---|---|---|---|---|---|---|---|
| LINK/ETH | S4-11 | S4B-03 | 24 → 19 (−5, −20.8%) | 4.16 → 2.82 (−1.34, −32.2%) | 7.14 → 4.28 | 5 → 4 | 1.16 → 1.31 |
| AVAX/SOL | S4-15 | S4B-04 | 34 → 22 (−12, −35.3%) | 7.18 → 5.13 (−2.05, −28.6%) | −18.11 → −6.77 | 3 → 4 | 1.13 → 1.74 |
| DOGE/XRP | S4-19 | S4B-05 | 37 → 27 (−10, −27.0%) | 8.21 → 5.57 (−2.65, −32.2%) | 15.55 → 16.50 | 5 → 5 | 1.18 → 0.81 |

**The `park_anchor` half of this comparison does not exist.** S4-A ran every copula trial with the default `coins_only`, so there is no S4-A `park_anchor` baseline, and S4-B's four `park_anchor` trials are blocked. The crash-defense hypothesis is therefore **untested**, not refuted.

## Blocked Arm: `park_anchor` Cannot Execute in This Worktree

All four `park_anchor` trials (`S4B-07`..`S4B-10`) exit with `{"error": "BTC: missing_market_metadata"}` (exit code 2) before any proof is produced.

Root cause, confirmed by direct inspection of the resolved inputs:

- `src/qap/product_lab_inputs.py:100-107` builds the market-metadata tuple as `item for item in instruments if item != anchor or item in (first, second, direct)`. The anchor instrument is dropped unless it is also a pair leg.
- `src/qap/experiment/lab_replay.py:248` then passes `require_market_metadata=bool(metadata)`. Because the pair legs do have metadata, the flag is `True`, and the park order's `USDT → BTC` leg has no metadata entry.
- `src/qap/execution/multi_asset.py:171-175` raises `MultiAssetPreflightError(BTC, "missing_market_metadata")`.

Verified directly: for `AVAX/SOL` with a BTC anchor the resolved metadata set is `['AVAXUSDT', 'SOLUSDT']` — `BTCUSDT` is absent even though its snapshot exists on disk. For `LTC/BTC` with a BTC anchor the set is `['LTCUSDT', 'BTCUSDT', 'LTCBTC']`, because BTC is a pair leg there. So `park_anchor` only works when the anchor is one of the two traded coins, which is never the case for a third-asset crash hedge.

`tests/unit/experiment/test_lab_crash_defense.py` covers `park_anchor` only for the *missing anchor* case (`execution_data_missing`); there is no test for `park_anchor` with a resolved third-asset anchor through the product lab path, which is why the gap is not caught.

Two side effects of the blocked runs, both conservative:

1. `register_trials` runs before the replay, so the blocked configurations were recorded. `S4B-11` and `S4B-12` therefore report `settings_tried = 3` instead of 1, and their `corrected_p_value` is Bonferroni-inflated across 3 settings (`S4B-11`: raw `0.5030` → corrected `1.0000`; `S4B-12`: raw `0.1323` → corrected `0.3968`).
2. The blocked registrations overlap the 1d validation windows, so `S4B-11` and `S4B-12` carry `validation_reused: true`.

Neither effect can turn a failing trial into a passing one.

## Key Findings

1. **Zero Holm survivors (0/12).** No trial cleared the 2× tuning cost-budget gate, the walk-forward fold requirement, and Holm-Bonferroni at `alpha = 0.05`. This matches S4-A's 0/24.
2. **Turnover reduction worked mechanically but cannot move the gate.** Against their S4-A counterparts, trades fell 21–35% and validation cost fell 29–32%. The gate is `tuning_gross >= 2 × tuning_cost` (`src/qap/experiment/lab_proof.py:248`) — a *ratio*, so scaling turnover down scales both sides and leaves the ratio roughly unchanged. Best ratio achieved was `1.74` (`S4B-04`), still short of `2.0`.
3. **The 1d arm is the decisive evidence.** `S4B-12` (`LINK/ETH`, 1d) cut cost to `0.91%` and traded only 7 times, yet its tuning gross was `0.30%` against a `1.23%` requirement — ratio `0.49`. `S4B-11` (`DOGE/XRP`, 1d) landed at `1.20`. Ultra-low turnover compresses the edge as fast as it compresses the cost, so the gate stays shut. Passing it needs *edge per unit of cost*, not less trading.
4. **`S4B-05` (`DOGE/XRP`, 4h) is the only statistically interesting row and still fails.** `+16.50%` vs HODL, `+16.22%` vs the drift control, `5/8` folds, raw `p = 0.0220` — but tuning gross `5.08%` against a `12.48%` requirement, so `cost_budget_failed`. Even ignoring the gate, `0.0220 > 0.0042` at Holm rank 0.
5. **`S4B-12` is the most capital-efficient row.** `+10.92%` vs HODL on `0.91%` cost with 7 trades and `5/8` folds — the best return-per-cost in the family — but its tuning-period edge was too thin to clear the gate, and `corrected_p_value = 0.3968`.
6. **The crash-defense hypothesis is untested.** The four `park_anchor` trials never reached the replay. No conclusion about secular-bleed protection can be drawn from S4-B.
7. **`S4B-06` (`LTC/BTC` with an ETH anchor) ran cleanly.** The stored analysis records `anchor = binance:ETH` with a populated `anchor_close` series, and `ETHUSDT` appears in the resolved datasets at 4h. No `prepare` step was required for any of the 12 trials — the ETH anchor and the 1d bars were already prepared.

## Honest Next Step

Do not promote any S4-B configuration to live-paper. Two concrete follow-ups:

1. **Fix the anchor-metadata plumbing before re-running the crash-defense arm.** The one-line change is in `src/qap/product_lab_inputs.py:100-107`: include the anchor instrument in the `read_lab_metadata` tuple whenever `settings.crash_defense_mode == "park_anchor"` (or unconditionally, since the snapshot is already on disk). Add a product-path test with a third-asset anchor. Then re-run `S4B-07`..`S4B-10` unchanged — the preregistration is already on disk and the family size stays 12.
2. **Stop searching for a turnover fix for the 2× gate.** S4-B shows the gate is scale-invariant, so lower turnover cannot pass it. Either the gate's economic definition needs revisiting (it currently demands a 2:1 gross-to-cost ratio *in the tuning window*, which no pair in this universe achieved), or the search must target higher gross edge per rotation — a different research question from S4-B's.
