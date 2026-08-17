# Phase 14 — Acceptance and Regression Contract

**Purpose:** Define what proves the analytical-workbench UX redesign is complete. This is the verification companion to the Phase-14 architecture and route plans.

## Serious automated regressions

Automated tests are justified for repeatable semantic/integration defects, not for visual trivia. Keep or add coverage for:

1. application/error shell retains recovery navigation;
2. negative/rejected evidence cannot become success presentation;
3. signed relative comparison formatting cannot invert economic meaning;
4. exact persisted financial strings are not mutated;
5. a positive primary increment below a positive `success_threshold` is a threshold miss, not success-colored research evidence;
6. pair reciprocal orientation/anchor state remains URL-owned and analytically reciprocal;
7. final-OOS and forward-paper research-boundary states remain explicit;
8. paper no-fill evidence remains visible;
9. selected portfolio rebalance identity survives URL reload/back/forward;
10. Phase-11 critical path is `Experiment -> Portfolio -> Pair Workbench` through visible UI navigation.

Do not add automated tests solely for CSS classes, visual ordering, heading/copy edits, every disclosure title, repeated table wrappers, arbitrary card counts, or screenshot snapshots.

## Phase-11 Playwright contract

The two deterministic fixture flows remain mandatory after Phase 14:

```text
Known experiment
 -> Portfolio economics
 -> verify strict-HODL comparison and relative-wealth chart
 -> Pair workbench via Portfolio UI
```

and:

```text
Pair workbench
 -> invert orientation
 -> select anchor
 -> URL owns orientation/anchor/view
 -> synchronized anchor labels/charts remain correct
```

The first flow must not jump back to Experiment Detail with `page.goto` to reach Pair Workbench.

Run via the repository wrapper so the fixture API and frontend are deterministic:

```bash
uv run python scripts/run_playwright_e2e.py
```

## Agent Browser rendered matrix

Verify the real rendered application at both 1440×1000 and 390×844 for:

- Research Runs;
- Experiment Detail, including negative/invalid and final-OOS states where fixtures permit;
- Portfolio Economics;
- Pair Ratio, Log, Normalized, Anchor, reciprocal orientation;
- Paper Operations index;
- reconciled full-fill and no-fill Paper Operation Detail;
- error/not-found route inside the full AppShell.

### Per-route checks

- H1/section hierarchy matches the reading order.
- One primary verdict/economic outcome dominates the first view where relevant.
- Primary visual evidence is not buried under provenance.
- Technical/audit disclosures are closed by default.
- Raw SHAs/fingerprints/route IDs are absent from normal reading flow.
- 390px `documentElement.scrollWidth === innerWidth`.
- 200%-equivalent CSS reflow does not require page-level horizontal scrolling.
- wide audit tables/code scroll internally.
- no overlapping/clipped controls or text.
- focus ring is visible.
- skip link reaches `main`.
- `prefers-reduced-motion` suppresses nonessential transition duration.
- no unexpected page errors, console errors, or failed app requests.

## Accessibility gate

Run axe against primary states. Acceptance is:

- 0 WCAG A/AA violations;
- 0 incomplete findings requiring manual remediation in the tested state;
- status meaning is available in text rather than color alone;
- scrollable audit regions have keyboard access;
- headings/landmarks/labels are useful and unique enough for navigation.

## Standard frontend gate

```bash
cd web
pnpm install --frozen-lockfile
pnpm typecheck
pnpm typecheck:e2e
pnpm test
pnpm build
```

Generated OpenAPI/TypeScript contract regeneration must be checked whenever API DTOs change.

## Design-system convergence gate

Repository search must confirm:

- no dead legacy presentation component is retained only for compatibility;
- no parallel obsolete global card/layout system continues to override route hierarchy;
- chart series colors come from semantic chart tokens;
- status colors are used for status meaning, not arbitrary asset identity;
- exact/audit primitives remain only where real consumers need them.

## Completion definition

Phase 14 is complete only when:

- default route experience is verdict/evidence-first rather than provenance-first;
- research success is distinct from merely positive arithmetic deltas;
- primary economics use readable percentages/durations/value summaries and visuals;
- time-series charts are primary evidence for evolution through time;
- exact/raw evidence remains deliberately inspectable;
- negative evidence remains fully visible and semantically correct;
- Portfolio -> Pair navigation satisfies Phase 11.9;
- current frontend tests/typechecks/build and both critical Playwright flows pass;
- Agent Browser verifies responsive hierarchy, keyboard behavior, accessibility, no overflow, and no unexpected runtime errors.

## Non-goals

Phase 14 does not add live trading controls, browser experiment execution, accounts/auth, dashboard builders, topology/heatmaps, a new database/global state layer, an opaque composite QAP score, or browser-side financial reconstruction. The active Research Scanner/Candidate Workbench is Phase 15, not a filter hidden inside this UX phase.
