# Agent 1 — M5 Self-Explanatory Research / Truthful Funnel / Primary IA

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m5-research-experience`
**Branch:** `phase17-m5-research-experience`
**Can start:** after the Wave-6 coordination base is committed and the worktree is created
**Depends on:** M4 integrated through `c3c81ca`
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless unless a genuinely interactive verification requires presentation

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M5 is authoritative
- `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m4-current-approved-readiness.md`

Inspect the integrated M4 public contract and current Phase-16 shell before choosing implementation details. Do not assume the old `Discover / Validate / Results / Activity` presentation remains primary.

## Objective

Implement M5 end-to-end so the normal Product experience is understandable to a non-expert while remaining faithful to current QAP authority.

The primary visible mental model becomes:

```text
Home | Research | Portfolios | History
```

Normal Local Market Research must show:

1. what approved/current scope is ready for the selected timeframe;
2. why anything is excluded;
3. the backend-owned safe cutoff;
4. one normal timeframe choice;
5. one primary action: **Find research ideas**;
6. truthful task state while research is running;
7. backend-composed completed research-stage counts after publication;
8. Research Ideas and negative/unavailable evidence with claim-aware wording;
9. deeper IDs/protocol/lineage only under progressive disclosure.

The existing strict historical PIT flow remains available as Advanced Research and continues to require explicit `as_of` and its existing advanced controls.

## Current authoritative inputs

### M4 Product research

Use the integrated M4 endpoints and generated types as the sole normal-path readiness/launch authority:

```text
GET  /api/product-research/readiness?horizon=short|medium|swing
POST /api/product-research
```

Normal launch payload is only:

```text
horizon
readiness_id
```

Do not calculate readiness, safe cutoff, current-approved eligibility, direct-market readiness, or `as_of` in React.

### M3 Product market data

Use the existing Product market-data API for preparation/refresh only when the backend says that action is valid. Do not parse market-data generations in React to decide scientific readiness.

### Completed scanner evidence

`ScannerArtifactReader` already owns the immutable completed scanner tables and is the correct owner for M5's completed discovery-stage summary.

## Required backend read work

M5 needs the smallest backend additions that keep presentation semantics out of React.

### 1. Completed research-stage summary

Extend the existing completed scan read boundary, preferably `ScanDetailDto`/`ScannerArtifactReader`, with a backend-composed stage summary derived from already-published immutable scanner tables.

At minimum expose truthful values equivalent to:

```text
relationship_comparison_count
retained_relationship_count
enumerated_rule_count
valid_rule_count
invalid_rule_count
selected_for_replay_count
completed_replay_count
replay_unavailable_count
rejected_replay_count
research_idea_count
```

Preserve venue/horizon scope when aggregation would change meaning. Binance/Gate counts are venue-local unless a backend economic-pair deduplication contract already exists; do not invent one.

Important: current `candidate_count == len(scout_trials)` means fixed rule/trial rows, **not relationships**. Do not present it as a shrinking conversion funnel.

### 2. Claim-aware completed scan reads

M4 seals optional `research_claim_identity` and `research_scope_identity` into Product `ScanDefinition` while strict definitions omit them.

Expose the smallest claim-aware completed-scan read shape needed for M5 to distinguish:

- Product current-approved/current-survivor retrospective research;
- strict historical point-in-time research.

Primary UI needs a human-understandable claim type/label. Exact identities remain audit detail. Do not add a generic claim registry if a small current mapping is sufficient.

### 3. Backend-authorized mutation actions

The normal UI must not infer which mutations are allowed by reconstructing a workflow from raw reason strings.

Reuse M4/M3 state and add only the smallest typed read capability needed to authorize Product mutations such as:

```text
manage_universe
prepare_market_data
refresh_market_data
find_research_ideas
```

Pure navigation to already-existing immutable objects may remain ordinary UI navigation. Do not build a generic workflow/state-machine engine.

If the integrated M4 DTO already supplies enough typed authority to avoid frontend inference, do not add another layer.

## Required frontend/product work

### Primary shell

Change visible primary navigation to:

```text
Home | Research | Portfolios | History
```

- `/scanner` may remain the Research route.
- `/baskets` remains Portfolios.
- `/experiments` may be reused/relabelled as the initial History route.
- `/operations` remains available as a utility/contextual Activity destination rather than an equal-weight primary destination.
- `/prospective` remains a specialist/contextual route until M6.
- Existing specialist URLs do not need wholesale migration merely to change labels/IA.

Preserve the accessible shell, skip link, workspace markers, and route stability.

### Home

Keep Home as setup/resume, not a metrics dashboard. Replace coarse catalog-presence research guidance with M4 truth wherever normal Local Market research readiness is involved.

### Research normal flow

For Local Market `/scanner`, present normal Research in this order:

```text
What QAP will research
Data readiness / exclusions / data-through cutoff
One timeframe: Short-term | Medium-term | Longer-term
Find research ideas
Running/completed state
Completed research-stage summary
Research Ideas / negative evidence
Research details
```

Normal timeframe selection is one choice at a time.

Normal copy must explain the Product claim without pretending it is PIT research, e.g. current approved/currently available assets using admitted historical data through the displayed cutoff. Explicitly avoid implying today's full scope existed throughout the historical window.

### Advanced Research

Reuse the existing strict `DiscoveryHome` controls as Advanced Research rather than deleting them:

- explicit `as_of`;
- multiple horizons;
- manual pins;
- forensic mode;
- manual replay IDs;
- strict scanner protocol details.

Do not weaken or silently route these controls through the Product current-approved policy.

### Running state

Current authoritative operation state is only:

```text
running | completed | failed | interrupted
```

There is no durable intra-scan stage-progress contract. While running, show truthful task state and a link to Activity. Do **not** manufacture percentages, ETAs, or temporary stage counts.

### Completed result

Render the immutable completed scan, not the user's later current workspace state.

Lead with:

1. claim/timeframe/data-through boundary;
2. plain-language outcome;
3. backend-composed stage counts;
4. Research Ideas and valid negative/unavailable evidence;
5. limitations;
6. full ledger/IDs/protocol/lineage under disclosure.

Existing `ScanDetail` and `CandidateDetail` must become claim-aware. Product scans must not be labelled `PIT scope`, `PIT-admitted assets`, or `Point-in-time universe`.

The relationship graph may say paths were comparable/retained by the frozen SSD neighborhood search; it must not claim cointegration, causality, profitability, tradability, or future persistence.

A deep historical replay survivor passed the declared historical QAP/HODL/control gates. It is still not confirmed alpha, current capacity, live tradability, or authorization to trade.

### Follow-up wording boundary

The existing forward-freeze mutation is scan/horizon-wide and freezes all surviving ideas, not one candidate.

If a follow-up action is shown for a strict scan, label it truthfully as an all-survivor action. For current-approved Product scans, do **not** expose a follow-up mutation unless the backend already supports that claim; M6 owns compatibility and the longitudinal lifecycle.

### Sample Workspace

Keep the persistent Sample Workspace marker. Do not present Sample evidence as the user's Local Market current-approved state.

## Client/public contract synchronization

Wire the handwritten API client/query layer to the integrated M3/M4 generated contracts needed by M5. Keep generated OpenAPI/types synchronized with any bounded backend read additions.

Do not move scientific/readiness calculations into TypeScript merely because generated schemas are available.

## Acceptance

M5 is complete when all of the following are established:

1. Visible primary navigation is `Home | Research | Portfolios | History`; Activity is utility/contextual.
2. Normal Local Market Research consumes M4 readiness and launches with `horizon + readiness_id`; it has no primary user-entered `as_of`.
3. One timeframe is selected at a time in the normal flow.
4. Missing identity/current market/history/maintenance/direct-market state is presented from backend-owned reasons without being confused with scientific rejection.
5. Running research shows only authoritative operation lifecycle; no fake progress/ETA exists.
6. Completed Product scans are claim-aware and contain no false PIT wording.
7. Completed research-stage counts are backend-composed from immutable scanner artifacts; React does not reconstruct scientific funnel math.
8. Stage wording preserves the difference between relationship comparison, fixed-rule evaluation, promotion, replay unavailable, replay rejection, and Research Idea survival.
9. Normal mutation actions are backend-authorized rather than inferred from raw metrics/reason strings.
10. Strict historical PIT research remains available under Advanced Research with existing explicit controls.
11. Home uses Product truth for normal research setup/resume rather than catalog-file heuristics where M4 truth is available.
12. `/experiments` is reused as initial History rather than creating a second historical archive.
13. Specialist routes remain reachable and no M6/M7/M8 authority is absorbed.
14. Sample versus Local Market remains explicit.

Before calling the UI complete, inspect representative rendered states for at least:

```text
Sample Workspace
Local Market with no approved/ready scope
identity/current-market exclusion
history missing/insufficient
ready with safe cutoff
research running
completed valid negative
completed with Research Ideas
replay/direct evidence unavailable
task failed/interrupted
```

This may be a developer/cognitive walkthrough. Do not fabricate representative-user success metrics; M10 owns final representative-user comprehension closure.

## Verification intent

Testing remains opt-in. Do not create, modify, or run tests unless explicitly authorized or independently mandatory.

Use direct non-test evidence and the smallest relevant final checks, for example:

- isolated API/read-model evidence for claim/stage/action DTOs;
- fresh OpenAPI + generated-client consistency if the contract changes;
- focused Ruff/format/Pyright for changed Python;
- TypeScript typecheck/Vite production build for changed frontend;
- rendered browser inspection for the representative M5 states;
- `git diff --check` and complete diff inspection.

Do not use fake stage progress as verification data.

## Out of scope

- full M6 longitudinal Research Idea composition;
- changing prospective scientific rules;
- persistent M7 public-evidence collection;
- M8 portfolio/history economics redesign;
- current-approved basket convergence or the deferred old-scan/current-catalog basket issue;
- CCXT, resampling, live/private exchange authority;
- generic workflow/state-machine framework;
- legacy cointegration/correlation labels or thresholds;
- route churn solely for naming consistency.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final clean Git state;
3. resulting primary IA and normal-vs-Advanced Research flow;
4. exact backend stage-summary/claim/action contracts added or reused;
5. exact M4 readiness/launch integration behavior;
6. completed-result and Research Idea semantics, including negative/unavailable states;
7. checks actually run and why;
8. M6 handoff notes, unresolved risks, and any deliberate deviations.
