# Phase 16 — Human-Centered Workbench UX Re-architecture

Update context — 2026-08-19
Trigger: Slice 4 is complete and repository/browser verified, but the current workbench still exposes research-engine terminology and orchestration as primary UX to users who are not assumed to be developers or professional traders.
Purpose: Re-architect the web presentation around user goals, research comprehension, cross-session continuity, and progressive disclosure without changing QAP scientific/economic authority.
Impact: Adds a post-Slice-4 product phase. Runtime research contracts remain unchanged unless the explicit current-evidence capture checkpoint later proves a backend composition change is necessary.
Evidence: `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`, current `main` at `62416cc`, completed Slice-4 results and rendered acceptance.

Update context — 2026-08-19 (M1 freeze)
Trigger: The current-state investigation and rendered walkthrough are complete; no additional moderated participants are available in this implementation session.
Purpose: Resolve the terminology/information-architecture checkpoint so presentation implementation can proceed without inventing labels route-by-route.
Impact: `Home / Discover / Validate / Portfolios / Results / Activity` and the presentation vocabulary in the investigation are frozen as a `single-stakeholder provisional` implementation baseline. No backend contract is changed.
Evidence: `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md#17-milestone-1-terminology-and-ia-checkpoint`.

**Goal:** Make the completed local QAP workbench understandable and efficient for non-developer, non-professional-trader stakeholders/users while preserving exact research evidence, negative outcomes, provenance, and all established authority boundaries.

**Architecture:** Keep the existing FastAPI command/query boundary, React 19/TanStack application, immutable QAP/scanner artifacts, and existing evidence routes. Re-architect only the presentation hierarchy: a goal-oriented Home and primary navigation, plain-language task surfaces, visible causal/time boundaries, and progressive disclosure from user decision → contextual evidence → advanced research → exact audit.

**Tech Stack:** React 19.2, TypeScript 5.9, Vite 8, Tailwind CSS 4, TanStack Router, TanStack Query, Lightweight Charts, native SVG, existing FastAPI/OpenAPI contracts.

## Global constraints

- QAP artifacts, portfolio state, QAP replay/economics, scanner protocols, prospective rules, qualification rules, and basket policy remain authoritative outside React.
- Do not change the seven-command mutation vocabulary for presentation convenience:
  - `run_scan`
  - `generate_asset_momentum`
  - `freeze_forward_cohort`
  - `advance_forward_cohort`
  - `capture_public_evidence`
  - `qualify_candidate`
  - `run_basket`
- Do not introduce a generic execution endpoint, browser-side research engine, database, queue, scheduler, auth system, live exchange credentials, or live-capital action.
- Keep the loopback-only/single-operator/single-active-mutation V1 boundary.
- Preserve all negative, invalid, rejected, incomplete, and unavailable evidence; do not hide it to make the product look more successful.
- Keep operational state, evidence validity/completeness, and scientific/economic outcome visually distinct.
- Do not invent progress percentages/ETAs, conversion rates, drop-off percentages, or analytics baselines.
- Do not rename runtime/domain enums merely to improve copy. Translate them in presentation and preserve exact values in advanced/audit disclosure.
- Existing URLs may remain stable. Route-path migration is out of scope unless user research demonstrates a concrete navigation benefit that cannot be achieved with labels/shell composition.
- Existing Phase-14/Slice-4 accessibility, responsive, no-network browser-fixture, OpenAPI, and presentation-only financial-authority boundaries remain in force.
- No framework replacement. Do not add Material UI, Chakra, Bootstrap, Next.js, a second charting system, or an animation dependency without a separately demonstrated need.

## 1. Authoritative UX research input

The current-state investigation is:

`docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`

That document owns:

- actual current route/screen inventory;
- current strengths that must be preserved;
- task analysis;
- four canonical user journeys;
- cognitive-walkthrough findings;
- heuristic severity register;
- terminology architecture;
- IA hypothesis;
- progressive-disclosure contract;
- story map;
- future usability metrics.

This plan should link to that evidence instead of duplicating its full rationale.

## 2. Product model after Phase 16

The application should feel organized around what the user is trying to accomplish:

```text
Home
  ├─ Find research ideas        → Discover
  ├─ Continue validation        → Validate
  ├─ Build/analyze portfolio    → Portfolios
  └─ Resume previous work       → Results / Activity
```

Every detailed result follows the same disclosure order:

```text
Goal / verdict
    ↓
Contextual evidence
    ↓
Advanced research controls/details
    ↓
Exact audit / provenance
```

The recommended top-level navigation hypothesis is:

```text
Home | Discover | Validate | Portfolios | Results | Activity
```

`Research Runs`, `Pair`, `Portfolio Economics`, and `Paper Operations` remain real evidence routes; they do not all need to remain primary-navigation concepts.

## 3. Presentation vocabulary contract

Use the terminology mapping in the investigation document. The following are mandatory presentation principles:

- `candidate` may be shown primarily as **Research idea**;
- `prospective cohort` may be shown primarily as **Forward validation**;
- `freeze cohort` → **Start forward validation**;
- `advance cohort` → **Update forward evidence**;
- `capture public evidence` → **Update current market evidence**;
- `qualification` → **Current capital assessment**;
- `requested capital` → **Amount to evaluate**;
- `run basket through QAP` → **Analyze portfolio**;
- `operation` → **Activity/background task** where appropriate;
- exact enum/state names remain accessible in research/audit disclosure.

`tradable_now` must never be translated into language that implies QAP has live-capital authority. Primary copy should describe what current research evidence supports for the hypothetical amount and repeat the no-live-authority boundary where actionability is shown.

## 4. State visual grammar

The redesign must explicitly represent three axes rather than one generic badge color:

### Operational

`running / completed / failed / interrupted`

### Evidence

`valid / invalid / complete / incomplete / unavailable`

### Research/economic conclusion

Survival/rejection/qualification/basket result states.

A scientifically negative result from a completed valid operation must not look like a broken application.

## 5. File ownership map

### Shell and shared presentation

- Modify: `web/src/routes/index.tsx` — replace the root Research Runs rendering with the goal/resume Home composition.
- Modify: `web/src/components/AppShell.tsx` — primary information architecture and navigation labels/grouping.
- Modify: `web/src/styles/tokens.css` — status/attention/evidence tokens only if the current token set cannot express the three-axis state grammar.
- Modify: `web/src/styles/global.css` — shared shell/layout/disclosure behavior only.
- Reuse: existing `Badge`, `TableScroll`, error shell, charts, formatting, and route/query infrastructure.

Create a new shared UI component only when at least two completed route redesigns demonstrate the same stable need. Prefer native `<details>/<summary>` for simple progressive disclosure before adding abstraction.

### Home / orientation

- Create: `web/src/features/home/HomeWorkspace.tsx` — goal entry points, active operation, validations waiting/available, recent results.
- Modify: `web/src/routes/index.tsx` — load/reuse existing queries needed by Home; do not create a new backend dashboard endpoint unless existing queries prove materially insufficient.

### Discover / research ideas

- Modify: `web/src/features/discovery/DiscoveryHome.tsx`
- Modify: `web/src/features/discovery/ScanDetail.tsx`
- Modify: `web/src/features/discovery/CandidateDetail.tsx`

### Validate / current evidence

- Modify: `web/src/features/prospective/ProspectiveHome.tsx`
- Modify: `web/src/features/prospective/ProspectiveDetail.tsx`

### Portfolios

- Modify: `web/src/features/baskets/BasketHome.tsx`
- Modify: `web/src/features/baskets/BasketDetail.tsx`
- Modify only if necessary: `web/src/features/baskets/BasketGraph.tsx`

### Results / Activity

- Modify: `web/src/features/operations/OperationList.tsx`
- Modify: `web/src/features/operations/OperationDetail.tsx`
- Modify: `web/src/features/operations/presentation.ts`
- Recompose existing Experiment/Portfolio/Pair/Paper routes through navigation/entry-point changes before redesigning their evidence internals.

### Backend

Default: **no backend change**.

Potential later boundary decision only:

- if guided current-evidence capture cannot be implemented safely using the existing finite `capture_public_evidence` command, design one bounded application-composition operation at the backend boundary;
- do not implement that change from this plan without first recording the usability evidence and updating the operation contract/OpenAPI plan.

## 6. Milestone 0 — Freeze the current-state UX evidence

**Status:** completed by `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`.

**Produces:** actual route inventory, task analysis, journey maps, heuristic findings, terminology mapping, IA hypothesis, story map.

**Acceptance criteria:**

- [x] Current main/Slice-4 routes are described accurately rather than as imagined separate screens.
- [x] No-results/rejected research outcomes are separated from application errors.
- [x] Prospective validation is modeled as a cross-session causal journey, not simulated future data.
- [x] Qualification is modeled as QAP classification of explicit hypothetical capital, not user acceptance/rejection.
- [x] Basket flow includes relationship evidence, not only the 3–6 asset-count rule.
- [x] Invented conversion/drop-off metrics are removed.

## 7. Milestone 1 — Stakeholder terminology and IA checkpoint

**Status:** complete — `single-stakeholder provisional` baseline frozen on 2026-08-19. Milestone 2 presentation work may proceed.

**Files:**

- Modify: `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`
- Modify: this plan only if decisions change implementation ownership.

**Interfaces:**

- Consumes: terminology table, IA hypothesis, story map.
- Produces: frozen presentation labels and navigation grouping.

**Steps:**

- [x] Review the six proposed primary destinations against the stated stakeholder/user profile and current rendered workflows: Home, Discover, Validate, Portfolios, Results, Activity.
- [x] Place current tasks into destinations: find/understand an idea → Discover; forward/current-capital work → Validate; portfolio work → Portfolios; finished research/paper evidence → Results; background execution → Activity; orient/resume → Home.
- [x] Record the principal confusion boundaries qualitatively rather than inventing a score: Results vs Activity, candidate vs asset, prospective vs simulated future, user qualification vs QAP classification, Operations vs Paper Operations.
- [x] Freeze plain-language translations for historical survivor/rejected and `research_only` / `small_capacity` / `tradable_now` states, including the explicit no-live-authority wording.
- [x] Freeze the navigation and terminology table as `single-stakeholder provisional`, with explicit observation-based reopen triggers.

**Acceptance criteria:**

- A non-developer stakeholder can explain where to start each canonical task without being told the current route name.
- `tradable_now` presentation wording cannot reasonably be read as live-trading authorization.
- Advanced research terminology remains discoverable but is not required to navigate the core flow.

The no-additional-participant branch has been exercised: the recommended IA/terminology is now the `single-stakeholder provisional` implementation baseline. Reopen it only under the observation triggers recorded in the investigation.

## 8. Milestone 2 — Goal-oriented Home and shell

**Status:** complete at `eb40327`.

**Files:**

- Create: `web/src/features/home/HomeWorkspace.tsx`
- Modify: `web/src/routes/index.tsx`
- Modify: `web/src/components/AppShell.tsx`
- Modify as needed: shared styles/tokens.

**Interfaces:**

- Consumes: existing experiment/results query, operations query, forward-validation query, basket/scan links.
- Produces: goal-oriented start/resume experience and frozen primary navigation.

**Steps:**

- [x] Replace root `ExperimentList` with Home.
- [x] Present four primary goals: find ideas, continue validation, analyze portfolio, review prior work.
- [x] Surface at most one active mutation prominently, with status and Activity link.
- [x] Surface forward validations that are waiting/ready for later evidence without requiring users to remember cohort IDs.
- [x] Surface recent finished research results without turning Home into another evidence table.
- [x] Move Research Runs/Paper Operations out of the primary novice navigation according to the frozen IA while preserving their routes and deep links.
- [x] Keep keyboard/skip-link/navigation semantics intact.

**Acceptance criteria:**

- A first-time user can choose a goal from `/` without knowing QAP subsystem names.
- Returning users can see where unfinished/recent work lives.
- Exact evidence routes remain reachable.

## 9. Milestone 3 — Discover and Research Idea experience

**Status:** complete at `b1cce7a`.

**Files:**

- Modify: `web/src/features/discovery/DiscoveryHome.tsx`
- Modify: `web/src/features/discovery/ScanDetail.tsx`
- Modify: `web/src/features/discovery/CandidateDetail.tsx`

**Interfaces:**

- Consumes: existing scanner protocol/read models and `run_scan` / momentum operation.
- Produces: novice-first discovery and historical-evidence comprehension.

**Steps:**

- [x] Make the default scan command ask only for ordinary user intent: analysis date and research timeframe.
- [x] Move manual pins, forensic mode, manual replay candidate IDs, and protocol details into `Advanced research controls`.
- [x] Keep all existing command fields available; do not remove operator capability.
- [x] On Scan Detail, lead with scope, number of research ideas that received meaningful historical evaluation, and a concise summary of accepted/rejected/unavailable evidence.
- [x] Present a prioritized Research Ideas section before the complete candidate-trial ledger.
- [x] Keep the complete trial ledger available under `All evaluated rules` / advanced evidence so negative evidence and denominator remain visible.
- [x] Translate raw replay/model-source statuses in primary copy while preserving exact enum text in detail disclosure.
- [x] Candidate Detail must lead with pair + plain historical verdict + comparison/control context + next valid action.
- [x] Move candidate ID, scan ID, model/template/resolution/orientation, promotion mechanics, and exact lineage into research/audit disclosure.
- [x] Rename `Freeze prospective cohort` in the primary layer to `Start forward validation` while preserving exact backend behavior.

**Acceptance criteria:**

- A user can find and understand a research idea without knowing candidate IDs or replay enums.
- Invalid/rejected evidence remains visible and is not converted into success-colored UX.
- Advanced users retain all current manual/forensic/replay capability.

## 10. Milestone 4 — Forward Validation and Current Capital experience

**Status:** stopped before source mutation at the documented capture-readiness boundary. See `docs/research/2026-08-19-qap-phase16-m4-boundary-stop-handoff.md`.

**Files:**

- Modify: `web/src/features/prospective/ProspectiveHome.tsx`
- Modify: `web/src/features/prospective/ProspectiveDetail.tsx`

**Interfaces:**

- Consumes: existing freeze/advance/capture/qualification commands and prospective/qualification read models.
- Produces: causal cross-session validation UX with guided evidence readiness.

**Steps:**

- [ ] Present list items as Forward Validations rather than cohort records in the primary layer.
- [ ] Show the frozen research idea, freeze time, predefined horizon/maturity, and current stage.
- [ ] Add a visual temporal boundary between historical evidence and later evidence.
- [ ] Rename primary `Advance cohort` action to `Update forward evidence`; explain that QAP applies the frozen horizon and the operator is only advancing through available information.
- [ ] Present partial vs matured outcomes in plain language without calling partial evidence a failure.
- [ ] Replace the current three equal-weight command cards with a staged task hierarchy: update forward evidence → ensure current market evidence → evaluate amount.
- [ ] Build a current-evidence readiness summary from existing read-model facts before exposing capture mechanics.
- [ ] When capture is needed, guide the existing bounded capture commands contextually. Venue symbol/base/quote/capture kind belong in Advanced/manual capture unless they cannot be inferred safely from authoritative evidence.
- [ ] Present qualification as `Current capital assessment`, asking primarily for `Amount to evaluate` and the relevant as-of/current state.
- [ ] Present the result in plain language with explicit no-live-authority text.
- [ ] Keep exact state, q-safe values, gates, snapshot IDs, checkpoint IDs, and request details under evidence/audit disclosure.

**Boundary checkpoint:**

If authoritative existing read models do not provide enough information for React to determine which finite capture command is appropriate **without inferring financial/scientific truth**, stop this milestone and design the smallest backend application-composition change. Do not create a frontend capture oracle.

**Acceptance criteria:**

- The user can explain what was frozen, what happened later, and what evidence is current.
- The user is never asked to choose an arbitrary forward-test duration.
- The user does not need exchange symbol syntax for the normal path when authoritative context already determines it.
- Qualification wording cannot be mistaken for live-trading permission.

## 11. Milestone 5 — Portfolio builder and result experience

**Files:**

- Modify: `web/src/features/baskets/BasketHome.tsx`
- Modify: `web/src/features/baskets/BasketDetail.tsx`
- Modify only if needed: `web/src/features/baskets/BasketGraph.tsx`

**Interfaces:**

- Consumes: existing scan/candidate/momentum/basket read models and `run_basket` command.
- Produces: evidence-first portfolio construction and verdict-first portfolio research result.

**Steps:**

- [ ] Present the builder around selecting 3–6 assets/research ideas, not around source scan/configuration first.
- [ ] Use authoritative evidence to derive or constrain compatible source scope; keep source scan/horizon/resolution available in advanced details.
- [ ] Show relationship availability directly on the topology as assets are selected.
- [ ] Describe admissible relationship rules in plain language first; exact model/template/orientation/manual/indirect status remains available in details.
- [ ] Keep momentum explicitly contextual/pair-blind rather than implying it is relationship evidence.
- [ ] Keep pre-run state topology-only; never preview resolver opinion or target.
- [ ] Rename the primary action to `Analyze portfolio`.
- [ ] On Basket Detail, lead with economic/research verdict and benchmark comparison, then authoritative graph opinions/target explanation, then execution/audit evidence.
- [ ] Preserve HODL/control/basket semantics exactly; React must not calculate a substitute research score.

**Acceptance criteria:**

- A user can understand why an asset/relationship can or cannot be included without knowing scan IDs or decision-resolution rules.
- Pre-run and post-run authority boundaries remain visually obvious.
- A negative basket result is presented as valid completed research, not an operational error.

## 12. Milestone 6 — Results and Activity architecture

**Files:**

- Modify: `web/src/features/operations/OperationList.tsx`
- Modify: `web/src/features/operations/OperationDetail.tsx`
- Modify: `web/src/features/operations/presentation.ts`
- Modify as needed: navigation entry points into existing Experiment/Portfolio/Pair/Paper features.

**Interfaces:**

- Consumes: existing operation/result/evidence routes.
- Produces: coherent resume/history model without new storage.

**Steps:**

- [ ] Present Operations primarily as `Activity` with human labels for the seven command kinds.
- [ ] Keep exact operation kind/request metadata in Operation Detail.
- [ ] Preserve the existing explicit statement that operational failure does not imply scientific failure.
- [ ] Create a `Results` entry path using existing experiment/paper/basket/scan evidence queries rather than introducing a new result database.
- [ ] Group result links by user meaning: research idea, forward validation, portfolio result, research run, paper evidence.
- [ ] Preserve exact lineage/deep links across Scan → Idea → Validation → Basket → QAP evidence.

**Acceptance criteria:**

- Users know whether they are looking at background activity or research evidence.
- Existing specialist evidence routes remain available.
- No new persistence or duplicated research index is created unless current read APIs demonstrably cannot supply the view.

## 13. Milestone 7 — Visual-system convergence

**Files:**

- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/global.css`
- Modify existing shared UI components only where repeated route work demonstrates the need.

**Interfaces:**

- Consumes: frozen state grammar and implemented task surfaces.
- Produces: coherent QAP visual language.

**Steps:**

- [ ] Establish distinct treatments for operational activity, evidence completeness/validity, and research conclusion.
- [ ] Establish surface hierarchy for goal, verdict, contextual evidence, advanced research, and audit detail.
- [ ] Standardize number/identifier presentation: human-readable value first; exact value/ID on demand.
- [ ] Use motion only where it communicates state transition or coordinated evidence focus; prefer existing CSS/native capabilities.
- [ ] Preserve reduced-motion behavior and existing accessible focus/touch targets.
- [ ] Give Basket/Portfolio graph/evidence coordination the strongest visual treatment after information hierarchy is correct.

**Acceptance criteria:**

- The application no longer looks like six unrelated forms/tables sharing Tailwind classes.
- Attention intensity follows meaning, not simply positive/negative color.
- Dense evidence remains readable on desktop and degrades gracefully on mobile.

## 14. Milestone 8 — Human-centered acceptance and closure

This phase is not complete merely because the redesigned pages render.

**Required evaluation:**

- walk the four canonical journeys from the investigation;
- perform a cognitive walkthrough from a novice perspective;
- confirm the user can distinguish operation failure from scientific rejection;
- confirm the user can distinguish historical, forward, and current evidence;
- confirm no user-facing wording implies live-trading authority;
- confirm advanced/audit evidence remains discoverable.

When real stakeholder/user sessions are available, record observations using the metrics defined in the investigation rather than inventing conversion targets.

**Existing repository acceptance to preserve:**

- current frontend type/build contract;
- current no-network deterministic critical browser workflows;
- current desktop/mobile rendered accessibility/overflow/runtime acceptance;
- current OpenAPI synchronization when API contracts change;
- existing repository verification required by repository policy for any executable changes.

Do not create a broad screenshot/CSS-copy test suite. Add or update automated tests only for meaningful semantic/interaction contracts changed by this phase; ordinary visual polish remains rendered QA.

## 15. Explicit non-goals

- a new research slice;
- new predictive models;
- changes to scanner protocol, promotion, QAP economics, HODL/control semantics, prospective windows, liquidity mathematics, basket resolver, or portfolio accounting;
- generic workflow engine;
- account/auth system;
- live trading;
- cloud/multi-user deployment;
- server-side basket draft persistence;
- client-side graph resolver or financial calculator;
- hiding exact evidence;
- deleting specialist Experiment/Portfolio/Pair/Paper routes;
- analytics platform before there is a concrete measurement need;
- wholesale route-path migration;
- framework or component-library rewrite.

## 16. Exit criteria

Phase 16 is complete when:

1. Home/navigation reflect user goals rather than implementation subsystems.
2. Discovery can be operated without understanding manual replay IDs/forensic/model internals, while those capabilities remain available.
3. a Research Idea page explains historical verdict before provenance.
4. Forward Validation visibly preserves the freeze/later-evidence boundary and guides current evidence rather than exposing capture mechanics first.
5. Current capital assessment is understandable without implying live authority.
6. Portfolio construction starts from ideas/assets/evidence and preserves the pre-run/post-run QAP authority boundary.
7. Results and Activity are distinct mental models.
8. operation/evidence/research states have distinct visual semantics.
9. exact audit/provenance remains reachable everywhere it matters.
10. negative research evidence remains first-class.
11. no backend scientific/economic authority moved into React.
12. the human-centered acceptance walkthrough is green and the existing executable/browser acceptance contracts remain satisfied.

## 17. Execution order

```text
M0 current-state investigation                  ✅
        ↓
M1 terminology + IA stakeholder checkpoint      ✅ provisional freeze
        ↓
DESIGN FREEZE                                   ✅
        ↓
M2 Home + shell
        ↓
M3 Discover + Research Idea
        ↓
M4 Forward Validation + Capital Assessment
        ↓
M5 Portfolio builder + result
        ↓
M6 Results + Activity
        ↓
M7 visual-system convergence
        ↓
M8 human-centered + repository/browser closure
```

Do not begin broad visual polish before M2–M6 have established the information hierarchy. Do not reopen QAP research-engine architecture merely because an internal term is hard to explain; solve presentation first, then escalate only if the existing application boundary truly cannot support the user task safely.
