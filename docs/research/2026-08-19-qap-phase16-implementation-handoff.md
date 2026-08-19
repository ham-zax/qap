# QAP Phase 16 — Implementation Summary and Handoff

> Current continuation: M2 and M3 are complete; M4 stopped at its backend capture-readiness boundary. Continue from [the M4 boundary handoff](2026-08-19-qap-phase16-m4-boundary-stop-handoff.md), not from the older M2 start instructions below.

Update context — 2026-08-19
Trigger: Phase 16 current-state UX investigation and terminology/information-architecture checkpoint are complete.
Purpose: Give a fresh implementation agent one authoritative starting point for executing the human-centered workbench re-architecture without replaying prior design work or reopening scientific/backend contracts.
Impact: Documentation-only handoff. No runtime contract changes.
Evidence: `main` at `d5f362e`; `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`; `docs/plans/16-human-centered-workbench-ux-rearchitecture.md`.

## 1. Start here

Repository:

```text
/home/hamza/repo/qap
```

Branch:

```text
main
```

Authoritative state when this handoff was written:

```text
d5f362e docs: freeze phase16 terminology and ia
fc14d29 docs: define phase16 human-centered workbench
62416cc fix: close slice4 review findings
```

The executable Slice-4 application is complete. Phase 16 is a **presentation/information-architecture re-architecture over that completed application**, not a new research-engine slice.

Do not restart Slice 4. Do not repeat M0/M1. Begin at **Phase 16 M2 — Goal-oriented Home and shell**.

## 2. Read these documents in this order

1. `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`
   - authoritative current-state task analysis, journeys, cognitive walkthrough, heuristic findings, terminology architecture, IA freeze, and reopen triggers.
2. `docs/plans/16-human-centered-workbench-ux-rearchitecture.md`
   - executable M2–M8 implementation plan and file ownership.
3. `docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`
   - proof of the completed Slice-4 command/query/browser boundary that Phase 16 must preserve.
4. `docs/plans/14-analytical-workbench-ux-redesign.md`
   - existing verdict-first/evidence/audit presentation constraints that still apply.
5. `README.md` and `docs/plans/README.md`
   - current product/phase status.

Do not treat older route labels or old Slice-3 Candidate Workbench language as the target UX when they conflict with the Phase-16 freeze.

## 3. What is already complete

### Research/product engine

Slices 1–4 are complete and already expose the required research workflows:

```text
historical discovery
→ historical QAP evidence
→ forward validation
→ current-capital assessment
→ multi-asset portfolio research
→ durable operations / lineage
```

The seven admitted mutation commands are frozen:

```text
run_scan
generate_asset_momentum
freeze_forward_cohort
advance_forward_cohort
capture_public_evidence
qualify_candidate
run_basket
```

Phase 16 must not replace or generalize this surface merely for presentation convenience.

### UX investigation

M0 is complete.

The repository contains an actual route/task inventory, rendered cognitive walkthrough, task analysis, journey maps, user flows, heuristic findings, story map, terminology architecture, and future usability measures.

### Terminology / IA checkpoint

M1 is complete as a `single-stakeholder provisional` design freeze.

Primary navigation is frozen as:

```text
Home | Discover | Validate | Portfolios | Results | Activity
```

Implementation may proceed. Reopen these labels/groupings only if direct user observation later hits one of the explicit reopen triggers in the investigation document.

## 4. Frozen user mental model

The application is organized around goals, not backend subsystems.

```text
Home
  ├─ Find research ideas        → Discover
  ├─ Continue validation        → Validate
  ├─ Build/analyze portfolio    → Portfolios
  └─ Resume previous work       → Results / Activity
```

Task placement is frozen:

| User task | Primary destination |
|---|---|
| decide what to do / resume | Home |
| find a research idea | Discover |
| understand historical evidence | Discover |
| continue forward validation | Validate |
| update current market evidence | Validate |
| evaluate hypothetical capital | Validate |
| build/analyze portfolio | Portfolios |
| browse finished research | Results |
| inspect paper execution evidence | Results |
| track running/completed/failed work | Activity |

`Results` and `Activity` are intentionally different:

```text
Results  = scientific/economic evidence
Activity = operational execution state
```

Never infer research success from operation completion.

## 5. Frozen presentation vocabulary

Primary user-facing copy uses plain language first. Exact internal terms remain available under Advanced research / Exact evidence.

| Internal term | Primary presentation |
|---|---|
| candidate | Research idea |
| candidate trial | Evaluated rule |
| deep replay survivor | Passed historical research checks |
| deep replay rejected | Did not pass historical research checks |
| model source unavailable | Required model evidence unavailable |
| prospective cohort | Forward validation |
| freeze cohort | Start forward validation |
| advance cohort | Update forward evidence |
| checkpoint | Evidence update |
| capture public evidence | Update current market evidence |
| qualification | Current capital assessment |
| requested capital | Amount to evaluate |
| `research_only` | Research only |
| `small_capacity` | Smaller amount supported |
| `tradable_now` | Current evidence supports this amount |
| basket | Portfolio research |
| run basket through QAP | Analyze portfolio |
| operation | Activity / background task |
| experiment | Research result |
| forensic | Advanced research mode |

Whenever `tradable_now` is rendered in primary copy, pair it with:

> Research assessment only — QAP does not place or authorize live trades.

Never use `Buy`, `Trade`, `Approved`, `Safe to trade`, or equivalent live-authority language.

## 6. Non-negotiable architecture boundaries

Do not change these unless the user explicitly reopens the architecture:

- FastAPI/QAP artifacts remain authoritative for scientific/economic truth.
- React may present, sort, group, filter, scale, and visualize backend-produced values; it must not invent financial/research truth.
- No browser-side QAP, accounting, resolver, target allocation, qualification math, benchmark economics, or model fitting.
- Negative/rejected/invalid/incomplete/unavailable evidence remains visible.
- Operational state, evidence state, and research/economic conclusion remain separate dimensions.
- No fake progress percentages or ETAs.
- No invented product conversion/drop-off metrics.
- No auth/account/cloud/multi-user redesign.
- No live trading or exchange credentials.
- No new database, queue, scheduler, workflow engine, or server-side basket draft.
- No Material UI/Chakra/Bootstrap/Next.js/framework rewrite.
- Existing URLs may stay stable; route-path migration is not a goal.
- Existing specialist Experiment/Portfolio/Pair/Paper routes remain available.

The supported application remains local/single-operator/loopback-only with one active mutation at a time.

## 7. Progressive-disclosure contract

Every primary surface should converge on four layers:

```text
1. Goal / verdict
2. Contextual evidence
3. Advanced research controls/details
4. Exact audit / provenance
```

Examples of material that normally belongs in levels 3–4:

```text
candidate IDs
scan IDs
manual replay IDs
forensic mode
model/template/resolution
orientation
capture mechanics
venue symbols
q_safe_buy / q_safe_sell
checkpoint IDs
snapshot IDs
artifact fingerprints
raw enum/status names
```

Do not delete any of this evidence. Move it below the information required for the user's immediate decision.

## 8. Immediate next milestone — M2 Home + shell

### Existing code reality

Current `/` still renders `ExperimentList`:

```text
web/src/routes/index.tsx
```

Current primary navigation in:

```text
web/src/components/AppShell.tsx
```

is still:

```text
Discovery
Prospective
Baskets
Research runs
Operations
Paper operations
```

The existing TanStack query layer already provides:

```text
experiments()
operations()
forwardCohorts()
scans()
baskets()
```

in:

```text
web/src/api/queries.ts
```

M2 should reuse those existing reads. Do not add a Home API or new persistence merely to compose the start page.

### Smallest coherent M2 implementation

Create:

```text
web/src/features/home/HomeWorkspace.tsx
```

Modify:

```text
web/src/routes/index.tsx
web/src/components/AppShell.tsx
```

and shared styles/tokens only if the new shell genuinely needs them.

Recommended implementation shape:

1. Make `/` load the existing data required for orientation/resume:
   - finished/recent experiments;
   - operations;
   - forward validations.
2. Render four first-viewport goals:

```text
Find research ideas       → /scanner
Continue validation       → /prospective
Analyze a portfolio       → /baskets
Review prior results      → /experiments
```

3. Below those goals show only compact resume information:
   - at most one active mutation/background task with an Activity link;
   - forward validations that are available to resume;
   - a short list of recent finished research results.
4. Do not turn Home into an aggregate metrics dashboard.
5. Change visible primary navigation to:

```text
Home        → /
Discover    → /scanner
Validate    → /prospective
Portfolios  → /baskets
Results     → /experiments initially
Activity    → /operations
```

6. Remove `Paper operations` from primary navigation but preserve `/paper-operations/*` routes and contextual/deep access.
7. Preserve skip-link, keyboard, active-navigation, responsive, and accessible semantics already present in `AppShell`.

### Important route decision

Do **not** create `/results` or `/activity` only to make route paths match presentation labels.

Stable route paths are an explicit Phase-16 constraint.

For M2 use:

```text
Results  → existing /experiments
Activity → existing /operations
```

M6 may later create a dedicated Results entry composition only if existing evidence queries justify it. Do not pre-build M6 during M2.

### M2 acceptance

A first-time user should be able to answer:

```text
Where do I find new ideas?
Where do I continue an existing validation?
Where do I analyze a portfolio?
Where do I see finished work?
Where do I see a running task?
```

without knowing the words Scanner, Prospective Cohort, Experiment, Operation, or Paper Operation.

Do not advance into M3 until M2 is coherent and checkpointed.

## 9. Subsequent implementation order

Follow the plan sequentially:

```text
M2 Home + shell
    ↓
M3 Discover + Research Idea
    ↓
M4 Forward Validation + Current Capital Assessment
    ↓
M5 Portfolio builder + result
    ↓
M6 Results + Activity
    ↓
M7 visual-system convergence
    ↓
M8 human-centered + repository/browser closure
```

Do not jump directly to M7 visual polish. The hierarchy/terminology changes must land first so the visual system reinforces the correct mental model rather than polishing the old operator console.

## 10. M3 implementation guidance

Primary files:

```text
web/src/features/discovery/DiscoveryHome.tsx
web/src/features/discovery/ScanDetail.tsx
web/src/features/discovery/CandidateDetail.tsx
```

Required outcome:

- normal scan initiation asks primarily for analysis date + timeframe;
- manual pins, forensic mode, manual replay IDs, and protocol mechanics move behind Advanced research controls;
- all capabilities remain reachable;
- Scan Detail groups backend statuses into understandable sections before the complete ledger;
- the full trial denominator and negative evidence remain available under `All evaluated rules`;
- do not invent a frontend score/ranking;
- Candidate Detail becomes Research Idea detail in primary copy;
- historical verdict/control comparison comes before IDs/provenance;
- `Start forward validation` is the primary next action when allowed.

## 11. M4 implementation guidance

Primary files:

```text
web/src/features/prospective/ProspectiveHome.tsx
web/src/features/prospective/ProspectiveDetail.tsx
```

Required outcome:

- call these Forward Validations in the primary UX;
- visibly preserve the freeze/time boundary;
- do not present later evidence as simulated future data;
- do not let users choose arbitrary forward-test durations;
- staged flow becomes:

```text
Update forward evidence
→ ensure/update current market evidence
→ evaluate amount
```

- current capital assessment is a QAP classification, not a user approval/rejection decision;
- normal path should prefill/hide raw capture mechanics when authoritative read data already determines them;
- exact capture/checkpoint/q-safe/gate/snapshot details remain available below.

### M4 stop condition

If React cannot determine the appropriate existing finite capture action from authoritative read-model facts without inventing scientific/financial truth, stop M4 and propose the smallest backend composition owner.

Do not build a frontend capture oracle and do not add a generic job/capture endpoint.

## 12. M5 implementation guidance

Primary files:

```text
web/src/features/baskets/BasketHome.tsx
web/src/features/baskets/BasketDetail.tsx
web/src/features/baskets/BasketGraph.tsx  # only if actually needed
```

Required outcome:

- start from 3–6 assets/research ideas and available relationship evidence;
- source scan/horizon/resolution move to advanced context where they can be derived/constrained;
- relationship availability is understandable without candidate IDs;
- momentum remains contextual/pair-blind, not relationship evidence;
- pre-run view remains topology/evidence only;
- no resolver/target preview before QAP;
- primary action becomes `Analyze portfolio`;
- completed result leads with economic/research verdict and benchmarks;
- negative completed research is not styled as an operational failure.

## 13. M6 implementation guidance

Primary files:

```text
web/src/features/operations/OperationList.tsx
web/src/features/operations/OperationDetail.tsx
web/src/features/operations/presentation.ts
existing Experiment/Portfolio/Pair/Paper entry points as needed
```

Required outcome:

- rename primary Operations experience to Activity;
- preserve exact operation kind/request metadata in detail;
- keep explicit `operational failure != scientific failure` language;
- create the Results entry experience from existing evidence queries;
- no new result database/index unless existing APIs demonstrably cannot support it;
- Paper Operations becomes secondary `Paper execution evidence` under Results/contextual navigation;
- preserve all deep lineage.

## 14. M7 implementation guidance

Only after M2–M6 stabilize the information hierarchy:

- converge visual tokens and surface hierarchy;
- distinguish operational/evidence/research state treatments;
- human-readable value first, exact ID/value on demand;
- use motion only when it explains state/evidence transition;
- preserve reduced-motion/accessibility;
- invest strongest coordinated visual treatment in Basket/Portfolio evidence after authority boundaries are already correct.

Do not introduce a design-system/component-framework rewrite.

## 15. M8 closure guidance

The Phase-16 plan explicitly requires preservation of the existing executable/browser acceptance contract.

At closure, verify the four canonical journeys from the investigation:

```text
Find and understand a research idea
Validate an idea over time/current evidence
Build and understand a portfolio
Resume/audit previous work
```

The final walkthrough must demonstrate that a novice can distinguish:

```text
operational failure vs research rejection
historical evidence vs later forward evidence vs current evidence
research-only / limited-capacity / current-evidence-supported states
finished Results vs background Activity
```

and that no wording implies live trading authority.

Automated work should protect meaningful semantic/interaction regressions. Do not create a broad screenshot/CSS-copy test suite; ordinary visual polish belongs in rendered QA.

## 16. Agent execution protocol

For implementation work on the connected WSL/Linux repository:

1. Before the first source-code mutation, load and follow:
   - `causal-coding`;
   - `ponytail`;
   - `mcp-harness-router`.
2. Inspect current `HEAD` and dirty state before assuming this handoff is still exact.
3. Preserve legitimate changes from other agents/users. Do not reset, overwrite, or attribute them to this mission.
4. Treat the Phase-16 investigation and M1 terminology/IA freeze as authoritative. Do not spend another implementation session redesigning the navigation or vocabulary without new contradictory evidence.
5. Trace the existing owner before changing code. Prefer the smallest composition change over new layers.
6. Reuse existing routes, TanStack queries, API DTOs, shared components, styles, and evidence views before creating abstractions.
7. Keep each milestone coherent and checkpoint it before starting the next one.
8. If an implementation fact refutes an assumption, update the plan/evidence and make the smallest contract-safe correction; do not silently work around it.
9. Do not broaden the mission into backend research changes unless a documented Phase-16 boundary checkpoint actually fires.
10. Stop at M8 closure. Do not invent a Phase 17 automatically.

## 17. What the next agent must not do

Do not:

- re-run a broad UX discovery exercise before M2;
- reopen `Home / Discover / Validate / Portfolios / Results / Activity` because another label feels nicer;
- make `tradable_now` look like trade authorization;
- hide rejected/invalid/unavailable evidence;
- collapse freeze and later evidence into one wizard;
- turn qualification into a user accept/reject action;
- fake progress percentages;
- invent frontend research scores;
- preview basket resolver targets before QAP;
- add a generic capture/job API;
- move research truth into React;
- rename backend enums for presentation convenience;
- rewrite the frontend stack;
- introduce route migrations without a demonstrated navigation requirement;
- polish the whole visual system before M2–M6 information hierarchy is correct.

## 18. Copy-paste mission for a fresh agent

Use the following as the starting mission:

> Work in `/home/hamza/repo/qap` on `main`. Start by checking current HEAD/working-tree state and preserve any legitimate concurrent changes. Read `docs/research/2026-08-19-qap-phase16-implementation-handoff.md`, `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`, and `docs/plans/16-human-centered-workbench-ux-rearchitecture.md`. Phase 16 M0 and M1 are complete; the IA `Home / Discover / Validate / Portfolios / Results / Activity` and terminology contract are frozen as the current provisional baseline. Do not redo UX discovery or reopen those decisions without contradictory user evidence. Before source mutation invoke Causal Coding, Ponytail, and MCP Harness Router. Implement Phase 16 sequentially starting at M2 Home + shell, using existing React/TanStack/FastAPI contracts and stable routes, preserving all scientific/economic authority and negative evidence. Checkpoint each milestone before proceeding. Only consider a backend composition change if the explicit M4 current-evidence capture boundary fails. Continue through M8 closure, then stop; do not invent new product scope.

## 19. One-screen status summary

```text
Research engine / Slices 1–4     ✅ complete
Phase 16 M0 UX investigation     ✅ complete
Phase 16 M1 IA/terminology       ✅ frozen provisional baseline

NEXT
Phase 16 M2 Home + shell

THEN
M3 Discover + Research Idea
M4 Forward Validation + Capital
M5 Portfolio builder + result
M6 Results + Activity
M7 visual-system convergence
M8 human-centered closure

PRIMARY IA
Home | Discover | Validate | Portfolios | Results | Activity

CORE RULE
Simplify presentation, not research truth.
```
