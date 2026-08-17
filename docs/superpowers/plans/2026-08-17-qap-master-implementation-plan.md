# QAP Master Implementation Plan

**Goal:** Build a clean, deterministic, spot-only wealth-compounding system, expressed through owned-inventory rebalancing, that can prove or reject relative-rebalancing strategies against matched passive ownership before any live-capital authority exists.

**Architecture:** One Python modular monolith owns market semantics, inventory, relationship evidence, allocation, execution, accounting, and experiments. FastAPI exposes authoritative results through OpenAPI to a React/Vite analytical SPA. QAP v1/v2 remain read-only evidence sources and never become runtime dependencies.

**Tech Stack:** Python 3.14, `uv`, pytest, Ruff, Pyright, Decimal-based accounting, NumPy/Pandas/PyArrow where data/model work requires them, Pydantic at external manifest/HTTP boundaries, FastAPI for the HTTP boundary, React 19.2 latest patched line, TypeScript, Vite 8.1 line, TanStack Router/Query, and TradingView Lightweight Charts 5.2 line. Additional visualization libraries are not dependencies until a concrete research view earns them.

## Global Constraints

- QAP's primary objective is portfolio wealth growth relative to matched passive HODL after realistic costs; inventory is the owned state being reallocated, and coin-unit accumulation is secondary attribution.
- Portfolio inventory is the economic object; pairs are evidence/execution atoms.
- Operate only on explicitly admitted assets the operator is willing to own.
- Spot-only, long-only, no leverage, no borrowing, no derivatives, no interest-bearing trading mechanics.
- QAP v1/v2 are read-only historical references. No runtime imports or architecture inheritance by default.
- Models are replaceable evidence instruments and cannot mutate holdings directly.
- Policy emits target allocation; execution produces fills; portfolio owns balances; accounting derives results.
- Partial rebalancing and residual inventory are first-class.
- Matched HODL from the same frozen starting basket is the primary control.
- Costs are explicit and applied exactly once.
- Historical decisions use only completed point-in-time data and default to next-bar-open execution.
- Frontend never owns wallet, fill, or accounting truth.
- No database, microservice, plugin framework, scheduler, multi-exchange abstraction, or live broker layer until a present requirement proves it necessary.
- Hand-written source/test files have a 500-line decomposition-review threshold and 700-line hard cap; generated files, lockfiles, vendor material, and data fixtures are narrowly exempt. A >700-line hand-written exception requires explicit design approval before implementation.
- Mixed-responsibility God objects are rejected even below the numeric cap; one coherent reason to change per module is the stronger rule.
- Avoid generic `utils`/`helpers`/`common` dumping grounds, speculative base classes, factories, registries, and inheritance layers without current consumers.
- Prefer explicit domain names, small pure functions, immutable value objects, composition, and inward dependency flow.
- No live order placement without a separate Phase 12 go/no-go approval.
- Plans may be refined as evidence appears, but changes to economic objective, action-space, state ownership, benchmark semantics, timing semantics, historical-reference boundary, or live-capital authority require design review.

## Intended Repository Shape

Files and directories are created only in the phase that needs them.

```text
qap/
  README.md
  AGENTS.md
  pyproject.toml
  uv.lock
  .gitignore
  src/qap/
    market/
    portfolio/
    relationship/
    policy/
    execution/
    evaluation/
    experiment/
    api/
  tests/
    unit/
    scenarios/
    contract/
    fixtures/
  web/
    package.json
    pnpm-lock.yaml
    vite.config.ts
    src/
      api/
      routes/
      features/
        portfolio/
        pair-workbench/
        experiments/
      components/
      styles/
    tests/
  docs/
    REFERENCE_BOUNDARY.md
    superpowers/specs/
    superpowers/plans/
    plans/
  data/              # gitignored runtime data
  runs/              # gitignored generated experiment artifacts
```

No generic `services/`, `utils/`, `common/`, `framework/`, or `plugins/` package is created up front. Shared code is extracted only after two real consumers establish a stable concept.

## Wave 1 — Prove Financial Truth

### Phase 00: Constitution and Repository Foundation

**Plan:** `docs/plans/00-constitution-and-repository-foundation.md`

Create the smallest executable Python repository, encode concise agent/project instructions, establish deterministic tooling, and prevent generated data/secrets from entering Git.

**Exit:** one importable package, one smoke test, lint/type/test commands green, and no product behavior beyond repository mechanics.

### Phase 01: Domain Kernel and Inventory Semantics

**Plan:** `docs/plans/01-domain-kernel-and-inventory-semantics.md`

Implement explicit assets, canonical pairs, quantities, portfolio state, allocation targets, and immutable state transitions. Establish `Decimal` accounting and the single-owner wallet invariant.

**Exit:** deterministic scenario tests prove balance conservation, no negative holdings, pair orientation identity, and valid allocation semantics.

### Phase 02: Market-Data Admission and Reproducibility

**Plan:** `docs/plans/02-market-data-admission-and-reproducibility.md`

Implement completed-bar semantics, local fixture/Parquet loading, validation, alignment, and fingerprints. Do not add an exchange SDK yet.

**Exit:** a frozen dataset can be reloaded byte-for-semantics identically; gaps/duplicates/orientation errors fail visibly; no future bar can enter an earlier decision window.

### Phase 03: Accounting, HODL, and Economic Evaluation

**Plan:** `docs/plans/03-accounting-hodl-and-economic-evaluation.md`

Implement common-numeraire valuation, matched HODL, HODL-relative portfolio wealth growth, per-asset attribution, cost/turnover accounting, and concentration diagnostics before any strategy model exists.

**Exit:** deterministic fixtures prove the strategy/HODL ratio, per-asset deltas, and accounting reconciliation under known hand-calculated cases.

## Wave 2 — Prove the Accumulation Mechanism

### Phase 04: Relationship Evidence, Pairs, and Anchor Lens

**Plan:** `docs/plans/04-relationship-evidence-pairs-and-anchor-lens.md`

Implement raw/log ratio evidence, canonical orientation, normalized path data, and anchor decomposition. No predictive model is introduced.

**Exit:** pair inversion and `log(X/Y)=log(X/A)-log(Y/A)` properties hold on synchronized fixtures, with explicit invalid-data handling.

### Phase 05: Policy, Target Allocation, and Rebalancing

**Plan:** `docs/plans/05-policy-target-allocation-and-rebalancing.md`

Implement a pure deterministic policy and rebalance planner that converts current inventory plus evidence into long-only target allocations and economically filtered deltas.

**Exit:** scenario tests demonstrate no-action, partial rebalance, full rotation as a special case, minimum-notional behavior, and no direct wallet mutation from policy.

### Phase 06: Deterministic Paper Execution and Replay

**Plan:** `docs/plans/06-deterministic-paper-execution-and-replay.md`

Implement direct-market paper fills at next-bar-open, explicit fee/slippage, idempotent fill application, and replay orchestration.

**Exit:** the same manifest/data produces the same fills and final holdings; costs are applied once; no negative balance or last-bar lookahead is possible.

### Phase 07: Experiments, Controls, and Research Protocol

**Plan:** `docs/plans/07-experiments-controls-and-research-protocol.md`

Implement small frozen manifests, fingerprints, result artifacts, matched HODL, a simple deterministic rebalance control, and explicit IS/OOS labeling.

**Exit:** one command/function reproduces a run from manifest and records positive, neutral, or negative outcomes without promotion bureaucracy.

## Wave 3 — Make QAP Inspectable

### Phase 08: FastAPI Contract and Web Boundary

**Plan:** `docs/plans/08-fastapi-contract-and-web-boundary.md`

Expose read-oriented portfolio, pair, series, and experiment resources through typed Pydantic DTOs/OpenAPI. Keep business logic in domain packages.

**Exit:** API contract tests prove serialization and error semantics; generated TypeScript types can be produced from OpenAPI without hand-maintained duplicates.

### Phase 09: React Analytical Workbench and Charts

**Plan:** `docs/plans/09-react-analytical-workbench-and-charts.md`

Build the local SPA with Portfolio, Pair Workbench, Anchor Lens, and Experiments surfaces. Use Lightweight Charts for synchronized financial series.

**Exit:** a user can visually inspect the same authoritative run that Python produced, switch pair orientation/anchor views, and see allocation/rebalance events without browser-side accounting.

## Wave 4 — Test Real Relationship Models

### Phase 10: First Real Relationship-Model Experiments

**Plan:** `docs/plans/10-first-real-relationship-model-experiments.md`

Implement a transparent rolling-log-ratio control model first, then perform an explicit admission review for the historically important Student-t Copula hypothesis. Reimplement Student-t only if the review identifies a specific present falsifiable question that survives the v1/v2 evidence boundary; historical importance alone is not enough.

**Exit:** the transparent model is economically evaluable under the common contract, and Student-t is either explicitly rejected without code or, if admitted, evaluated under identical policy/execution/baseline contracts on frozen OOS windows. No model is promoted merely for statistical fit.

## Wave 5 — Harden Paper Operation

### Phase 11: Paper-Operation Hardening

**Plan:** `docs/plans/11-paper-operation-hardening.md`

Add larger real datasets, one explicit public market-data venue adapter, operational reconciliation, explicit two-leg spot bridge routing if required, run inspection, and targeted browser end-to-end coverage.

**Exit:** paper runs remain deterministic/reconcilable under realistic data volume and cost/routing semantics, with operator-visible failures rather than fallback guesses.

## Wave 6 — Decide Live Readiness

### Phase 12: Live-Readiness Gate

**Plan:** `docs/plans/12-live-readiness-gate.md`

This is a decision/review phase, not automatic live implementation. Reconcile paper semantics, venue constraints, failure recovery, secrets, kill-switch requirements, compliance/action-space, and evidence quality.

**Exit:** either a documented `NO-GO` with reasons or a separately approved live-execution design. Earlier phases do not authorize live capital.

## Wave 7 — Automate Development Safely

### Phase 13: Autonomous Development Harness

**Plan:** `docs/plans/13-autonomous-development-harness.md`

Build an external repository-development loop that reads approved plans, executes bounded tasks, verifies them, records progress, and escalates architectural/economic changes.

**Exit:** autonomous sessions can continue approved engineering work without the harness becoming a dependency of QAP financial runtime or broadening scope on its own.

## Cross-Phase Verification Strategy

Every phase uses the narrowest verification that proves its risk boundary.

Baseline Python commands after Phase 00:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests
uv run python scripts/check_source_size.py
```

The source-size check warns/fails only on hand-written source/test files according to the 500/700-line rule and narrowly excludes generated/lock/vendor/data artifacts.

Web commands after Phase 09:

```bash
cd web
pnpm test
pnpm typecheck
pnpm build
```

Broader suites run only when affected behavior warrants them. Documentation-only changes use link/path/diff checks rather than manufacturing runtime tests.

## Required Scenario Fixtures

The executable plan intentionally keeps a small set of hand-auditable fixtures:

1. **Two-asset no-cost rotation** — exact balance conservation.
2. **Two-asset cost case** — exact fee/slippage drag applied once.
3. **No-action case** — target change is below economic threshold.
4. **Partial-rebalance case** — residual inventory remains after fill.
5. **Last-bar case** — decision cannot fill without next execution bar.
6. **Orientation case** — `X/Y` and `Y/X` share identity and reciprocal/log-sign semantics.
7. **Anchor case** — direct ratio equals anchor decomposition within declared tolerance.
8. **Matched-HODL case** — strategy and benchmark begin from identical vector.
9. **Deterministic replay case** — repeated run yields identical authoritative artifact hashes.
10. **Rejected-data case** — duplicates/gaps/ambiguous orientation fail explicitly.

Large stochastic test generation is not required initially. Property-based testing is reconsidered only after focused examples expose invariants that would materially benefit from broader generated domains.

## Historical Migration Rule

No plan task says "copy the old implementation." When a phase needs historical knowledge, the task must:

1. identify the relevant v1/v2 source;
2. state the behavior/evidence being considered;
3. classify it `REIMPLEMENT`, `TRANSPLANT`, `WRAP_TEMPORARILY`, or `REJECT`;
4. write a clean-QAP contract/test;
5. implement inside the new ownership model;
6. verify intended parity or intentional divergence.

The old repo remains read-only throughout normal clean-QAP work.

## Stop Conditions

Implementation stops and returns to design review when any task would:

- replace matched-HODL-relative wealth with standalone fiat P&L or another materially different primary objective;
- make one pair/model own portfolio economics;
- require leverage, derivatives, borrowing, or interest-bearing mechanics;
- create a second mutable wallet/accounting owner;
- introduce lookahead timing;
- silently synthesize executable markets;
- replace matched HODL with a materially different benchmark definition;
- import the historical repository at runtime;
- require a database/service/plugin framework without a demonstrated present consumer;
- expose live-capital order placement;
- broaden the autonomous harness beyond an approved plan.

## Completion Definition

The master plan is complete only when Phase 11 has produced a trustworthy paper product and Phase 12 has recorded a deliberate live-readiness decision. Phase 13 is a development-productivity capability and does not affect whether QAP's financial core is economically valid.
