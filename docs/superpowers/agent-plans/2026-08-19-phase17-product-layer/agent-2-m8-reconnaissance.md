# Agent 2 — M8 Portfolios / History / Activity Convergence Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only reconnaissance
**Workspace:** `/home/hamza/repo/qap` READ-ONLY
**Can start:** immediately after the Wave-8 coordination base is committed
**Depends on:** M6 integrated at `c1db648`; M7 writer contract frozen
**Execution lifetime:** persistent-agent-loop for continuity only

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M8 is authoritative
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- integrated M5/M6 Product Research/Research Idea contracts
- current basket/portfolio/history/activity code and immutable artifact readers

Use Causal Coding's read-only investigation policy. Do not mutate the repository.

Do not inspect or mutate Agent 1's active M7 worktree.

Do not run tests, builds, market captures, migrations, generators, downloads, or mutating APIs.

## Objective

Investigate the exact M8 implementation boundary needed to complete the primary Product IA:

`Home | Research | Portfolios | History`

while preserving existing portfolio economics and immutable research authority.

M8 must remain a composition/presentation milestone, except for the smallest backend compatibility repair that is genuinely required to let Product Research Ideas participate in the already-approved manual basket semantics.

## Highest-priority questions

### 1. Product current-approved scan -> basket compatibility

Current known issue: basket construction historically requires strict `scanner-v1-s1` source identity.

Determine precisely:

- where that rejection occurs;
- which scanner/basket scientific assumptions actually depend on strict PIT identity;
- whether the current Product-v1 scanner protocol preserves all basket-relevant scientific/economic primitives;
- what claim/scope lineage must be retained if Product Research Ideas are admitted to a manual basket;
- whether Product current-approved basket support can be a separately-versioned compatible claim without weakening strict PIT behavior;
- the smallest safe compatibility change, if any.

Do not assume Product basket compatibility merely because M6 prospective compatibility worked.

### 2. Deferred old-scan/current-catalog coupling

Re-investigate the previously identified coupling where basket work for an older completed scan may compare against the current catalog identity or current dataset generation.

Determine:

- exact current owners/callers;
- whether M3 immutable generation lineage now provides enough information to repair it safely;
- whether M8 Product Portfolios actually requires this repair;
- whether the repair should remain separate from Product claim compatibility or can share one minimal lineage seam.

Do not silently bundle unrelated catalog/lifecycle redesign.

### 3. Existing Portfolios semantics

Map the current manual basket workflow end-to-end:

- source scan/candidate selection;
- 3-6 asset constraints;
- exact-edge/manual selection;
- asset momentum inputs;
- basket resolver target authority;
- ordinary QAP experiment/economic outputs;
- HODL/simple-control comparisons;
- turnover/cost/concentration information already available;
- current UI/API owners.

Identify which labels/steps should be simplified around the M6 Research Idea mental model without changing resolver targets or turning the Product into an optimizer.

### 4. History composition

Map current completed evidence across:

- Product and PIT scans;
- Research Ideas;
- follow-up cohorts/reselections/checkpoints;
- persisted qualifications;
- basket research;
- ordinary QAP experiments;
- paper operational evidence where relevant.

Determine the smallest backend read/composition contract that lets History answer:

- what was tested;
- what was supported/rejected/unavailable;
- what later weakened or remained supported;
- what current amount assessments were made and when;
- what remains uncertain;
- what valid next action/navigation exists.

Do not create a new durable History database or duplicate immutable artifacts.

### 5. Preserve evidence-layer and ownership distinctions

History/Portfolios must not collapse:

- operator asset approval;
- current market/data readiness;
- historical relationship/discovery evidence;
- historical economic replay evidence;
- later prospective evidence;
- current public-market/capacity evidence;
- portfolio-expression evidence.

A rejected candidate cannot imply an asset is invalid. A missing dataset cannot revoke operator admission. A later-stage failure cannot rewrite earlier published evidence.

### 6. Objective-aware presentation

Use the legacy inventory/HODL thesis only as product-intent evidence.

Current QAP manifests/results remain authoritative for actual economics.

Determine what existing artifacts can truthfully support Product explanations of:

- matched passive HODL/control comparison;
- contributing assets/relationships;
- concentration;
- turnover/cost burden.

Do not replace the declared objective with a generic USD-return headline.

### 7. Activity as utility

Map what remains necessary from `/operations` now that primary IA is already `Home | Research | Portfolios | History`.

Determine the smallest contextual links/status surfaces needed from Home/Research/Portfolios/History while preserving the specialist Activity route for audit/troubleshooting.

No generic workflow engine.

## M7 handoff awareness

Agent 1 concurrently owns M7 persistent collection.

Do not inspect its worktree. Base M8 design only on the frozen M7 mission contract and current integrated code.

Assume M7 will add current collection state and time-specific qualification evidence beside the M6 longitudinal Research Idea. History should consume those as read-only chronology, not become a scheduler/capacity owner.

## Deliverable

Return a concrete read-only implementation brief containing:

1. exact Git state before/after and no-mutation confirmation;
2. current Portfolios owner/caller/artifact map;
3. definitive Product current-approved -> basket compatibility verdict;
4. exact old-scan/current-catalog basket coupling and repair recommendation;
5. smallest safe Product Portfolio compatibility/read/write contract;
6. current History sources and recommended composition/read model;
7. objective/HODL/control presentation fields that are genuinely supported today;
8. Activity utility convergence recommendation;
9. recommended M8 writer topology — one writer or a truly safe M8-A/M8-B fan-out, with shared seams identified;
10. M9 handoff/process-state implications and hard stop conditions.

## Hard boundaries

Do not propose or implement:

- automatic portfolio discovery/optimization;
- changing basket resolver targets;
- new portfolio economics, HODL/control definitions, costs, fills, or strategy authority;
- weakening strict PIT research;
- Product basket compatibility by simply skipping protocol checks without equivalent lineage proof;
- a new History database;
- a generic workflow/state machine;
- live/private exchange authority;
- M9 packaging decisions.
