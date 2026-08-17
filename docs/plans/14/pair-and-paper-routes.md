# Phase 14 — Pair and Paper Route Redesign

**Purpose:** Define Phase-14 behavior for Pair Workbench and forward-paper operation surfaces. Shared presentation/accessibility rules come from `architecture-and-design-system.md`.

## `/pair/:runId/:assetX/:assetY` — Pair Workbench

### Chart-first layout

The route headline is the requested/displayed orientation in readable form. A small `Pair workbench` eyebrow and descriptive-only research disclaimer provide context without displacing charts.

Primary controls are compact and grouped:

- reciprocal orientation action;
- anchor selection;
- Ratio / Log ratio / Normalized paths / Anchor lens view selection.

URL state remains authoritative for:

- pair route identity;
- displayed orientation;
- anchor;
- selected chart view.

Reciprocal orientation must not change canonical pair identity or fabricate a separate model fit.

### Primary evidence

For non-anchor views, show the selected pair chart followed by persisted model evidence. For anchor view, show the synchronized anchor decomposition followed by the same persisted model-evidence context.

When persisted model evidence is absent, render an explicit model-free state; do not leave an empty chart that suggests missing UI data.

Shared cursor/range synchronization must remain intact. Ratio/log/normalized/anchor labels must state orientation/units clearly.

### Secondary/audit content

Move these behind deliberate disclosure:

- strategy rebalance markers/actions and their machine IDs;
- canonical pair identity details;
- fit/evidence reciprocity;
- deterministic identity-coordinate explanation;
- source fingerprints;
- anchor identity-error metadata;
- exact technical decision/fill IDs.

Closed disclosures should remove this content from the normal reading flow. Long fingerprints are internally scrollable and keyboard-focusable when necessary.

### Serious regression contract

Automated tests protect URL/orientation/anchor identity and genuine analytical semantics. Browser verification covers chart prominence, control layout, synchronized cursor/range, mobile overflow, keyboard focus, and disclosures.

## `/paper-operations` — Operational Evidence Index

Render scannable paper-rebalance cards. Normal reading flow includes:

- execution timestamp;
- reconciliation status;
- forward-paper / operational-dry-run evidence badge;
- fill count;
- readable fees/slippage/bridge residual;
- explicit `Not candidate or deployment evidence` boundary;
- `Inspect operation` action.

Raw route IDs and long operation IDs are secondary. The page has no execution/mutation controls.

The summary DTO does not contain authoritative no-fill count; do not derive or invent one on the list page.

## `/paper-operations/:operationId` — Paper Operation Detail

### First viewport

Use a human H1 such as `Paper rebalance`, not the raw operation ID. Show:

- breadcrumb;
- reconciliation badge;
- `Forward paper · operational dry run` badge;
- compact operational outcome sentence;
- execution timestamp and bridge;
- fills / no-fill leg count when the detail DTO supports it through persisted orders;
- fees, slippage, bridge residual;
- explicit research-boundary banner stating the artifact is not valid for parameter selection, model promotion, or deployment evidence.

Operation/fingerprint identities remain available below.

### Execution story

Present an ordered operational flow from persisted evidence:

```text
Starting portfolio
 -> sells to bridge
 -> bridge inventory
 -> buys from bridge
 -> ending portfolio
```

This flow is explanatory only. It uses persisted orders/fills and does not recalculate wallet/accounting truth.

No-fill/rejection outcomes are primary operational evidence. Example presentation:

`No fill · SOL · Below Minimum Notional`

A no-fill reason must remain visible without opening the full orders table. A fully filled operation must not show a false exception section.

### Allocation/tracking evidence

Target allocation may be visualized from persisted `target_weights`. Starting/ending holdings are quantities unless authoritative corresponding weights exist in the DTO. Do not infer starting/ending portfolio weights from quantities/prices/fills in React merely to make a comparison chart.

Target tracking and independent reconciliation remain readable normal sections because they explain operational correctness. Exact tables are available in audit disclosures where appropriate.

### Technical/audit disclosures

Collapse by default:

- exact route/order table;
- fill table and fill IDs;
- full starting/target/ending quantity tables;
- venue precision/minimum-notional metadata;
- valuation/reference-price tables;
- input fingerprint;
- exact unrounded decimals.

Wide tables/fingerprints scroll inside focusable regions at 390px and must not expand document width.

## Files / ownership

Primary files include:

- `web/src/features/pairs/PairWorkbench.tsx`
- `web/src/features/pairs/PairRatioChart.tsx`
- `web/src/features/pairs/RelationshipEvidencePanel.tsx`
- `web/src/features/pairs/RelationshipEvidenceChart.tsx`
- `web/src/features/pairs/AnchorLensPanel.tsx`
- `web/src/features/pairs/RebalanceMarkerOverlay.tsx`
- `web/src/features/pairs/pairSearch.ts`
- `web/src/features/paper/PaperOperationList.tsx`
- `web/src/features/paper/PaperOperationDetail.tsx`
- `web/src/features/paper/PaperExecutionFlow.tsx`

## Serious regression policy

Keep/introduce automated tests for:

- reciprocal orientation and anchor URL state;
- model-free pair evidence state;
- identity/anchor semantics that could invert analytical meaning;
- forward-paper research boundary;
- explicit no-fill evidence;
- exact financial string preservation.

Do not add tests for visual card counts, copy-only rearrangement, every disclosure, or screenshot snapshots.

## Rendered acceptance

At desktop and 390px mobile verify:

- Ratio, Log, Normalized, and Anchor states;
- reciprocal orientation via keyboard/click;
- synchronized cursor/range;
- anchor charts/labels;
- pair provenance closed by default;
- paper list cards and healthy/no-fill detail cases;
- no false exception section for a full-fill operation;
- opened technical tables/fingerprints remain internally scrollable and keyboard accessible;
- document width equals viewport width;
- axe A/AA 0 violations / 0 incomplete;
- no unexpected console/page errors.
