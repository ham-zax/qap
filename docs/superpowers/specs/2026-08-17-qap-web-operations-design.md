# QAP Web, Operations, Verification, and Maintainability Design

**Date:** 2026-08-17

**Status:** Review draft; companion to `2026-08-17-qap-system-design.md`

## 15. Web product design

### 15.1 Recommended 2026 stack

As of this design date, official project documentation supports this selection:

- React 19.2 line, always using the latest patched release;
- TypeScript, current stable supported by the toolchain;
- Vite 8.1 line for SPA build/dev tooling;
- TanStack Router for typed routes/search state;
- TanStack Query for server-state fetching/cache;
- FastAPI for Python HTTP/OpenAPI boundary;
- TradingView Lightweight Charts 5.2 line for financial time series;
- Apache ECharts 6 only when a research scatter/heatmap/matrix genuinely needs it.

Versions are revalidated at implementation time; the architecture is not coupled to a specific patch release.

### 15.2 Why React + Vite, not Angular/Next/another signal framework

React + Vite is the smallest strong fit for a local analytical SPA over a Python backend. Angular would add framework surface that does not solve QAP's core complexity. A Next.js server layer would duplicate backend responsibility already owned by FastAPI. Signal-first frameworks are technically attractive but do not currently justify a smaller ecosystem for a chart-heavy analytical product.

No Redux/Zustand is introduced initially. TanStack Query owns server state, Router owns URL state, and ordinary React state owns local view interaction.

### 15.3 Core screens

#### Portfolio

Shows:

- QAP vs matched HODL vs simple baseline;
- relative-wealth curve;
- current holdings;
- allocation history;
- per-asset inventory vs HODL;
- costs and turnover;
- concentration.

#### Pair Workbench

For canonical `X <-> Y`:

- orientation toggle `X/Y` <-> `Y/X`;
- raw ratio;
- log ratio;
- normalized X and Y overlay;
- relationship-model panes;
- rebalance markers;
- data validity/coverage.

#### Anchor Lens

For pair `X/Y` and anchor `A`, synchronized views show:

- `X/Y`;
- `X/A`;
- `Y/A`.

This is decomposition/context, not a separate model authority.

#### Experiments

Shows:

- hypothesis;
- basket/window/model/policy;
- benchmark/control;
- IS/OOS status;
- result and provenance;
- rejected/neutral status as prominently as positive results.

### 15.4 Deferred visualizations

Deferred until evidence demands them:

- universe relationship heatmaps;
- large pair matrices;
- topology/network graphs;
- regime maps;
- high-dimensional research dashboards;
- generalized model-performance landscapes.

The system must not build a giant graph UI because v1/v2 once explored topology.

### 15.5 Chart truth boundary

Charts render authoritative backend results. The browser may perform explicitly visual transforms such as zoom/pan, normalize-to-100, or log display, but those transforms cannot mutate experiment economics or feed execution decisions.

## 16. API design

FastAPI is a thin boundary over application/domain functions, not an alternate business layer.

Initial resource families:

```text
GET /api/health
GET /api/portfolios/{portfolio_id}
GET /api/portfolios/{portfolio_id}/performance
GET /api/pairs/{asset_x}/{asset_y}
GET /api/pairs/{asset_x}/{asset_y}/series
GET /api/experiments
GET /api/experiments/{experiment_id}
```

The first API is intentionally read-oriented. Experiment execution remains the deterministic command/runner boundary until a later operator workflow demonstrates that an HTTP mutation endpoint is necessary.

OpenAPI is the frontend contract source. TypeScript DTOs/client types are generated rather than hand-maintained in parallel.

Errors use a stable typed envelope with machine-readable code, human-readable message, and relevant context. Ambiguous market mapping, missing required data, temporal invalidity, unsupported routing, benchmark mismatch, or accounting invariant failure return explicit failures rather than silent fallbacks.

## 17. Storage and provenance

Initial system storage is local-first:

```text
data/market/        immutable/partitioned admitted market data (gitignored)
runs/<run_id>/      run manifest + compact results + derived series (gitignored unless fixture)
tests/fixtures/     tiny deterministic datasets committed for tests
```

Each run records:

- run ID;
- git commit and dirty flag as supplemental provenance;
- deterministic code fingerprint over authoritative local source/config bytes;
- configuration fingerprint;
- data fingerprint(s) plus explicit data locators relative to the configured data root;
- relationship model/version;
- policy/version;
- cost/execution contract;
- timestamps;
- deterministic seed if randomness exists;
- result summary.

Large market datasets and generated runs are not committed to Git.

## 18. Testing and evidence strategy

Testing is proportional to actual risk.

### 18.1 Highest-value invariants

The most important executable invariants are:

- conservation/reconciliation of inventory through fills;
- no negative holdings;
- cost applied exactly once;
- deterministic replay;
- no decision uses future data;
- same starting vector for strategy and HODL;
- pair inversion/orientation consistency;
- target allocation validity;
- no unsupported instrument/action enters execution;
- result fingerprints change when authoritative inputs change.

### 18.2 Test layers

- focused unit tests for pure transformations;
- deterministic scenario tests for wallet/replay/accounting;
- contract tests for API serialization/OpenAPI;
- frontend component tests only for meaningful interaction/formatting contracts;
- end-to-end browser tests only for the few flows where integrated behavior matters;
- property-based testing considered later only where it materially strengthens an invariant beyond focused examples.

No tests are added merely to inflate coverage or prove implementation details.

### 18.3 Golden historical parity

Historical v1 behavior is compared only when clean QAP intentionally chooses parity. A difference from v1 is not automatically a regression.

## 19. Error and failure philosophy

QAP fails closed on semantic ambiguity and fails visibly on economic/accounting inconsistency.

Legitimate outcomes include:

- no action;
- insufficient evidence;
- unsupported market route;
- rejected experiment;
- no robust OOS effect;
- strategy underperforms HODL;
- model works only in a concentrated pocket.

The system must not manufacture activity to make dashboards look alive.

## 20. Security and deployment boundary

Initial usage is local/single-operator.

- API binds locally by default;
- no public deployment is assumed;
- no authentication subsystem is built until network exposure or multi-user access exists;
- exchange/API secrets never enter Git or experiment artifacts;
- secrets may come from operational environment/secret storage, but business policy does not;
- CORS is narrow and explicit;
- live trading credentials are not needed for historical/paper phases.

## 21. Autonomous-agent harness boundary

The future autonomous development harness is deliberately outside QAP's financial runtime.

Its job is to execute approved plans on the repository:

```text
inspect approved plan
  -> choose next bounded task
  -> implement
  -> run task-specific verification
  -> review diff/evidence
  -> record progress
  -> continue
```

It must stop/escalate when a task would change:

- economic objective;
- action-space/Shariah boundary;
- architecture ownership;
- authoritative execution/accounting semantics;
- scope beyond the approved plan;
- live-capital authority.

The harness never becomes a dependency of `src/qap` and is implemented only after the core development workflow is proven manually.

## 22. Rejected primary architecture approaches

### Strategy-first transplant

Fastest route to visible features, but it would encourage copying v1 mechanisms, trade lifecycle, CLI structure, and hidden assumptions. Rejected.

### Research-platform-first

Maximizes evidence machinery before proving the product kernel and risks recreating v2. Rejected as the primary architecture.

### Recommended: allocation-first inventory kernel

```text
market observations
 -> relationship evidence
 -> policy
 -> target allocation
 -> deterministic execution
 -> portfolio state
 -> HODL-relative accounting
```

This is recommended because it directly models the economic object, makes partial rebalancing native, isolates models, and allows accounting truth to be proven with a dummy policy before statistical sophistication enters.

## 23. Non-negotiable invariants

### Economic

1. Matched-HODL-relative portfolio wealth is the primary objective; a reporting numeraire is only a valuation coordinate.
2. Inventory is the owned economic state; per-asset coin accumulation is secondary attribution, not a substitute for wealth creation.
3. Passive ownership is the primary control.
4. Costs are explicit and applied exactly once.
5. Assets are admitted inventory, not anonymous tickers.
6. A claimed active edge must survive comparison to simpler admissible behavior.

### Mechanism

6. Relative relationships are the information source.
7. Rebalancing/rotation is the monetization mechanism.
8. Partial rebalancing is first-class.
9. Residual inventory is first-class state.
10. No-action is first-class.

### Architecture

11. Portfolio inventory is the economic owner; pair relationships are evidence atoms.
12. Models are instruments, not authorities.
13. Signal evidence cannot silently become economic authority.
14. One mutable state has one owner.
15. Frontend never owns financial truth.
16. QAP v1/v2 are references, not runtime/architecture dependencies.

### Evidence

17. Point-in-time correctness is mandatory.
18. OOS evidence dominates in-sample persuasion.
19. Concentrated edge is not generalized edge.
20. Reproducibility should be cheap and deterministic, not bureaucratic.
21. Research cannot silently mutate default policy.

### Scope and maintainability

22. No abstraction without a present boundary or at least two real consumers.
23. No feature without a present falsifiable reason.
24. No hidden environment-variable business state.
25. No live execution until historical/paper semantics reconcile and a separate live-readiness gate is approved.
26. Hand-written source and test files have a **500-line review threshold** and a **700-line hard cap**. A file approaching 500 lines triggers decomposition review; a hand-written file may exceed 700 lines only after an explicit design exception is recorded before implementation. Generated files, lockfiles, third-party/vendor material, and data fixtures are exempt from the numeric cap but must never be edited as if they were normal source.
27. A file must have one coherent reason to change. Line count is a guardrail, not permission to build a 650-line God object; mixed responsibilities, excessive fan-in/fan-out, or unrelated state ownership require decomposition earlier.
28. Avoid generic dumping grounds such as `utils.py`, `helpers.py`, `common.py`, or catch-all `services.py`. Shared code is extracted under a domain name only after real consumers establish the concept.
29. Public functions/classes expose narrow contracts; implementation details remain local. Prefer composition, pure functions, immutable value objects, explicit dependency flow, and small modules over inheritance/factory/registry stacks.
30. Functions and methods should stay small enough to understand without scrolling through multiple responsibilities. A function growing beyond roughly 60–80 logical lines or requiring multiple unrelated phases is a decomposition signal, not a target allowance.
31. Tests follow production boundaries and assert behavior/invariants rather than private implementation. Test files are subject to the same 500/700 line guard unless generated.
32. Dependency direction must remain inward toward domain/economic truth; web/API/adapters may depend on core contracts, never the reverse.

## 24. Anti-bloat admission test

Before adding any model, chart, package, abstraction, service, database, test framework, or operational system, answer:

1. What present QAP question does this answer?
2. Who owns its state?
3. Who consumes its result?
4. What simpler mechanism already exists?
5. What evidence would demonstrate usefulness?
6. What invariant does it preserve?
7. What happens if we do not build it now?

If the final answer is effectively "nothing; maybe later," do not build it.

### 24.1 Source-size and God-object guard

Repository verification should enforce the maintainability rule mechanically for hand-written code:

```text
< 500 lines   -> normal
500-700 lines -> warning/review required before further growth
> 700 lines   -> fail verification unless the file is explicitly exempt/generated
```

The automated check does not replace design judgment. A 300-line file with unrelated responsibilities can still be wrong; a generated route tree or lockfile may legitimately exceed the cap. Exemptions must be path-based, narrow, and documented in the checker rather than disabled globally.

## 25. Phase map

Implementation is decomposed into bounded plans under `docs/plans/`:

0. Constitution and repository foundation.
1. Domain kernel and deterministic inventory semantics.
2. Market-data admission and reproducible datasets.
3. Evaluation, HODL, and accounting truth.
4. Relationship evidence and pair/anchor math.
5. Policy, target allocation, and rebalancing.
6. Deterministic paper execution and replay.
7. Research/experiment protocol and simple controls.
8. FastAPI contract and typed web boundary.
9. React analytical workbench and core charts.
10. First real relationship-model experiments.
11. Paper-operation hardening and reconciliation.
12. Live-readiness gate (no live implementation authority by default).
13. Autonomous development harness, external to financial runtime.

Each phase has its own exit criteria. Later phases may refine future plans, but must not silently rewrite already-approved economic invariants.

## 26. First shippable QAP

The first meaningful product milestone is not a giant research suite and not live trading. It is a deterministic local application that can:

1. load one frozen historical dataset for a small admitted basket;
2. compute pair ratio/anchor relationship views;
3. run a deterministic policy that requests target allocations;
4. execute spot paper rebalances with explicit costs;
5. reconcile wallet holdings without negative balances or double-applied fills;
6. compare the ending basket to matched HODL and a simple rebalance baseline;
7. reproduce the run from its manifest/fingerprints;
8. render Portfolio, Pair Workbench, Anchor Lens, and Experiment views in the web app.

Only after this slice is economically/accountingly trustworthy does a real relationship model become a candidate for authority.
