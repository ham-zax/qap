# Phase 11 — Paper-Operation Hardening Implementation Plan

**Goal:** Harden the proven deterministic engine for realistic multi-asset paper operation using the Phase-02 public Spot adapter, larger admitted datasets, venue precision metadata, explicit direct/two-leg routing, independent reconciliation, and a small operator workflow.

**Architecture:** Keep venue/network behavior in `qap.market.adapters` and execution routing in `qap.execution`. Core portfolio/policy/evaluation contracts remain unchanged. Add operational realism only where it can be reconciled back to the deterministic model.

**Tech Stack:** Python 3.14, HTTPX, existing NumPy/Pandas/PyArrow stack, FastAPI/React from prior phases, Playwright only for a few critical integrated browser flows.

## Global Constraints

- Still paper-only; no authenticated order placement.
- Reuse the single Binance Spot public REST adapter admitted in Phase 02; do not create a second downloader/adapter path.
- Re-verify the then-current official Binance Spot metadata/filter contract before adding precision/minimum-notional behavior.
- Venue adapter remains replaceable and cannot leak exchange-specific types into domain packages.
- Multi-leg execution uses explicit real spot legs and pays cost on every leg.
- Bridge/settlement asset must be explicitly admitted for transient execution ownership; no hidden USDT/BTC fallback. Any bridge residue/dust remains in actual portfolio inventory and is included in evaluation even when the bridge is not a target-basket asset.
- Reconciliation must independently detect balance or result drift.
- No scheduler, daemon platform, Kafka, database, multi-exchange abstraction, or live credential.

## File Map

**Modify:**
- `src/qap/market/adapters/binance_public.py` — extend the already-tested Phase-02 public adapter only for the current metadata/filter fields required by paper precision; do not fork a second acquisition path.
- existing market/execution models only where precision/routing contracts require backward-compatible fields.

**Create:**
- `src/qap/market/metadata.py` — explicit tick/step/min-notional metadata normalized from the Phase-02 venue response.
- `src/qap/execution/precision.py` — deterministic quantity/price rounding against declared market metadata.
- `src/qap/execution/routing.py` — direct or one declared bridge asset; no graph search.
- `src/qap/execution/multi_asset.py` — deterministic sell-overweights-then-buy-underweights rebalance execution.
- `src/qap/experiment/reconciliation.py` — independent fill->holdings/result recomputation at the orchestration layer; may consume execution fills and evaluation functions without creating a core import cycle.
- extend `tests/integration/market/test_binance_public_adapter.py` only for metadata/filter behavior newly required here; reuse the Phase-02 recorded market-data fixtures.
- `tests/fixtures/binance/exchange_info_subset.json` — add only if Phase-02 fixtures do not already contain the exact precision/filter fields required.
- `tests/unit/execution/test_precision.py`
- `tests/unit/execution/test_routing.py`
- `tests/scenarios/test_two_leg_bridge_execution.py`
- `tests/scenarios/test_multi_asset_rebalance.py`
- `tests/scenarios/test_independent_reconciliation.py`
- `web/e2e/portfolio-workbench.spec.ts`
- `web/e2e/pair-anchor-lens.spec.ts`
- Playwright config/package dependency only after the two E2E flows are defined.

## Section 11.1 — Re-verify Venue Precision/Filter Contract

**Interfaces:**
- Consumes: then-current official Binance Spot documentation plus the existing Phase-02 adapter contract.
- Produces: a focused extension of normalized venue metadata, not a second market-data architecture.

**Steps:**
- [ ] Re-verify only the current public fields needed for paper execution precision: symbol/base/quote/status, price tick, quantity step, minimum/notional constraints, and any field semantics already consumed by the Phase-02 adapter.
- [ ] Extend recorded fixtures only where these fields are absent.
- [ ] Confirm the Phase-02 kline acquisition/storage path is still the only public data path.
- [ ] Do not consume account/private/trading endpoints.

**Acceptance criteria:**
- Precision/filter semantics are based on current official source and the Phase-02 public-data boundary remains single-owner.

## Section 11.2 — Larger Admitted Data Windows

**Interfaces:**
- Consumes: the Phase-02 adapter/storage/fingerprint path.
- Produces: larger immutable admitted datasets for realistic paper runs.

**Behavior:**
- Use the existing explicit download/admit path; no background downloader or second parser is created.
- Larger windows retain the same source timestamp, gap, orientation, fingerprint, and universe-mode semantics established in Phase 02.
- These runs remain development/forward-paper evidence according to their manifest role; data acquisition does not change holdout status implicitly.

**Steps:**
- [ ] Acquire at least one representative multi-asset window through the existing Phase-02 adapter.
- [ ] Re-run admission/fingerprint checks and record data role before inspection.
- [ ] Do not add caching/streaming infrastructure beyond the local Parquet contract.

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
- Consumes: route, next-bar execution-reference open for every leg, current ledger, cost/precision metadata.
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
3. Preflight every required non-`B`/`B` market, next-bar execution-reference price, precision constraint, and expected two-leg notional before mutating balances.
4. Execute overweight non-`B` assets -> `B` first in deterministic order: descending absolute target-value reduction, then stable `AssetId.key` tie-break.
5. Recompute actual available `B` after costs/rounding while reserving any `B` quantity/value required by the target allocation.
6. Execute `B` -> underweight non-`B` assets in deterministic order: descending absolute target-value increase, then stable `AssetId.key` tie-break.
7. Never spend more than actual available `B` after prior fills/costs; scale/stop remaining buys deterministically when costs/rounding exhaust available settlement balance.
8. Record unfilled remainder and final target-weight tracking error explicitly. Preserve any execution-only bridge dust in the real terminal `PortfolioState`; Phase-03 valuation/evaluation must include its value rather than dropping it because it is outside the target allocation.

The initial multi-asset algorithm does not solve a general asset-to-asset matching or route-optimization problem. Two-asset direct execution remains Phase 06; multi-asset execution uses the declared hub.

**Steps:**
- [ ] Add three-asset and four-asset scenarios including one bridge route.
- [ ] Assert deterministic ordering and no negative balances.
- [ ] Report post-execution target-weight tracking error.

## Section 11.7 — Independent Reconciliation

**Interfaces:**
- Consumes: starting state + append-only fills + market `PriceSnapshot` values/results.
- Produces: independently recomputed ending state and reconciliation report.

**Behavior:**
- Recompute holdings from raw fill deltas without using the replay ledger's stored terminal state.
- Compare every asset quantity exactly after declared quantization.
- Recompute fee totals and turnover from raw fills; call the normal evaluation functions on the independently reconstructed state for terminal values/HODL-relative result rather than duplicating valuation formulas.
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
acquire/validate declared data through the Phase-02 public adapter
 -> freeze experiment family/data role/manifest
 -> run experiment
 -> inspect reconciliation status
 -> inspect Portfolio and Pair Workbench
 -> record conclusion and holdout-consumption status
```

For any policy being considered beyond research-only status, include a genuinely prospective `forward_paper` run that begins only after the candidate family/rule, cost model, and decision semantics are frozen. Forward-paper observations may reveal defects and justify a new research generation, but once used to retune the rule they become development evidence and the next deployment candidate requires a new prospective period.

**Steps:**
- [ ] Document exact commands in a concise operator section of README or `docs/operator-paper.md` only after commands exist.
- [ ] Keep experiment launch command-based; do not add async web jobs unless a later operator review demonstrates the need.
- [ ] Document the freeze timestamp/manifest for any prospective `forward_paper` candidate and preserve its no-retuning boundary in the resulting artifact/research note.

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

If the optional Phase-02 live-network smoke remains present, run it separately and explicitly; ordinary Phase-11 verification relies on recorded deterministic fixtures rather than the public network.

## Phase Exit Criteria

- [ ] The single Phase-02 public Spot adapter remains the only acquisition path and supports larger admitted paper datasets.
- [ ] Venue precision/minimum constraints affect paper fills explicitly.
- [ ] Direct and one-declared-bridge routes are deterministic and costed per real leg.
- [ ] Multi-asset rebalance remains long-only and reconciled.
- [ ] Independent reconciliation detects tampering/drift.
- [ ] Critical web inspection flows work end-to-end.
- [ ] A frozen survivor can accrue prospective `forward_paper` evidence without silently reusing that observed period for retuning.
- [ ] No live/private exchange API or infrastructure platform was introduced.

## Stop Conditions

Stop and redesign before adding authenticated order endpoints, a second/parallel venue data path, multiple venue adapters, route graph optimization, asynchronous worker queues, databases, schedulers, websocket market streams, or automatic failover. Those are live/operational architecture decisions, not paper-hardening conveniences.
