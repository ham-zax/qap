# Phase 14 — UX Architecture and Design System

**Purpose:** Define the frontend presentation contract shared by all Phase-14 route redesigns. This document contains architecture/design decisions only; route-specific implementation is split into sibling plans.

## Authority boundary

The React/Vite/TanStack Router/Query application is a read-only analytical presentation layer over OpenAPI-generated DTOs. The browser may format, scale, sort, filter, and visualize backend-produced values. It must not recalculate portfolio accounting, benchmark economics, fills, model evidence, research status, final-OOS state, or other financial/research truth.

Current-schema artifacts only are supported. Phase 14 adds no migration UI, compatibility renderer, old-schema fallback, database, global mutable financial state, live trading controls, authenticated account state, or browser-owned run execution.

## Styling and component architecture

- Use Tailwind CSS v4 through the first-party Vite plugin plus QAP semantic CSS variables.
- Keep the existing Lightweight Charts integration for time-series financial evidence.
- Extract shared components only after at least one real route requires them; route-first extraction is preferred to framework-first construction.
- Do not add Radix, Storybook, Lucide, a second charting library, a component framework, Redux/Zustand, or another design dependency without a demonstrated current consumer.
- Native controls are preferred when they satisfy the interaction and accessibility contract.
- `ExactNumber`/`TableScroll` may remain where audit content genuinely consumes them; dead presentation components are deleted rather than retained as compatibility wrappers.

## UX laws

The workbench follows these concrete rules:

1. **Jakob's Law:** use familiar analytical-dashboard hierarchy: title/verdict, primary evidence, secondary explanation, audit.
2. **Hick's Law:** keep the first view focused on decisions rather than exposing all controls/details simultaneously.
3. **Chunking:** group roughly 3–5 related KPIs rather than creating flat metric walls.
4. **Von Restorff:** one dominant research/operational outcome is visually unmistakable.
5. **Gestalt proximity/common region:** explanatory copy stays with the evidence it qualifies.
6. **Serial-position effect:** conclusion first; machine identity/provenance last.
7. **Recognition over recall:** human labels appear in normal reading flow; raw IDs remain audit data.
8. **Fitts's Law:** important controls/links have practical hit targets, including mobile use.
9. **Progressive disclosure:** exact values, fingerprints, SHAs, routes, fills, and precision metadata are deliberate disclosures.
10. **Accessibility is information architecture:** status is never color-only, heading hierarchy is correct, keyboard controls work, and long audit data does not become the default screen-reader experience.

## Information hierarchy

The default UI should let a user answer, without opening technical details:

1. Did the strategy outperform or underperform its declared objective?
2. Compared with which primary control and HODL counterfactual?
3. Did the result meet the predeclared success threshold?
4. How did performance evolve through time?
5. How did portfolio composition change?
6. What execution cost/no-fill burden occurred?
7. What pair/model evidence was persisted?
8. Did a paper operation reconcile and were any legs rejected/no-fill?
9. What research boundary applies (development, final OOS consumed/unconsumed, forward paper)?

Technical/audit data includes run/research-family IDs, dataset IDs, git SHA, code/manifest/data fingerprints, exact decimals, route/fill IDs, venue precision metadata, full event/rebalance/fill tables, canonical pair implementation details, and reciprocity fingerprints. This evidence remains available; Phase 14 changes prominence, not evidentiary retention.

## Design language

### Semantic surfaces

Use three ordinary surface roles:

- `canvas`: page/background and low-emphasis regions;
- `panel`: primary bounded content/visual sections;
- `subtle`/raised: nested KPI or secondary explanation surfaces.

Raised elevation/shadow is reserved for overlays/popovers, not every card. Borders and spacing distinguish most hierarchy.

### Semantic status

Use text plus semantic treatment for:

- positive research outcome;
- negative research outcome;
- warning/threshold miss/partial condition;
- informational/research-boundary state;
- reconciliation mismatch/error.

Arithmetic direction and research success are distinct. A positive numeric delta below a declared positive success threshold must not use the same success treatment as a passing result.

### Typography and numbers

- Page H1: compact analytical title; one per route.
- Section H2/H3 hierarchy must be structural rather than decorative.
- Normal prose uses readable proportional text.
- KPIs and financial columns use tabular lining numerals.
- Default display values are rounded/readable; exact persisted strings are available through explicit audit/exact-value affordances and must never be numerically mutated in the browser.
- Tiny non-zero values must remain visibly non-zero when formatting would otherwise imply zero.

### Spacing and responsive layout

- Base rhythm is 4px-derived.
- Mobile page gutters: 16px.
- Desktop content gutters: roughly 24–32px within the established max-width shell.
- Primary controls are at least practical 44px-class targets where touch is expected.
- No page-level horizontal overflow at 390px; wide audit tables/code are internally scrollable and keyboard reachable.
- 200%-equivalent reflow must not require horizontal page scrolling.

### Motion

Use motion only for small state transitions. `prefers-reduced-motion` removes nonessential transitions/animations. No chart/metric animation may imply financial significance.

## Chart contract

Every time-series chart must expose:

- a clear title;
- what each line represents;
- units/orientation;
- zero/parity meaning where relevant;
- accessible textual summary/legend;
- persisted/backend-produced data only.

Chart series colors come from chart semantic tokens rather than arbitrary route hex values. Asset/series identity colors must not casually reuse success/error colors. Status markers may use status tokens because status is their meaning.

Comparison visuals must preserve sign and distinguish arithmetic direction from declared pass/fail semantics. Composition visuals may use backend-provided weights; React must not derive economic weights from raw quantities/fills when the DTO does not provide authoritative weights.

## Controls and disclosures

- Current selection is text/state + visual treatment, not color alone.
- URL-owned analytical state remains URL-owned (pair orientation/view/anchor; selected rebalance decision where implemented).
- Native `<select>` is acceptable for anchor selection.
- Disclosures remain keyboard-operable native `<details>/<summary>` unless a concrete interaction requires more.
- Long tables use `TableScroll`/equivalent contained regions with keyboard access.
- Error/empty/loading states retain AppShell navigation and a recovery path.

## Accessibility baseline

Acceptance targets:

- WCAG A/AA axe audit: 0 violations and 0 incomplete findings on tested route states;
- visible focus ring with sufficient contrast;
- skip link reaches `main`;
- headings are sequential and useful;
- status is not color-only;
- closed disclosures remove hidden audit content from normal reading flow;
- horizontal scroll regions are focusable when keyboard scrolling is required;
- 390px document width equals viewport width;
- reduced-motion preference is honored.

## Shared component policy

Proven shared concepts may include:

- status badge/presentation mapping;
- human/exact numeric formatting;
- outcome/verdict framing;
- zero-centered comparison bars;
- backend-weight composition bars;
- breadcrumbs;
- audit disclosure/table primitives.

A component catalog is not part of Phase 14. If later route count/consumer count makes an isolated catalog materially useful, propose it separately rather than adding tooling silently.

## Verification

Architecture/design-system convergence is verified through:

- repository search for duplicate/dead presentation components and hardcoded status/series colors;
- frontend typecheck/tests/build;
- Agent Browser rendered desktop/mobile checks;
- axe, keyboard, reduced-motion, reflow, overflow, and console/network checks;
- no CSS/screenshot snapshot test suite.
