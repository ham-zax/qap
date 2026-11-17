# RD-1 — Research-Policy Decision Proposal Before Strategy Admission Changes

Date: 2026-11-16.
Status: proposal delivered — **pending explicit approval**; no new strategy trials run; research contracts unchanged.
Authoritative plan: [Plan 25](../plans/25-audit-repairs-and-evidence-integrity.md).
Audit source: [2026-11-16 Audit](2026-11-16-audit/README.md).
Completion note: [Audit Repair Completion](../reviews/2026-11-16-audit-repair-completion.md).

Update context — 2026-11-17
Trigger: review of this proposal against the current signal, statistics, and ledger source.
Purpose: correct misleading or incomplete claims, separate current behavior from proposed contracts, and record the freeze blockers that remain open.
Impact: no research contract changed and no policy adopted. The experiment specification is downgraded from "frozen" to a draft pending completion and approval. `final_oos` untouched.
Evidence: [lab_strategy_registry.py](../../src/qap/policy/lab_strategy_registry.py), [lab_features.py](../../src/qap/relationship/lab_features.py), [lab_copula.py](../../src/qap/relationship/lab_copula.py), [lab_statistics.py](../../src/qap/experiment/lab_statistics.py), [product_lab_store.py](../../src/qap/product_lab_store.py), [lab_settings.py](../../src/qap/policy/lab_settings.py).

## Purpose and Authority

This document delivers the `RD-1` research-policy proposal required by Plan 25 before any change to model-admission thresholds, multiple-testing correction structure, or benchmark controls.
No new strategy trials ran, no `final_oos` data was inspected, and no existing research contract (`PortfolioState`, matched HODL, simple rebalancing control, next-open historical fills, 2x tuning cost gate, or `tests/invariants/test_quant_compiler_laws.py`) was relaxed.

The new model-admission rules, attribution controls, and experiment-wide ledger in §2–§5 are **proposals**.
Existing dual benchmarks and SPA settings remain implemented. The current signal path applies no cointegration, stationarity, or independence gate (see §1.1).

## 1. Per-Method Assumptions, Variables, and Structural-Break Treatment

The "formation-only requirement" and "proposed structural-break rule" columns are proposed contracts, not current behavior.
§1.1 states what the inspected code does today.

| Method family | Traded residual / signal variable | Formation-only requirement (proposed) | Key assumptions | Proposed structural-break / breakdown rule (requires approval) |
| --- | --- | --- | --- | --- |
| `Z-Score` (`ratio`) | Normalized price ratio `(A/A_0)/(B/B_0)` minus rolling mean, scaled by rolling std | Lookback & entry/exit thresholds tuned on train split only | 1:1 normalized price ratio mean-reverts over `lookback` | Abstain or exit to neutral if rolling variance collapses (`< 1e-12`) or half-life exceeds `2 * lookback` |
| `Z-Score` (`ols` / `tls`) | `log(A) - alpha - beta * log(B)` | Regression `(alpha, beta)` fit strictly on trailing window `<= t-1` | Stationary cointegrating residual over fit window | Require formation-window residual stationarity check before admission; monitor rolling residual drift |
| `Z-Score` (`kalman`) | Adaptive state-space filtered residual `log(A) - alpha_t - beta_t * log(B)` (not a forecast innovation) | Initial state & process/obs noise fixed before validation | Time-varying linear relationship with bounded drift | Do not label adaptive Kalman residuals as fixed-equilibrium spreads; hold current inventory if residual variance spikes above 3x formation median |
| `Spread Copula` (`direct`) | Rolling detrended log-price deviations `(d_A, d_B)` | Empirical/parametric copula fit per refit block on trailing data | Stationary marginal deviations & stable conditional rank | **Must beat a matched univariate-deviation control** (see §2) |
| `Spread Copula` (`anchored`) | Rolling anchor-regression residuals `(r_A, r_B)` on `log(anchor)` | Anchor regressions & copula fit strictly on trailing formation/refit data | Both `A~anchor` and `B~anchor` residuals are stationary and coupled | Admit only when formation-window asset-anchor stationarity and dependence checks pass (see §3) |
| `Ratio Trend` | Rolling trend/momentum on `log(A/B)` with deadband hysteresis | Lookback & deadband tuned on train split only | Directional persistence exceeds 2x spot friction | Regime-filter or abstention when realized volatility < friction threshold |
| `Anchor Lead-Lag 1m` | Contemporaneous anchor-beta residual on `1m` returns (see §1.1) | Lead-lag beta estimated on trailing `1m` window | Short-horizon information propagation survives `1m` execution delay | Halt signal if lagged `R^2` or cross-correlation drops below formation floor (neither statistic is computed today; adding one is a new method, not a repair) |

### 1.1 Current behavior versus proposed contract

Inspected at this revision. Nothing in this table is a change request.

| Method family | Current behavior (inspected) | Proposed change (requires approval) |
| --- | --- | --- |
| `Z-Score` (`ratio`) | `hedge_residual` returns the normalized ratio; `trailing_zscore` scales it by a trailing window | None stated |
| `Z-Score` (`ols` / `tls`) | `hedge_residual` fits `beta` and a rolling intercept on the trailing `lookback` window that **includes the current completed candle**, so the residual at bar `t` uses bar `t`'s own close. The preference is then applied to the next bar's open, so the fit remains causal for next-open execution. | Fit strictly on `<= t-1`. This is a proposed change, not current behavior, and it needs approval because it changes historical signal values. |
| `Z-Score` (`kalman`) | Sequential intercept/slope filter observing each completed price once | None stated |
| `Spread Copula` (`direct`) | Per refit block, a copula is fit on the formation slice of detrended deviations and evaluated on the following block | Matched univariate-deviation control (§2) |
| `Spread Copula` (`anchored`) | Per refit block, anchor betas and intercepts are fit on the formation slice only, then applied to the evaluation block | Formation-window stationarity and independence admission (§3) |
| `Ratio Trend` | Fast/slow trailing means of the cumulative log ratio, differenced against a deadband | None stated |
| `Anchor Lead-Lag 1m` | **Contemporaneous anchor-beta residual, not cross-correlation or lagged-beta inference.** Betas come from the trailing return window `[r-lookback, r)`. The residual uses the same-bar anchor and asset returns at return index `r`. Each return spans price indices `r` to `r+1`, so storage at `values[r+1]` aligns the residual with the current completed candle. This indexing adds no extra one-bar delay. No cross-correlation estimate or lead-lag test is computed. | Any genuine lagged-beta or cross-correlation inference is unimplemented and would be a new method, not a repair |

No cointegration, stationarity, or independence admission check exists in the current signal path.
`cointegration` is a descriptive measurement consumed by the advisor and the pair analysis; the signal path (`lab_signals.py` → `lab_strategy_registry.py` → `lab_copula.py`) applies no cointegration, stationarity, or independence gate.
The §3 admission rules are therefore proposals to add checks, not descriptions of existing ones.

## 2. Direct Filtered-Deviation Copula Claim Resolution

- **Decision question:** Does a direct filtered-deviation copula (`lab_copula` without an anchor) claim cross-asset dependence or only a univariate mean-reversion/deviation effect?
- **Proposed contract change:** Treat direct filtered-deviation copula as **unproven cross-asset dependence** unless it outperforms a **matched univariate-deviation control** (each leg scored on its own trailing detrended quantile without cross-asset copula conditioning) on net validation wealth after costs.
- **Approval evidence required:** Side-by-side paired comparison across liquid pairs showing positive incremental net wealth after costs over both matched HODL and the univariate-deviation control (report max drawdown separately as a diagnostic, not an added acceptance condition).

## 3. Anchor-Residual Stationarity, Independence Abstention, and Sample Sufficiency

- **Current gap:** `lab_copula` emits finite conditional ranks on independent random walks (`coint p = [0.332, 0.110]`), and default `lookback = 96` is below the 100-observation minimum of the existing cointegration helper.
- **Proposed contract:**
  1. **Sample sufficiency:** Require exact formation window `formation_bars = max(120, lookback)` (`120` bars minimum for `lookback = 96`) for cointegration-gated admission without weakening locked `tests/invariants/test_quant_compiler_laws.py`.
  2. **Stationarity admission:** On formation data only, require both `(A, anchor)` and `(B, anchor)` residual series to pass Engle-Granger cointegration at `p <= 0.05` before enabling anchored copula trading.
  3. **Independence abstention:** Near-zero Kendall's tau or Spearman's rho does not exclude nonlinear dependence, so a rank-correlation screen alone is not sufficient evidence of independence. Chatterjee's xi (`scipy.stats.chatterjeexi`, available in the pinned `scipy 1.18.1`) is a **candidate statistic only**. [SciPy documents](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chatterjeexi.html) a default asymptotic normal p-value. Its calibration for serially dependent formation residuals is not established here. Before choosing a test or applying a significance threshold to admission, this proposal requires documented time-series calibration plus simulation evidence of false-positive rates and power under the declared formation window. No bootstrap or test design is selected here, and no correctness claim is made without that evidence.
  4. **Explicit definition of abstain:** Entry-gate abstention (failed stationarity, independence, or structural-break check) **holds current inventory** without trading to avoid turnover costs. Exiting an active position returns to `50/50` neutral (`preference = 0.0`); `park_usdt` is reserved exclusively for crash defense.
  5. **Uncertainty reporting:** Expose formation test p-values, sample size `n`, and refit-block stability in diagnostics.

## 4. Benchmarks, Multiple Testing, and Experiment-Wide Research Ledger

- **Dual-benchmark evaluation:** Evaluate every candidate against **both** matched passive HODL and the predeclared simple rebalancing control under the same declared family and `9,999`+ SPA bootstrap replicates (`qap.lab.proof.v2`).
- **Actor isolation vs. research ledger:** Keep `actor_id` in `LabStudyStore` strictly as workspace/storage isolation. Add a separate **experiment-wide research ledger** that records every pair, anchor, bar, method, and parameter family tested across research waves so prior peeks cannot be hidden behind fresh actor IDs.
- **Duplicate correction assessment:** `corrected_spa` returns `min(1, raw * max(1, trials))`, using the per-pair configuration count from the family ledger. The study service passes `outer_family_size = 1` to its resolvability preflight. The batch runner passes the plan row count `K`. That preflight checks numerical resolution against `alpha / outer_family_size`; it does not apply Holm correction to completed results. Historical S4 reports separately record outer Holm analysis. A future experiment must declare and apply its outer-family analysis explicitly. Before changing correction semantics, assess overlap between the per-pair configuration family and the outer family through calibrated simulations. Do not assume that `m_pair * K` necessarily double-counts, or that another correction is always tighter. Do not relax `alpha = 0.05` or remove a required correction without explicit approval.

## 5. Attribution Controls, Zero-Cost Diagnostics, and Cost Stress

- **Risk-matched attribution control:** Preserve matched HODL and the simple rebalancing control. Propose adding an optional **risk-matched (volatility/turnover-matched) passive control** as a secondary diagnostic—never as a replacement for HODL or the simple control.
- **Zero-cost diagnostics vs. cost add-back:** Label `terminal + paid_costs` strictly as `cost add-back approximation`. Any separate zero-cost diagnostic must explicitly declare whether it uses **frozen trades** (re-evaluating actual executed fills at zero fee) or **rerun policy** (re-running signal/auto-tune at zero fee).
- **Predeclared stress & fresh evidence window:** Before inspecting any fresh calendar window (and without touching `final_oos`), predeclare:
  - Fee/slippage stress multipliers: `1.0x`, `1.5x`, `2.0x` base spot fees + L2 depth impact.
  - Parameter sensitivity band: `±20%` on `lookback` and `entry` (the `LabSettings` z-score entry threshold; the field is `entry`, not `entry_z`).
  - Next validation window dates and exact family size `K` locked in a signed plan file prior to data fetch.

The multipliers and the sensitivity band above are proposed shapes, not fixed configurations.
The exact stressed fields, the base cost values they multiply, and the number of sensitivity cells remain unresolved (§6.2).

## 6. Carried Hypotheses (Not Preregistered or Profitable)

The following audit presets are carried strictly as **unvalidated hypotheses** for future `RD-1`-approved testing:
- Low-turnover `4h`/`1d` BTC-anchored copula with `minimum_hold >= 12` and `park_anchor` crash defense.
- `1d` Kalman with explicit formation-window residual stationarity gating.

### 6.1 Draft Experiment Specification (Incomplete — Pending Completion and Approval)

This is a **draft**, not a frozen specification.
It cannot be frozen until every blocker in §6.2 is resolved and the completed specification is approved.

| Field | Draft value | Status |
| --- | --- | --- |
| Pairs | `SOL/ETH`, `AVAX/ETH`, `LINK/ETH`, `BNB/ETH` | Proposed |
| Anchor | `BTC` (`binance:BTC`) | Proposed |
| Methods & settings | `copula` (`lookback=96`, `copula_probability=0.02`, `minimum_hold=12`, `crash_defense_mode="park_anchor"`, `auto_tune=False`) and `zscore` (`hedge_method="kalman"`, `lookback=96`, `auto_tune=False`) | Proposed; partial `LabSettings` only |
| Bar & horizon | `4h`, `days=180` | Proposed; **not** a fresh-data guarantee |
| Trial budget & correction | `K = 8` proposed rows, `m_pair >= 2` per pair, `alpha = 0.05`, Holm-Bonferroni + SPA (`replicates = 9_999`, `seed = 20260930`) | `K` is a proposed row count only; `m_pair` is a lower bound only |

`days=180` is a trailing lookback that ends at the latest available completed bar, so it overlaps history already inspected in earlier waves.
It does not establish fresh data, and it does not create an uninspected window.

`K = 8` is the proposed row count for four pairs times two methods.
It is not a fixed family size.
Each pair carries at least **two** distinct method configurations before any existing history or tuning expansion, so `m_pair >= 2` is the correct lower bound and the earlier `m_pair = 1` understated the correction multiplier.
The actual per-pair count must be computed from the existing family ledger (`LabStudyStore.projected_trial_count`, which unions registered `trials.json` entries with the new configurations) rather than assumed.
Previously registered configurations can increase the multiplier. Record the ledger snapshot used for each count.
The full hypothesis family, including carried history, must be fixed before approval.
Fixing it must not discard existing research history or alter correction semantics.

### 6.2 Unresolved freeze blockers

None of these may be invented or assumed at approval time.

1. **Absolute training and validation start/end dates.** The split is currently a fraction of the loaded window (`proof_fraction`), not a calendar boundary. The absolute dates depend on the resolved data window and are unresolved.
2. **Consumption-role audit.** Which prior waves consumed which bars, and therefore which part of any proposed window is already inspected, is unresolved.
3. **Complete serialized `LabSettings`.** The draft lists a subset of fields. Freeze each method's complete serialized settings, including defaults. The Kalman draft also omits `minimum_hold` and `crash_defense_mode`. Record costs, entry/exit thresholds, sizing, cooldown, fold settings, and the serialized `significance` corresponding to the proposed alpha.
4. **Fixed base costs and execution assumptions.** The base fee, slippage, and depth-impact values that the stress multipliers scale, and the fill/reference-price assumptions they apply to, are unresolved.
5. **Exact stress and sensitivity configurations.** The stressed fields, the multiplier grid, and the sensitivity cell count are unresolved.
6. **Seed and family accounting.** The SPA seed is proposed, but the family size, the per-pair counts, and the outer-family size used by the resolvability preflight are unresolved.

### 6.3 Preserved boundaries

This proposal does not change the economic objective, the benchmark ladder (matched HODL → predeclared simple rebalancing control → relationship policy), the admissible owned-spot action space, cost/fill/reference-price semantics, dataset or holdout roles, universe eligibility, or the Shariah boundary.
This correction does not inspect `final_oos` or reset any earlier consumption status.

Note: Neither `120` formation observations nor `9,999` bootstrap replicates guarantees adequate statistical power; approval authorizes running this bounded experiment only, not certifying profitability or live-readiness.
