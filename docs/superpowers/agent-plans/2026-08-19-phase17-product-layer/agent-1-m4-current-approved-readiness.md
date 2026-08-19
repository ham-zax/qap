# Agent 1 — M4 Current-Approved Policy and Explainable Readiness

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m4-current-approved`
**Branch:** `phase17-m4-current-approved`
**Can start:** after the Wave-5 coordination base is committed
**Depends on:** complete M3 integrated at `c1d97eb`
**Execution lifetime:** `persistent-agent-loop` required

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m4-reconnaissance.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`

Inspect the integrated M2/M3 owners directly: `ProductUniverse.resolved_scope()`, `ProductMarketData.projection()`, M3 prepare/refresh, Scanner-V1 protocol/preparation/universe/run/replay, and API operation composition.

## Mission

Implement M4 end-to-end: a separately versioned **current-approved/current-survivor retrospective research claim**, backend-owned explainable readiness and safe cutoff, and a normal Product research initiation seam that does not require the user to supply raw `as_of`.

The strict historical point-in-time Scanner-V1 path must remain intact and independently usable.

## Ownership

Own the smallest coherent backend/Product slice for:

- explicit Product-default current-approved policy/claim identity;
- binding explicit M2 approved/current scope to that claim;
- consuming M3 immutable-generation coverage/provenance/maintenance state;
- selected-timeframe readiness and backend safe cutoff;
- structured ready/excluded reasons;
- bounded direct-market readiness summary;
- Product-default research launch using the backend-selected cutoff;
- API/OpenAPI/generated client synchronization required by the new contract;
- minimal docs synchronization if executable public contracts change.

Do not implement the M5 React/primary-IA redesign.

## Frozen claim boundary

The Product-default claim is retrospective research over operator-approved assets that are currently resolved/available on selected supported Spot venues, using trailing admitted historical data through a backend-owned safe cutoff.

It is **not** historical point-in-time universe reconstruction. Current directory observations are current availability evidence only; they must not be converted into historical lifecycle proof.

Universe semantics are search-bearing. The new Product-default claim therefore needs a new explicit/versioned identity; do not reuse `scanner-v1-pit-universe-v1` as though the universe claim were unchanged.

Reuse existing Scanner-V1 candidate/scout/promotion/replay/economic rules only where their assumptions remain valid, and preserve the new claim identity in immutable scan evidence.

## Readiness contract

For one selected timeframe (`short`, `medium`, or `swing`), backend truth must distinguish at least:

- approved scope;
- resolved/current supported venue paths;
- ready assets/paths;
- excluded assets/paths with structured reasons;
- required native interval/history coverage;
- direct-market readiness where replay requires it;
- latest safe completed-data cutoff;
- Product market-data maintenance state.

Keep these meanings distinct where applicable:

- `not_approved`;
- `identity_review_required`;
- `current_market_unavailable`;
- `history_missing`;
- `history_insufficient`;
- `refresh_running`;
- `refresh_failed`;
- `direct_market_unavailable`.

Do not import legacy QAP eligibility thresholds or promotion labels. Historical bar availability must never stand in for strict PIT lifecycle evidence.

## Safe cutoff

Normal Product research must not ask the user for `as_of`. The backend selects the latest cutoff supported by the exact ready scope and required completed generations, capped by current-directory observation truth where necessary.

The cutoff and readiness response must bind enough M2/M3 identity/provenance that a stale frontend cannot silently launch against a materially changed scope/generation set.

## Product-default scanner composition

Preserve the existing advanced/manual strict scanner endpoint/path.

For Product-default research, compose the current-approved policy explicitly rather than changing the meaning of the strict default scanner protocol. If scanner preparation needs a bounded extension point for an explicit Product asset allowlist or frozen generation fingerprints, keep it versioned and fail closed. Deep replay must receive the same protocol/claim identity as discovery; do not let candidate discovery and replay disagree about protocol identity.

Do not add a new scientific mutation command merely to label Product research. Prefer the smallest composition over the existing scanner operation authority unless repository constraints prove that unsafe.

## Acceptance

M4 is complete only when all are true:

1. strict historical PIT Scanner-V1 semantics remain unchanged for the existing path;
2. Product-default research has a separate explicit/versioned current-approved claim identity;
3. readiness is backend-owned and explainable for the selected timeframe;
4. approved/current scope comes from M2, generation/coverage/provenance truth comes from M3;
5. safe cutoff is backend-selected and no primary Product `as_of` input is required;
6. stale/mismatched scope or generation bindings fail closed before research starts;
7. direct-market unavailability is a replay limitation, not asset invalidity;
8. Product preparation failure/incomplete evidence remains distinct from valid negative/rejected research;
9. API/OpenAPI/generated client contracts are synchronized where changed;
10. no M5 primary UI redesign, legacy thresholds, CCXT, synthetic direct markets, private exchange authority, or generic workflow framework is absorbed.

## Verification intent

Testing remains opt-in; do not create, modify, or run tests unless explicitly authorized or independently mandatory.

Use the smallest meaningful non-test evidence, for example focused static checks, deterministic direct composition/runtime smokes, OpenAPI/client regeneration comparison, import boundaries, and build/type checks if frontend generated contracts change. Verify strict PIT behavior by inspecting/using the unchanged strict path rather than rewriting it.

## Out of scope

- M5 Research IA/funnel implementation;
- M6 Research Idea lifecycle;
- M7 collector/SQLite;
- live/private exchange authority;
- changing QAP economics, costs, controls, HODL benchmark, capacity, or prospective truth;
- the separately deferred old-scan/basket catalog coupling unless M4 correctness is impossible without addressing it.

## Finish report

Return:

1. status;
2. branch/worktree/commit/final Git state;
3. exact current-approved claim identity and strict-PIT preservation evidence;
4. readiness/safe-cutoff behavior and exclusion taxonomy;
5. Product-default research-initiation behavior and stale-binding protection;
6. public/shared interfaces changed;
7. checks actually run and why;
8. M5 handoff plus remaining risks/deviations.
