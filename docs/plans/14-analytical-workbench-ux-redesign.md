# Analytical Workbench UX Redesign Implementation Plan

**Goal:** Redesign the QAP web workbench so an end user can understand the research verdict, economic outcome, benchmark comparison, portfolio changes, and paper-operation result within seconds, while keeping exact audit/provenance data available only on demand.

**Architecture:** Keep the existing read-only React/Vite/TanStack Router/Query architecture and OpenAPI-generated DTOs, but replace the ad-hoc presentation layer with one explicit QAP design system. Reorganize every route around verdict-first summaries, human-formatted metrics, primary visual evidence, interpretation, and progressive-disclosure audit/provenance. The browser remains a presentation layer: it may format, scale, sort, filter, and visualize backend-produced values, but it must not recalculate portfolio accounting, benchmark economics, fills, model evidence, or research truth.

**Tech Stack:** React 19, TypeScript 5.9, Vite 8, TanStack Router/Query, generated OpenAPI types, **Tailwind CSS v4 + semantic CSS design tokens**, **native HTML first + Radix Primitives only when a concrete interaction requires them**, **Lucide React as the single icon family**, Lightweight Charts 5.2 for time series, semantic CSS/SVG for small categorical/composition visuals, CSS Modules only as a chart-specific escape hatch, Vitest/Testing Library for serious semantic regressions, and Agent Browser for rendered UX/accessibility verification.

## Global Constraints

- Wealth relative to the correct matched passive counterfactual remains the primary economic story; coin accumulation stays secondary.
- Negative, neutral, rejected, invalid, and incomplete evidence must remain first-class inspectable outcomes. The redesign must never hide negative evidence or cosmetically imply success.
- No browser-side financial engine. Do not recompute wallet balances, fills, HODL, benchmark wealth, authoritative costs, or experiment outcomes in React.
- Presentation transforms are allowed only when they preserve backend meaning: percentage formatting of a backend relative-return ratio, compact number formatting, elapsed-time formatting, chart scaling, ordering, and visual grouping.
- Exact persisted values remain available for audit, but **raw 40–70 digit decimals are not primary UI copy**.
- Git SHAs, code/data/manifest fingerprints, run IDs, route IDs, venue precision fields, and other machine-oriented provenance are **technical details**, not default end-user content.
- Do not add a second full charting dependency. Continue using Lightweight Charts for time series and semantic CSS/SVG for small categorical/composition visuals. Do not add Recharts, ECharts, Plotly, Highcharts, or a dashboard framework.
- Do not add D3 by default. If a specific small visual genuinely needs scale/tick/bin math, add only the narrow package needed (`d3-scale` or `d3-array`) in the task that demonstrates that need; D3 must not become the renderer.
- Tailwind CSS v4 is the primary styling system. Pages must consume shared semantic tokens/primitives rather than inventing route-local colors, radii, shadows, spacing scales, or typography.
- CSS Modules are an escape hatch only for complex chart/visual internals that become materially clearer than equivalent utilities; they are not a second general styling system.
- Do not add runtime CSS-in-JS (`styled-components`, Emotion, or equivalents).
- Use native HTML for ordinary controls and semantics. Use Radix Primitives only where browser-native behavior is insufficient or deceptively complex: tooltip, popover, select/listbox-style selection, tabs, and modal/dialog if a future concrete interaction requires one.
- Do not mix Radix, Headless UI, React Aria, MUI, Chakra, Mantine, or shadcn-generated component stacks. QAP owns the styled component API above the chosen primitives.
- Use Lucide React as the only application icon family. Do not mix icon families or use icons as the sole label for unfamiliar analytical actions.
- Do not add Redux/Zustand or another global-state layer. TanStack Query remains server state; Router remains URL state; local React state remains view interaction.
- Do not introduce backend DTO changes merely to make the frontend prettier. If an authoritative semantic value is absent, omit that visual or explicitly plan a later backend contract rather than deriving financial truth in the browser.
- Preserve URL-addressable pair orientation, anchor, and view state.
- Preserve visible TradingView attribution for Lightweight Charts.
- Keep the current dark analytical theme for this overhaul; do not add a theme switcher or parallel light theme. Semantic tokens must make a future theme possible without route rewrites.
- Do not maintain legacy UI or obsolete-artifact compatibility. Replace weak presentation patterns directly; current-schema artifacts are the only supported evidence inputs. No migration UI, fallback schema, compatibility formatter, or dual rendering path.
- Per current testing preference, add automated tests only for serious/repeatable regressions or semantic financial mistakes. Do not create tests for every card, heading, spacing rule, or visual arrangement.
- Agent Browser is the primary acceptance tool for layout, hierarchy, mobile behavior, accessibility, and interaction quality.

## Decisive Frontend Architecture

This overhaul must make one coherent presentation-architecture decision up front, then implement it incrementally through real route slices. Do not create the whole component system before it has consumers, and do not let each feature page choose its own framework, colors, controls, or formatting rules.

### Styling stack

**Primary:** Tailwind CSS v4 through the first-party Vite plugin.

**Token ownership:** `web/src/styles/tokens.css` remains the single semantic source for application color roles, typography, spacing, radii, borders, elevation, motion, and chart presentation variables. Tailwind `@theme` variables expose the constrained vocabulary as utilities; ordinary CSS custom properties hold semantic values that should also be consumed by charts/SVG/CSS Modules.

**Base stylesheet:** `web/src/styles/global.css` imports Tailwind and `tokens.css`, owns reset/base typography/focus/selection/root overflow rules, and contains only genuinely global layout semantics. It must stop being a route-by-route component stylesheet.

**Escape hatch:** CSS Modules are allowed only for a chart/visual component whose internals become clearer with scoped selectors than with utility classes. A module must still consume QAP tokens; it must not define an alternate palette or spacing scale.

**Rejected approaches:**

- handcrafted global utility CSS as the primary styling system — too easy to duplicate responsive/state utilities and drift;
- styled-components / Emotion / runtime CSS-in-JS — adds runtime styling machinery without solving a QAP requirement;
- MUI / Chakra / Mantine / other large pre-styled systems — too much visual/theming surface and would make QAP inherit another product's design language;
- shadcn/ui as a wholesale component layer — useful source material, but copying a large generated component catalog would create ownership and consistency overhead QAP does not need.

### Component behavior stack

Use this hierarchy consistently:

```text
Browser-native semantic HTML
        ↓
Radix Primitive only when native behavior is insufficient
        ↓
QAP-owned styled UI primitives
        ↓
QAP analytical components
        ↓
Route/page composition
```

Control-selection rules:

| Need | Use | Do not use |
|---|---|---|
| ordinary action | native `<button>` wrapped by QAP `Button` styling | clickable `<div>` |
| navigation | TanStack `Link` / native anchor semantics | button that imperatively changes URL |
| independent audit disclosure | native `<details>/<summary>` via QAP `Disclosure` styling | custom accordion state |
| grouped tabs/views | Radix Tabs + QAP styling when the interaction is actually tabbed content | row of unrelated toggle buttons pretending to be tabs |
| small finite native choice | native `<select>` with QAP styling | custom popover/listbox |
| richer selectable list | Radix Select only when native select cannot meet the need | hand-built ARIA listbox |
| contextual exact value/help | Radix Popover for interactive content; Radix Tooltip for short nonessential explanation | tooltip containing critical evidence |
| modal task | Radix Dialog only when a concrete modal workflow exists | modal as a reading surface |
| search text | native `<input type="search">` | custom combobox until autocomplete is actually required |
| autocomplete | proven accessible combobox primitive only when the data volume demands it | bespoke input + floating `<div>` |
| evidence rows/records | semantic `<table>` | ARIA `grid` unless cells genuinely have application-like focus behavior |

Do not install every Radix package pre-emptively. Add only the primitives used by the current implementation slice so bundle and maintenance cost stay proportional to real interactions.

### Framework/component decision record

| Option | Decision | Reason |
|---|---|---|
| Tailwind CSS v4 | **Adopt** | build-time utilities, first-party Vite integration, semantic `@theme` token API, strong responsive/state vocabulary |
| CSS Modules | **Selective escape hatch** | excellent local scope for bespoke chart/visual internals, but unsuitable as a second general design-system vocabulary |
| styled-components / Emotion | **Reject** | runtime styling machinery and another abstraction without a QAP-specific benefit |
| Radix Primitives | **Adopt selectively** | accessible unstyled behavior for difficult interactions without visual lock-in |
| Headless UI | **Do not mix** | capable alternative, but using two headless systems would fragment focus/state/composition conventions |
| React Aria | **Do not adopt now** | excellent accessibility/i18n foundation, but larger conceptual surface than this mostly read-oriented workbench currently needs; reconsider only if future collection/form complexity materially grows |
| shadcn/ui | **Do not adopt wholesale** | generated components can inspire patterns, but QAP should own a deliberately small component API instead of importing a broad starter catalog |
| MUI / Chakra / Mantine | **Reject** | pre-styled/themed suites would couple QAP to a generic SaaS visual system and add more component surface than required |
| Recharts / ECharts / Plotly / Highcharts | **Reject** | duplicates Lightweight Charts and is unnecessary for simple comparison/composition visuals |

Package policy: follow the repository's existing exact-version convention. Target the current stable Tailwind v4.3 line identified by the research, but pin the exact resolved package versions in `web/package.json`/`pnpm-lock.yaml`; do the same for Lucide and any Radix package only when that package gains a real consumer.

### Icons

Use **Lucide React only**. Import icons individually. Icons reinforce an already-labeled action/status; unfamiliar analytical actions keep visible text. Default sizes are 16px inline, 18px for ordinary controls, and 20px for prominent controls, while the actual hit target remains substantially larger.

### Visualization stack

Use one visualization rule:

| Visual | Implementation |
|---|---|
| relative wealth through time | Lightweight Charts |
| pair ratio / persisted model evidence | Lightweight Charts |
| benchmark deltas around zero | semantic CSS/SVG |
| allocation composition | CSS/SVG |
| before → target → after composition | CSS/SVG |
| paper execution flow | SVG/semantic HTML |
| tiny card sparkline, only if it materially helps scanning | small SVG |
| complex scale/tick/bin math, only when demonstrated necessary | narrow `d3-scale` / `d3-array` import |

Do not introduce another general chart renderer merely to draw bars, composition strips, or a flow diagram.

### Component-catalog policy

Do **not** add Storybook during the first redesign slices. First prove the shared components through real route consumers. A component catalog may be proposed later only after multiple routes share a stable primitive/analytics layer and isolated examples would materially improve consistency or maintenance. Agent Browser against the real application remains the primary visual-development and accessibility acceptance path.

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

## QAP Design Language Specification

The visual direction is **research instrument, not crypto casino**: professional analytical density, restrained surfaces, strong hierarchy, precise typography, and saturated color only where it communicates state or series identity. Avoid neon/glow treatment, decorative gradients, oversized consumer-fintech pills, glassmorphism, animated counters, and ornamental charts.

### Theme and semantic color roles

Ship one dark theme in this overhaul. Preserve the broad character of the current palette, but rename tokens by **semantic role** so feature code never depends on palette position or hex values.

Initial token vocabulary:

```css
:root {
  color-scheme: dark;

  --surface-canvas: #0b0e13;
  --surface-panel: #121720;
  --surface-subtle: #1a2230;
  --surface-raised: #202a38;

  --text-primary: #edf1f7;
  --text-secondary: #c4ccd8;
  --text-muted: #9ca8b8;

  --border-default: #303a4a;
  --border-strong: #4a586b;

  --accent-primary: #78a9ff;
  --status-positive: #68d391;
  --status-negative: #ff9b9b;
  --status-warning: #f6d365;
  --status-info: #78a9ff;

  --chart-grid: var(--border-default);
  --chart-baseline: var(--text-muted);
}
```

These values are starting points, not assumed WCAG-certified combinations. Before freezing the token set, measure every text/surface, focus, badge, and meaningful chart/UI combination in the rendered app. Ordinary text must meet WCAG 2.2 AA contrast where applicable; meaningful non-text controls/graphics must meet the applicable non-text contrast threshold.

Never encode `outperformed`, `underperformed`, `reconciled`, `rejected`, `no fills`, or research-boundary status by color alone. Use text plus a consistent icon/shape treatment.

### Typography

Use an OS system sans stack; remove `Inter` from the token unless QAP later deliberately bundles the font. Reserve monospace for literal machine identity, not ordinary financial values.

```text
Verdict display   32/38 desktop · 28/34 mobile · 700
Page title        24/32 desktop · 22/28 mobile · 650–700
Section heading   18/26 · 600
Card heading      16/22 · 600
Body              14/21 · 400
KPI value         22–24/28 · 600–700
Compact table     13/18 · 400–500
Metadata/label    12/16 · 500
```

All financial columns and KPI numbers use `font-variant-numeric: tabular-nums lining-nums`. Monospace is restricted to Run ID, Git SHA, manifest/data fingerprints, route IDs, and exact literal decimal values inside audit/provenance views.

### Spacing, shape, border, and elevation

Use a 4px base rhythm and a deliberately small vocabulary:

```text
1 = 4px    micro gap
2 = 8px    tightly related inline items
3 = 12px   compact groups
4 = 16px   mobile/card padding
5 = 20px   desktop card padding
6 = 24px   section gap / desktop gutter floor
8 = 32px   major section gap
10 = 40px  major semantic separation
12 = 48px  hero-to-primary-content boundary
```

Shape rules:

- small radius: 6px;
- ordinary cards/controls: 8px;
- large analytical surfaces/popovers: 12px maximum;
- no fully rounded pills except compact status chips where the shape communicates badge semantics;
- ordinary analytical surfaces use 1px borders and no shadow;
- `surface-raised` plus restrained shadow is reserved for overlays/popovers, not every card;
- the verdict hero may use stronger border/background contrast but must not look promotional.

### Layout grid and responsive composition

- Desktop analytical canvas remains wide: keep the current roughly 90rem maximum, with 24–32px outer gutters.
- Use a 12-column grid only where it clarifies desktop composition; do not make every page/grid section use 12 columns.
- At 390px, use 16px page gutters and design a mobile composition rather than shrinking desktop panels.
- **The document never scrolls horizontally. A genuine table may scroll inside its own labeled frame.**
- Full-width time-series charts should not be constrained to article-style narrow reading widths.
- Mobile cards stack; toolbars may wrap or become a compact vertical control group; desktop side-by-side audit panes become previous/next selected-detail navigation.
- Test reflow at 390×844 and at 200% zoom; do not rely on a single CSS breakpoint screenshot.

### Density

Define only two internal densities during the overhaul:

- **comfortable** — navigation, cards, filters, heroes, mobile, primary analytical controls;
- **compact** — desktop audit/evidence tables only.

Do not expose a user-selectable density setting in P0. Analytical density should come from good grouping and progressive disclosure, not tiny controls or 10px text.

### Motion

Motion explains state change only:

```text
instant = 80ms
fast    = 120ms
normal  = 180ms
```

Use for hover/focus feedback, popover/disclosure state, and small opacity/transform transitions. Do not animate KPI counts, chart entrance on every route, page transitions, large layout reflows, or decorative success states. Honor `prefers-reduced-motion` globally.

### Status vocabulary

Keep a controlled set of semantic labels. Metadata is not a badge.

```text
Research:    OUTPERFORMED · UNDERPERFORMED · NEUTRAL · INVALID
Operations:  RECONCILED · MISMATCH · NO FILLS · REJECTED
Boundary:    DEVELOPMENT · FINAL OOS · FORWARD PAPER · RESEARCH ONLY
```

`BTC/USDT`, dates, `periodic-2`, model IDs, and basket names remain ordinary metadata. Status badges are always readable without color and never infer domain truth themselves; route/domain mapping supplies the authoritative status and the component only renders it.

## Control and Interaction Rules

### Result cards and KPI tiles

- Result cards are the default discovery unit for experiments and paper operations because each item has a verdict/outcome to communicate.
- A card answers one sentence and shows at most 3–4 secondary facts before its primary action.
- Raw run/operation IDs never occupy the title line.
- KPI strips contain **3–4 tiles maximum in the first viewport**. More metrics belong in grouped secondary sections.
- KPI components receive explicit semantic state from a mapper; they never decide that a positive number is automatically “good.”

### Tabs, segmented controls, selects, and filters

- Use **tabs** only when switching between peer content panels where exactly one panel is visible.
- Use a **segmented control/toggle group** for a small mutually exclusive chart representation such as Ratio / Log / Normalized / Anchor when keeping the chart in place is the intent.
- Use a **native select** for a small finite list such as anchor choice unless the interaction proves native select insufficient.
- Do **not** add search, filtering, sorting controls, or pagination to Research runs merely because the DTO can support them.
- Add collection controls only after rendered use demonstrates a concrete scanning problem: a material run count, repeated difficulty locating a known run, or a workflow that requires comparison by verdict/model.
- When that threshold is reached, introduce the smallest useful visible set first and keep its state URL-backed. Search + Verdict + Model is the likely first candidate, not a Phase-14 requirement.
- Do not build autocomplete, `More filters`, saved filters, or a card/table view switch until a concrete workflow demonstrates the need.

### Tooltips, popovers, dialogs, and disclosures

- Tooltips contain short nonessential clarification only. They must never contain the only copy of a benchmark result, no-fill reason, research boundary, or exact-value audit record.
- Exact values use a small interactive `Exact` affordance backed by a popover or disclosure with `Copy exact value` and a non-focus-stealing status announcement.
- Independent audit/provenance blocks use native `<details>/<summary>` styled consistently.
- Dialogs are not a default reading surface. Because QAP is read-only, do not add a Dialog dependency until a concrete modal task exists.

### Tables and long histories

- Use semantic `<table>` for genuinely tabular evidence; do not upgrade static evidence tables to ARIA `grid`.
- Wrap wide tables in a named keyboard-focusable scroll frame; the page itself must retain viewport width.
- Do not paginate by default. First reduce long evidence pages through progressive disclosure and one-selected-item navigation. Add explicit pagination only when a real table/history remains materially long after that redesign; never use infinite scroll for auditable evidence.
- Where cross-row comparison is not important on mobile, show a compact summary card and keep the complete table in the audit disclosure.
- Portfolio rebalance history uses a **DecisionNavigator**: one selected decision at a time, chronological navigation, selected decision in URL/query state, and full exact execution evidence behind its detail disclosure.

### Empty, loading, error, and status states

- **Loading:** preserve page shell and skeleton only the structure that is actually loading; do not present placeholder numbers that look like evidence.
- **Empty:** state what is absent and why it matters (`No paper operations yet`, `No persisted pair evidence for this run`), plus the relevant safe navigation action.
- **Invalid/corrupt evidence:** render as an explicit evidence state, never as a success-styled card.
- **Error:** keep the global shell, show stable API error code/message where available, preserve Retry and contextual navigation.
- **Background/status feedback:** use `role="status"` for transient copy/filter feedback that does not take focus; important failures remain persistent content.

### Keyboard and target rules

- Every action is keyboard reachable with a visible `:focus-visible` treatment.
- Maintain the existing internal 44×44px target goal for primary interactive controls; icon glyph size is independent from hit target size.
- Use ordinary browser Tab order. Arrow/Home/End behavior appears only where the chosen control pattern defines it (tabs/listbox/menu), not as a global terminal-style navigation layer.
- Escape dismisses popovers/dialogs where applicable and focus returns to the invoking control.

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

## Data Presentation Contract

### Exact value versus display value

Every financial datum has two presentation layers:

```text
exact persisted API string
        ├── audit/copy representation (literal)
        └── formatter → human display representation
```

The human representation is disposable presentation. The exact string is the audit record. Never perform subsequent portfolio/model/accounting calculations from the formatted output.

Recommended semantic formatting rules:

| Data | Default display | Audit/exact representation |
|---|---|---|
| benchmark return/delta | `−0.85%` | exact relative-return string |
| allocation/weight | `37.4%` | exact decimal |
| fee/value | currency/quote-aware concise value such as `$1.24` when the unit is known | exact amount + explicit unit |
| large overview value | compact form such as `$1.24M` only in overview context | full localized amount + exact source |
| slippage | basis points when sub-percent is clearer, e.g. `12.4 bp` | exact fraction/value |
| ratio | 4–6 significant digits according to chart/context | exact ratio |
| asset quantity | instrument-relevant concise precision + asset symbol | exact quantity |
| turnover | `4.2%` | exact fraction/value |
| duration | `9 h`, `3 d 4 h` | exact seconds in audit only |
| timestamp | `Jan 12, 2024 · 14:30 UTC` | exact ISO timestamp |
| tiny nonzero percent | `<0.01%` or basis points | exact value |
| exact zero | `0.00%` where the semantic scale warrants it | exact source |

Formatting precision is defined by **semantic type**, not by one universal decimal-place count.

### Provenance rules

Machine identity must be discoverable, copyable, and visually subordinate:

```text
Technical provenance
  Run ID                 [Copy]
  Research family        [Copy]
  Git commit             [Copy]
  Manifest SHA           [Copy]
  Dataset fingerprint    [Copy]
```

- The route may contain a run/operation ID without repeating it as the page title.
- Literal machine IDs use monospace only inside technical/audit presentation.
- Fingerprints do not become badges, KPI cards, hero copy, or chart annotations.
- `Technical provenance` is collapsed by default on every route.

## Chart and Visual Conventions

### Every time-series chart

Every Lightweight Charts surface is wrapped in `ChartFrame` and supplies:

1. visible title;
2. one-sentence description of the unit/comparison;
3. explicit legend/series names;
4. a nearby textual conclusion/summary;
5. unit-aware tooltip/crosshair values;
6. optional `View chart data as table` disclosure when a tabular fallback is useful;
7. visible TradingView attribution;
8. a keyboard/screen-reader path that does not require interpreting the canvas.

The chart is never the sole place where the user can discover whether evidence was positive, negative, neutral, rejected, or incomplete.

### Scale and encoding rules

- Relative comparisons use a visible zero/baseline.
- Positive/negative color is accompanied by direction text/icon and numeric sign.
- Do not use area fills that imply magnitude when the line relationship is the actual evidence.
- Allocation composition uses one stable asset-color mapping within a page/session; do not reuse status red/green as arbitrary asset colors.
- Pair orientation must be explicit in chart title, axis/tooltip labels, and URL state.
- Normalized/log/anchor views must label their units/transformation in plain language.
- Sparse/missing/invalid model-evidence periods remain visibly absent/invalid; do not interpolate a visually continuous success story.
- Small comparison/flow visuals must remain interpretable in text when CSS/SVG is unavailable.

### Chart palette ownership

Define chart-series roles in `tokens.css` and expose them to Lightweight Charts/SVG through CSS custom properties or a tiny token adapter. Do not hard-code unrelated hex colors in individual chart components.

## Accessibility and Internationalization Baseline

Release target: **WCAG 2.2 A/AA plus deliberate practices above the minimum where they improve analytical usability.**

| Area | QAP requirement |
|---|---|
| keyboard | every actionable control reachable/operable without pointer |
| focus | always-visible `:focus-visible` indication on every interactive element |
| text contrast | meet applicable WCAG AA text contrast |
| UI/graphic contrast | meet applicable non-text contrast for meaningful controls/graphics |
| target size | internal 44×44 goal for primary controls; never rely on icon dimensions as hit area |
| reflow | no document-level horizontal scroll at 390px / 320-CSS-pixel-equivalent ordinary content |
| color | never sole carrier of analytical/status meaning |
| headings | sequential, meaningful H1 → H2 → H3 structure |
| landmarks | meaningful header/nav/main/footer/aside/section labeling |
| tables | real headers/captions/labels; scroll frames announced when horizontally scrollable |
| charts | textual summary + accessible data path |
| errors | persistent app shell, clear error, retry/context navigation |
| status feedback | programmatically determinable without forcing focus |

Accessibility tools are necessary but insufficient. An axe result of zero violations is not itself a completion claim; Agent Browser/manual judgment must still verify hierarchy, keyboard order, focus, reflow, meaning without color, and chart interpretability.

### Keyboard conventions

```text
Tab / Shift+Tab   move between controls
Enter / Space     activate native buttons/links as appropriate
Escape            dismiss open popover/dialog where the pattern defines it
Arrow keys        only inside tabs/listbox/menu/other pattern-defined composite widgets
Home / End        only where the chosen primitive's accessibility contract defines it
```

Do not create a Bloomberg-style global keyboard command layer during this redesign.

### Internationalization readiness

The product remains en-US for now, but implementation must avoid needless localization debt:

- keep `<html lang="en-US" dir="ltr">` explicit;
- use `Intl.NumberFormat` and `Intl.DateTimeFormat` rather than hand-built commas/date ordering;
- display timezone explicitly for research timestamps;
- do not concatenate translatable sentence fragments inside formatter functions;
- use logical CSS properties in bespoke CSS where practical;
- allow buttons/headings/status copy to grow rather than fixed-width clipping;
- do not localize asset symbols such as BTC/ETH/USDT;
- exact machine IDs remain literal.

## Shared Component/File Structure

This is the **target ownership map**, not a mandate to create every file in the first slice. A shared component is created only when the current route needs it or when a second real consumer proves extraction is useful. Prefer keeping a small route-local presentation helper over introducing a speculative global primitive.

### Create when first consumed

**Foundation and formatting**

- `web/src/lib/format.ts`
  - Single presentation-formatting boundary for percentages, money/value, quantities, ratios, basis points, durations, timestamps, compact overview values, and exact/audit representation.
  - Accepts exact API strings; returns `{ display, exact, ariaLabel? }` without feeding parsed values back into domain logic.
  - Uses `Intl.NumberFormat` / `Intl.DateTimeFormat` where appropriate.

- `web/src/components/ui/Badge.tsx`
  - Controlled semantic tones (`positive`, `negative`, `neutral`, `warning`, `info`) and soft/outline variants.

- `web/src/components/ui/Disclosure.tsx`
  - Consistent native `<details>/<summary>` shell for audit/provenance/advanced evidence.

- `web/src/components/ui/DataTableFrame.tsx`
  - Named, keyboard-focusable contained horizontal scrolling for genuine tables; supersedes route-level table wrappers.

- `web/src/components/ui/Select.tsx`
  - Native-select styling first; a Radix-backed replacement is allowed only if a later route demonstrates a richer selection requirement.

- `web/src/components/ui/SegmentedControl.tsx`
  - Small mutually exclusive view control built from semantic buttons/`aria-pressed`; used for chart representation switches such as Ratio / Log / Normalized / Anchor.

**Analytical presentation**

- `web/src/components/analytics/VerdictHero.tsx`
  - Shared dominant verdict/outcome surface; accepts already-mapped semantic verdict, supporting copy, metrics, and actions; contains no financial logic.

- `web/src/components/analytics/KpiTile.tsx`
  - Consistent first-viewport KPI tile with label/value/secondary/tone/exact-value affordance.

- `web/src/components/analytics/MetricValue.tsx`
  - Replaces `ExactNumber` as the default human-facing numeric primitive and delegates formatting to `lib/format.ts`.

- `web/src/components/analytics/ExactValue.tsx`
  - Explicit `Exact` affordance, copy action, literal audit value, and `role="status"` copy feedback.

- `web/src/components/analytics/ResultCard.tsx`
  - Shared outcome-first discovery card shell for experiments and paper operations.

- `web/src/components/analytics/Breadcrumbs.tsx`
  - Predictable route context and back-navigation.

- `web/src/components/analytics/ChartFrame.tsx`
  - Shared title/description/controls/text-summary/table-fallback frame around Lightweight Charts because the chart canvas itself is not an accessible conclusion.

- `web/src/components/analytics/DecisionNavigator.tsx`
  - One-selected-rebalance navigation with desktop timeline + mobile previous/next composition.

- `web/src/components/analytics/ProvenancePanel.tsx`
  - Consistent collapsed machine-identity presentation and copy affordances.

- `web/src/components/analytics/EmptyState.tsx`
- `web/src/components/analytics/ErrorState.tsx`
  - Shared non-success states that preserve navigation and research semantics.

**Small visuals**

- `web/src/components/visuals/ComparisonBars.tsx`
  - CSS/SVG zero-centered bars for backend-produced relative comparisons; text remains authoritative.

- `web/src/components/visuals/CompositionBars.tsx`
  - Horizontal composition display for backend-provided asset weights; no browser-side weight derivation.

- `web/src/features/paper/PaperExecutionFlow.tsx`
  - Read-only semantic/SVG stepper from persisted order/fill DTOs; no simulated routing or financial derivation.

### Modify

- `web/package.json`
  - Add Tailwind v4/Vite and Lucide React in the first route slice. Add a Radix package only when a concrete later interaction needs it.
  - Do not add a pre-styled component framework, general chart framework, runtime CSS-in-JS library, or global state library.

- `web/pnpm-lock.yaml`
  - Lock only the deliberate design-system/tooling dependencies from `web/package.json`.

- `web/vite.config.ts`
  - Add the first-party Tailwind Vite plugin while preserving TanStack Router and test/server configuration.

- `web/src/components/AppShell.tsx`
  - Refine navigation labels, active-state treatment, and responsive header using QAP primitives/tokens.

- `web/src/components/MetricCard.tsx`
  - Delete after call sites migrate to `analytics/KpiTile`; do not maintain two KPI component APIs.

- `web/src/components/ExactNumber.tsx`
  - Delete after all call sites move to `analytics/MetricValue`/`ExactValue`; do not maintain a compatibility wrapper.

- `web/src/components/TableScroll.tsx`
  - Delete after all call sites migrate to `ui/DataTableFrame`; preserve the serious overflow regression at the new shared boundary rather than keeping two wrappers.

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
  - Replace palette-style names with the semantic token contract defined in this plan; expose the constrained Tailwind theme vocabulary and shared CSS variables used by charts/SVG/CSS Modules.

- `web/src/styles/global.css`
  - Import Tailwind, retain only reset/base/focus/root/shell semantics, and remove route-level “every section is the same bordered card” styling as feature components migrate to utilities/primitives.

### Existing files intentionally retained

- `web/src/components/charts/TimeSeriesChart.tsx`
- `web/src/components/charts/SynchronizedChartGroup.tsx`
- `web/src/features/pairs/PairRatioChart.tsx`
- `web/src/features/pairs/AnchorLensPanel.tsx`
- `web/src/api/client.ts`
- `web/src/api/queries.ts`
- `web/src/api/types.ts`

Their data/interaction contracts remain valid; this plan changes presentation hierarchy around them.

## Task 1: First vertical slice — Research runs + minimum design foundation

**Files:**
- Modify: `web/package.json`
- Modify: `web/pnpm-lock.yaml`
- Modify: `web/vite.config.ts`
- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/global.css`
- Create: `web/src/lib/format.ts`
- Create: `web/src/components/ui/Badge.tsx`
- Modify: `web/src/features/experiments/ExperimentList.tsx`
- Modify: `web/src/features/experiments/ExperimentList.test.tsx` only if an existing serious semantic assertion must change.

**Interfaces:**
- Consumes: current `RunSummaryDto` values and existing `/experiments` route behavior.
- Produces: the first real redesigned route plus only the formatting/token/status patterns proven necessary by that route.

**Steps:**
- [ ] Add Tailwind CSS v4 and `@tailwindcss/vite`; wire the Vite plugin without changing TanStack Router, test environment, or API proxy behavior.
- [ ] Do **not** add Radix, Lucide, Storybook, D3, or another shared-component dependency in this slice unless the Research runs route demonstrates a concrete need that native HTML/CSS cannot meet.
- [ ] Convert only the token/base values needed by the first route to the semantic dark-theme contract; preserve chart variables and unrelated working styles until their owning routes migrate.
- [ ] Remove `Inter` from the default font token unless a bundled font file is deliberately introduced; use the system stack.
- [ ] Start moving `global.css` toward Tailwind/base ownership without rewriting unrelated routes. Preserve existing selectors needed by routes not yet migrated.
- [ ] Implement only the formatter functions this route consumes: signed relative percentage and research timestamp/date formatting. The module becomes the single future formatting boundary, but unused formatter APIs are not created yet.
- [ ] Define a formatting contract that always retains the exact source string and never returns a transformed value for domain calculations.
- [ ] Handle tiny nonzero percentages without silently displaying misleading zero (`<0.01%` or basis points according to semantic context); normalize visual negative zero while retaining literal source in exact audit content when relevant.
- [ ] Add only the shared `Badge` primitive because the first route has repeated semantic status/data-role treatment. Keep the result-card composition inside `ExperimentList.tsx` until Paper operations proves a second real consumer.
- [ ] Replace the dense definition-list cards with a deliberate hierarchy: experiment name, verdict/data role, primary comparison, basket, model/policy context, and one `View result` action.
- [ ] Keep invalid artifacts visible as explicit invalid-result cards rather than suppressing them.
- [ ] Move raw research-family/run IDs, dirty flag, and sibling/trial metadata into quiet secondary metadata; do not add an interactive disclosure until the detail route needs the same pattern.
- [ ] Use a responsive card grid on wider screens and one column on mobile.
- [ ] Do **not** add search, filters, sorting, pagination, a card/table toggle, or autocomplete in this slice.

**Testing/verification:**
- Keep or extend serious regressions for exact-value preservation, tiny-nonzero formatting, and sign preservation only.
- Reuse the current Experiment list test that negative evidence remains visible; update only assertions broken by meaningful semantic copy changes.
- Do not add tests for token values, Tailwind classes, card padding, card count, or responsive layout.
- Run: `cd web && pnpm install --frozen-lockfile && pnpm test && pnpm typecheck && pnpm build` after the lockfile is established.
- Agent Browser: verify `/experiments` at 1440×1000 and 390×844, including scanability, negative/invalid evidence, keyboard focus, axe A/AA, and zero document-level horizontal overflow.

**Acceptance criteria:**
- Research runs is visibly redesigned and usable before a broad component framework exists.
- A user can identify which runs won/lost and against which control without opening them.
- Long exact decimals are not primary card copy; raw IDs/hashes are not the focal point.
- Tiny meaningful values are not formatted to a misleading zero.
- Status meaning does not rely on color.
- The new formatting/status code contains no portfolio/model/accounting logic.
- No new dependency duplicates an existing responsibility.

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

## Task 3: Redesign experiment detail around a research verdict

**Files:**
- Create: `web/src/components/visuals/ComparisonBars.tsx`
- Modify: `web/src/features/experiments/ExperimentDetail.tsx`
- Modify: `web/src/features/experiments/ExperimentDetail.test.tsx` only for existing research-boundary semantics.

**Interfaces:**
- Consumes: current `ExperimentDetailDto.result`, manifest, commitment, provenance.
- Produces: plain-language verdict, benchmark comparison visual, compact research context, collapsed technical provenance.

**Steps:**
- [ ] Build a deterministic presentation mapper from result status + primary comparison into the discriminated verdict state consumed by `VerdictHero`, producing copy such as `Underperformed periodic-2 by 0.85%` or `Outperformed HODL by 1.2%`.
- [ ] Never infer success from sign alone when the DTO status/threshold says otherwise; status remains authoritative and the component tone merely renders that state.
- [ ] Show HODL comparison, primary-control comparison, and matched-contribution comparison in zero-centered `ComparisonBars` when available.
- [ ] Put experiment description, basket, model, policy, anchor, and data window into `What was tested?` rather than a raw manifest dump.
- [ ] Summarize final-OOS state in plain language.
- [ ] Move raw family ID, parent run ID, dataset IDs/fingerprints, git SHA, code fingerprint, and manifest fingerprint into `ProvenancePanel` collapsed as `Technical provenance`.
- [ ] Show exact benchmark values through `ExactValue` affordances rather than inline 40–70 digit prose.
- [ ] Keep prominent links to portfolio economics and pair evidence using the shared action/button treatment.

**Testing/verification:**
- Preserve a serious semantic regression proving a negative final-OOS run is still presented as negative evidence and final-OOS state remains visible.
- Do not add tests for comparison-bar geometry or disclosure styling.

**Acceptance criteria:**
- First viewport communicates verdict, benchmark, research role, and next analytical action.
- Fingerprints and SHAs are absent from the default expanded reading flow.

## Task 4: Turn portfolio economics into the primary visual dashboard

**Files:**
- Create: `web/src/components/visuals/CompositionBars.tsx`
- Create: `web/src/components/analytics/DecisionNavigator.tsx`
- Modify: `web/src/routes/portfolio.$runId.tsx`
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

**Interfaces:**
- Consumes: current `ExperimentDetailDto`, `PortfolioSnapshotDto`, `PortfolioPerformanceDto`.
- Produces: verdict-first economics dashboard using only persisted/backend-derived economics.

**Steps:**
- [ ] Use `VerdictHero` for status + primary-control and HODL relative outcome.
- [ ] Limit first-row `KpiTile`s to the economic decision set: vs HODL, vs primary control, max relative drawdown, and trading cost/fills.
- [ ] Promote `RelativeWealthChart` directly below the hero and wrap it in `ChartFrame` with a textual summary and optional data-table disclosure.
- [ ] Move `LogRelativeWealthChart` into `Advanced compounding view` disclosure while keeping it accessible.
- [ ] Redesign `BenchmarkLadder` into human-readable comparison bars/cards; move `BenchmarkRoleTable` into `Compare all benchmark roles` disclosure.
- [ ] Use backend-provided holding weights to render starting/terminal composition bars; keep exact holdings tables under `Exact holdings` disclosure.
- [ ] Use same-mark value deltas for the primary per-asset HODL-delta visual; do not compare heterogeneous raw coin quantities as if they shared a unit.
- [ ] Present fees, slippage, turnover, and fill count together in an execution-cost block.
- [ ] Format `time_below_*_seconds` as readable durations; retain exact seconds only in technical details if needed.
- [ ] Collapse detailed external-flow IDs unless flows are the current explanatory factor.
- [ ] Replace the all-expanded rebalance audit with `DecisionNavigator`: desktop timeline/list + one selected decision detail; mobile previous/next + one selected detail.
- [ ] Persist selected decision in portfolio route search state so reload/back/forward navigation preserves analytical context.
- [ ] The selected decision keeps current weights, baseline target, QAP target, evidence IDs, modeled cost, requested deltas, fills, and post-fill holdings; exact execution detail remains inside an audit disclosure.
- [ ] Migrate every portfolio table to `DataTableFrame`; no document-level horizontal overflow.

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

## Task 5: Make pair analysis chart-first and interpretation-first

**Files:**
- Modify: `web/src/features/pairs/PairWorkbench.tsx`
- Modify: `web/src/features/pairs/RelationshipEvidencePanel.tsx`
- Modify: `web/src/features/pairs/RebalanceMarkerOverlay.tsx`
- Modify: `web/src/features/pairs/AnchorLensPanel.tsx` only for explanatory copy/layout where necessary.
- Modify: `web/src/features/pairs/PairWorkbench.test.tsx` only for URL/orientation/semantic regressions.

**Interfaces:**
- Consumes: current pair series/evidence/anchor DTOs and URL search state.
- Produces: one coherent pair-analysis workspace without changing pair identity or model calculations.

**Steps:**
- [ ] Use readable pair/orientation title and one compact toolbar.
- [ ] Use QAP `SegmentedControl` for Ratio / Log / Normalized / Anchor, a native-styled `Select` for anchor choice, and one explicit orientation action; do not introduce tabs for chart rendering modes.
- [ ] Place the selected pair chart and synchronized evidence chart as the dominant content, each inside the shared chart framing/summary convention.
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

## Task 6: Redesign paper operations as operational outcomes

**Files:**
- Create: `web/src/features/paper/PaperExecutionFlow.tsx`
- Modify: `web/src/features/paper/PaperOperationList.tsx`
- Modify: `web/src/features/paper/PaperOperationDetail.tsx`
- Modify: `web/src/features/paper/PaperOperationList.test.tsx` only for exact-value/research-boundary regressions already worth protecting.
- Modify: `web/src/features/paper/PaperOperationDetail.test.tsx` only when serious semantics change.

**Interfaces:**
- Consumes: current paper-operation summary/detail DTOs.
- Produces: readable paper-operation outcome cards, flow visualization, and progressive execution audit.

**Steps:**
- [ ] Use shared `ResultCard` on the list and `VerdictHero` + `KpiTile`s on detail; replace raw operation ID as primary card/H1 content with `Paper rebalance` + readable timestamp/context and expose the raw ID only through technical metadata.
- [ ] Collapse the three repeated research eligibility fields into one clear forward-paper boundary banner while retaining exact flags in `ProvenancePanel`/technical details.
- [ ] Show reconciliation, fills, no-fill/rejected legs, fees, slippage, and bridge residual as the primary operation summary using the shared formatters.
- [ ] Build `PaperExecutionFlow` from persisted orders/fills only: start → sells → bridge → buys → end.
- [ ] Use composition bars for starting/ending holdings if weights are already available in the DTO; if not available, keep holdings as readable cards/tables rather than deriving weights from quantities/value in React.
- [ ] Keep no-fill reasons visible and prominent when present.
- [ ] Move full route/order table, fill table, venue precision metadata, input fingerprint, and exact values into `Execution audit` / `Technical execution details` disclosures using `DataTableFrame` and `ExactValue`.
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

## Task 7: Converge every route on the QAP design system and delete legacy presentation

**Files:**
- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/global.css`
- Delete when unused: `web/src/components/MetricCard.tsx`
- Delete when unused: `web/src/components/ExactNumber.tsx`
- Delete when unused: `web/src/components/TableScroll.tsx`
- Delete: any feature-specific CSS/classes made obsolete by Tailwind/QAP primitives.

**Interfaces:**
- Consumes: all redesigned pages, shared primitives, analytics components, and chart wrappers proven by real route consumers.
- Produces: one coherent responsive visual system with no parallel legacy component/styling path.

**Steps:**
- [ ] Audit every redesigned route for one-off hex values, arbitrary radii/shadows, repeated spacing values, ad-hoc button/status treatments, and route-owned formatting; replace them with tokens/primitives.
- [ ] Calibrate the three surface roles (`canvas`, `panel`, `subtle/raised`) so hero, primary visual, secondary explanation, and audit content have visibly different emphasis without turning every section into a bordered card.
- [ ] Freeze the typography scale and ensure KPI/financial columns use tabular lining numerals.
- [ ] Verify the 4px spacing rhythm and consistent 16px mobile / 24–32px desktop gutters across routes.
- [ ] Keep stronger accent/status treatment limited to outcome, warnings, current selection, focus, and chart series; decorative saturation is removed.
- [ ] Ensure all chart colors come from chart semantic tokens and asset colors do not reuse positive/negative status colors as arbitrary series identity.
- [ ] Verify popovers/overlays are the only normal consumers of raised elevation/shadow.
- [ ] Verify contained table scrolling and eliminate any root horizontal overflow caused by long IDs, exact values, legends, or toolbars.
- [ ] Verify `prefers-reduced-motion` removes nonessential transition/animation behavior.
- [ ] Run contrast measurements for final token combinations in rendered context; adjust tokens centrally rather than patching individual components.
- [ ] Review whether the now-proven shared component set actually needs an isolated component catalog. If not, keep Storybook out of Phase 14. If yes, write a separate bounded tooling proposal rather than silently adding it here.
- [ ] Delete superseded components/styles as soon as all call sites move; do not retain old and new implementations “just in case.”

**Testing/verification:**
- No CSS/screenshot snapshot tests.
- Agent Browser + axe on all primary routes at 1440×1000 and 390×844.
- Use repository search to confirm no surviving feature code imports deleted `MetricCard`, `ExactNumber`, or `TableScroll` components.

**Acceptance criteria:**
- Feature pages consume the same tokens, primitives, numeric formatter, status vocabulary, and chart framing.
- No legacy presentation component remains solely for backward compatibility.
- Pages no longer look like every piece of information has equal importance.
- Default mobile views remain within viewport width.
- Outcome, primary visual, secondary explanation, and audit layers are visually distinct.

## Task 8: Rendered end-to-end UX acceptance

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
- [ ] Run axe WCAG A/AA on each primary route, then manually inspect any `incomplete` findings and do not equate `0 violations` with complete accessibility.
- [ ] Verify keyboard navigation for skip link, global nav, pair controls, segmented controls, selects, any popovers actually introduced, disclosures, decision navigation, and scrollable tables.
- [ ] Verify visible focus survives every interactive state and focus returns correctly after dismissing popovers.
- [ ] Verify 390px `document.documentElement.scrollWidth === window.innerWidth` on every primary route and repeat a 200% zoom/reflow sanity check.
- [ ] Verify statuses/verdicts/no-fill/reconciliation remain understandable with color mentally removed; text/icon/sign must carry the meaning.
- [ ] Enable `prefers-reduced-motion: reduce` and verify no essential information depends on animation.
- [ ] Verify each Lightweight Charts surface has nearby text summary, explicit unit/orientation, usable tooltip/crosshair labels, TradingView attribution, and the planned accessible data path.
- [ ] Verify long exact decimals, SHAs, fingerprints, route IDs, and venue precision fields remain contained and absent from the default expanded reading flow.
- [ ] Verify no unexpected console/page errors and no chart host runaway sizing/remount regression.
- [ ] Capture screenshots of each primary route/state for final human visual review; screenshots are evidence, not snapshot tests.
- [ ] Run frontend gate: `pnpm install --frozen-lockfile`, `pnpm test`, `pnpm typecheck`, `pnpm build`, and `git diff --check -- web`.

**Acceptance criteria:**
- A reviewer can answer `did it work, compared with what, and why` from the first viewport of experiment/portfolio pages.
- Fingerprints/SHAs/raw IDs are not visible until a technical disclosure is opened.
- Long exact decimals are not default visible prose.
- Negative evidence remains visually normal and inspectable, not hidden or rendered as an application error.
- No document-level horizontal overflow at 390px and no essential loss of content/controls at 200% zoom.
- Zero unresolved WCAG A/AA violations in tested routes, with incomplete/manual findings explicitly reviewed.
- Every chart conclusion remains available without requiring visual interpretation of the canvas.
- Reduced-motion mode preserves all analytical meaning.
- No browser-side authoritative financial recomputation has been introduced.

## Serious Regression Tests Worth Keeping

The redesign should **not** test every visual detail. Automated regression coverage should remain concentrated on failures that would materially damage research correctness or navigation:

1. route/API error preserves the QAP shell and recovery navigation;
2. negative/rejected evidence remains visible and is not converted into a success state;
3. signed relative comparisons are not inverted when rendered as human percentages;
4. exact persisted financial strings are not mutated by display formatting;
5. pair reciprocal orientation + anchor URL state remains authoritative;
6. final-OOS / forward-paper research-boundary state remains visible and correctly labeled;
7. explicit paper no-fill evidence is not dropped from the user-visible result;
8. tiny nonzero financial values are not formatted into a misleading visible zero;
9. `DecisionNavigator` cannot display the detail for a different rebalance than the selected URL/state identity.

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
- No experiment mutation/run button in **Phase 14**. Phase 14 is the results/evidence UX overhaul, not the scanner/execution workbench.
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

## Follow-on Product Boundary: Research Scanner and Candidate Workbench

Phase 14 does **not** satisfy the broader research-workbench requirement. A follow-on phase must own the active research workflow explicitly rather than hiding it inside Research-run filters.

The required scanner pipeline is:

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

That phase must preserve the existing research constitution: simple-first controls, family/search-denominator accounting, dataset-role/final-OOS discipline, no browser-owned financial truth, no live-capital authority, and explicit current-schema inputs. It requires its own API/mutation contracts and implementation plan; it must **not** be smuggled into Phase 14 as client-side filtering of completed runs.

## Recommended Implementation Order

1. Research runs vertical slice: Tailwind/tokens + minimum formatting/status primitives + migrated route.
2. Global shell/navigation, extracting only patterns already repeated by the first slice.
3. Experiment verdict page; add exact-value/provenance components only when this route consumes them.
4. Portfolio economics dashboard; add KPI/chart/table/decision-navigation primitives here when required.
5. Pair workbench; add segmented/native selection controls here when required.
6. Paper operations; extract shared result-card patterns only if the second real consumer proves they belong globally.
7. Cross-page visual-system convergence and legacy deletion.
8. Agent Browser rendered acceptance and final verification.

This order deliberately prefers **route-first extraction over framework-first construction**. Each slice leaves behind only abstractions proven by concrete consumers.

### Route replacement lifecycle

For each route, use one replacement lifecycle:

```text
build against current schema
  → focused semantic/type/build checks
  → Agent Browser desktop QA
  → Agent Browser mobile/reflow/a11y QA
  → replace route
  → delete superseded components/styles
  → remove any temporary development-only switch
```

A temporary route/build flag is allowed only to isolate unfinished work during implementation. It must be deleted when that route is accepted. Do not leave dual old/new renderers, legacy artifact adapters, schema fallbacks, migration UI, or compatibility formatting behind.

## Research and Standards Basis

The implementation decisions above are grounded in the following authoritative/current references and mature-product patterns. They are design evidence, not dependencies to copy wholesale.

- Tailwind CSS v4 theme variables and first-party Vite integration: https://tailwindcss.com/docs/theme and https://tailwindcss.com/docs/installation/using-vite
- Radix Primitives accessibility/unstyled composition model: https://www.radix-ui.com/primitives/docs/overview/introduction and https://www.radix-ui.com/primitives/docs/overview/accessibility
- Lightweight Charts 5.2 and its accessibility guidance: https://tradingview.github.io/lightweight-charts/docs and https://tradingview.github.io/lightweight-charts/tutorials/a11y/intro
- WAI-ARIA Authoring Practices for complex controls: https://www.w3.org/WAI/ARIA/apg/patterns/
- WCAG 2.2 reflow, focus, contrast, target size, and status-message guidance: https://www.w3.org/WAI/WCAG22/Understanding/
- Lucide React/icon consistency: https://lucide.dev/guide/react/
- TradingView screener/watchlist patterns: https://www.tradingview.com/support/solutions/43000724233-chart-view-mode/ and https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/
- Coinbase Advanced analytical-panel organization: https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/dashboard-overview
- Bloomberg Terminal/Launchpad as a reference for professional analytical density and compartmentalization: https://professional.bloomberg.com/products/bloomberg-terminal/

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
