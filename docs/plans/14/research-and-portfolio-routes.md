# Phase 14 — Research and Portfolio Route Redesign

**Purpose:** Define the Phase-14 implementation contract for Research Runs, Experiment Detail, and Portfolio Economics. Shared visual/formatting rules come from `architecture-and-design-system.md`.

## `/experiments` — Research Runs

### Default experience

Render persisted runs as scannable result cards rather than an artifact table. Each valid card shows:

- experiment name;
- research status badge;
- data-role/final-OOS badge;
- basket/model/policy/anchor context;
- readable primary comparison;
- family search denominator as **family attempts**;
- execution/run timestamp where useful;
- a clear `View result` action.

Invalid artifacts remain visible as invalid evidence with their validation message. Raw run/family IDs, dirty-state markers, and other machine identifiers are secondary/audit information rather than the card headline.

Do not add search/filter/dashboard-builder infrastructure merely because cards exist. Add discovery controls only when the real run population demonstrates a present need. This route is a browser over completed persisted evidence; it is **not** the active Research Scanner/Candidate Workbench defined by Phase 15.

### Serious semantics

- Negative/rejected evidence must never receive success presentation.
- Signed primary comparisons must preserve their sign.
- `family_attempt_count` counts every attempt in the research family, including the current run; copy must say `1 family attempt`, `N family attempts`, never “sibling trials”.
- Exact persisted financial values remain recoverable without forcing long decimals into the visible card.

## `/experiments/:runId` — Experiment Detail

### First viewport

Present:

1. breadcrumb back to Research Runs;
2. research status/data-role badges;
3. experiment name;
4. plain-language verdict relative to the primary benchmark;
5. primary comparison and strict-inventory HODL comparison;
6. the **predeclared success threshold** when the primary metric is threshold-governed;
7. direct actions to Portfolio Economics and Pair Workbench when the persisted basket supports a pair view.

A positive arithmetic increment below a positive success threshold remains a threshold miss. Research `status` and `success_threshold` are authoritative; visual comparison bars must not imply that every right-of-zero value is a successful research result.

### Secondary evidence

- `What was tested?`: basket, relationship model, policy, anchor, universe mode, data window.
- `Benchmark outcome`: zero-centered comparison visual with sign/threshold semantics.
- `Research boundary`: data role, final-OOS consumption status, family attempt count, primary metric, holdout execution state.
- `Technical provenance`: collapsed by default; contains run ID, family ID, parent run, git/code/manifest/data fingerprints and holdout identity.

No browser-side recomputation of benchmark results or success state.

## `/portfolio/:runId` — Portfolio Economics

Portfolio is the primary economics dashboard for one persisted experiment.

### First viewport

Show:

- breadcrumb to Experiment Detail;
- result/data-role badges;
- `Portfolio economics` H1;
- plain-language research verdict;
- at most four dominant KPIs:
  - vs primary control;
  - vs strict inventory HODL;
  - maximum relative drawdown;
  - execution fills/cost summary;
- direct **Pair workbench** navigation using the same canonical basket/orientation/anchor URL contract as Experiment Detail;
- primary relative-wealth chart immediately below the outcome block.

The direct Portfolio -> Pair handoff is a Phase-11 critical integration contract and must be covered by Playwright without jumping back to Experiment Detail.

### Secondary sections

- benchmark ladder visual; full role-economics table stays in disclosure;
- portfolio composition using backend-provided starting/terminal weights;
- allocation history chart;
- same-mark inventory/value attribution vs HODL/matched contribution;
- risk/execution cost summaries;
- declared external-flow context;
- compact rebalance-decision navigator;
- advanced log-relative compounding view in disclosure.

### Rebalance decision navigation

Do not render every decision expanded. One selected decision owns the visible audit state. Selection is encoded in the URL so reload/back/forward preserve the exact decision identity. Desktop may use a compact decision rail; mobile uses Previous/Next or an equivalently bounded control. Every decision's exact holdings/fills/evidence remains available through audit disclosure.

### Portfolio economic authority

Use only backend-provided holdings, weights, costs, performance series, same-mark deltas, controls, and rebalance audit data. Do not reconstruct portfolio weights or economic attribution from raw fills in React.

## Files / implementation ownership

Primary route/component files include:

- `web/src/features/experiments/ExperimentList.tsx`
- `web/src/features/experiments/ExperimentDetail.tsx`
- `web/src/features/experiments/presentation.ts`
- `web/src/routes/portfolio.$runId.tsx`
- `web/src/features/portfolio/PortfolioOverview.tsx`
- `web/src/features/portfolio/BenchmarkLadder.tsx`
- `web/src/features/portfolio/BenchmarkRoleTable.tsx`
- `web/src/features/portfolio/RelativeWealthChart.tsx`
- `web/src/features/portfolio/LogRelativeWealthChart.tsx`
- `web/src/features/portfolio/AllocationHistoryChart.tsx`
- `web/src/features/portfolio/InventoryVsHodlTable.tsx`
- `web/src/features/portfolio/ExternalFlowContext.tsx`
- `web/src/features/portfolio/RebalanceDecisionAudit.tsx`

Shared visual primitives are introduced only when actually consumed by these routes.

## Automated regression policy

Keep automated coverage focused on serious behavior:

- negative/rejected evidence remains negative;
- signed relative-percent formatting is not inverted;
- exact persisted values are not numerically altered;
- final-OOS research boundary is not lost;
- positive arithmetic increment below the predeclared threshold is not presented as research success;
- selected rebalance URL state identifies the same decision after reload;
- error shell/recovery navigation remains available.

Do not write tests for CSS class counts, every disclosure title, arbitrary card order, screenshot snapshots, or prose that Agent Browser can inspect more effectively.

## Rendered acceptance

At 1440×1000 and 390×844:

- `/experiments` is scannable and negative/invalid evidence is obvious;
- Experiment Detail first viewport answers result/control/threshold/research-boundary questions;
- Portfolio first viewport contains the primary economics and relative-wealth chart begins within or immediately after it;
- direct Portfolio -> Pair navigation works;
- rebalance decision selection survives reload/back/forward;
- audits are closed by default;
- no page-level horizontal overflow;
- exact/audit tables scroll internally;
- axe A/AA is 0 violations / 0 incomplete;
- keyboard focus and skip navigation are visible;
- no unexpected console/page/network errors.
