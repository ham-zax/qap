# Agent 1 — M6 Longitudinal Research Idea / Evidence Layers / All-Survivor Follow-Up

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m6-research-idea`
**Branch:** `phase17-m6-research-idea`
**Can start:** after the Wave-7 coordination base is committed and the worktree is created
**Depends on:** M5 integrated at `6b40028`
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless unless a genuinely interactive verification requires presentation

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M6 is authoritative
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m5-research-experience.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m6-reconnaissance.md`

Inspect the integrated M5 claim-aware scan/candidate reads and the existing prospective/qualification owners before choosing implementation details.

## Objective

Implement M6 so one historical Research Idea becomes a truthful longitudinal Product object without creating a second scientific state model.

Compose existing immutable evidence into one user-facing lineage:

```text
Historical discovery / relationship evidence
        ↓
Historical economic replay evidence
        ↓
All-survivor prospective follow-up
        ↓
Later forward evidence
        ↓
Current public-market / capacity evidence
```

A later weak/negative/unavailable result must identify **which evidence layer changed** and must never rewrite an earlier valid historical claim.

## Critical reconnaissance result

Current-approved Product scans are already scientifically compatible with the existing prospective chain.

Do **not** redesign or weaken:

- strict historical Scanner-V1;
- `PROSPECTIVE_V1`;
- forward horizon rules;
- normalization;
- cost policy;
- primary-control semantics;
- qualification authority.

The M4 Product scanner changes its claim/protocol identity while retaining the scientific/economic primitives used by the prospective system. Existing freeze/forward/qualification code does not reject the Product scanner identity.

M6 is therefore a **Product composition/read/action mission**, not a scientific compatibility migration.

## Required longitudinal read composition

Prefer a read-only Research Idea projection keyed by the existing immutable historical identity:

```text
scan_id + candidate_id
```

Do not mint a new durable global `ResearchIdea` entity and do not copy authoritative scientific artifacts into new mutable storage.

The projection should compose references/statuses equivalent to:

```text
historical
  source scan
  candidate
  M5 claim type/label
  timeframe/pair/rule
  discovery status
  historical replay status
  deep_replay_run_id

follow_up
  not_started | waiting | accumulating | supported | not_supported | unavailable
  cohort memberships
  membership kind: new_freeze | reselection
  active freeze identity
  forward start/end
  checkpoints/outcomes

current evidence
  persisted qualification assessments
  assessment as_of

portfolio expression
  existing basket references only
```

This is a presentation/read composition. Existing scanner/prospective/QAP/qualification artifacts remain authoritative.

### Reselection is mandatory

The current `ForwardCohortDetailDto.freezes` exposes only new candidate freezes. Existing prospective semantics can instead record a `ReselectionRecord` that points a newly selected candidate at an already-active freeze.

A valid cohort can therefore have active automatic members while `candidate_freezes` is empty.

M6 must expose/resolve reselection lineage so the Product does not falsely say an idea has no follow-up.

At minimum preserve:

```text
new candidate_id
source_scan_id
active_freeze_id
reselected_at
automatic/manual attribution
```

and resolve the active evidence stream owning that freeze.

## Evidence-layer semantics

Use existing authoritative artifacts and return presentation-safe layer state from the backend. React must not independently reconstruct scientific verdicts from raw booleans.

### Historical discovery

May say that the frozen discovery process retained/evaluated a historical relationship/rule.

Must not imply:

- cointegration;
- causality;
- profitability;
- future persistence;
- current capacity;
- live tradability.

### Historical economic replay

Use existing deep-replay states:

```text
deep_replay_survivor
deep_replay_rejected
setup/replay unavailable
```

A survivor means the exact historical implementation passed the declared QAP-vs-HODL and primary-control checks. It does not establish later persistence or current capacity.

### Later forward evidence

Compose existing checkpoint/outcome truth without changing prospective rules.

Presentation states may be equivalent to:

```text
not_started
waiting_for_later_evidence
later_evidence_accumulating
later_evidence_supported
later_evidence_not_supported
later_evidence_unavailable
```

Rules:

- no checkpoint: follow-up exists, but no genuinely later evidence was evaluated;
- partial: evidence is accumulating; not a final verdict;
- matured + required existing gates pass: later evidence supported the idea under the declared prospective checks;
- matured + gates fail: later evidence did not support the original idea under the declared checks;
- invalid: required later evidence was unavailable.

A later negative must **not** be phrased as if the earlier historical evidence was retroactively false.

### Current public-market / capacity evidence

Persisted qualifications are time-specific assessments. Show their `as_of` boundary.

Do not infer current readiness from an old qualification.

Safe Product translations remain conceptually:

```text
research_only  -> Research only
small_capacity -> A smaller amount is supported by the current evidence
tradable_now   -> Current research evidence supports this hypothetical amount
```

Always preserve the existing no-live-authority statement.

M7, not M6, owns automatic/persistent current-evidence accumulation and current readiness.

## Product all-survivor follow-up action

Normal Product follow-up is generation/horizon-wide, never a single-candidate scientific mutation.

Reuse the existing scientific mutation:

```text
OperationKind.FREEZE_FORWARD_COHORT
```

Do not add an eighth scientific operation kind.

Add the smallest Product wrapper/action boundary needed so a normal Product user can start follow-up without entering raw `freeze_at`.

The backend should:

1. accept the completed Product research generation/reference rather than a candidate-specific scientific claim;
2. verify it is an appropriate completed Product scan;
3. infer its single Product horizon;
4. verify historical Research Ideas/survivors exist;
5. stamp the freeze boundary at backend request acceptance;
6. submit the existing all-survivor freeze operation.

If follow-up for that generation/horizon already exists, Product state should prefer **View follow-up** rather than presenting a misleading duplicate Start action.

Keep the existing advanced `/api/forward/cohorts` endpoint and strict/manual freeze controls unchanged.

### UX wording

Primary completed-Research action should be equivalent to:

> Start follow-up for all N Research Ideas

Explain:

> QAP follows all ideas that passed the historical checks so later results are not cherry-picked after the fact.

On an individual Research Idea page, make the generation-wide scope explicit.

For a reselection, explain that QAP linked the new historical selection to the already-active frozen evidence stream rather than starting an overlapping prospective experiment.

## Frontend/product composition

Build on M5's claim-aware Research result and Research Idea pages.

Normal Product user should experience later/current evidence as sections of the same Research Idea rather than being sent through `Validate` as a separate mental model.

Existing specialist URLs may remain stable:

```text
/prospective
/prospective/$cohortId
/candidate/$scanId/$candidateId
```

Do not delete them. They remain useful for specialist/audit navigation.

Where M5 already removed Validate from primary navigation, preserve that IA.

## API/public contract

Add only the smallest read/action DTOs needed for the longitudinal Product composition.

Prefer extending a narrowly adjacent existing read owner rather than creating a generic workflow/timeline subsystem.

Generated OpenAPI/client contracts must stay synchronized if public endpoints/DTOs change.

## Acceptance

M6 is complete when all of the following are established:

1. A Product historical survivor can be viewed as one claim-aware longitudinal Research Idea.
2. Existing historical evidence is preserved unchanged when later/current evidence is added.
3. Later forward state distinguishes not-started/waiting/partial/matured-supported/matured-not-supported/unavailable semantics without changing `PROSPECTIVE_V1`.
4. Product read composition resolves both new freezes and `ReselectionRecord` membership correctly.
5. A valid reselection-only cohort is not presented as zero Research Ideas.
6. Product current-approved scans can initiate follow-up through a backend-authorized generation-wide wrapper that reuses `FREEZE_FORWARD_COHORT`.
7. The normal Product user does not enter `freeze_at`.
8. The follow-up action explains all-survivor anti-cherry-picking semantics.
9. Existing strict/advanced freeze endpoint remains available and unchanged in scientific meaning.
10. Persisted current-capital assessments are shown as time-specific evidence, not falsely treated as continuously current readiness.
11. `research_only`, `small_capacity`, and `tradable_now` remain research/capacity evidence states and do not become live-trading authority.
12. No persistent M7 collector, Product basket compatibility repair, new scientific protocol, or generic workflow engine is absorbed.

Inspect representative states covering at least:

```text
Product Research Idea with no follow-up
follow-up started but no checkpoint
partial later evidence
matured supported later evidence
matured not-supported later evidence
invalid/unavailable later evidence
reselection membership into an active freeze
historical qualification displayed with its assessment time
Product result with existing follow-up -> View follow-up
strict PIT candidate remains on existing advanced semantics
```

Do not fabricate representative-user usability metrics; M10 owns final comprehension closure.

## Verification intent

Testing remains opt-in. Do not create, modify, or run tests unless explicitly authorized or independently mandatory.

Use direct non-test evidence and the smallest relevant final checks, for example:

- isolated read-model evidence proving new-freeze and reselection membership composition;
- direct Product all-survivor wrapper evidence showing backend-stamped freeze time and existing operation reuse;
- persisted evidence-layer examples for partial/matured/invalid outcomes;
- fresh OpenAPI/generated-client synchronization if public contracts change;
- focused Ruff/format/Pyright for changed Python;
- TypeScript typecheck/Vite build for changed frontend;
- rendered browser walkthrough for representative M6 states;
- `git diff --check` and complete diff inspection.

## Out of scope / stop conditions

Stop rather than expanding M6 if the work begins to require:

- changing Scanner-V1 economics or strict PIT identity;
- changing `PROSPECTIVE_V1` scientific rules;
- changing qualification scientific authority;
- creating global durable Research Idea storage;
- duplicating scanner/prospective/qualification artifacts into a new state database;
- implementing persistent capture scheduling/14-day accumulation;
- repairing Product basket compatibility or the old-scan/current-catalog basket coupling;
- adding a generic timeline/workflow framework;
- adding CCXT, resampling, private exchange authority, or live-capital authority.

If a future Product protocol changes horizon windows, normalization, primary control, or cost semantics, stop and return to design/versioning review rather than assuming prospective compatibility from Product V1.

## M7 handoff

M7 should receive the exact active Research Idea / frozen-instrument lineage needed to feed existing current-capture readiness and qualification owners. M7 must resolve instruments from frozen QAP lineage, not pair text or ticker equality.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final clean Git state;
3. exact longitudinal Research Idea read/API composition;
4. exact Product all-survivor follow-up wrapper behavior and operation reuse;
5. reselection handling and active-freeze resolution;
6. evidence-layer semantics for historical/later/current states;
7. resulting Product UI/IA behavior and specialist-route preservation;
8. checks actually run and why;
9. M7 handoff notes, deferred basket compatibility, unresolved risks, and deliberate deviations.
