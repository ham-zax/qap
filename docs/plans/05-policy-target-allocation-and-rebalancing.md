# Phase 05 — Policy, Target Allocation, and Rebalancing Implementation Plan

**Goal:** Convert relationship evidence and current inventory into explicit long-only target allocations and economically meaningful quantity deltas without allowing policy logic to mutate holdings.

**Architecture:** `qap.policy` is pure decision logic. `qap.portfolio.rebalance` translates a validated target allocation into desired quantities using an explicit valuation snapshot. Execution routing remains out of scope until Phase 06.

**Tech Stack:** Python 3.14, `Decimal`, existing portfolio/evaluation/relationship types, pytest.

## Global Constraints

- Policy emits intent, never fills and never balance mutations.
- Target allocation is the primary decision object; OPEN/CLOSE position lifecycle is not introduced.
- Long-only weights only.
- Partial rebalancing and no-action are first-class.
- A deterministic dummy policy is implemented before any statistical policy.
- Rebalance planning uses explicit current prices and cannot infer hidden market routes.

## File Map

**Create:**
- `src/qap/policy/__init__.py`
- `src/qap/policy/decision.py` — `PolicyDecision`, reason/evidence references.
- `src/qap/policy/deterministic.py` — timestamp/evidence-keyed deterministic target policy for tests/replay.
- `src/qap/portfolio/rebalance.py` — target quantities, asset deltas, minimum-notional filter.
- `tests/unit/policy/test_decision.py`
- `tests/unit/policy/test_deterministic.py`
- `tests/unit/portfolio/test_rebalance.py`
- `tests/scenarios/test_partial_rebalance_plan.py`

## Section 05.1 — Policy Decision Contract

**Interfaces:**
- Consumes: current `PortfolioState`, admitted basket, optional relationship evidence references.
- Produces: `PolicyDecision` containing either validated `AllocationTarget` or explicit no-action.

**Behavior:**
- Decision includes decision ID, as-of UTC timestamp, policy ID/version string, target or `None`, reason code, and evidence fingerprints/IDs used.
- `no_action` is explicit and does not require a fake all-current target.
- Decision object has no methods that change portfolio state.

**Steps:**
- [ ] Write construction tests for target and no-action decisions.
- [ ] Implement immutable decision type.
- [ ] Keep reason codes finite and explicit (`scheduled_target`, `evidence_target`, `below_threshold`, `insufficient_evidence`) rather than free-form-only state.

## Section 05.2 — Deterministic Target Policy

**Interfaces:**
- Consumes: current timestamp and a frozen mapping/schedule of target allocations.
- Produces: `PolicyDecision`.

**Behavior:**
- At declared timestamps/evidence keys, return the predefined target.
- Otherwise return no-action.
- No randomness, price forecasting, or model thresholds.
- Configuration is passed explicitly at construction; no environment lookup.

**Steps:**
- [ ] Write tests for exact trigger/non-trigger behavior.
- [ ] Implement the smallest callable/class needed by replay; no abstract policy registry.

**Verification:**

```bash
uv run pytest -q tests/unit/policy
```

## Section 05.3 — Target Quantity Calculation

**Interfaces:**
- Consumes: current `PortfolioState`, validated `AllocationTarget`, current decision-time `ValuationSnapshot` built from completed bar closes.
- Produces: target quantities and per-asset quantity deltas fixed at the decision time for later execution.

**Behavior:**
- Determine current total portfolio value using the same valuation snapshot.
- Target value per asset = total value × target weight.
- Target quantity = target value / asset price.
- Quantity delta = target quantity - current quantity.
- Calculations use `Decimal`.
- The planner does not round to exchange lot size yet; Phase 06 execution owns instrument precision.

**Steps:**
- [ ] Write a two-asset 50/50 hand calculation.
- [ ] Write a 70/30 partial rebalance case.
- [ ] Implement immutable `RebalancePlan` with current state reference/fingerprint, target quantities, and deltas.

**Verification:**

```bash
uv run pytest -q tests/unit/portfolio/test_rebalance.py
```

## Section 05.4 — Minimum-Notional No-Action Filter

**Interfaces:**
- Consumes: `RebalancePlan`, valuation snapshot, explicit `min_rebalance_notional`.
- Produces: filtered plan or explicit no-action result.

**Behavior:**
- Calculate one-way desired rebalance notional as `0.5 * sum(abs(target_value_i - current_value_i))` in the valuation numeraire; this avoids double-counting the same value as both a sell and a buy in a fully invested basket.
- If one-way desired rebalance notional is below the declared minimum, return no-action with reason `below_minimum_notional`.
- Minimum is explicit per run/config; no hard-coded exchange threshold is treated as universal.
- Do not estimate predictive benefit or introduce Kelly/optimizer logic.

**Steps:**
- [ ] Add exact-below, exact-equal, and above-threshold tests.
- [ ] Preserve the unfiltered target in diagnostic output without treating it as an executed action.

## Section 05.5 — Partial Rebalance Scenario

**Scenario:**
- Start with 100% asset X by value.
- Deterministic policy requests 60% X / 40% Y.
- Planner emits a reduction in X and increase in Y while retaining residual X.
- No wallet state changes because execution has not happened.

**Steps:**
- [ ] Add scenario test proving residual inventory is first-class.
- [ ] Add a full 0/100 rotation case and assert it uses the same target-allocation machinery, not a separate CLOSE path.

**Verification:**

```bash
uv run pytest -q tests/scenarios/test_partial_rebalance_plan.py
```

## Phase Verification

```bash
uv run pytest -q tests/unit/policy tests/unit/portfolio/test_rebalance.py tests/scenarios/test_partial_rebalance_plan.py
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
```

## Phase Exit Criteria

- [ ] Policy is pure and cannot mutate holdings.
- [ ] No-action is explicit.
- [ ] Target allocation converts deterministically to target quantities/deltas.
- [ ] Partial rebalance and full rotation share one allocation mechanism.
- [ ] Minimum-notional filtering prevents meaningless dust plans.
- [ ] No execution-market routing or statistical authority has entered the policy layer.

## Stop Conditions

Do not add Kelly sizing, leverage, stop-loss position objects, order types, market routing, model selection, optimizer frameworks, or environment-driven thresholds. Those either violate the action space or belong to later boundaries.
