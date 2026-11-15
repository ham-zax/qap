# Pair Rotation Lab — Honest Earning Answer (L5, 2026-10-27)

Evidence source: `docs/research/2026-10-27-lab-earning-trials.json` (10 predeclared trials, `15m` bars, `180` days, `band_lookback=672`, 8 folds, `auto_tune=true`, `LabSettings` default costs: 10 bps fee, 5 bps slippage, 10 bps impact).

## Verdict

**0 of 10 trials passed.** None of the tested rules beat matched HODL or the predeclared rebalancing control after realistic costs (`corrected_p_value = 1.0` for all 10 trials). QAP has **no demonstrated earning edge** yet and must remain research-only (no live capital).

## Per-trial results

Gross vs HODL (approx.) is computed from `strategy - hodl + fees_usdt + slippage_usdt` on the 10,000 USDT starting capital.

| Trial | Pair | Method | Call | vs HODL | vs Control | Folds | Val. trades | Fees + Slippage (USDT) | Approx. Gross vs HODL (USDT) | Corrected p |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `SOL/ETH` | `zscore` | `cost_budget_failed` | -2.74% | -2.74% | 0/8 | 98 | 406.68 | +239.97 | 1.0 |
| 2 | `BNB/ETH` | `zscore` | `cost_budget_failed` | -4.68% | -4.68% | 1/8 | 86 | 365.78 | +48.62 | 1.0 |
| 3 | `LINK/ETH` | `zscore` | `cost_data_missing` | -4.93% | -5.35% | 2/8 | 91 | 484.30 | +164.67 | 1.0 |
| 4 | `AVAX/SOL` | `zscore` | `cost_budget_failed` | -3.49% | -3.49% | 4/8 | 84 | 611.88 | +400.83 | 1.0 |
| 5 | `DOGE/XRP` | `zscore` | `cost_budget_failed` | -6.14% | -6.22% | 0/8 | 91 | 601.33 | +251.02 | 1.0 |
| 6 | `ADA/DOT` | `zscore` | `cost_budget_failed` | -5.44% | -5.44% | 2/8 | 100 | 856.33 | +537.79 | 1.0 |
| 7 | `LTC/BTC` | `zscore` | `cost_budget_failed` | -6.16% | -6.51% | 1/8 | 99 | 838.88 | +390.55 | 1.0 |
| 8 | `SOL/ETH` | `trend` | `cost_budget_failed` | -17.99% | -17.99% | 0/8 | 142 | 1,291.11 | +197.97 | 1.0 |
| 9 | `SOL/ETH` | `copula` | `cost_budget_failed` | -30.80% | -30.80% | 0/8 | 687 | 2,762.04 | +890.22 | 1.0 |
| 10 | `LINK/ETH` | `trend` | `cost_data_missing` | -31.78% | -32.10% | 0/8 | 147 | 2,668.62 | +611.50 | 1.0 |

## Bottleneck & Critical-Thinking Diagnosis

1. **Turnover costs overwhelm `15m` signals.** Every `zscore` trial executed 84–100 validation trades (~366–856 USDT in fees and slippage). Even where the approximate gross spread over HODL was positive (+49 to +538 USDT), trading costs consumed 1.5x to 7.5x of that gross edge.
2. **`trend` and `copula` severely over-trade on `15m` bars.** `trend` triggered 142–147 trades (1,291–2,669 USDT in costs) and `copula` triggered 687 trades (2,762 USDT in costs, losing 30.80% vs HODL).
3. **Missing cost metadata on `LINK/ETH`.** Trials 3 and 10 returned `cost_data_missing`, preventing the 2x tuning cost gate from evaluating them.

## Improvement Plan (Stage B, no boundary changes)

1. **Shift to slower bars (`1h` and `4h`) per `docs/research/2026-10-27-preregistration-h1-h3.md`.** Slower bars reduce trade count and increase expected move per rotation relative to fixed fee/slippage/impact.
2. **Add turnover/hysteresis discipline before running H1–H3.** Require wider entry/exit bands or minimum hold periods in `LabSettings` tuning grids, especially for `trend` and `copula`.
3. **Resolve `LINK/ETH` cost-data coverage** before including `LINK/ETH` in Stage B preregistered trials.
4. **Escalation boundary:** Do not alter the economic objective (wealth vs HODL and control), cost/fill semantics, fold/significance rules, `final_oos` holdout role, or point-in-time universe eligibility (Stage C) without explicit approval from Hamza.
