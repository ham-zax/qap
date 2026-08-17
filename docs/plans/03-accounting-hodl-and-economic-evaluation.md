# Phase 03 — Accounting, HODL, and Economic Evaluation Implementation Plan

**Goal:** Establish authoritative economic evaluation before any relationship model or strategy logic exists, including matched HODL, HODL-relative portfolio wealth growth and path, attribution, turnover/cost reporting, drawdown, and concentration diagnostics.

**Architecture:** `qap.evaluation` derives read-only economic results from portfolio states plus one explicit market-owned `PriceSnapshot`. It never mutates holdings or own observed prices. HODL is constructed from the same frozen starting ownership vector as the strategy.

**Tech Stack:** Python 3.14, `Decimal`, pytest.

## Global Constraints

- Strategy and HODL start from exactly the same `PortfolioState`.
- A valuation numeraire is an aggregation coordinate, not the product objective.
- No implicit FX/crypto routing or synthetic executable market is introduced by valuation.
- Every terminal comparison uses one consistent timestamp and one explicit price set; for bar-based experiments the default terminal valuation is the close of the final completed bar in the declared window.
- Evaluation must support negative, zero, and positive results without special-case promotion logic.

## File Map

**Create:**
- `src/qap/evaluation/__init__.py`
- `src/qap/evaluation/valuation.py` — pure portfolio valuation using Phase-02 `qap.market.PriceSnapshot`; no duplicate price container.
- `src/qap/evaluation/hodl.py` — matched passive benchmark creation.
- `src/qap/evaluation/metrics.py` — HODL-relative portfolio wealth growth/path and drawdown helpers.
- `src/qap/evaluation/attribution.py` — per-asset quantity/value contribution and concentration.
- `src/qap/evaluation/result.py` — compact immutable economic result record.
- `tests/unit/evaluation/test_valuation.py`
- `tests/unit/evaluation/test_hodl.py`
- `tests/unit/evaluation/test_metrics.py`
- `tests/unit/evaluation/test_attribution.py`
- `tests/scenarios/test_hand_calculated_economics.py`

## Section 03.1 — Portfolio Valuation

**Interfaces:**
- Consumes: `PortfolioState` and Phase-02 `PriceSnapshot`.
- Produces: deterministic portfolio value in the snapshot's declared numeraire.

**Behavior:**
- Every positive holding requires an explicit price in the supplied snapshot.
- Missing prices fail closed; there is no hidden path search or fallback quote asset.
- `qap.evaluation` performs value arithmetic only; observed price identity/timestamp validation remains owned by `qap.market.PriceSnapshot`.

**Steps:**
- [ ] Write tests for complete valuation and missing-held-asset price using explicit `PriceSnapshot` fixtures.
- [ ] Implement pure `value_portfolio(state, prices)` with no second price/valuation container.

**Verification:**

```bash
uv run pytest -q tests/unit/evaluation/test_valuation.py
```

## Section 03.2 — Matched HODL Construction

**Interfaces:**
- Consumes: frozen starting `PortfolioState`.
- Produces: `HodlBenchmark` whose holdings remain the same quantities throughout the comparison window.

**Behavior:**
- Benchmark stores the exact starting state/fingerprint-equivalent representation.
- It performs no rebalance, fee, or trade.
- Comparison rejects a strategy result whose declared starting state differs from the benchmark's starting state.

**Steps:**
- [ ] Write tests proving HODL quantities remain unchanged.
- [ ] Write a mismatch test where strategy and benchmark starts differ and comparison fails.
- [ ] Implement `HodlBenchmark` without adding a generic benchmark framework.

**Verification:**

```bash
uv run pytest -q tests/unit/evaluation/test_hodl.py
```

## Section 03.3 — Primary Metric

**Interfaces:**
- Consumes: terminal strategy state, matched HODL state, one terminal `PriceSnapshot`; optionally aligned strategy/HODL valuation sequences for path diagnostics.
- Produces: terminal `hodl_relative_basket_growth`, relative-wealth path, and relative drawdown diagnostics.

**Formula:**

```text
strategy_value = V(strategy_terminal, prices_T)
hodl_value     = V(hodl_terminal, prices_T)
relative_growth = strategy_value / hodl_value - 1
```

**Behavior:**
- `hodl_value` must be positive.
- Decimal division is performed under one explicit local decimal context/precision chosen for financial evaluation.
- Result can be negative, zero, or positive.
- Both states are valued with the same terminal snapshot.
- For a path, strategy and HODL values share the exact same evaluation timestamps and mark-price snapshots.
- `relative_wealth_t = strategy_value_t / hodl_value_t`; maximum relative drawdown is a diagnostic from that path, not a second optimization objective.

**Steps:**
- [ ] Add hand-calculated examples: exact tie, +10%, and -10% relative outcomes.
- [ ] Add a short literal relative-wealth path with a known peak-to-trough drawdown.
- [ ] Implement terminal/path metrics with no annualization or Sharpe-like optimization in this phase.

**Verification:**

```bash
uv run pytest -q tests/unit/evaluation/test_metrics.py
```

## Section 03.4 — Per-Asset Inventory and Value Attribution

**Interfaces:**
- Consumes: strategy terminal state, HODL terminal state, market `PriceSnapshot`.
- Produces: per-asset quantity ratio/delta and terminal relative-value contribution.

**Behavior:**
- Quantity delta: `strategy_qty - hodl_qty`.
- Quantity ratio is reported only when HODL quantity is positive; otherwise record an explicit non-comparable status rather than divide by zero.
- Value contribution uses the same terminal valuation snapshot.
- Sum of per-asset value deltas must equal total strategy-value minus HODL-value within exact Decimal arithmetic/tolerance defined in the module.

**Steps:**
- [ ] Write two-asset attribution fixture with one accumulated asset and one reduced asset.
- [ ] Implement contribution record and reconciliation assertion/helper.

**Verification:**

```bash
uv run pytest -q tests/unit/evaluation/test_attribution.py
```

## Section 03.5 — Concentration Diagnostics

**Interfaces:**
- Consumes: terminal strategy state plus market `PriceSnapshot`; attribution contributions.
- Produces: terminal value-weight concentration and positive-contributor share concentration.

**Behavior:**
- Report max single-asset terminal weight.
- Report Herfindahl-Hirschman-style sum of squared value weights as a diagnostic only.
- For positive relative-value contribution, report fraction explained by largest positive contributor when total positive contribution is non-zero.
- These are diagnostics, not automatic veto thresholds in Phase 03.

**Steps:**
- [ ] Add equal-weight and single-asset concentration fixtures.
- [ ] Implement pure diagnostic functions.

## Section 03.6 — Cost and Turnover Fields Without Premature Execution Coupling

**Interfaces:**
- Produces: economic result fields later populated by Phase 06.

**Behavior:**
- Define `EconomicResult` fields for `fees_value`, `slippage_value`, `turnover_value`, and `rebalance_count` as explicit supplied values.
- Phase 03 scenario tests use zero or hand-supplied values.
- `qap.evaluation` must not import future execution internals; Phase 06 converts its fill ledger into these values at the boundary.

**Steps:**
- [ ] Create immutable `EconomicResult` containing start/terminal values, HODL value, relative growth, attribution, concentration, and supplied cost/turnover summary.
- [ ] Add validation that cost/turnover values are non-negative.

## Section 03.7 — Hand-Calculated Scenario

**Scenario:**

Use a committed in-test two-asset starting basket with simple integer quantities and terminal prices so a human can calculate:

- HODL terminal value;
- strategy terminal value;
- relative growth;
- per-asset value deltas;
- concentration.

**Steps:**
- [ ] Implement scenario without calling policy, relationship, or execution code.
- [ ] Keep expected values literal in the test so the evaluation layer is not testing itself through duplicate helper formulas.

**Verification:**

```bash
uv run pytest -q tests/scenarios/test_hand_calculated_economics.py
```

## Phase Verification

```bash
uv run pytest -q tests/unit/evaluation tests/scenarios/test_hand_calculated_economics.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Same-start HODL benchmark is enforced.
- [ ] Primary HODL-relative portfolio wealth growth and relative-wealth path are hand-calculation verified.
- [ ] Relative drawdown is available as a diagnostic so terminal outperformance cannot hide a materially different path.
- [ ] Per-asset attribution reconciles to total relative value.
- [ ] Concentration diagnostics exist without premature thresholds.
- [ ] Cost/turnover fields exist without coupling evaluation to execution internals.
- [ ] Evaluation never mutates portfolio state.

## Stop Conditions

Do not add Sharpe/Sortino optimization, portfolio optimizer libraries, graph valuation routing, benchmark registries, or model-specific metrics here. Economic truth must remain small and interpretable before research sophistication arrives.

## Targeted Quant Review Addendum — Incremental Relative-Wealth Series

The terminal wealth ratio remains the primary economic headline, but Phase 03 must also expose an aligned incremental relative-performance series for later statistical inference.

For candidate policy `C` and declared benchmark/control `B`, when both marked wealth paths are strictly positive at aligned evaluation timestamps:

```text
d_t = delta_log(W_C,t) - delta_log(W_B,t)
```

The sum of `d_t` must reconcile, within declared numerical tolerance, to the log of the candidate-vs-control gross wealth-growth ratio. This is an accounting/evaluation artifact, not an alpha claim by itself.

- [ ] Strategy and control use identical evaluation timestamps and authoritative `PriceSnapshot` values.
- [ ] Refuse log-relative computation if either wealth path is non-positive; never silently clip/offset wealth.
- [ ] Test cumulative incremental log performance against the terminal relative-growth log ratio.
- [ ] Preserve terminal relative wealth, turnover, fees, slippage, drawdown, and concentration alongside the series.
- [ ] Phase 07 may consume this series for dependence-aware inference without moving statistics into `qap.evaluation`.
