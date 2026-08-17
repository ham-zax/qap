# Phase 06 — Deterministic Paper Execution and Replay Implementation Plan

**Goal:** Execute approved direct-spot rebalance intents deterministically from historical reference prices, apply explicit slippage/fees/quantization exactly once, reconcile holdings, and replay the full point-in-time loop without lookahead or pretending bar prices are guaranteed fills.

**Architecture:** `qap.execution` owns execution semantics and fill records. `PortfolioLedger` in `qap.portfolio` is the single mutable owner that applies fill deltas idempotently to immutable `PortfolioState` snapshots. `qap.execution.replay` orchestrates time; it does not duplicate policy/accounting logic.

**Tech Stack:** Python 3.14, `Decimal`, existing market/policy/portfolio types, pytest.

## Global Constraints

- Phase 06 supports direct spot market legs only.
- Default decision timing is completed bar `t` -> next bar open **execution reference** -> modeled fill after explicit slippage/fee/quantization.
- No fill is created when no next execution bar exists.
- Fees are modeled explicitly in the direct market's quote asset.
- Slippage is an explicit adverse price adjustment, not a second hidden fee.
- Fill application is idempotent.
- Explicit exogenous inventory flows, when supplied by a later experiment, are deterministic/idempotent and are the only non-fill state-change source admitted by replay.
- No negative balances, leverage, borrowing, synthetic execution, or hidden stablecoin routing.
- Multi-leg bridge routing is deferred to Phase 11.

## File Map

**Create:**
- `src/qap/execution/__init__.py`
- `src/qap/execution/costs.py` — explicit fee/slippage basis-point model.
- `src/qap/execution/fills.py` — fill record and buy/sell arithmetic.
- `src/qap/execution/direct.py` — direct-market execution of one rebalance leg.
- `src/qap/execution/replay.py` — deterministic event loop and trace.
- `src/qap/portfolio/ledger.py` — sole replay-state owner for applied fill/flow IDs and resulting inventory snapshots.
- `src/qap/portfolio/flows.py` — optional explicit deposit/withdrawal event contract for later accumulation experiments.
- `tests/unit/execution/test_costs.py`
- `tests/unit/execution/test_fills.py`
- `tests/unit/execution/test_direct.py`
- `tests/unit/portfolio/test_ledger.py`
- `tests/unit/portfolio/test_flows.py`
- `tests/scenarios/test_deterministic_replay.py`
- `tests/scenarios/test_last_bar_cannot_fill.py`
- `tests/scenarios/test_cost_applied_once.py`

## Section 06.1 — Explicit Cost Model

**Interfaces:**
- Produces: `CostModel(fee_bps, slippage_bps)` consumed by direct execution.

**Behavior:**
- Basis points are non-negative Decimal values.
- `fee_rate = fee_bps / 10000`.
- Buy modeled execution price = next-bar reference open × `(1 + slippage_rate)`.
- Sell modeled execution price = next-bar reference open × `(1 - slippage_rate)`.
- The reference open is a causal observable, not a claim that the entire requested quantity was executable exactly at that market print.
- Fee is charged in quote asset on executed quote notional.
- Cost model contains no venue inference or account-tier logic.

**Steps:**
- [ ] Write zero-cost and non-zero-cost arithmetic tests.
- [ ] Reject negative bps and sell slippage >=10000 bps.
- [ ] Implement pure calculations.

## Section 06.2 — Fill Contract

**Interfaces:**
- Consumes: decision ID, direct market orientation, side, base quantity/quote budget, next-bar reference price, cost model.
- Produces: immutable `Fill` with explicit balance deltas.

**Buy behavior:**
- Convert the canonical market reference price to `Decimal` via its stable serialized decimal form (for example `Decimal(str(reference_open))`), never `Decimal(float)`.
- Given quote budget, reserve fee from that budget so total quote debit never exceeds available budget.
- Compute executable base quantity from adjusted execution price.
- Quote delta is negative total spent; base delta is positive received quantity.

**Sell behavior:**
- Base debit equals sold quantity.
- Gross quote proceeds use adverse execution price.
- Fee is deducted from quote proceeds.
- Quote delta is net positive proceeds.

**Fill fields:**
- stable fill ID derived from replay/run identity + decision/leg identity;
- decision ID;
- execution timestamp;
- venue/instrument/base/quote/side;
- reference price;
- execution price;
- base quantity;
- gross quote notional;
- fee amount and fee asset;
- slippage value diagnostic;
- explicit per-asset balance deltas.

**Steps:**
- [ ] Write literal hand-calculated buy/sell tests.
- [ ] Implement `Decimal` arithmetic and explicit quantization hook; use a no-op/high-precision default until market precision metadata is added later.

## Section 06.3 — Portfolio Ledger and Idempotency

**Interfaces:**
- Consumes: current `PortfolioState`, `Fill`.
- Produces: next state and append-only applied-fill record.

**Behavior:**
- `PortfolioLedger` owns current state and the applied event identities needed to prevent duplicate fills/flows.
- Applying an unseen fill validates every resulting balance before committing.
- Applying the same fill ID twice returns/rejects as duplicate without changing state a second time.
- Fill deltas and explicitly declared exogenous inventory-flow deltas are the only paths into actual holdings in replay.
- An `ExternalInventoryFlow` has a stable flow ID, effective UTC timestamp, asset, and signed `Decimal` quantity delta. Withdrawals that would make inventory negative fail closed.
- External flows are not fills, do not acquire invented execution costs, and cannot be synthesized from policy decisions.

**Steps:**
- [ ] Write duplicate-fill, duplicate-flow, insufficient-balance/withdrawal, and valid-fill/flow tests.
- [ ] Implement ledger as the sole mutable object; exposed snapshots remain immutable.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_ledger.py
```

## Section 06.4 — Direct Rebalance Execution

**Interfaces:**
- Consumes: Phase-05 desired delta for a two-asset direct pair, explicit `MarketInstrument`, next-bar reference open, cost/quantization model, current ledger state.
- Produces: zero or one direct fill for the initial slice.

**Behavior:**
- Asset reduction determines sell side; asset increase determines destination.
- The requested economic conversion must exactly match the declared direct market pair in either orientation.
- Inverse orientation is handled mathematically from the declared direct instrument; an entirely different market is not substituted.
- If no direct route exists, return `unsupported_direct_route` rather than synthesizing a bridge.
- Quantity is capped by actually available source balance.

**Steps:**
- [ ] Test X->Y direct sell and Y->X direct buy orientation.
- [ ] Test unsupported route and insufficient balance.
- [ ] Keep multi-asset/multi-leg execution out of this phase.

## Section 06.5 — Replay Timing Loop

**Interfaces:**
- Consumes: validated aligned bars, starting ledger, relationship builder, deterministic policy, rebalance planner, direct execution config.
- Produces: `ReplayTrace` of observation times, decisions, plans, fills, and portfolio snapshots.

**Loop:**

```text
for each completed decision bar t except final bar:
  decision_time = bar_t.open_time + interval
  apply each not-yet-applied declared external flow with effective_time <= decision_time
  expose only bars with bar_end_exclusive <= decision_time
  build relationship evidence
  ask policy for decision
  if target:
    build rebalance plan using completed bar-t prices
    if actionable:
      use bar t+1 open as the contiguous execution reference
      derive modeled fill from declared slippage/fee/quantization
      apply fill once
  record trace
```

**Behavior:**
- Relationship builder never sees `t+1` when deciding at `t`.
- A contribution with `effective_time <= decision_time` is owned inventory visible to policy at that decision; a later contribution is not. The same declared flow schedule must be replayable identically for strategy and controls in Phase 07.
- Reference price comes only from `t+1` open; modeled execution price is derived deterministically from that reference plus the declared cost/slippage contract.
- Final-bar decision cannot fill.
- Iteration order and IDs are deterministic.

**Steps:**
- [ ] Build a tiny two-asset scenario where the scheduled dummy policy triggers once.
- [ ] Assert exact decision timestamp, fill timestamp, fill price, and ending quantities.
- [ ] Repeat run and assert trace equality.

## Section 06.6 — Cost-Applied-Once Scenario

**Steps:**
- [ ] Create a scenario with easy integer prices and 10 bps fee/slippage.
- [ ] Hand-calculate expected ending balances independently in test literals.
- [ ] Assert fill fee/slippage diagnostics and terminal holdings.
- [ ] Reapply fill to ledger and assert no second cost/state change occurs.

## Phase Verification

```bash
uv run pytest -q tests/unit/execution tests/unit/portfolio/test_ledger.py tests/scenarios/test_deterministic_replay.py tests/scenarios/test_last_bar_cannot_fill.py tests/scenarios/test_cost_applied_once.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Direct spot fill arithmetic is hand-verified.
- [ ] Fees/slippage are explicit and applied once.
- [ ] Test/output language distinguishes `reference_price` from `execution_price`; no result claims a guaranteed fill at the OHLC bar open.
- [ ] Ledger idempotency prevents duplicate fills.
- [ ] Replay is deterministic.
- [ ] No lookahead is possible through the replay's public history boundary.
- [ ] Explicit external flows are ordered, idempotent, auditable, and cannot create negative inventory.
- [ ] Final-bar decisions remain unfilled.
- [ ] Unsupported routing fails closed.

## Stop Conditions

Do not add market orders to a live venue, websocket feeds, partial venue fills, bridge routing, leverage, margin, order books, sophisticated impact models, or multiple simultaneous conversion legs. Phase 06 proves semantics first; operational realism comes later.

## Optional Differential-Oracle Check

After the QAP baseline replay is green, perform one bounded NautilusTrader spike for a deliberately simple case such as periodic rebalance with fixed costs. Compare holdings, fill direction, explicit costs, and terminal wealth. Treat mismatches as semantic-review evidence, not as proof that the third-party engine is authoritative. Do not make NautilusTrader a runtime dependency of `src/qap`.
