# QAP Research Console + Human Semantic Layer Implementation Plan

**Goal:** Reshape ordinary Research around one persistent console where the researcher chooses a pair, research type, period, and optional settings, then watches real backend data and results appear with a deterministic human-readable interpretation layer.

**Architecture:** Keep QAP's existing backend research, evidence, economic, identity, admission, holdout, and execution contracts authoritative. The React layer becomes a research instrument: it owns user intent, staged presentation, chart composition, and deterministic explanation of already-authoritative values, while evidence selection, support validation, and economic truth remain backend-owned. The existing pair controller remains feature-local; no generic workflow engine or new research engine is introduced.

**Tech Stack:** React 19, TypeScript, TanStack Query, existing QAP API client/queries, existing Tailwind-style utility tokens, existing `TimeSeriesChart` and `RelativeWealthChart`.

**Status:** Approved interaction plan. The current branch implements the console presentation and flow; this document's task list remains a design record, not evidence of representative-user acceptance. CLI verification and remaining limitations are reported with the implementation.

Update context — 2026-09-24
Trigger: review of the proposed console against the current UI, backend authority, relationship calculations, and failing interaction checks.
Purpose: make saved-result behavior, data binding, permission scope, and verification explicit before implementation.
Impact: the UI may change, but economic, identity, holdout, and authority contracts remain backend-owned.
Evidence: `ProductResearchAuthority`, `ProductPairStudy`, research recipe declarations, and the 14-failure frontend baseline (8 newly stale workspace tests).

Update context — 2026-09-24 (implementation continuation)
Trigger: the user asked to commit the five review corrections before completing the broader UX redesign.
Purpose: record that the proposal now has branch implementation while keeping visual acceptance separate.
Impact: no backend scientific or economic contract changed. The plan's acceptance criteria remain the review standard; tests and production build verify code behavior, not visual usability.
Evidence: commit `e84ed0d`, the subsequent Research Console source changes, focused CLI interaction checks, and the full web-suite baseline.

## Global Constraints

- The ordinary mental model is **choose question → start → watch → understand → adjust → run again**.
- The researcher chooses **pair, research type, period, and optional settings**. QAP resolves admissible venue/data/evidence internally.
- Evidence, recipe, compilation, dataset, fingerprint, operation, and model-version identifiers are not primary navigation concepts.
- Preserve all existing scientific/economic authority: methods, cost/fill rules, HODL and primary-control comparisons, final-OOS handling, universe eligibility, identity/admission rules, and live-capital boundaries do not change.
- Preserve explicit user authority where it is genuinely required. In particular, temporary USDT bridge authority remains an explicit decision and must never be inferred.
- The human semantic layer is deterministic presentation logic over authoritative backend values. It must not use an LLM, invent missing facts, create a new research verdict, select a winner, or emit buy/sell/trade recommendations.
- Relationship color communicates **magnitude/attention**, not desirability. Never use green/red to imply that a positive or negative z-score is good/bad.
- Technical validity and human interpretation are separate. A valid calculation may still describe an ordinary/near-reference condition.
- "Live" means honest progressive UI updates as real API stages complete. Do not fabricate streaming prices, fake percentages, timers, or intermediate results the backend has not produced.
- Successful evidence/support checks happen silently. Surface evidence mechanics only when they block the requested research or when the user opens technical details.
- Preserve browser-local draft semantics and independently durable backend results. Do not turn local storage into a scientific ledger.
- Reuse the existing dark visual system and chart components. Do not add a UI framework, chart library, tooltip package, font package, or theme dependency.
- Verify changed behavior with focused CLI interaction and pure-function tests. Browser acceptance remains a separate user gate.
- Distinguish a saved browser draft from a durable backend operation. Never describe a relationship read as a saved result.
- Bind every displayed relationship observation and chart to the same orientation, venue, cutoff, and source fingerprints; keep old run economics attached only to their recorded manifest.

## 1. Product Contract

### Research Console

Ordinary Research opens directly into one persistent console. The screen does not transform into a sequence of backend forms after Start.

Desktop target:

```text
Research Console                                      Saved research ▾

┌─ Research question ───────────┐  ┌─ Research canvas ────────────────────────┐
│ Pair                          │  │ W / PIXEL · 90 days                     │
│ [ W ]  /  [ PIXEL ]           │  │                                        │
│                               │  │ Data   Relationship   Simulation  Result │
│ Research type                 │  │  ✓          ●              ○        ○    │
│ [ Relationship ]              │  │                                        │
│ [ Backtest comparison ]       │  │ What this says                         │
│                               │  │ Ratio is noticeably below its recent    │
│ Period                        │  │ mean; residual remains near the fitted   │
│ [30d] [90d] [180d]            │  │ relationship.                           │
│                               │  │                                        │
│ Advanced settings ▾*          │  │ [ Normalized paths | Ratio ]            │
│                               │  │                                        │
│ [ Start research ]            │  │              real chart                │
└───────────────────────────────┘  │                                        │
                                   │ Key measurements                        │
                                   │ Ratio z  -1.95σ   Residual z  -0.46σ   │
                                   │                                        │
                                   │ Model details ▾  Evidence & provenance ▾│
                                   └─────────────────────────────────────────┘
```

On narrow screens the controls stack above the canvas. The canvas remains the dominant visual object after the pair is selected.

### Research types

V1 exposes only research intentions already supported honestly by the current backend:

| Research type | User question | Existing backend behavior |
| --- | --- | --- |
| **Relationship** | "How are these assets behaving relative to each other?" | Resolve/prepare pair data, fetch pair context and series, render relationship interpretation and charts, then stop. No recipe/support/economic run is required. |
| **Backtest comparison** | "What happened if the admitted relationship methods were acted on under the declared economic rules?" | Resolve relationship data first, then use the existing default recipe, backend support check, execution path, HODL/control economics, and result records. Both currently declared pair methods remain visible. |

Do not add a separate ordinary "method picker" in V1. Exact component/model selection remains an advanced Experiment Lab concern. This prevents the Research Console from becoming another recipe-authoring UI.

### Start action

Use one stable verb: **Start research**.

- Relationship mode: Start research means prepare/fetch the relationship and finish with descriptive results.
- Backtest comparison: Start research means prepare/fetch the relationship, obtain the backend-declared recipe, perform the support check, and launch the economic comparison if runnable.
- After completion, the same action becomes **Run again**.
- Changing pair, type, period, or settings invalidates stale presentation/run state but does not silently launch anything.

## 2. Honest Progressive Feedback

Replace the single free-form progress sentence with a typed presentation stage driven by completed/active API work.

Relationship stages:

```text
Data → Relationship → Ready
```

Backtest-comparison stages:

```text
Data → Relationship → Simulation → Result
```

Allowed runtime states:

- `idle`
- `resolving_data`
- `measuring_relationship`
- `waiting_for_authority`
- `checking_comparison`
- `running_comparison`
- `loading_results`
- `complete`
- `blocked`
- `failed`

The stage strip reflects real ownership:

- a stage becomes complete only after the corresponding API call/result exists;
- the active stage may show an indeterminate motion indicator;
- no fake percent-complete value is shown;
- while a backtest runs, keep the already-fetched relationship chart and semantic summary visible;
- partial result/chart load failure must not erase relationship data or other successfully loaded results.

A real permission interruption stays inside the canvas instead of opening a new workflow:

```text
Research paused

W / PIXEL has no admitted direct market.
This simulation can use W/USDT and PIXEL/USDT and models costs on both legs.

[ Allow USDT bridging for research in this workspace ]

Why is this required? ▾
```

The explanation is concise by default; exact execution/evidence mechanics remain in the disclosure. This explicit permission persists in the workspace for the current verified USDT identity and is not scoped to one pair or attempt.

For a brand-new Backtest comparison, QAP must not fabricate economic defaults in React.
If the exact recipe has not yet been declared by the backend, Start research uses the
backend-declared defaults after relationship preparation. Advanced settings become
editable once that declaration exists, and saved parameter overrides remain available
for later reruns. A saved research item that already has declared overrides may show
those overrides before Run again.

Contextual next actions remain research actions, never trading advice:

- Relationship complete: **Backtest this pair** is one explicit launch action using backend-declared defaults. Changing the research-type selector alone never launches.
- Backtest complete: **Change settings** and **Run again**.
- Blocked research: present the backend-supported corrective action, such as a shorter
  period or missing identity/authority decision.

## 3. Human Semantic Layer

### Ownership

Extend the existing frontend-only `researchPresentation.ts`. It already owns readable research method names/descriptions, so it is the correct place for deterministic relationship presentation semantics.

The semantic layer consumes backend values; it does not alter them.

Proposed presentation interfaces:

```ts
type RelationshipMetricKind = 'ratio' | 'residual'

type RelationshipBand =
  | 'near_reference'
  | 'noticeable_displacement'
  | 'large_displacement'
  | 'unavailable'

interface RelationshipInterpretation {
  kind: RelationshipMetricKind
  score: number | null
  band: RelationshipBand
  tone: 'neutral' | 'info' | 'warning'
  label: string
  direction: string | null
  explanation: string
}
```

The implementation uses these presentation semantics explicitly; do not collapse them into an untyped label/string helper.

### Presentation-only z-score bands

For a valid finite score:

| Absolute z-score | Label | Tone | Meaning |
| --- | --- | --- | --- |
| `< 1` | **Near reference** | neutral | close to the recent/fitted reference |
| `>= 1 && < 2` | **Noticeable displacement** | info | meaningfully away from the reference, but not presented as a signal |
| `>= 2` | **Large displacement** | warning | far from the reference and worth inspecting |

These are **UI interpretation bands only**. They do not change model thresholds, strategy entry rules, research status, or economic success criteria.

Direction is described separately:

- rolling log-ratio, negative: **below its recent reference level**;
- rolling log-ratio, positive: **above its recent reference level**;
- residual, negative: **below fitted relationship**;
- residual, positive: **above fitted relationship**.

Do not label negative red or positive green.

### Invalid observations

When backend status is `insufficient_history` or `insufficient_variance`:

- do not assign a semantic band from the score;
- show the backend reason in plain language;
- keep exact status/code in Model details;
- never render an unavailable score as zero.

### Combined "What this says"

Generate the headline/paragraph from the two authoritative observations with bounded deterministic rules.

Required combinations include:

- both near reference: "Both relationship measures are close to their recent/fitted references."
- ratio displaced, residual near: "The price ratio is displaced, while the residual model remains near its fitted relationship."
- residual displaced, ratio near: "The residual model is displaced, while the price ratio remains near its recent mean."
- both displaced in the same direction: "Both relationship measures are displaced in the same direction."
- both displaced in opposite directions: "The relationship measures point in different directions; inspect the chart and model details."
- one unavailable: explain the available measure and state that the other could not be interpreted at this cutoff.
- both unavailable: show the concrete backend availability reason, not an interpretation.

Every summary ends or is followed by a quiet boundary:

> Descriptive relationship evidence only; this is not a trading recommendation or proof of profitable economics.

### Metric hierarchy

Primary:

- rolling ratio z-score;
- residual z-score;
- human interpretation label/direction;
- actual tested period/cutoff.

Secondary:

- raw ratio;
- data availability/observation counts;
- selected venue/interval in compact status text.

Hidden by default:

- log ratio scalar;
- normalized current scalar values;
- alpha;
- beta;
- model IDs/versions;
- reciprocity fields;
- source fingerprints;
- dataset IDs/paths;
- capability codes;
- recipe/compilation/operation identifiers.

Normalized values belong primarily in the normalized-path chart and its hover readout, where the baseline is visible.

### Observation-count wording

The API exposes `coverage_observations`, `required_observations`, and `window_observations`. Do not invent a "95% usable" percentage from these values.

Render plain facts such as:

> 180 observations available · 171 required · 180-bar window

Only show a percentage if a backend contract explicitly defines the denominator and interpretation.

### Info controls

Use small accessible information disclosures only for definitions, never for the main conclusion.

Example:

```text
Rolling ratio  −1.95σ   ⓘ
Noticeable displacement · below recent ratio mean
```

The info disclosure answers "what does this metric mean?" and can expose:

> Measures how far the current log price ratio is from its rolling average, in standard deviations. Negative means the current ratio is below that average.

Implement with existing/native disclosure behavior rather than a new tooltip dependency. Hover must not be the only way to access the definition; keyboard/touch activation must work.

## 4. Chart and Detail Hierarchy

### Main canvas

Once series data exists, the graph becomes the center of the Research Console rather than a later technical section.

Primary chart choices:

- **Normalized paths** — default human view; makes relative movement legible against an explicit rebased baseline.
- **Ratio** — direct pair-ratio view.

Advanced views remain available under **More views**:

- Log ratio.
- BTC/reference lens when requested and actually available.

Do not add a z-score history chart unless the backend supplies authoritative z-score series. The current API exposes current z-score observations but not a z-score time series; do not reconstruct one in React.

### Details hierarchy

Below the human summary/chart:

1. **Key measurements** — exact z-scores, raw ratio, observation counts.
2. **Model details** — calculation validity, alpha/beta, model IDs/versions, window/reciprocity, exact log ratio.
3. **Evidence & provenance** — venue paths, datasets, source fingerprints, cutoff, generation/provenance paths.
4. **Methodology** — definitions, supported/unimplemented capability notes, limitations such as residual OLS not being a formal cointegration test.

The current "What QAP can test" block moves into Methodology/advanced details. The current "Economic replay is a separate question" block disappears from ordinary presentation; only a real blocked economic action surfaces inline.

The descriptive observations use the horizon's backend-defined lookback. Backtest recipe overrides can use different model settings. Show that difference beside the advanced settings; do not imply the descriptive z-scores were calculated with an edited backtest lookback. If context and chart series disagree on orientation, venue, cutoff, or source fingerprints, do not compose them into one interpretation; retry the reads or show a recoverable mismatch. Before launching a separately declared recipe, require the same ordered pair, horizon, interval, cutoff, and pair-generation bindings as the displayed context; on mismatch, retain the descriptive view and offer a fresh comparison retry.

### Result hierarchy for Backtest comparison

When the backend operation completes:

- retain the relationship summary/chart in the same console, but lead with the economic conclusion and method comparison in Backtest mode;
- show one compact all-method economic summary immediately below;
- keep exact HODL and primary-control deltas;
- keep the backend result/verdict unchanged;
- initial selected method remains the first declared method, never the historical winner;
- show the selected method's relative-wealth chart and human explanation;
- keep costs/fills, exact test settings, reproducibility, and run identifiers behind disclosures.

Do not repeat the same HODL/control deltas in multiple large cards.

## 5. Visual Direction

The signature element is the **persistent research canvas with the live stage strip**. Everything else stays visually restrained.

- Reuse existing color tokens: canvas/panel/foreground/secondary/accent/info/warning/negative/positive.
- Accent owns selection and the Start research action.
- Neutral/info/warning own relationship magnitude. Positive/negative colors remain reserved for contracts where the backend semantics actually mean positive/negative economic evidence or success/failure.
- Use the existing text face for controls/explanation; use tabular numerals and existing mono treatment only for exact data/identifiers.
- Avoid equal-size metric-card grids. Visual weight follows interpretation → chart → key measurements → details.
- Keep one principal console surface with internal dividers/whitespace rather than nested cards around every metric.
- Desktop: approximately 300–340 px control column plus a flexible research canvas.
- Mobile: controls → Start research → progress → semantic summary → chart → measurements → disclosures.
- Maintain at least 44 px interaction targets and no page-level horizontal scroll at 360 px. Charts/tables may own contained overflow.
- Preserve focus position while data stages update. Do not auto-scroll the user to newly arrived backend sections.

## 6. File Map

### Existing files to modify

- `web/src/features/discovery/ResearchHome.tsx`
  - Route-level Research framing. Rename ordinary pair work to the Research Console and keep Scan assets / Custom experiment secondary.
- `web/src/features/home/HomeWorkspace.tsx`
  - Change the primary entry from "Start a comparison" to "Start research" and describe pair/type/period rather than backend stages.
- `web/src/features/discovery/ResearchStudyWorkspace.tsx`
  - Keep saved work compact, rename ordinary saved objects from comparisons/studies to saved research in visible copy, and allow the console to use more horizontal space.
- `web/src/features/discovery/researchStudies.ts`
  - Add persisted `ResearchMode`, migrate existing v1 browser drafts, include type in human attempt/question labels.
- `web/src/features/discovery/useResearchStudies.ts`
  - Consume the migrated study shape without changing cross-tab conflict ownership.
- `web/src/features/discovery/PairResearchSetup.tsx`
  - Present pair, research type, period, and optional settings as researcher choices; keep identity/admission only as contextual blockers.
- `web/src/features/discovery/PairResearch.tsx`
  - Remain the bounded feature controller; own mode-aware API sequencing, typed progress, bridge interruption, stable console layout, and stale/single-flight protection.
- `web/src/features/discovery/researchPresentation.ts`
  - Extend existing presentation ownership with deterministic relationship bands, direction wording, metric definitions, and combined "What this says" copy.
- `web/src/features/discovery/PairStudyResults.tsx`
  - Become a thin composer for human summary + main relationship chart + hidden technical details; remove equal-weight metric/model/economic cards.
- `web/src/features/discovery/PairExperimentPreview.tsx`
  - Keep economic settings behind Advanced settings for Backtest comparison; do not appear in Relationship mode.
- `web/src/features/discovery/PairResearchCompletion.tsx`
  - Keep economic summary/results inside the same console hierarchy and collapse forensic detail.
- `docs/plans/README.md`
  - Record this plan as the new proposed Research interaction frontier.
- `README.md`
  - Update only after implementation to describe the Research Console as implemented behavior; do not change current implementation claims merely because the plan exists.

### Focused files to create

- `web/src/features/discovery/PairRelationshipSummary.tsx`
  - Render "What this says", the two semantic z-score indicators, concise key measurements, and accessible metric-definition disclosures.
- `web/src/features/discovery/PairStudyTechnicalDetails.tsx`
  - Own Model details, Evidence & provenance, and Methodology disclosures currently mixed into the 500+ line PairStudyResults component.

Do not create a generic workflow/state-machine framework, generic metric-card system, or new chart abstraction.

## 7. Implementation Tasks

### Task 1: Add researcher intent to saved research

**Files:**
- Modify: `web/src/features/discovery/researchStudies.ts`
- Modify: `web/src/features/discovery/useResearchStudies.ts`
- Modify: `web/src/features/discovery/ResearchStudyWorkspace.tsx`

**Interfaces:**
- Consumes: existing browser-local `StudyLibrary`, current v1 stored payloads, existing attempts.
- Produces: `ResearchMode = 'relationship' | 'backtest_comparison'` on each `ResearchStudy`, migrated persisted drafts, human labels containing research type.

**Steps:**
- [ ] Add the two-mode type and a visible label mapping owned by the research feature.
- [ ] New research defaults to `relationship` so the simplest chart-first descriptive workflow is the default.
- [ ] Read the new `qap.research-studies.v2:${workspace}` key first. If absent, read the existing `qap.research-studies.v1:${workspace}` key and migrate each valid study to `backtest_comparison`, because the pre-console behavior represented a backtest comparison. Preserve IDs, names, assets, horizon, settings, and attempt references exactly.
- [ ] Save only the v2 shape to the new v2 key. Leave the legacy v1 payload untouched so migration is non-destructive.
- [ ] During the migration period, treat storage events for either the v1 or v2 workspace key as an external-change conflict so an older open tab cannot silently overwrite the current draft.
- [ ] Include research type in `studyQuestion()` / attempt copy so an earlier Relationship result cannot be confused with a later Backtest comparison.
- [ ] Only backtests create durable operation attempts. Reopening Relationship mode restores a draft and invites a fresh read. Reopening a backtest restores its recorded operation without automatically fetching current relationship evidence as if it were historical.
- [ ] Keep the submitted question/settings snapshot attached to each visible attempt. Changing mode or inputs clears the active result view without deleting historical attempts.
- [ ] Change visible "Saved comparisons/studies" copy to "Saved research" without claiming browser storage is authoritative.

**Acceptance criteria:**
- Existing saved work reopens with the same historical meaning.
- New work has an explicit research type.
- Browser storage still remains convenience state; backend results remain independently addressable.

### Task 2: Turn the pair form into Research Console controls

**Files:**
- Modify: `web/src/features/discovery/PairResearchSetup.tsx`
- Modify: `web/src/features/discovery/PairResearch.tsx`
- Modify: `web/src/features/discovery/ResearchStudyWorkspace.tsx`

**Interfaces:**
- Consumes: migrated `ResearchStudy.mode`, asset selectors, horizon choices, existing identity/admission mutations.
- Produces: one visible research-intent control surface and one stable Start research action.

**Steps:**
- [ ] Arrange Pair, Research type, Period, and Advanced settings as the only ordinary choices before Start.
- [ ] Keep exact identity/admission actions hidden unless a selected asset actually requires them; preserve the chosen pair while the blocker is resolved.
- [ ] Replace "Run comparison" as the universal verb with **Start research**; after a completed run use **Run again**.
- [ ] Relationship mode does not show economic method/cost settings.
- [ ] Backtest comparison shows a collapsed Advanced settings disclosure only when the backend recipe declaration or saved parameter overrides make exact settings available. A first run with no declaration uses backend defaults; React must not invent them.
- [ ] Keep pair-orientation and optional BTC/reference lens secondary; do not let them compete with Start research.
- [ ] Widen the workspace so controls and canvas can form the 300–340 px / flexible desktop layout while stacking cleanly on mobile.

**Acceptance criteria:**
- A ready user can identify pair, research type, period, and Start research without reading backend terminology.
- No successful evidence/support stage requires an extra confirmation.

### Task 3: Make orchestration mode-aware and progressively observable

**Files:**
- Modify: `web/src/features/discovery/PairResearch.tsx`

**Interfaces:**
- Consumes: current pair-context/series APIs, market-data preparation, recipe product context, support check, run operation, bridge-authority mutation.
- Produces: typed presentation stage, relationship data as soon as available, optional economic operation/result path.

**Steps:**
- [ ] Replace the free-form progress string with the explicit runtime stage union from Section 2.
- [ ] In Relationship mode, execute context → bounded preparation if needed → series; then mark complete without requesting recipe/support/run APIs.
- [ ] In Backtest comparison mode, execute the same relationship path first and publish context/series immediately, then continue recipe → support → run using the existing backend contract.
- [ ] Preserve the relationship canvas while the economic operation is running.
- [ ] Convert bridge authority into the single inline `waiting_for_authority` interruption. After authorization, refresh context/support and continue the same declared user intent.
- [ ] Preserve existing single-flight locking, stale-draft invalidation, operation resume, and "no React effect launches scientific work" constraints.
- [ ] Keep pending launch inputs fixed until the backend returns an operation reference. The Custom Experiment one-click launcher must also prevent edited drafts from launching an earlier checked recipe unnoticed.
- [ ] Track context, chart, operation, and experiment-detail read states independently: a chart retry must never repeat a backtest or erase a completed summary.
- [ ] Translate backend preparation/support failures into one actionable message near the affected control; keep exact reason/code under technical detail.
- [ ] Never synthesize intermediate scientific values for the stage strip.

**Acceptance criteria:**
- Relationship research finishes without economic machinery.
- Backtest comparison automatically traverses successful backend stages and only pauses for a real user decision or blocker.
- The user sees real relationship data before a longer economic run finishes.

### Task 4: Implement the deterministic human semantic layer

**Files:**
- Modify: `web/src/features/discovery/researchPresentation.ts`
- Create: `web/src/features/discovery/PairRelationshipSummary.tsx`

**Interfaces:**
- Consumes: `ProductPairStudyContextDto.relationship`, especially observation `status`, `values.score`, observation counts, orientation, and cutoff.
- Produces: presentation-only band/tone/direction/summary copy and the main human-readable relationship summary.

**Steps:**
- [ ] Implement the exact presentation bands and direction rules in Section 3 as pure functions with no React or API calls.
- [ ] Treat non-valid/missing/non-finite scores as unavailable, never as zero.
- [ ] Implement the bounded two-measure summary combinations; do not generate open-ended prose.
- [ ] Render "What this says" before raw metrics.
- [ ] Render ratio and residual z-scores with neutral/info/warning semantic indicators and exact signed values.
- [ ] Move computation validity out of the hero badge; show it under Model details.
- [ ] Render observation counts as exact available/required/window facts; do not invent percentages.
- [ ] Add accessible info disclosures for metric definitions. Main interpretation must remain understandable without opening them.
- [ ] Include the descriptive-evidence limitation without overwhelming the main conclusion.

**Acceptance criteria:**
- The screenshot case `ratio z ≈ -1.95`, `residual z ≈ -0.46` reads as a displaced ratio plus a residual near the fitted relationship, while retaining both exact values.
- No semantic color/copy implies buy/sell, opportunity, profitability, or good/bad direction.
- Alpha/beta/model IDs are absent from the default summary.

### Task 5: Rebuild Pair Study around the chart and progressive disclosure

**Files:**
- Modify: `web/src/features/discovery/PairStudyResults.tsx`
- Create: `web/src/features/discovery/PairStudyTechnicalDetails.tsx`
- Reuse: `web/src/components/charts/TimeSeriesChart.tsx`

**Interfaces:**
- Consumes: existing pair context/series/capability data and Task-4 presentation functions.
- Produces: main research canvas, primary chart controls, compact measurements, three technical disclosures.

**Steps:**
- [ ] Render `PairRelationshipSummary` first, then the chart as the largest surface.
- [ ] Make Normalized paths the default primary view and Ratio the second primary view.
- [ ] Move Log ratio and optional reference/BTC lens under a quiet More views control.
- [ ] Remove current normalized-value cards; exact normalized values remain available through chart values/technical detail where the rebased baseline is visible.
- [ ] Keep Raw ratio as a secondary key measurement; move exact log ratio into Model details.
- [ ] Move alpha, beta, model ID/version, reciprocity, technical "valid" status, and window internals into Model details.
- [ ] Move dataset paths/fingerprints/cutoff provenance into Evidence & provenance.
- [ ] Move capability inventory, unimplemented Student-t Copula note, and OLS-not-cointegration explanation into Methodology.
- [ ] Remove the ordinary "Economic replay is a separate question" section. Economic blocking/authority belongs to PairResearch orchestration.
- [ ] Keep exact backend values and source boundaries unchanged; this task changes hierarchy only.

**Acceptance criteria:**
- A user can understand the relationship state and inspect the real graph without encountering alpha/beta/model IDs first.
- An expert can still reach every currently exposed technical value with at most one disclosure per detail category.
- PairStudyResults becomes materially smaller and stops owning unrelated economic-authority UI.

### Task 6: Integrate economic results into the same console hierarchy

**Files:**
- Modify: `web/src/features/discovery/PairExperimentPreview.tsx`
- Modify: `web/src/features/discovery/PairResearchCompletion.tsx`
- Modify: `web/src/features/discovery/PairResearch.tsx`

**Interfaces:**
- Consumes: existing recipe declaration, operation result/run IDs, experiment detail/performance queries, HODL and primary-control economics.
- Produces: one continuous relationship → simulation → result experience.

**Steps:**
- [ ] Treat PairExperimentPreview as Advanced settings/context, not a separate numbered screen.
- [ ] Keep recipe-derived method names, costs, execution mode, and editable declared parameters available without requiring a second "check" action.
- [ ] A reopened completed result must offer working settings controls without an extra backtest. Run again uses refreshed trailing history, clearly labeled when the cutoff or binding changes.
- [ ] When the operation completes, place the all-method economic summary immediately after the existing relationship canvas rather than presenting a separate workflow.
- [ ] Keep both method rows, exact vs-HODL and vs-primary-control values, and backend verdicts visible together.
- [ ] Keep first-declared-method selection as the initial detail; never select a historical winner automatically.
- [ ] Keep the selected method's relative-wealth chart prominent.
- [ ] After Relationship completion, offer **Backtest this pair** as a research next action that switches mode without launching; never translate relationship displacement into a trading action.
- [ ] Collapse ending-wallet/fill/cost tables, exact settings, reproducibility, and operation/compilation identifiers beneath clear disclosures while retaining the exact values.
- [ ] Remove duplicate large metrics already present in the method summary.

**Acceptance criteria:**
- Backtest comparison reads as one research session, not Relationship evidence followed by a second application.
- The economic result retains the exact existing backend meaning and controls.
- Forensic/reproducibility detail remains available without dominating the result.

### Task 7: Make the whole Research area use the console vocabulary

**Files:**
- Modify: `web/src/features/discovery/ResearchHome.tsx`
- Modify: `web/src/features/home/HomeWorkspace.tsx`
- Modify: `web/src/features/discovery/ResearchStudyWorkspace.tsx`

**Interfaces:**
- Consumes: the completed Research Console and existing secondary Scanner/Experiment Lab entry points.
- Produces: one clear primary Research destination and secondary advanced tools.

**Steps:**
- [ ] Change the ordinary Research heading to **Research Console** with copy centered on pair/type/period/Start research.
- [ ] Keep Scan assets and Custom experiment reachable as secondary tools below/outside the primary console, not equal-weight tabs.
- [ ] Change Home's primary action to **Start research** and describe the researcher choices rather than preparation/support implementation stages.
- [ ] Keep saved research and earlier runs compact; opening/switching saved work must not replace the console with a project-management UI.
- [ ] Preserve primary Home / Research / Portfolios / History navigation and existing route URLs.
- [ ] Update stale workspace interaction tests and repair the Custom Experiment launch race as part of the same correction pass.

**Acceptance criteria:**
- Home → Research lands in the same mental model used inside the console.
- The ordinary user does not need to learn Scanner, recipes, evidence generations, or Experiment Lab before starting pair research.

### Task 8: Record the interaction contract without overstating acceptance

**Files:**
- Modify: `docs/plans/README.md`
- Modify after implementation only: `README.md`
- Keep as historical record: `docs/superpowers/plans/2026-09-24-intuitive-research-experience.md`

**Interfaces:**
- Consumes: implemented Research Console behavior.
- Produces: current plan-map and root-product documentation that distinguish implementation from later usability acceptance.

**Steps:**
- [x] Add this plan to the plan map as the successor interaction direction discovered through the 2026-09-25 live browser walkthrough.
- [ ] Preserve the 2026-09-24 plan as historical implementation evidence rather than rewriting its completed claims.
- [ ] After implementation, update root README terminology from "comparison workflow" to the Research Console and document the two research types, semantic presentation boundary, and hidden technical-detail hierarchy.
- [ ] Do not claim actual market streaming, human acceptance, or new scientific capability.

**Acceptance criteria:**
- Documentation tells a consistent chronology: first simplification → live browser finding → Research Console/semantic-layer revision.
- Planned/implemented/accepted states remain distinguishable.

## 8. Boundaries and Deferred Work

Out of scope for this plan:

- new mathematical relationship models;
- formal cointegration testing;
- model search or automatic winner selection;
- new strategy/economic objectives;
- changes to HODL, primary-control, cost, fill, timing, ending-wallet, residue, or success-threshold semantics;
- new final-OOS/promotion rules;
- replacing identity/admission contracts;
- automatic grant of bridge or asset authority;
- live exchange credentials/orders;
- live websocket market-price streaming;
- cloud accounts or cross-device saved-research synchronization;
- LLM-generated research interpretation;
- a generic workflow/state-machine framework;
- browser acceptance performed by this CLI-only implementation pass.

A future streaming-data project may make the research canvas update from live market observations, but this plan must not simulate that capability. In this scope, "live" means progressive display of real outputs as existing research stages complete.

## 9. Completion Criteria

Implementation is ready for a separate usability review when:

- the default Research screen is recognizably one Research Console;
- pair, research type, period, optional settings, and Start research are the only ordinary pre-run choices;
- Relationship mode stops after real relationship analysis without invoking economics;
- Backtest comparison automatically continues through the existing backend support/economic path;
- a real bridge/identity decision interrupts only when required and resumes the same research intent;
- real relationship data appears progressively and remains visible while later stages run;
- the first visible explanation says what the relationship measurements mean in ordinary language;
- exact z-scores remain visible while alpha/beta/model IDs/provenance are hidden by default;
- z-score color conveys magnitude/attention, never good/bad direction;
- the chart is the dominant result surface;
- economic results retain exact HODL/control/cost/verdict semantics;
- every currently exposed technical/provenance datum remains reachable through bounded disclosures;
- no frontend-generated interpretation is presented as a backend scientific or economic verdict.
- focused CLI tests pass for migration, both research types, stale responses, bridge authority, saved result editing, and partial read failures; unrelated baseline failures are reported separately.
