# Phase 14 — Analytical Workbench UX Redesign

**Goal:** Make the read-only QAP workbench understandable without requiring users to interpret raw decimals, fingerprints, SHAs, route IDs, or artifact internals.

**Architecture:** Keep the existing React/Vite/TanStack Router/Query/OpenAPI architecture and QAP-owned backend truth. Reorganize the presentation around **verdict first → primary visual evidence → explanation → audit/provenance on demand**. Phase 14 does not add research execution, live trading, a database, or browser-owned financial logic.

**Status:** Implemented and under integrated acceptance/remediation. Detailed architecture and route plans are split below so this phase overview remains reviewable rather than becoming a planning God object.

## Plan set

1. [`14/architecture-and-design-system.md`](14/architecture-and-design-system.md)
   - frontend authority boundary;
   - Tailwind/QAP token architecture;
   - UX laws and information hierarchy;
   - color/typography/spacing/motion/accessibility contracts;
   - chart, table, control, disclosure, and exact-value conventions.
2. [`14/research-and-portfolio-routes.md`](14/research-and-portfolio-routes.md)
   - Research Runs;
   - Experiment Detail;
   - Portfolio Economics;
   - direct Portfolio → Pair Workbench integration;
   - threshold/family-attempt semantics;
   - serious regression boundaries.
3. [`14/pair-and-paper-routes.md`](14/pair-and-paper-routes.md)
   - Pair Workbench chart-first behavior;
   - reciprocal orientation/anchor URL state;
   - paper-operation list/detail outcome hierarchy;
   - no-fill/reconciliation/audit presentation.
4. [`14/acceptance-and-regression.md`](14/acceptance-and-regression.md)
   - serious automated regressions;
   - Phase-11 Playwright integration contract;
   - Agent Browser desktop/mobile matrix;
   - accessibility/reflow/reduced-motion/console gates;
   - final Phase-14 completion definition.

## Global constraints

- Browser is presentation-only. It may format, sort, scale, filter, and visualize backend-produced values, but it does not own accounting, HODL/control economics, fills, research status, target allocation truth, model fitting, or final-OOS state.
- Current-schema artifacts only. No compatibility/migration UI for obsolete artifact formats.
- Negative evidence remains visible; no UI wording/color may manufacture a positive research conclusion.
- Wealth relative to the correct matched passive counterfactual remains the primary economic objective.
- Primary-control success follows the predeclared success rule/threshold, not merely the sign of an arithmetic delta.
- Final-OOS and forward-paper boundaries remain explicit and cannot be relabeled in the browser.
- No live-capital controls, authenticated exchange access, private credentials, order placement, async trading jobs, or account state.
- No new global state/database/chart framework/component framework unless a later plan proves a concrete need.
- Automated UI tests stay focused on serious semantic/integration regressions; rendered QA owns ordinary layout/polish checks.

## Product thesis

Every primary route should answer, in order:

1. **Did it work?**
2. **Compared with what and under what declared success rule?**
3. **What visual evidence shows the path/outcome?**
4. **What operational/research limitation matters?**
5. **Why should I trust it?** — exact values/provenance/audit are available deliberately rather than dominating the screen.

Machine identity is not deleted. Run IDs, family IDs, dataset IDs, git SHA, code/manifest/data fingerprints, exact decimals, route/fill IDs, venue precision metadata, full event/rebalance/fill tables, and canonical pair internals remain evidence; they move behind technical/audit disclosure.

## Route outcomes

### Research Runs

Completed persisted evidence is shown as scannable result cards with status/data role, human primary comparison, basket/model/policy context, family-attempt denominator, and `View result`. This is not the active scanner.

### Experiment Detail

The first viewport leads with the research verdict, primary control/HODL comparisons, and the predeclared success threshold. Benchmark visuals distinguish arithmetic direction from research success. Research boundary and family-attempt pressure are visible; provenance is collapsed.

### Portfolio Economics

The first viewport leads with the economic verdict, at most four key metrics, and the primary relative-wealth chart. Backend-provided weights drive composition visuals. One URL-owned rebalance decision is inspected at a time. A direct Portfolio → Pair Workbench action satisfies the Phase-11 integrated inspection contract.

### Pair Workbench

Charts and interpretation dominate. Reciprocal orientation, anchor, and view remain URL-owned. Persisted relationship evidence follows the descriptive chart. Strategy markers, canonical construction, reciprocity details, source fingerprints, and identity metadata are secondary audit content.

### Paper Operations

The list emphasizes reconciliation, fills, costs, bridge residual, timestamp, and the forward-paper research boundary. Detail pages lead with reconciliation/no-fill outcomes and the persisted execution story. Route IDs, exact fills, venue precision metadata, fingerprint, and exact tables are collapsed.

## Serious regressions worth automating

- error shell/recovery navigation disappears;
- negative/rejected evidence is rendered as success;
- signed percent formatting reverses meaning;
- exact persisted numeric strings are changed;
- a positive primary delta below its threshold is success-colored;
- pair reciprocal orientation/anchor URL state changes identity;
- final-OOS or forward-paper research boundary is lost;
- paper no-fill evidence becomes hidden;
- portfolio rebalance URL identity drifts;
- Experiment → Portfolio → Pair requires a route shortcut rather than visible navigation.

Do not build a broad screenshot/CSS-copy test suite.

## Explicit non-goals

- live trading controls or capital authority;
- browser-side experiment execution;
- auth/accounts redesign;
- dashboard builder;
- topology/heatmaps;
- new global state/database;
- second charting framework;
- opaque composite “QAP score”;
- hiding/deleting negative evidence;
- reconstructing financial truth from raw fills in React;
- compatibility UI for obsolete artifact schemas;
- active research scanning/candidate generation.

## Phase-15 boundary

Phase 14 intentionally does **not** satisfy the active research-workbench workflow. Phase 15 owns the separate Research Scanner and Candidate Workbench:

```text
portfolio / admitted-universe selection
  → pair or candidate-set generation
  → model selection
  → parameter-family selection
  → bounded scan execution
  → candidate ranking with control-aware evidence
  → portfolio/candidate combination analysis
  → freeze candidate / manifest for the next research stage
```

See [`15-research-scanner-and-candidate-workbench.md`](15-research-scanner-and-candidate-workbench.md). It must preserve simple-first controls, family/search-denominator accounting, data-role/final-OOS discipline, QAP-owned replay/economics, current-schema inputs, and the no-live-capital boundary.

## Implementation order / status

The implemented route-first order is:

1. Research Runs + minimum design/formatting foundation;
2. global shell/navigation;
3. Experiment Detail verdict page;
4. Portfolio Economics dashboard;
5. Pair Workbench;
6. Paper Operations;
7. design-system convergence/dead legacy removal;
8. rendered end-to-end acceptance.

Each route replacement follows:

```text
current-schema implementation
 → focused semantic/type/build checks
 → desktop browser QA
 → mobile/reflow/a11y QA
 → delete superseded presentation
 → final integrated verification
```

No dual legacy/current renderers remain “just in case.”

## Completion definition

Phase 14 is complete only when the detailed acceptance plan is green, including:

- verdict-first default experience;
- readable economic/operational summaries and visual evidence;
- explicit success-threshold semantics;
- exact/provenance evidence available on demand;
- negative evidence preserved honestly;
- Portfolio → Pair critical integration flow;
- frontend tests/typechecks/build and critical Playwright flows green;
- Agent Browser desktop/mobile accessibility, keyboard, reflow, overflow, reduced-motion, and runtime checks green.

## Standards basis

Implementation decisions use current authoritative standards/docs where relevant, including Tailwind CSS v4/Vite integration, Lightweight Charts accessibility guidance, WAI-ARIA Authoring Practices, and WCAG 2.2. External product patterns are design references only; QAP does not outsource financial/research authority to them.
