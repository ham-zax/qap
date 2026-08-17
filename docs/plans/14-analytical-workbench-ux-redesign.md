# Analytical Workbench UX Redesign Implementation Plan

**Goal:** Redesign the QAP web workbench so an end user can understand the research verdict, economic outcome, benchmark comparison, portfolio changes, and paper-operation result within seconds, while keeping exact audit/provenance data available only on demand.

**Architecture:** Keep the existing read-only React/Vite/TanStack Router/Query architecture and OpenAPI-generated DTOs. Reorganize presentation around verdict-first summaries, human-formatted metric cards, existing time-series charts, lightweight CSS/SVG comparison visuals, and progressive-disclosure audit panels. The browser remains a presentation layer: it may format, scale, sort, and visualize backend-produced values, but it must not recalculate portfolio accounting, benchmark economics, fills, or research truth.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, TanStack Router/Query, generated OpenAPI types, Lightweight Charts 5.2 for time series, semantic HTML/CSS for static comparison/composition visuals, Vitest/Testing Library for high-value regressions, Agent Browser for rendered UX/accessibility verification.

## Global Constraints

- Wealth relative to the correct matched passive counterfactual remains the primary economic story; coin accumulation stays secondary.
- Negative, neutral, rejected, invalid, and incomplete evidence must remain first-class inspectable outcomes. The redesign must never hide negative evidence or cosmetically imply success.
- No browser-side financial engine. Do not recompute wallet balances, fills, HODL, benchmark wealth, authoritative costs, or experiment outcomes in React.
- Presentation transforms are allowed only when they preserve backend meaning: percentage formatting of a backend relative-return ratio, compact number formatting, elapsed-time formatting, chart scaling, ordering, and visual grouping.
- Exact persisted values remain available for audit, but **raw 40–70 digit decimals are not primary UI copy**.
- Git SHAs, code/data/manifest fingerprints, run IDs, route IDs, venue precision fields, and other machine-oriented provenance are **technical details**, not default end-user content.
- Do not add a new charting dependency. Continue using Lightweight Charts for time series and semantic CSS/SVG for small categorical/composition visuals.
- Do not add Redux/Zustand or another global-state layer. TanStack Query remains server state; Router remains URL state; local React state remains view interaction.
- Do not introduce backend DTO changes merely to make the frontend prettier. If an authoritative semantic value is absent, omit that visual or explicitly plan a later backend contract rather than deriving financial truth in the browser.
- Preserve URL-addressable pair orientation, anchor, and view state.
- Preserve visible TradingView attribution for Lightweight Charts.
- Do not maintain legacy UI compatibility. Replace weak presentation patterns directly rather than layering compatibility wrappers around them.
- Per current testing preference, add automated tests only for serious/repeatable regressions or semantic financial mistakes. Do not create tests for every card, heading, spacing rule, or visual arrangement.
- Agent Browser is the primary acceptance tool for layout, hierarchy, mobile behavior, accessibility, and interaction quality.

## UX Laws and Design Rules Applied

### 1. Jakob's Law — use familiar analytical-dashboard structure

Each detail page follows a predictable order:

1. page context / breadcrumb;
2. verdict or operation outcome;
3. 3–5 key metrics;
4. primary explanatory visual;
5. secondary breakdowns;
6. audit/provenance details.

Do not make users learn a different hierarchy on experiments, portfolios, pairs, and paper operations.

### 2. Hick's Law — reduce simultaneous choices

- Keep primary global navigation to research runs and paper operations.
- Limit each page hero to at most two primary actions.
- Pair controls remain grouped into orientation, view, and anchor; do not scatter additional switches throughout the page.
- Audit details do not compete with the primary analytical flow.

### 3. Miller's Law / chunking — present small meaningful groups

- No section should lead with a flat list of 10–20 metrics.
- Use 3–5 KPI cards per decision group.
- Break long audits into summary rows/disclosures instead of fully expanded tables.
- Group related metrics by question: outcome, risk, cost, holdings, evidence, provenance.

### 4. Von Restorff Effect — make the primary verdict unmistakable

Every experiment and portfolio page gets one visually dominant outcome block. It states the status in words and the most important relative comparison. Secondary metrics must not visually compete with it.

### 5. Gestalt proximity/common region — group cause and explanation

- Benchmark comparisons sit next to the benchmark visual.
- Cost metrics sit together.
- Holdings composition and holdings deltas sit together.
- Pair score interpretation sits adjacent to the evidence chart.
- Technical provenance lives in one bounded disclosure region.

### 6. Serial-position effect — conclusion first, machine detail last

The first screen answers the economic question. SHA/fingerprint/raw-ID content appears only near the end of the page and collapsed by default.

### 7. Recognition over recall — translate domain identifiers into readable labels

Prefer:

- `Periodic rebalance (every 2 bars)` over `control:periodic-2` when the DTO permits a safe label;
- `Development` over `development`;
- `Final OOS · consumed` over raw state flags;
- `Underperformed HODL by 0.84%` over `strategy_vs_hodl = -0.008428...`.

Raw identifiers remain available in technical details.

### 8. Fitts's Law — make controls easy to acquire

- Interactive controls maintain at least 44×44 CSS-pixel hit targets.
- Segmented chart controls have clear active state and adequate spacing.
- Links used as primary actions render as button-like action targets, not tiny inline text.

### 9. Progressive disclosure — details on demand

Default view shows interpretation and decision-useful evidence. Exact values, full role tables, all rebalance rows, precision metadata, source fingerprints, code fingerprints, and manifest hashes live in collapsed `details`/audit panels.

### 10. Accessibility is part of information architecture

- Status is always text + visual treatment, never color-only.
- Charts keep nearby textual summaries.
- Heading hierarchy must be sequential.
- Tables remain keyboard-scrollable when needed.
- Compact-number presentation must not force screen readers to announce 70-digit values in the normal reading flow.
- Mobile 390px view must have no document-level horizontal overflow.

## Product Information Hierarchy

### What the default UI should answer

An end user should be able to answer these questions without opening technical details:

1. **Did the strategy outperform or underperform?**
2. **Compared with HODL and which primary control?**
3. **Was the result positive, neutral, or negative evidence?**
4. **How did performance evolve over time?**
5. **What changed in the portfolio?**
6. **What did execution cost?**
7. **For a pair model, what relationship was observed and how did it evolve?**
8. **For a paper operation, did it reconcile and were any legs rejected/no-filled?**
9. **What research boundary applies: development, final OOS, or forward paper?**

### What moves behind “Technical details” / “Audit trail”

- run ID;
- research-family ID and parent run ID;
- dataset IDs;
- git commit SHA;
- code fingerprint;
- manifest SHA/fingerprint;
- data/source fingerprints;
- raw relationship reciprocity fingerprints;
- paper-operation input fingerprint;
- exact unrounded decimals;
- venue tick/step/minimum precision metadata;
- raw route IDs;
- full event/rebalance/fill tables.

The UI does **not** delete these fields from the evidence system. It changes their prominence.

## Target Page Experience

### Research runs `/experiments`

Default experience: scan outcomes, not manifests.

Each run card shows:

- experiment name;
- status badge (`Positive`, `Neutral`, `Negative`, `Invalid`);
- data-role badge (`Development`, `Final OOS`, etc.);
- basket;
- plain-language primary comparison such as `-0.85% vs periodic-2`;
- model/policy short labels;
- one clear `View result` action.

Secondary details such as raw research-family ID, raw run ID, dirty-code flag, and sibling count move into a compact metadata row or card disclosure.

### Experiment detail `/experiments/:runId`

First screen:

- breadcrumb back to Research runs;
- experiment name + status/data-role badges;
- **Research verdict hero**:
  - plain-language headline;
  - primary-control comparison;
  - HODL comparison;
  - final-OOS/research-boundary state;
- action row: `Portfolio economics`, `Pair evidence` when available.

Below the fold:

1. `What was tested?` — basket, model, policy, date window, anchor;
2. `Benchmark outcome` — zero-centered comparison bars for HODL, primary control, matched contribution when available;
3. `Research context` — sibling count and claim boundary in readable language;
4. `Technical provenance` — collapsed.

The page should not lead with family IDs, fingerprints, or SHA strings.

### Portfolio economics `/portfolio/:runId`

This becomes the primary economics dashboard.

First screen:

- breadcrumb / experiment context;
- **Outcome hero:** e.g. `QAP finished 0.85% below periodic-2`;
- secondary line: `0.84% below HODL after modeled costs`;
- 4 KPI cards maximum:
  - vs HODL;
  - vs primary control;
  - maximum relative drawdown;
  - total modeled trading cost / fills.

Primary visual:

- existing relative-wealth line chart, immediately below the hero.
- Log-relative chart becomes an “Advanced compounding view” disclosure unless it is explicitly the current analytical task.

Secondary sections:

- **Benchmark comparison:** visual bars + concise labels; full role economics table collapsed under `Compare all benchmark roles`.
- **Portfolio allocation:** allocation-history chart plus starting/ending composition bars built from backend-provided weights.
- **What changed:** same-mark value deltas vs HODL visualized by asset; quantity deltas remain secondary because heterogeneous coin quantities are not comparable across assets.
- **Execution cost:** fee, slippage, turnover, fill count cards; raw exact values available on demand.
- **External flows:** concise contribution/withdrawal summary; full flow-ID audit collapsed.
- **Rebalance audit:** one compact timeline/list row per decision with selected/no-action state and reason; each row expands to target weights, evidence references, requested deltas, fills, and post-fill holdings.

No audit decision expands by default.

### Pair workbench `/pair/:runId/:assetX/:assetY`

First screen becomes chart-first rather than provenance-first.

Header:

- readable pair title (`BTC / USDT`);
- displayed orientation badge;
- short evidence disclaimer;
- controls grouped into one compact toolbar.

Main analytical area:

1. current requested ratio/log/normalized/anchor chart;
2. persisted model-evidence chart directly beneath it with synchronized time/crosshair;
3. short text summary of latest persisted evidence status/value when available;
4. rebalance markers as a collapsed `Strategy actions on this pair` section.

Move these behind `How this evidence is constructed`:

- canonical-pair implementation detail;
- identity-coordinate explanation;
- fit/evidence reciprocity;
- source fingerprints.

The common-reference identity coordinate warning remains accessible but no longer dominates the page header.

### Paper operations `/paper-operations`

Cards show operational outcomes rather than IDs:

- operation time/date;
- `Reconciled` / mismatch badge;
- fill count;
- no-fill count when nonzero;
- total fee/slippage presentation values;
- basket/bridge context;
- `Inspect operation` action.

Raw operation ID becomes secondary copyable metadata.

### Paper operation detail `/paper-operations/:operationId`

First screen:

- breadcrumb;
- `Paper rebalance` title rather than raw operation ID as H1;
- reconciliation badge;
- one compact research-boundary banner: `Forward paper only — not valid for model selection, promotion, or deployment evidence.`;
- summary cards: fills, rejected/no-fill legs, fees, slippage, bridge residual.

Primary visual:

- **Execution flow:** semantic stepper/timeline showing `Starting portfolio → sells → bridge inventory → buys → ending portfolio`, using persisted order/fill information only.
- **Before vs after composition:** horizontal composition bars from persisted starting/ending holdings/weights when available.

Secondary detail:

- no-fill/rejection callouts remain visible when present;
- full order/fill tables live under `Execution audit`;
- venue precision metadata, route IDs, input fingerprint, and exact values live under `Technical execution details`.

## Shared Component/File Structure

### Create

- `web/src/components/StatusBadge.tsx`
  - Textual semantic status with non-color-only cue.
  - Supports experiment status, reconciliation status, data role, and no-fill/rejected state through explicit variants rather than arbitrary strings.

- `web/src/components/OutcomeHero.tsx`
  - Shared dominant verdict/outcome surface.
  - Accepts eyebrow, headline, supporting copy, status, metrics/actions as React nodes.
  - Contains no financial logic.

- `web/src/components/MetricValue.tsx`
  - Replaces `ExactNumber` as the end-user presentation primitive.
  - Supports presentation modes: `relative-change`, `quantity`, `value`, `weight`, `integer`, `duration`, `raw-short`.
  - Keeps the original string attached for audit/copy where appropriate, but screen readers announce the readable value by default.
  - Never changes the underlying API value or feeds calculations back into the application.

- `web/src/components/DisclosurePanel.tsx`
  - Consistent semantic `details/summary` shell for `Technical details`, `Audit trail`, and advanced analytical sections.

- `web/src/components/Breadcrumbs.tsx`
  - Small route-context component for predictable back-navigation.

- `web/src/components/visuals/ComparisonBars.tsx`
  - CSS/SVG zero-centered bars for backend-produced relative comparisons.
  - Presentation-only numeric scaling.
  - Text labels remain authoritative/accessible.

- `web/src/components/visuals/CompositionBars.tsx`
  - Horizontal composition display for backend-provided asset weights.
  - Does not derive portfolio weights from values or quantities.

- `web/src/features/paper/PaperExecutionFlow.tsx`
  - Read-only semantic stepper built from persisted order/fill DTOs.
  - No simulated routing or financial derivation.

### Modify

- `web/src/components/AppShell.tsx`
  - Refine navigation labels, active-state treatment, and responsive header.

- `web/src/components/MetricCard.tsx`
  - Add hierarchy variants for primary/secondary KPI use; keep it presentation-only.

- `web/src/components/ExactNumber.tsx`
  - Remove after all call sites move to `MetricValue`; do not maintain a compatibility wrapper.

- `web/src/features/experiments/ExperimentList.tsx`
  - Convert flat evidence articles into scannable result cards.

- `web/src/features/experiments/ExperimentDetail.tsx`
  - Verdict-first layout; technical provenance collapsed.

- `web/src/features/portfolio/PortfolioOverview.tsx`
  - Reorder sections around outcome → primary chart → benchmarks → allocation → execution → audit.

- `web/src/features/portfolio/BenchmarkLadder.tsx`
  - Convert from raw metric-card ladder to concise benchmark comparison summary using human relative-change labels.

- `web/src/features/portfolio/BenchmarkRoleTable.tsx`
  - Keep as audit-level exact comparison table inside a disclosure panel.

- `web/src/features/portfolio/ExternalFlowContext.tsx`
  - Default to compact flow summary; full identifiers/details collapsed.

- `web/src/features/portfolio/InventoryVsHodlTable.tsx`
  - Add same-mark value-delta visual; retain exact table only as details.

- `web/src/features/portfolio/AllocationHistoryChart.tsx`
  - Improve title/subtitle/legend language; chart data contract unchanged.

- `web/src/features/portfolio/RelativeWealthChart.tsx`
  - Promote to primary economics visual and improve plain-language chart annotation.

- `web/src/features/portfolio/LogRelativeWealthChart.tsx`
  - Treat as advanced view rather than equal-weight default section.

- `web/src/features/portfolio/RebalanceDecisionAudit.tsx`
  - Replace vertically heavy expanded audit presentation with compact decision timeline/disclosures.

- `web/src/features/pairs/PairWorkbench.tsx`
  - Chart-first hierarchy and demoted technical relationship metadata.

- `web/src/features/pairs/RelationshipEvidencePanel.tsx`
  - Add latest-status/readable-summary area without recomputing model evidence.

- `web/src/features/pairs/RebalanceMarkerOverlay.tsx`
  - Present marker audit as secondary/collapsed strategy-action evidence.

- `web/src/features/paper/PaperOperationList.tsx`
  - Outcome cards with readable operation summaries.

- `web/src/features/paper/PaperOperationDetail.tsx`
  - Outcome-first operation flow; collapse raw orders/fills/metadata/provenance.

- `web/src/routes/__root.tsx`
  - Preserve full shell for failures and route-level context.

- `web/src/styles/tokens.css`
  - Add hierarchy/status/spacing tokens needed by the redesigned surfaces.

- `web/src/styles/global.css`
  - Replace generic “every section is the same bordered card” styling with explicit page, hero, KPI, chart, disclosure, toolbar, timeline, and responsive layout classes.

### Existing files intentionally retained

- `web/src/components/charts/TimeSeriesChart.tsx`
- `web/src/components/charts/SynchronizedChartGroup.tsx`
- `web/src/features/pairs/PairRatioChart.tsx`
- `web/src/features/pairs/AnchorLensPanel.tsx`
- `web/src/api/client.ts`
- `web/src/api/queries.ts`
- `web/src/api/types.ts`

Their data/interaction contracts remain valid; this plan changes presentation hierarchy around them.

## Task 1: Establish the semantic presentation layer

**Files:**
- Create: `web/src/components/StatusBadge.tsx`
- Create: `web/src/components/OutcomeHero.tsx`
- Create: `web/src/components/MetricValue.tsx`
- Create: `web/src/components/DisclosurePanel.tsx`
- Create: `web/src/components/Breadcrumbs.tsx`
- Modify: `web/src/components/MetricCard.tsx`
- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/global.css`
- Remove after migration: `web/src/components/ExactNumber.tsx`

**Interfaces:**
- Consumes: existing exact string DTO values and semantic status/data-role fields.
- Produces: reusable end-user formatting and hierarchy components used by all redesigned feature pages.

**Steps:**
- [ ] Define semantic display formats without embedding domain calculations in components.
- [ ] `relative-change` renders backend ratio values as readable percentages while retaining the original exact string for technical inspection.
- [ ] `duration` converts backend seconds into readable units (`9 h`, `2.4 d`) as a presentation transform.
- [ ] `value`, `quantity`, and `weight` use concise significant-digit formatting and explicit unit/context supplied by the caller.
- [ ] Ensure short values are not pointlessly reformatted and long values never dominate normal reading flow.
- [ ] Ensure screen readers announce the readable value rather than a duplicated 40–70 digit exact value.
- [ ] Add `StatusBadge` text/iconography semantics for positive/neutral/negative/invalid/reconciled/mismatch/forward-paper states.
- [ ] Build `OutcomeHero` with one dominant headline and bounded supporting metrics/actions.
- [ ] Build one consistent disclosure visual for technical/audit content.
- [ ] Update design tokens for primary/secondary surfaces, muted technical copy, status backgrounds/borders, tighter mobile spacing, and readable numeric typography.

**Testing/verification:**
- Keep or extend the existing exact-value regression only if necessary to prove readable display does not corrupt the original persisted value.
- Do not add snapshot tests for visual variants.
- Run: `cd web && pnpm test && pnpm typecheck && pnpm build`.

**Acceptance criteria:**
- A 70-digit decimal never appears as default visible copy.
- Exact source strings remain inspectable without becoming the primary screen-reader output.
- Status meaning does not rely on color.
- Shared components contain no portfolio/model/accounting logic.

## Task 2: Redesign global shell and navigation hierarchy

**Files:**
- Modify: `web/src/components/AppShell.tsx`
- Modify: `web/src/routes/__root.tsx`
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: existing TanStack routes and root error state.
- Produces: consistent global navigation, page context, and recovery shell.

**Steps:**
- [ ] Label `/experiments` as `Research runs` in navigation while preserving the route.
- [ ] Keep `Paper operations` as the second primary destination.
- [ ] Add clear active-route styling via TanStack Link state rather than hand-maintained local state.
- [ ] Ensure mobile header wraps/condenses without page overflow.
- [ ] Keep route errors inside the same shell and preserve both primary destinations plus Retry.
- [ ] Provide a predictable breadcrumb slot/pattern for detail pages.

**Testing/verification:**
- Preserve the existing serious route-error-shell regression.
- Use Agent Browser for normal navigation/active-state/layout behavior instead of adding tests for labels or CSS.

**Acceptance criteria:**
- User is never trapped on a detail/error page without a route back to research runs or paper operations.
- Global navigation fits at 390px without horizontal document overflow.

## Task 3: Redesign research-run discovery

**Files:**
- Modify: `web/src/features/experiments/ExperimentList.tsx`
- Modify: `web/src/features/experiments/ExperimentList.test.tsx` only if an existing semantic assertion must change.
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: `ExperimentListDto` / `RunSummaryDto` exactly as generated today.
- Produces: scannable result cards linking to existing detail routes.

**Steps:**
- [ ] Replace the dense definition-list card with a deliberate summary hierarchy: name, status/data role, primary comparison, basket, model/policy, action.
- [ ] Render `incremental_vs_primary_control` as a human relative percentage when present.
- [ ] Keep invalid artifacts visible as explicit invalid-result cards rather than suppressing them.
- [ ] Move research family ID, raw run ID, dirty flag, and sibling/trial metadata into a secondary metadata disclosure/row.
- [ ] Use responsive grid layout on wider screens and one-column cards on mobile.
- [ ] Do not add search/filter controls until the visible run count demonstrates a real need; this redesign should not invent dashboard machinery.

**Testing/verification:**
- Reuse the current test that negative evidence remains visible; update only assertions broken by meaningful semantic copy changes.
- Agent Browser: scanability at desktop and 390px mobile.

**Acceptance criteria:**
- A user can identify which runs won/lost and against which control without opening them.
- Raw IDs/hashes are not the visual focal point.

## Task 4: Redesign experiment detail around a research verdict

**Files:**
- Create: `web/src/components/visuals/ComparisonBars.tsx`
- Modify: `web/src/features/experiments/ExperimentDetail.tsx`
- Modify: `web/src/features/experiments/ExperimentDetail.test.tsx` only for existing research-boundary semantics.
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: current `ExperimentDetailDto.result`, manifest, commitment, provenance.
- Produces: plain-language verdict, benchmark comparison visual, compact research context, collapsed technical provenance.

**Steps:**
- [ ] Build a deterministic presentation mapper from result status + primary comparison into copy such as `Underperformed periodic-2 by 0.85%` or `Outperformed HODL by 1.2%`.
- [ ] Never infer success from sign alone when the DTO status/threshold says otherwise; status remains authoritative.
- [ ] Show HODL comparison, primary-control comparison, and matched-contribution comparison in zero-centered `ComparisonBars` when available.
- [ ] Put experiment description, basket, model, policy, anchor, and data window into `What was tested?` rather than a raw manifest dump.
- [ ] Summarize final-OOS state in plain language.
- [ ] Move raw family ID, parent run ID, dataset IDs/fingerprints, git SHA, code fingerprint, and manifest fingerprint into collapsed `Technical provenance`.
- [ ] Keep prominent links to portfolio economics and pair evidence.

**Testing/verification:**
- Preserve a serious semantic regression proving a negative final-OOS run is still presented as negative evidence and final-OOS state remains visible.
- Do not add tests for comparison-bar geometry or disclosure styling.

**Acceptance criteria:**
- First viewport communicates verdict, benchmark, research role, and next analytical action.
- Fingerprints and SHAs are absent from the default expanded reading flow.

## Task 5: Turn portfolio economics into the primary visual dashboard

**Files:**
- Create: `web/src/components/visuals/CompositionBars.tsx`
- Modify: `web/src/features/portfolio/PortfolioOverview.tsx`
- Modify: `web/src/features/portfolio/BenchmarkLadder.tsx`
- Modify: `web/src/features/portfolio/BenchmarkRoleTable.tsx`
- Modify: `web/src/features/portfolio/ExternalFlowContext.tsx`
- Modify: `web/src/features/portfolio/InventoryVsHodlTable.tsx`
- Modify: `web/src/features/portfolio/AllocationHistoryChart.tsx`
- Modify: `web/src/features/portfolio/RelativeWealthChart.tsx`
- Modify: `web/src/features/portfolio/LogRelativeWealthChart.tsx`
- Modify: `web/src/features/portfolio/RebalanceDecisionAudit.tsx`
- Modify: `web/src/features/portfolio/PortfolioOverview.test.tsx` only for serious semantic regressions.
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: current `ExperimentDetailDto`, `PortfolioSnapshotDto`, `PortfolioPerformanceDto`.
- Produces: verdict-first economics dashboard using only persisted/backend-derived economics.

**Steps:**
- [ ] Use `OutcomeHero` for status + primary-control and HODL relative outcome.
- [ ] Limit first-row KPIs to the economic decision set: vs HODL, vs primary control, max relative drawdown, and trading cost/fills.
- [ ] Promote `RelativeWealthChart` directly below the hero.
- [ ] Move `LogRelativeWealthChart` into `Advanced compounding view` disclosure while keeping it accessible.
- [ ] Redesign `BenchmarkLadder` into human-readable comparison bars/cards; move `BenchmarkRoleTable` into `Compare all benchmark roles` disclosure.
- [ ] Use backend-provided holding weights to render starting/terminal composition bars; keep exact holdings tables under `Exact holdings` disclosure.
- [ ] Use same-mark value deltas for the primary per-asset HODL-delta visual; do not compare heterogeneous raw coin quantities as if they shared a unit.
- [ ] Present fees, slippage, turnover, and fill count together in an execution-cost block.
- [ ] Format `time_below_*_seconds` as readable durations; retain exact seconds only in technical details if needed.
- [ ] Collapse detailed external-flow IDs unless flows are the current explanatory factor.
- [ ] Redesign rebalance audit as a compact chronological list/timeline with every decision initially collapsed.
- [ ] Each expanded decision keeps current weights, baseline target, QAP target, evidence IDs, modeled cost, requested deltas, fills, and post-fill holdings.
- [ ] Keep all tables inside `TableScroll`; no document-level horizontal overflow.

**Testing/verification:**
- Preserve the serious semantic test that HODL outperformance is not mislabeled as relationship/accumulation alpha.
- Preserve any existing tests that protect authoritative benchmark/delta values.
- Do not add tests for each KPI card, disclosure, or composition-bar label.
- Agent Browser must verify 1440×1000 and 390×844, including collapsed audit behavior and chart readability.

**Acceptance criteria:**
- First viewport answers whether QAP beat HODL and the primary control.
- The main explanatory chart appears before audit tables.
- Starting/ending allocation is visually understandable without reading exact quantities.
- Detailed rebalance evidence remains available but does not create a 20k+ pixel default mobile page.

## Task 6: Make pair analysis chart-first and interpretation-first

**Files:**
- Modify: `web/src/features/pairs/PairWorkbench.tsx`
- Modify: `web/src/features/pairs/RelationshipEvidencePanel.tsx`
- Modify: `web/src/features/pairs/RebalanceMarkerOverlay.tsx`
- Modify: `web/src/features/pairs/AnchorLensPanel.tsx` only for explanatory copy/layout where necessary.
- Modify: `web/src/features/pairs/PairWorkbench.test.tsx` only for URL/orientation/semantic regressions.
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: current pair series/evidence/anchor DTOs and URL search state.
- Produces: one coherent pair-analysis workspace without changing pair identity or model calculations.

**Steps:**
- [ ] Use readable pair/orientation title and compact toolbar.
- [ ] Keep orientation toggle, view segmented control, and anchor selector in one visual control group.
- [ ] Place the selected pair chart and synchronized evidence chart as the dominant content.
- [ ] Add a short readable summary of latest persisted evidence status/value where the DTO already provides it.
- [ ] Keep the disclaimer that pair evidence is descriptive and not proof of tradable alpha.
- [ ] Move canonical identity, synthetic/common-reference coordinate explanation, reciprocity fields, and fingerprints into `How this evidence is constructed`.
- [ ] Move rebalance marker audit beneath a collapsed `Strategy actions on this pair` section.
- [ ] Preserve synchronized crosshair/time-range behavior and URL state exactly.

**Testing/verification:**
- Keep existing orientation/URL-state tests because they protect a serious analytical identity contract.
- Do not add tests for heading copy or visual order.
- Agent Browser checks both reciprocal orientations, anchor lens, mobile toolbar, and synchronized charts.

**Acceptance criteria:**
- Pair chart is visible before provenance jargon.
- User can understand which pair/orientation is displayed and what the evidence means without reading fingerprints.
- No regression in reciprocal orientation or anchor URL state.

## Task 7: Redesign paper operations as operational outcomes

**Files:**
- Create: `web/src/features/paper/PaperExecutionFlow.tsx`
- Modify: `web/src/features/paper/PaperOperationList.tsx`
- Modify: `web/src/features/paper/PaperOperationDetail.tsx`
- Modify: `web/src/features/paper/PaperOperationList.test.tsx` only for exact-value/research-boundary regressions already worth protecting.
- Modify: `web/src/features/paper/PaperOperationDetail.test.tsx` only when serious semantics change.
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: current paper-operation summary/detail DTOs.
- Produces: readable paper-operation outcome cards, flow visualization, and progressive execution audit.

**Steps:**
- [ ] Replace raw operation ID as primary card/H1 content with `Paper rebalance` + readable timestamp/context; expose the raw ID as secondary copyable metadata.
- [ ] Collapse the three repeated research eligibility fields into one clear forward-paper boundary banner while retaining exact flags in technical details.
- [ ] Show reconciliation, fills, no-fill/rejected legs, fees, slippage, and bridge residual as the primary operation summary.
- [ ] Build `PaperExecutionFlow` from persisted orders/fills only: start → sells → bridge → buys → end.
- [ ] Use composition bars for starting/ending holdings if weights are already available in the DTO; if not available, keep holdings as readable cards/tables rather than deriving weights from quantities/value in React.
- [ ] Keep no-fill reasons visible and prominent when present.
- [ ] Move full route/order table, fill table, venue precision metadata, input fingerprint, and exact values into `Execution audit` / `Technical execution details` disclosures.
- [ ] Preserve read-only behavior; no Run/Submit/Execute control is introduced.

**Testing/verification:**
- Keep regression coverage for the serious research-boundary prohibition and exact financial-value preservation.
- Keep/no-add a focused no-fill test only if needed to prevent a rejected leg from disappearing in the new summary.
- Do not test every flow-step label or table wrapper.
- Agent Browser verifies healthy/reconciled and no-fill operation fixtures on desktop/mobile.

**Acceptance criteria:**
- User can understand whether the paper operation succeeded/reconciled and what execution cost without reading raw route IDs.
- No-fill evidence remains obvious, not hidden in a dense table.
- Technical precision/fingerprint data is available but collapsed.

## Task 8: Replace “wall of cards” styling with intentional visual hierarchy

**Files:**
- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/global.css`

**Interfaces:**
- Consumes: all redesigned semantic classes/components.
- Produces: coherent responsive visual system.

**Steps:**
- [ ] Define three surface levels: page background, primary analytical surface, secondary/audit surface.
- [ ] Reserve stronger border/background contrast for the single outcome hero and warnings; ordinary sections use quieter boundaries.
- [ ] Use a 12-column desktop grid only where it simplifies composition; collapse to one column on mobile.
- [ ] Give KPI values strong typographic scale and tabular numerals.
- [ ] Use consistent spacing rhythm between hero, primary visual, sections, and details.
- [ ] Keep chart containers bounded and responsive.
- [ ] Preserve table internal scrolling and prevent root horizontal overflow.
- [ ] Ensure status styles meet contrast requirements in dark mode and remain understandable without color.
- [ ] Avoid decorative gradients, glassmorphism, animated counters, or finance-dashboard theatrics that do not improve comprehension.

**Testing/verification:**
- No CSS snapshot tests.
- Agent Browser + axe on all primary routes at 1440×1000 and 390×844.

**Acceptance criteria:**
- Pages no longer look like every piece of information has equal importance.
- Default mobile views remain within viewport width.
- Outcome, primary visual, secondary explanation, and audit layers are visually distinct.

## Task 9: Rendered end-to-end UX acceptance

**Files:**
- No production files unless QA uncovers a concrete defect.
- Update this plan's execution/checkpoint section only if the mission workflow requires durable evidence.

**Interfaces:**
- Consumes: completed redesign.
- Produces: rendered UX evidence before commit/completion claim.

**Steps:**
- [ ] Start isolated API/Vite instances against current-schema experiment and paper-operation artifacts.
- [ ] Agent Browser: Research runs desktop/mobile.
- [ ] Agent Browser: Experiment detail positive/negative/invalid where fixtures exist.
- [ ] Agent Browser: Portfolio dashboard desktop/mobile; verify first viewport contains verdict + primary economics and no audit disclosure is open by default.
- [ ] Agent Browser: Pair ratio/log/normalized/anchor views; reciprocal orientation; synchronized cursor/range.
- [ ] Agent Browser: Paper operation healthy/reconciled and explicit no-fill case.
- [ ] Agent Browser: missing/invalid route retains full navigation shell and recovery action.
- [ ] Run axe WCAG A/AA on each primary route.
- [ ] Verify keyboard navigation for skip link, global nav, pair controls, disclosures, and scrollable tables.
- [ ] Verify 390px `document.documentElement.scrollWidth === window.innerWidth` on every primary route.
- [ ] Verify no unexpected console/page errors.
- [ ] Capture screenshots of each primary route for final visual review.
- [ ] Run frontend gate: `pnpm test`, `pnpm typecheck`, `pnpm build`.

**Acceptance criteria:**
- A reviewer can answer `did it work, compared with what, and why` from the first viewport of experiment/portfolio pages.
- Fingerprints/SHAs/raw IDs are not visible until a technical disclosure is opened.
- Long exact decimals are not default visible prose.
- Negative evidence remains visually normal and inspectable, not hidden or rendered as an application error.
- No document-level horizontal overflow at 390px.
- Zero unresolved WCAG A/AA violations in tested routes.
- No browser-side authoritative financial recomputation has been introduced.

## Serious Regression Tests Worth Keeping

The redesign should **not** test every visual detail. Automated regression coverage should remain concentrated on failures that would materially damage research correctness or navigation:

1. route/API error preserves the QAP shell and recovery navigation;
2. negative/rejected evidence remains visible and is not converted into a success state;
3. signed relative comparisons are not inverted when rendered as human percentages;
4. exact persisted financial strings are not mutated by display formatting;
5. pair reciprocal orientation + anchor URL state remains authoritative;
6. final-OOS / forward-paper research-boundary state remains visible and correctly labeled;
7. explicit paper no-fill evidence is not dropped from the user-visible result.

Do **not** add tests solely for:

- card count;
- CSS class names;
- exact visual ordering that Agent Browser can verify;
- every disclosure title;
- every heading/string rewrite;
- table wrappers already covered by the shared component;
- screenshot snapshots.

## Explicit Non-Goals

- No live trading controls.
- No experiment mutation/run button in the browser.
- No user accounts/auth redesign.
- No drag-and-drop dashboard builder.
- No broad universe heatmaps or topology graphs.
- No new backend database.
- No new global state library.
- No new charting library.
- No composite “QAP score” that collapses distinct research/economic metrics into one opaque number.
- No hiding or deleting negative evidence.
- No browser reconstruction of economics from raw fills.
- No compatibility/migration UI for obsolete artifact schemas; current-schema artifacts are the only supported evidence inputs.

## Recommended Implementation Order

1. Shared semantic presentation layer.
2. Global shell/navigation.
3. Research-run list.
4. Experiment verdict page.
5. Portfolio economics dashboard.
6. Pair workbench.
7. Paper operations.
8. Cross-page visual-system refinement.
9. Agent Browser rendered acceptance and final verification.

This order delivers visible value early while ensuring shared formatting and hierarchy conventions exist before feature pages are rewritten.

## Completion Definition

The UX overhaul is complete only when all of the following are true:

- the default experience is verdict-first rather than provenance-first;
- primary economics are shown as readable percentages/durations/value summaries and explanatory visuals;
- time-series charts are the primary means of understanding evolution over time;
- static comparison/composition visuals replace dense tables where a visual encoding is more legible;
- exact/raw evidence remains available through deliberate audit disclosures;
- fingerprints and SHAs are no longer primary content;
- portfolio and paper-operation audits are collapsed by default;
- pair provenance no longer dominates the chart workspace;
- negative evidence remains fully visible and semantically correct;
- current frontend tests, TypeScript, and production build pass;
- Agent Browser confirms desktop/mobile hierarchy, accessibility, keyboard behavior, no overflow, and no unexpected console/page errors.
