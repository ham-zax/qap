# Agent 2 — M6 Longitudinal Research Idea / Evidence-Layer Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Can start:** after the Wave-6 coordination base is committed
**Depends on:** M4 integrated through `c3c81ca`; executable M5 runs concurrently in an isolated worktree
**Execution lifetime:** persistent-agent-loop required for continuity
**Developer visibility:** headless

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m5-research-experience.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M6 is authoritative
- `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`

Inspect stable `main`; do not inspect or mutate Agent 1's active M5 worktree.

## Objective

Produce the bounded repository-grounded reconnaissance required to implement M6 immediately after M5 integration.

M6 must make later evidence feel like the evolution of one Research Idea while preserving the exact authority and chronology of distinct evidence layers:

```text
original historical evidence
later forward evidence
current public-market evidence/readiness
hypothetical-capital assessment
```

A later weakening/failure must identify the affected evidence layer and must not rewrite an earlier valid historical conclusion.

The normal follow-up action must preserve the existing anti-cherry-picking rule: all surviving ideas from the relevant research generation/horizon are followed together.

This mission is read-only. Do not implement M6.

## Investigation ownership

Map the exact current owners/callers for:

- completed scan/candidate historical evidence and economic replay status;
- `freeze_completed_scan()` and all-survivor cohort creation;
- current protocol/claim checks that may reject the newly integrated M4 current-approved Product scans;
- forward cohort/checkpoint/outcome artifact ownership;
- current public-evidence readiness and qualification ownership;
- requested-capital/current-state QAP results;
- candidate/forward/qualification API read models and current React routes;
- evidence lineage IDs that can compose one longitudinal Research Idea without copying scientific state;
- where `Validate` can cease being a primary mental-model destination while specialist `/prospective` routes remain stable;
- exactly what M6 must consume from M5's claim-aware Research result and Research Idea cards.

## Highest-priority compatibility question

M4 intentionally left downstream follow-on compatibility unresolved. Current helpers may still require strict `scanner-v1-s1` identity or current-catalog assumptions.

Determine precisely whether a current-approved Product survivor can today:

```text
completed Product scan
    -> freeze all survivors for one horizon
    -> prospective checkpoints
    -> current evidence readiness
    -> qualification at a hypothetical amount
```

If not, identify the smallest scientific-boundary-safe compatibility seam M6 must add.

Do not weaken strict historical PIT checks globally. Product follow-up must preserve the original Product scan's claim/scope identity and exact historical evidence rather than relabelling it as strict PIT research.

Also separate the previously deferred old-scan/current-catalog basket coupling from M6 unless it is actually required for longitudinal Idea follow-up.

## Evidence-layer map the report must produce

For each existing artifact/read model, identify which layer it can truthfully support and what it cannot conclude.

At minimum cover distinctions equivalent to:

### Historical relationship/discovery evidence

Can support the frozen graph/scout relationship/rule evidence.
Cannot by itself claim economic success, forward persistence, current capacity, or live authority.

### Historical economic/replay evidence

Can support whether the exact implementation survived declared QAP-vs-HODL and primary-control checks.
Cannot claim future performance/current tradability.

### Later forward evidence

Can support prospective checkpoint/outcome state after freeze.
Must never be used to rewrite the earlier historical result.

### Current public-market/capacity evidence

Can support capture readiness, current state, and requested-capital qualification according to the existing backend contract.
Cannot authorize a live trade.

### Portfolio-expression evidence

Identify where basket/portfolio evidence belongs in the chronology, but do not pull M8 Portfolio convergence into M6.

The report should recommend plain-language backend-derived status semantics such as:

```text
historical evidence supported the idea
later evidence weakened the idea
current market evidence is incomplete
this amount is not supported by current evidence
```

without inventing a new scientific verdict layer.

## All-survivor follow-up

Confirm the exact existing invariant around cohort creation:

- which promotions/survivors are enrolled;
- whether automatic and manual survivors are both included;
- what horizon/scan identity binds the cohort;
- how duplicate/repeated freeze attempts are handled;
- whether a candidate-level UI can safely invoke the same scan/horizon-wide action;
- what wording best exposes the anti-cherry-picking reason without changing backend semantics.

The intended Product explanation is conceptually:

> QAP follows all ideas that passed the historical checks so later results are not cherry-picked after the fact.

## M6 Product/read-model questions

Determine the smallest read composition M6 needs to make one longitudinal Research Idea page answer:

```text
What was originally researched?
What survived historically?
What happened later?
What current evidence exists or is missing?
What amount was evaluated, if any?
Which evidence layer weakened/failed?
What remains uncertain?
What valid next action exists?
```

Prefer composition over duplicated artifact storage. Immutable scientific artifacts remain authoritative.

Identify whether M6 needs:

- a new Product Research Idea read model joining existing IDs;
- a small extension to existing candidate/forward DTOs;
- or only frontend composition over already-typed backend reads.

Do not create a generic timeline/workflow engine.

## M5 handoff assumptions to verify after integration

Executable M5 is expected to provide:

- claim-aware completed Research results;
- stable Research Idea cards;
- truthful completed-stage summary;
- Product-vs-PIT wording;
- backend-authorized current actions;
- specialist forward routes still available underneath.

Because M5 is concurrent, do not assume its exact final DTO names. Focus on the semantic seam M6 will require and report what must be rechecked after M5 lands.

## Success conditions

The report is complete when it provides:

1. an exact owner/caller map for historical candidate/replay, freeze, forward checkpoint, current evidence readiness, qualification, and relevant API/UI reads;
2. a definitive answer on current-approved Product scan compatibility with all-survivor follow-up;
3. the smallest required M6 compatibility repair if Product scans cannot currently freeze/follow safely;
4. a falsifiable evidence-layer taxonomy tied to existing authoritative artifacts;
5. a proposed longitudinal Research Idea read composition with IDs/lineage and no duplicated scientific truth;
6. exact all-survivor semantics and user-facing action wording implications;
7. a recommendation for how `/prospective`/Validate becomes contextual without deleting specialist routes;
8. the M6 -> M7 handoff boundary for persistent current-evidence collection;
9. a one-writer vs justified parallel writer recommendation for executable M6;
10. confirmation that no repository mutation/tests/builds/downloads/captures occurred.

## Verification intent

Read-only repository evidence only:

- focused `rg` and bounded reads of scanner/prospective/qualification artifacts and API/UI callers;
- inspect immutable identity/linkage fields rather than inferring from filenames;
- inspect Git status before/after.

Do not run tests, builds, formatters, generators, captures, market downloads, migrations, or mutating API calls.

## Out of scope

- executable M5 review or mutation;
- M7 persistent collector/SQLite implementation;
- M8 Portfolio/History convergence;
- current-approved basket compatibility unless it is a hard dependency for M6 Idea follow-up;
- live/private exchange authority;
- CCXT;
- changing historical QAP economics;
- generic state machine/timeline infrastructure.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. exact read-only Git state before/after;
3. owner/caller map across the longitudinal evidence chain;
4. current-approved Product scan follow-up compatibility verdict and smallest required repair;
5. evidence-layer taxonomy tied to actual artifacts;
6. proposed longitudinal Research Idea read/API composition;
7. all-survivor follow-up semantics and UX implications;
8. recommended executable M6 writer topology;
9. M7 handoff risks/stop conditions and confirmation of no mutation/tests/builds/downloads.
