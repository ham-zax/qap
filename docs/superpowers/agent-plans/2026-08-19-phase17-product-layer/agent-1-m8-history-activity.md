# Agent 1 — Phase 17 M8-A History + Utility Activity Convergence

**Repository:** `/home/hamza/repo/qap`

**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m8-history`

**Branch:** `phase17-m8-history`

**Coordination base:** assigned by Wave-10 coordination commit

## Mission

Complete the History + utility Activity half of M8 without changing portfolio/scanner economics or the M8-0 basket source contract.

M8-0 is already integrated and gives Product baskets claim-aware source provenance plus immutable physical execution-generation bindings. M6 is already the authoritative longitudinal Research Idea composer. Reuse those truths; do not reconstruct them independently in React.

## Own

### 1. Backend-composed longitudinal History read

Provide the smallest backend-owned read/composition needed for History to present completed Product research as longitudinal Research Ideas rather than a disconnected scan + forward-validation ledger.

The History composition must preserve, from existing immutable owners:

- source research generation / scan identity;
- research claim kind and label;
- frozen data boundary (`Data through` for Product; historical cutoff for PIT where appropriate);
- historical Research Ideas / candidate identities;
- M6 historical replay state;
- M6 later evidence state;
- new-freeze / reselection lineage where useful for navigation;
- latest persisted current-capacity assessment and its exact `as_of`;
- portfolio/basket membership from persisted basket artifacts;
- exact specialist links for audit.

Prefer reuse of `research_idea_longitudinal()` or a narrowly extracted adjacent composition helper. Do not copy its state rules into React.

If an existing read endpoint can be extended cleanly, do that. Otherwise add one bounded History read contract. Do not create a History database or mutable History store.

### 2. History UX convergence

Update the primary `/experiments` History experience so normal Product users see the lifecycle approximately as:

```text
Research generation
  -> Research Ideas
      -> historical replay evidence
      -> later prospective evidence
      -> latest time-specific current assessment
      -> portfolio research membership
```

Forward cohorts remain exact specialist evidence under `/prospective/...`, but should no longer be presented as though "Validate" were a separate primary Product object when the evidence belongs to a Research Idea.

Specialist/uncomposable forward evidence may remain in a clearly secondary specialist section rather than being discarded.

History must preserve these distinctions:

```text
operator asset approval
market/data readiness
historical relationship evidence
historical economic replay
later prospective evidence
current capacity evidence
portfolio expression
```

Do not stamp today's mutable Product admission/readiness onto an old historical record.

Persisted qualification records are historical evidence only at their explicit `as_of`.

### 3. History portfolio/result composition

Consume the M8-0 claim-aware basket read contract when presenting portfolio research. History may show:

- source research claim;
- selected assets;
- basket result state;
- QAP result link.

Do not derive basket provenance or source claim in React.

Prefer higher-level ownership to duplicate raw QAP-run clutter. QAP runs already referenced by Research Ideas or baskets should primarily appear through those higher-level objects. Any remaining exact/unowned research runs may stay in a specialist/other section.

Paper operational evidence remains a separate evidence class and must not become scientific support.

### 4. Utility Activity affordance

Keep `Activity` out of primary navigation.

Home already surfaces a running background operation. Add the smallest truthful affordance so that, when nothing is running but the latest meaningful operation is `failed` or `interrupted`, Home can surface a small "Background task needs attention" state linking to Activity.

Do not make an operational failure a research verdict.

Do not force M7's long-lived collector into fake `OperationDto` records. Collector health remains Product maintenance/current-evidence context.

## Do not own

Do not modify:

- basket scientific protocol/source admission/replay/recovery;
- Product basket immutable generation binding;
- manual 3–6 asset construction semantics;
- exact-edge selection semantics;
- graph resolver targets;
- portfolio economic gates, HODL/control definitions, costs, accounting;
- M8-B BasketHome/BasketDetail/Portfolio presentation except unavoidable shared generated types from a genuinely necessary History API change;
- M7 collector/qualification policy;
- M9 launcher/process lifecycle hardening;
- M10 user study execution.

Do not add a generic timeline/workflow framework.

## Authority rules

- M6 backend composition owns longitudinal evidence-layer state.
- M8-0 basket read contract owns basket claim/provenance.
- immutable scanner/prospective/qualification/basket/QAP artifacts remain authority.
- React may translate authoritative enums/states into plain language, not derive new scientific classifications.

## Verification

Testing remains opt-in. Do not create, modify, or run tests unless separately authorized or independently mandatory.

Use direct deterministic non-test evidence for the History composer and the smallest final static/build checks relevant to changed files. If a rendered browser walkthrough is useful, keep it bounded to the changed History/Home states.

At minimum verify:

- Product Research Idea History shows historical/later/latest-assessment layers without React recomputation;
- reselection remains attached to the active evidence stream;
- a later negative/unavailable state does not rewrite historical replay state;
- persisted current assessment retains exact `as_of`;
- basket membership/source claim comes from backend basket truth;
- uncomposable specialist forward evidence remains reachable;
- failed/interrupted operation on Home is operational attention, not negative research;
- Activity remains utility navigation;
- no basket science/economics files changed.

## Completion report

Return:

1. status;
2. branch/worktree/commit/final Git state;
3. exact History backend/read contract added or reused;
4. longitudinal History composition semantics;
5. specialist forward evidence behavior;
6. portfolio/QAP/paper History ownership behavior;
7. Home/Activity change;
8. checks actually run;
9. M9/M10 handoff, risks, and deliberate non-scope.
