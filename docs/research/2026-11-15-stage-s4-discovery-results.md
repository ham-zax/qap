# Stage S4-A — Preregistered 1h / 4h Strategy Discovery Results (2026-11-15)

Update context — 2026-11-16
Trigger: Audit repair AR-7 ([Plan 25](../plans/25-audit-repairs-and-evidence-integrity.md), [2026-11-16 audit](2026-11-16-audit/README.md)).
Purpose: Clarify S4-A's `qap.lab.proof.v1` numerical-resolution limit and percentage denominators without modifying original trial outcomes or raw JSONL.
Impact: None on original `0/24` rejection; higher bootstrap resolution (`9,999` replicates in `qap.lab.proof.v2`) does not imply any rejected S4-A trial passes.
Evidence: [2026-11-15-stage-s4-trial-plan.json](2026-11-15-stage-s4-trial-plan.json), [2026-11-15-stage-s4-trials.jsonl](2026-11-15-stage-s4-trials.jsonl), and `src/qap/experiment/lab_proof.py`.

**Dated Corrections (2026-11-16):**
- **Bootstrap Resolution Limit (v1):** S4-A ran under `qap.lab.proof.v1` with `499` SPA bootstrap replicates (`raw_p_value >= 1/500 = 0.002`) and cumulative per-pair configuration multipliers up to `12` (`corrected_p_value >= 0.006`–`0.024`). Even at the minimum nonzero p-value, `corrected_p_value` exceeded the first Holm threshold `0.05 / 24 = 0.002083`. That finite-sample ceiling prevented statistical survival regardless of effect size, alongside S4-A's independent `cost_budget_failed` / `no_edge` failures. Repairing bootstrap resolution in `qap.lab.proof.v2` does not convert any S4-A trial into a pass.
- **Add-Back Gross & Denominators:** `gross_vs_hodl_pct` in the table is a cost add-back approximation `((terminal_value + paid_costs) / HODL_end - 1) * 100`, not a zero-cost replay. `cost_paid_pct` divides paid fees and slippage by starting portfolio value (`10,000`), whereas `vs_hodl_pct` and `gross_vs_hodl_pct` divide by ending HODL wealth.

- **Actor ID:** `stage-s4-20261115`
- **Trials:** 24 preregistered trials across 6 liquid Binance pairs (`SOL/ETH`, `BNB/ETH`, `LINK/ETH`, `AVAX/SOL`, `DOGE/XRP`, `LTC/BTC`)
- **Family Correction:** Holm-Bonferroni step-down at `alpha = 0.05` across all 24 trials (building on within-pair SPA + Bonferroni `corrected_p_value`)
- **Holm Survivors:** 0 / 24

| trial_id | pair | bar | method | call | vs_hodl_pct | vs_control_pct | gross_vs_hodl_pct | cost_paid_pct | folds_passing | validation_trades | corrected_p_value | holm_survives |
|----------|------|-----|--------|------|-------------|----------------|-------------------|---------------|---------------|-------------------|-------------------|---------------|
| S4-01 | SOL/ETH | 1h | zscore(kalman) | cost_budget_failed | -0.62 | -0.62 | 6.89 | 4.75 | 4/8 | 56 | 1.0000 | False |
| S4-02 | SOL/ETH | 1h | zscore(ols) | cost_budget_failed | -2.41 | -2.41 | 3.30 | 5.51 | 4/8 | 47 | 1.0000 | False |
| S4-03 | SOL/ETH | 4h | copula(BTC) | cost_budget_failed | -5.39 | -5.39 | -1.97 | 3.35 | 2/8 | 30 | 1.0000 | False |
| S4-04 | SOL/ETH | 4h | trend | no_edge | -0.89 | -0.89 | 1.01 | 1.21 | 4/8 | 16 | 1.0000 | False |
| S4-05 | BNB/ETH | 1h | zscore(kalman) | cost_budget_failed | -0.74 | -0.74 | 2.90 | 2.56 | 4/8 | 32 | 1.0000 | False |
| S4-06 | BNB/ETH | 1h | zscore(ols) | cost_budget_failed | 4.28 | 4.28 | 9.31 | 5.02 | 4/8 | 44 | 1.0000 | False |
| S4-07 | BNB/ETH | 4h | copula(BTC) | cost_budget_failed | 0.84 | 0.84 | 4.58 | 3.76 | 5/8 | 30 | 1.0000 | False |
| S4-08 | BNB/ETH | 4h | trend | no_edge | 1.68 | 1.76 | 3.36 | 1.19 | 5/8 | 14 | 1.0000 | False |
| S4-09 | LINK/ETH | 1h | zscore(kalman) | cost_budget_failed | -5.31 | -5.60 | -1.19 | 2.81 | 4/8 | 30 | 1.0000 | False |
| S4-10 | LINK/ETH | 1h | zscore(ols) | cost_budget_failed | -7.57 | -7.96 | -1.65 | 6.09 | 2/8 | 29 | 1.0000 | False |
| S4-11 | LINK/ETH | 4h | copula(BTC) | cost_budget_failed | 7.14 | 6.66 | 11.16 | 4.16 | 5/8 | 24 | 1.0000 | False |
| S4-12 | LINK/ETH | 4h | trend | cost_budget_failed | -6.86 | -7.15 | -4.82 | 1.40 | 2/8 | 15 | 1.0000 | False |
| S4-13 | AVAX/SOL | 1h | zscore(kalman) | cost_budget_failed | -3.75 | -3.75 | 3.20 | 4.35 | 4/8 | 30 | 1.0000 | False |
| S4-14 | AVAX/SOL | 1h | zscore(ols) | cost_budget_failed | -3.66 | -4.56 | 3.81 | 7.83 | 5/8 | 35 | 1.0000 | False |
| S4-15 | AVAX/SOL | 4h | copula(BTC) | cost_budget_failed | -18.11 | -18.86 | -11.32 | 7.18 | 3/8 | 34 | 1.0000 | False |
| S4-16 | AVAX/SOL | 4h | trend | no_edge | -10.62 | -10.62 | -7.86 | 1.75 | 2/8 | 10 | 1.0000 | False |
| S4-17 | DOGE/XRP | 1h | zscore(kalman) | cost_budget_failed | -6.52 | -6.69 | 3.22 | 5.81 | 1/8 | 46 | 1.0000 | False |
| S4-18 | DOGE/XRP | 1h | zscore(ols) | cost_budget_failed | 1.14 | 0.83 | 13.39 | 10.57 | 4/8 | 56 | 1.0000 | False |
| S4-19 | DOGE/XRP | 4h | copula(BTC) | cost_budget_failed | 15.55 | 15.28 | 25.00 | 8.21 | 5/8 | 37 | 0.2345 | False |
| S4-20 | DOGE/XRP | 4h | trend | cost_budget_failed | -12.03 | -12.12 | -6.44 | 3.36 | 1/8 | 26 | 1.0000 | False |
| S4-21 | LTC/BTC | 1h | zscore(kalman) | cost_budget_failed | -4.18 | -4.82 | 1.27 | 4.03 | 2/8 | 34 | 1.0000 | False |
| S4-22 | LTC/BTC | 1h | zscore(ols) | cost_budget_failed | -0.34 | -1.36 | 5.67 | 6.03 | 5/8 | 37 | 1.0000 | False |
| S4-23 | LTC/BTC | 4h | copula | cost_budget_failed | -4.07 | -5.11 | 0.91 | 5.05 | 3/8 | 34 | 1.0000 | False |
| S4-24 | LTC/BTC | 4h | trend | cost_budget_failed | 1.63 | 1.21 | 4.30 | 2.00 | 4/8 | 16 | 1.0000 | False |

## Key Findings

1. **Zero Holm Survivors (0/24):** None of the 24 preregistered trials survived both the 2x tuning cost-budget gate / walk-forward proof gates and Holm-Bonferroni at `alpha = 0.05`.
2. **Cost-Data Resilience Verified:** `LINK/ETH` ran cleanly across all 4 trials without `cost_data_missing` thanks to the trailing-20-bar median volume fallback (`S2-A`).
3. **Notable Gross/Net Observation:** `DOGE/XRP` 4h `copula(BTC)` achieved `+15.55%` vs HODL (`corrected_p_value = 0.2345`), but failed the strict 2x tuning-period cost-budget gate (`cost_budget_failed`).
4. **Honest Next Step:** No strategy is promoted to live-paper on the basis of S4-A alone; further research should focus on lower-turnover / higher-spread regimes or parameter-free controls without reusing `final_oos`.
