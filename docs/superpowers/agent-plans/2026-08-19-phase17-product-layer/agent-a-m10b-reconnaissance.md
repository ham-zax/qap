# Agent A — M10-B Research Cockpit + Experiment Lab Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only reconnaissance
**Workspace:** `/home/hamza/repo/qap` read-only on the Wave-12 coordination base
**Isolation reason:** Agent B concurrently owns the only writable M10-A worktree; this mission must reason from the frozen M10-0 contract and stable integrated Product baseline rather than chasing an in-flight implementation.
**Can start:** immediately after the Wave-12 coordination base is committed
**Depends on:** M10-0 approved; M10-A contract frozen in the source plan and Agent B mission
**Execution lifetime:** persistent-agent-loop for mission continuity only
**Developer visibility:** headless

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-b-m10a-research-recipe.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M10-B is authoritative
- `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
- current Product Research / Universe / scanner / operation / route / shared-shell UI code
- current generated API client and existing Product readiness/current-approved endpoints

Use:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

This mission is read-only. Do not inspect or mutate Agent B's active M10-A worktree.

Do not run tests, builds, generators, migrations, downloads, captures, or browser mutations.

## Objective

Map the smallest executable M10-B Product implementation onto the current repository so the Research experience can become research-intent-first immediately after M10-A integrates.

The target novice jobs are:

```text
Research a pair
W + BTC
-> choose Product timeframe
-> Check support / resolve setup without losing draft
-> Run
-> understand model/economic evidence

Scan my universe
-> choose Product timeframe
-> use existing current-approved scanner
-> understand truthful stage funnel

Experiment Lab
-> pair | fixed_basket
-> declare catalogued method/components/variants/data role
-> Check support
-> see all blockers/adaptations
-> run only when backend says runnable
```

This reconnaissance must distinguish what is already implemented and only hidden from what genuinely needs new Product composition.

## Frozen boundaries

- M10-A is the sole owner of `ResearchRecipeV1`, `SupportReportV1`, capability resolution, recipe compilation, immutable recipe/compilation lineage, and supported-recipe execution API.
- Universal Scan remains under the existing scanner owner and must not be routed through the recipe compiler.
- Focus Scan is deferred unless existing scanner scope reuse is almost mechanical; do not design new scanner mechanics in this mission.
- Scientific/economic classifications remain backend-owned.
- Strict historical PIT remains Advanced Research.
- Identity, admission, readiness, and data preparation remain separate backend authorities.
- Ticker equality never becomes identity proof.
- Protocol IDs, fingerprints, paths, hashes, and compilation lineage belong under progressive disclosure rather than the novice path.
- No live/private trading authority.

## Investigate

### 1. Current Product Research entry surface

Trace the exact current owners for:

- `/research` route and normal Product Research view;
- Advanced Research / strict PIT entry;
- current-approved Product launch path;
- scan status/stage funnel/result navigation;
- Research Idea detail and historical/economic replay links;
- shared shell/contextual help pattern.

Identify the smallest change that makes `Research a pair` and `Scan my universe` visually primary without duplicating scientific logic in React.

### 2. Exact-first asset search

Trace current market-directory/identity search behavior that caused exact `W` to be buried among substring matches.

Determine:

- current backend search owner and ordering semantics;
- whether exact > prefix > substring can be fixed in the backend/read owner without adding another search service;
- how Product pair selection should represent already-approved/ready assets versus assets needing one-time identity/admission/data setup;
- how the selected result can replace/collapse the long result list on mobile.

Do not weaken identity confirmation or admission rules.

### 3. Pair Research task composition

Map the minimum frontend/backend composition needed once M10-A exists:

```text
Asset A + Asset B
Product timeframe
frozen default QAP pair recipe family
Check support
setup interruption when needed
Run supported recipe
operation/result navigation
```

Identify what should be a local draft state versus durable backend state. Prefer local draft state unless current requirements genuinely need persistence.

The selected pair/draft must survive identity/admission/data preparation interruptions.

Do not expose raw `as_of` or scientific protocol knobs in the normal Product flow.

### 4. Just-in-time setup

Map the existing routes/actions for:

- identity confirmation;
- asset approval/admission;
- market-data prepare/refresh;
- readiness re-check.

Recommend the smallest way for Pair Research to interrupt with a bounded human-language setup task and return to the unfinished draft.

The Product should not teach canonical fingerprints/provenance vocabulary merely to let a user continue research.

### 5. Universal Scan presentation

Trace the current scanner launch, scope/readiness, operation status, stage counts, and result read models.

Determine the smallest UI reshaping needed to make **Scan my universe** an obvious normal Research action while preserving:

- current-approved scanner protocol;
- one Product timeframe at a time;
- truthful backend stage counts;
- negative/rejected/unavailable evidence;
- no invented frontend interestingness score;
- strict PIT scanner under Advanced Research.

Do not move Universal Scan into M10-A or invent a second scanner API unless the current route genuinely cannot serve the Product surface.

### 6. Experiment Lab

Using the frozen M10-A contract, map the smallest advanced surface for:

- `pair | fixed_basket` only;
- component/method selection from backend-described known capabilities;
- exact declared variants/parameters;
- data role/evaluation intent;
- `Check support` with compositional axes and all reasons;
- explicit adaptation distinction;
- Run only when backend `runnable=true`.

Determine whether M10-B actually needs a capability-list endpoint after M10-A or whether a small backend-described set from support/templates can be reused. Do not pre-approve an endpoint just for UI convenience.

### 7. Result/navigation composition

Determine how a recipe-run operation should land in existing Experiment/Research/History evidence surfaces without creating a second result database or a new scientific result type.

Map:

- operation completion -> experiment artifact/read route;
- pair recipe family/sibling visibility;
- final-OOS selection lineage under advanced audit disclosure;
- History placement once runs exist;
- relation to Research Ideas without pretending every manual experiment is a scanner-discovered Research Idea.

### 8. File ownership and writer topology

Return the smallest proposed M10-B file/owner map.

Identify any generated OpenAPI/client overlap expected after M10-A integration.

Recommend whether M10-B should be one writer or can safely split. Do not manufacture parallel work merely because two agents exist.

## Required output

Return:

1. current Product Research/Universe/scan route and component owner map;
2. exact-first search owner and smallest repair seam;
3. Pair Research UX/state/API composition map;
4. just-in-time setup flow that preserves the unfinished draft;
5. Universal Scan reuse map showing what stays scanner-owned;
6. Experiment Lab minimum surface over the frozen M10-A contract;
7. result/History/navigation composition;
8. exact files likely owned by M10-B and protected files it should not touch;
9. hidden blockers or contract gaps M10-A should expose before integration, if any;
10. recommended M10-B writer topology and implementation order.

No repository mutation and no test/build execution.
