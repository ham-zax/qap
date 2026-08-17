# Phase 11 — Paper-Operation Hardening Implementation Plan

**Goal:** Harden the proven deterministic engine for realistic multi-asset paper operation using larger public spot datasets, one explicit venue data adapter, market precision metadata, explicit direct/two-leg routing, independent reconciliation, and a small operator workflow.

**Architecture:** Keep venue/network behavior in `qap.market.adapters` and execution routing in `qap.execution`. Core portfolio/policy/evaluation contracts remain unchanged. Add operational realism only where it can be reconciled back to the deterministic model.

**Tech Stack:** Python 3.14, HTTPX, existing NumPy/Pandas/PyArrow stack, FastAPI/React from prior phases, Playwright only for a few critical integrated browser flows.

## Global Constraints

- Still paper-only; no authenticated order placement.
- One public market-data venue adapter only. The initial adapter is Binance Spot public REST because the historical product needs broad crypto spot coverage; implementation must verify the then-current official Binance Spot API contract before coding against it.
- Venue adapter is replaceable and cannot leak exchange-specific types into domain packages.
- Multi-leg execution uses explicit real spot legs and pays cost on every leg.
- Bridge/settlement asset must be explicitly admitted for transient execution ownership; no hidden USDT/BTC fallback. Any bridge residue/dust remains in actual portfolio inventory and is included in evaluation even when the bridge is not a target-basket asset.
- Reconciliation must independently detect balance or result drift.
- No scheduler, daemon platform, Kafka, database, multi-exchange abstraction, or live credential.

## File Map

**Modify:**
- `pyproject.toml` — ensure HTTPX is a runtime dependency (not merely a test/dev dependency) before the public network adapter imports it.
- existing market/execution models only where precision/routing contracts require backward-compatible fields.

**Create:**
- `src/qap/market/adapters/__init__.py`
- `src/qap/market/adapters/binance_public.py` — unauthenticated historical spot klines/exchange metadata adapter.
- `src/qap/market/metadata.py` — explicit tick/step/min-notional metadata normalized from venue response.
- `src/qap/execution/precision.py` — deterministic quantity/price rounding against declared market metadata.
- `src/qap/execution/routing.py` — direct or one declared bridge asset; no graph search.
- `src/qap/execution/multi_asset.py` — deterministic sell-overweights-then-buy-underweights rebalance execution.
- `src/qap/evaluation/reconciliation.py` — independent fill->holdings/result recomputation.
- `tests/integration/market/test_binance_public_adapter.py` — network test marked/skipped by default and driven from recorded contract fixture where possible.
- `tests/fixtures/binance/exchange_info_subset.json`
- `tests/fixtures/binance/klines_subset.json`
- `tests/unit/execution/test_precision.py`
- `tests/unit/execution/test_routing.py`
- `tests/scenarios/test_two_leg_bridge_execution.py`
- `tests/scenarios/test_multi_asset_rebalance.py`
- `tests/scenarios/test_independent_reconciliation.py`
- `web/e2e/portfolio-workbench.spec.ts`
- `web/e2e/pair-anchor-lens.spec.ts`
- Playwright config/package dependency only after the two E2E flows are defined.

## Section 11.1 — Verify and Record the Public Venue Contract

**Interfaces:**
- Consumes: then-current official Binance Spot REST documentation.
- Produces: a small adapter contract note/test fixtures, not a broad exchange abstraction.

**Steps:**
- [ ] Verify current official endpoints/fields for spot klines and exchange symbol filters at Phase-11 execution time.
- [ ] Record the exact fields QAP consumes: symbol/base/quote/status, interval/timestamps, OHLCV, price tick, quantity step, minimum notional or current equivalent constraints.
- [ ] Capture tiny sanitized response fixtures for deterministic tests.
- [ ] Do not consume account/private endpoints.

**Acceptance criteria:**
- Public data contract is based on current official source, not old-QAP code or memory.

## Section 11.2 — Binance Public Historical Adapter

**Interfaces:**
- Consumes: explicit symbol, interval, UTC `[start,end)` window.
- Produces: validated Phase-02 `MarketBar` series plus venue metadata.

**Behavior:**
- Adapter paginates deterministically according to current API contract.
- It rejects unavailable/non-spot/inactive symbols rather than guessing alternatives.
- Raw network payload is transformed immediately into clean QAP types.
- Retry policy is bounded for transient HTTP failures; semantic 4xx/data errors fail visibly.
- Downloaded validated data is persisted through the existing Parquet/fingerprint path.

**Steps:**
- [ ] Implement response parsing against recorded fixtures first.
- [ ] Add network integration test marked `network` so normal local verification does not depend on internet.
- [ ] Add one manual/explicit command for downloading a declared window; do not create a background downloader.

## Section 11.3 — Market Precision and Minimum Constraints

**Interfaces:**
- Consumes: normalized `MarketMetadata`.
- Produces: deterministic executable quantity/price rounding and admissibility checks.

**Behavior:**
- Quantity rounds down to allowed step size so paper execution never spends/owns more than planned because of rounding.
- Price/reference quantization follows market tick where relevant to modeled execution.
- Post-rounding notional below venue minimum becomes explicit no-fill/no-action reason.
- Dust remains visible in inventory.

**Steps:**
- [ ] Add literal Decimal tests for step/tick rounding.
- [ ] Integrate precision into Phase-06 direct execution without changing its cost/timing semantics.

## Section 11.4 — Explicit Routing

**Interfaces:**
- Consumes: source asset, destination asset, available declared spot instruments, optional declared bridge asset.
- Produces: `ExecutionRoute` of one or two real spot legs.

**Behavior:**
1. Prefer exact direct market when declared/available.
2. Otherwise, if one explicit bridge is configured and both source/bridge and destination/bridge spot markets exist, return exactly two legs.
3. Otherwise fail `unsupported_route`.

No graph search, automatic stablecoin selection, or synthetic fill exists.

**Steps:**
- [ ] Test direct route, inverse orientation handling, two-leg route, missing second leg, and undeclared bridge.
- [ ] Include route identity in run provenance.

## Section 11.5 — Two-Leg Bridge Paper Execution

**Interfaces:**
- Consumes: route, next-bar open for every leg, current ledger, cost/precision metadata.
- Produces: two fills at one execution timestamp/event sequence.

**Behavior:**
- Execute source -> bridge first.
- Only actually received bridge balance is available to second leg.
- Execute bridge -> destination second.
- Each leg applies its own adverse slippage and fee.
- If either required next-bar market observation is unavailable, do not synthesize it. Preflight both legs before mutating the ledger so missing-data failure is atomic at the rebalance-event level.
- Bridge residue/dust remains explicit.

**Steps:**
- [ ] Write a fully hand-calculated two-leg scenario with non-zero fees on both legs.
- [ ] Verify terminal balances and total cost equal independent literals.

## Section 11.6 — Deterministic Multi-Asset Rebalance

**Interfaces:**
- Consumes: multi-asset `RebalancePlan`, explicit route set/bridge, one synchronized execution timestamp.
- Produces: ordered sequence of fills and final portfolio snapshot.

**Algorithm:**
1. For a multi-asset basket, require one explicitly declared settlement/bridge asset `B` for the rebalance event. `B` is an execution hub, not automatically the analysis anchor or economic target.
2. Compute target deltas for all basket assets, including the desired final quantity/value of `B` when `B` is itself in the basket.
3. Preflight every required non-`B`/`B` market, next-bar price, precision constraint, and expected two-leg notional before mutating balances.
4. Execute overweight non-`B` assets -> `B` first in deterministic order: descending absolute target-value reduction, then asset symbol tie-break.
5. Recompute actual available `B` after costs/rounding while reserving any `B` quantity/value required by the target allocation.
6. Execute `B` -> underweight non-`B` assets in deterministic order: descending absolute target-value increase, then asset symbol tie-break.
7. Never spend more than actual available `B` after prior fills/costs; scale/stop remaining buys deterministically when costs/rounding exhaust available settlement balance.
8. Record unfilled remainder and final target-weight tracking error explicitly. Preserve any execution-only bridge dust in the real terminal `PortfolioState`; Phase-03 valuation/evaluation must include its value rather than dropping it because it is outside the target allocation.

The initial multi-asset algorithm does not solve a general asset-to-asset matching or route-optimization problem. Two-asset direct execution remains Phase 06; multi-asset execution uses the declared hub.

**Steps:**
- [ ] Add three-asset and four-asset scenarios including one bridge route.
- [ ] Assert deterministic ordering and no negative balances.
- [ ] Report post-execution target-weight tracking error.

## Section 11.7 — Independent Reconciliation

**Interfaces:**
- Consumes: starting state + append-only fills + valuation snapshots/results.
- Produces: independently recomputed ending state and reconciliation report.

**Behavior:**
- Recompute holdings from raw fill deltas without using the replay ledger's stored terminal state.
- Compare every asset quantity exactly after declared quantization.
- Recompute fee totals, turnover, terminal values, HODL-relative result.
- Any mismatch fails the paper run's `reconciled` status.

**Steps:**
- [ ] Build independent functions that do not call ledger apply helpers under test.
- [ ] Create tampered-fill/terminal-state tests proving reconciliation catches drift.

## Section 11.8 — Larger-Window Performance and Artifact Discipline

**Steps:**
- [ ] Run a representative multi-asset historical window large enough to expose memory/runtime issues without becoming a benchmark suite.
- [ ] Profile only if runtime is materially problematic; optimize the measured bottleneck rather than introducing a new compute framework.
- [ ] Confirm run artifacts remain compact and market data is referenced by fingerprint rather than copied per run.
- [ ] Confirm experiment list remains responsive by filesystem scan. If measured scan cost is materially unacceptable, stop and write a separate focused indexing plan rather than adding a speculative catalog in this phase.

## Section 11.9 — Critical Browser E2E Flows

**Flows:**
1. Open a known run -> Portfolio -> verify HODL-relative metric and relative-wealth chart -> navigate to Pair Workbench.
2. Pair Workbench -> invert orientation -> select anchor -> verify URL/state and synchronized anchor-lens labels.

**Steps:**
- [ ] Add Playwright only for these integrated flows after component/API tests already exist.
- [ ] Run against a local fixture API with deterministic data, not public network.
- [ ] Do not create broad screenshot regression coverage.

## Section 11.10 — Operator Paper Workflow

**Workflow:**

```text
download/validate declared data
 -> run frozen experiment manifest
 -> inspect reconciliation status
 -> inspect Portfolio and Pair Workbench
 -> record conclusion
```

**Steps:**
- [ ] Document exact commands in a concise operator section of README or `docs/operator-paper.md` only after commands exist.
- [ ] Keep experiment launch command-based; do not add async web jobs unless a later operator review demonstrates the need.

## Phase Verification

```bash
uv run pytest -q tests/unit tests/scenarios tests/contract/api
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
cd web
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright test e2e/portfolio-workbench.spec.ts e2e/pair-anchor-lens.spec.ts
```

Run marked network tests separately and explicitly:

```bash
uv run pytest -q -m network tests/integration/market/test_binance_public_adapter.py
```

## Phase Exit Criteria

- [ ] Real public spot data can be admitted reproducibly through one bounded adapter.
- [ ] Venue precision/minimum constraints affect paper fills explicitly.
- [ ] Direct and one-declared-bridge routes are deterministic and costed per real leg.
- [ ] Multi-asset rebalance remains long-only and reconciled.
- [ ] Independent reconciliation detects tampering/drift.
- [ ] Critical web inspection flows work end-to-end.
- [ ] No live/private exchange API or infrastructure platform was introduced.

## Stop Conditions

Stop and redesign before adding authenticated order endpoints, multiple venue adapters, route graph optimization, asynchronous worker queues, databases, schedulers, websocket market streams, or automatic failover. Those are live/operational architecture decisions, not paper-hardening conveniences.
