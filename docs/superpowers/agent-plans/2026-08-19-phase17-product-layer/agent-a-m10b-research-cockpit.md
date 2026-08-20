# Agent A — M10-B Research Cockpit + Experiment Lab

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed Product/API read composition
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m10b-research-cockpit`
**Branch:** `phase17-m10b-research-cockpit`
**Isolation reason:** M10-B is the only current writer after M10-A integration; the worktree protects `main` as the stable integration/review baseline while the Product surface is reshaped.
**Can start:** immediately after the Wave-13 coordination base is committed and this worktree is created
**Depends on:** M10-A integrated at `12ed08a`; Agent A M10-B reconnaissance
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless; progress/steering is not a stop request

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M10-B is authoritative
- `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-a-m10b-reconnaissance.md`
- integrated M10-A public/API/domain contract at `12ed08a`
- current Product Research, Research Universe, History, Experiment, Activity, operation, routing, and shared shell code

Before the first mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Testing remains opt-in. Do not create, modify, or run tests unless explicitly authorized or independently mandatory.

## Objective

Make Product Research start from the user's actual research intent instead of setup/provenance administration while consuming M10-A as the sole recipe/support/compiler authority.

The required primary jobs are:

```text
Research a pair
W + BTC
-> Product timeframe
-> backend-owned default QAP pair recipe
-> Check support
-> resolve genuine setup blockers inline without losing the draft
-> Run
-> inspect sibling/result evidence

Scan my universe
-> Product timeframe
-> existing current-approved scanner
-> truthful backend stage funnel
-> inspect retained/replayed/rejected/Research-Idea evidence

Experiment Lab
-> pair | fixed_basket only
-> backend-described admitted/known components
-> declare exact variants/parameters/data role
-> Check support
-> inspect every backend support axis/reason
-> Run only when support.runnable=true
```

M10-B is a Product composition milestone, not a new scientific engine.

## Integrated M10-A contract to consume

M10-A is integrated on main at `12ed08a`.

Confirmed public seams:

```text
POST /api/research-recipes/check-support
  ResearchRecipeCheckRequestDto
  -> ResearchRecipeCheckV1
       recipe: ResearchRecipeV1 | null
       support: SupportReportV1

POST /api/research-recipes/run
  ResearchRecipeRunRequestDto
  -> OperationRefDto

OperationKind.RUN_RESEARCH_RECIPE
completed OperationDto.result
  compilation_sha256
  run_ids[]
```

Generated TypeScript already exports:

- `ResearchRecipeCheckRequestDto`
- `ResearchRecipeCheckV1`
- `ResearchRecipeDraftV1`
- `ResearchRecipeRunRequestDto`
- `ResearchRecipeV1`
- `SupportReportV1`

M10-B must consume these. Do not reproduce support logic, runnable rules, component compatibility, family continuity, or final-OOS logic in React.

## One integration gap discovered after M10-A

M10-A owns capability metadata and immutable recipe-compilation lineage internally, but the integrated HTTP surface does not expose a capability descriptor/default-recipe read or compilation-lineage read.

M10-B may add the **smallest read-only application projection** genuinely required for:

1. a backend-owned versioned default Pair Research recipe/draft;
2. backend-described Experiment Lab component choices;
3. advanced recipe/compilation lineage disclosure for completed runs.

Reuse existing M10-A owners such as `CAPABILITY_CATALOG` and immutable recipe-compilation artifact readers. Do not create a second capability registry or lineage store. Do not change recipe/support/compiler scientific rules merely to suit the UI.

Prefer one compact descriptor/read shape over several speculative endpoints. Let actual Product consumption determine the minimum public projection.

## 1. Reconcile API consumption first

Before Product component work, reconcile the integrated contract through:

- `web/src/api/types.ts`;
- `web/src/api/client.ts`;
- `web/src/api/queries.ts`;
- existing Product market-data GET/prepare/refresh backend routes;
- M10-A Check support / launch / operation-result contract;
- the minimal backend descriptor/lineage reads described above if needed.

The current frontend client does not yet wrap M10-A research-recipe endpoints or Product market-data prepare/refresh. Add only the wrappers/query keys the Product flow actually uses.

Do not make generated OpenAPI types hand-authored sources of truth.

## 2. Shared exact-first asset selector

Build one shared selector used by both Pair Research and Research Universe.

Required ordering:

```text
exact symbol/code match
then prefix
then substring/other matches
```

The literal query `W` must surface exact `W` before entries such as `AAVEDOWN`, `BTCDOWN`, `WAL`, `WAN`, etc.

Reuse the existing Research Universe/directory data. No search service, backend index, fuzzy-search dependency, or ticker-to-identity inference.

On mobile, selecting an item must collapse/replace the long result list so the next action is visible.

Preserve separate identity confirmation and asset admission authorities.

## 3. Pair Research

Build Pair Research as the first normal Research task.

Own local unfinished draft state for:

- Asset A;
- Asset B;
- Product timeframe;
- backend-provided default recipe/draft identity where needed.

Do not persist draft state merely for convenience unless current navigation/setup flow genuinely requires a small existing mechanism.

Flow:

```text
select pair + timeframe
-> obtain/use backend-owned default versioned QAP pair recipe
-> Check support
-> show compositional support truth
-> if setup is needed, resolve it inline while preserving the pair draft
-> re-check support
-> launch exact canonical ResearchRecipeV1 only when support.runnable=true
-> follow operation
-> show/link exact resulting run siblings
```

Normal Pair Research must not expose raw `as_of`, manifest JSON, protocol IDs, or final-OOS research-design controls.

## 4. Just-in-time setup

Inline only the genuine blocker returned by backend support/readiness:

- identity confirmation;
- operator asset approval;
- Product market-data prepare/refresh;
- readiness re-check.

Use human task language such as "W needs one-time setup" instead of forcing fingerprint/provenance terminology into the novice path.

Preserve the unfinished pair selection and timeframe across setup actions.

Market-data preparation must use the existing Product owner/routes. Do not invent another downloader or setup state.

## 5. Reshape ResearchHome

The normal Research page order becomes:

1. **Research a pair**
2. **Scan my universe**
3. advanced Experiment Lab entry
4. strict historical PIT under **Advanced Research**

`Scan my universe` continues to use existing `ProductResearch`/current-approved scanner behavior. Do not route it through ResearchRecipeV1.

Preserve one Product timeframe at a time, backend-owned readiness, scanner stage counts, negative/rejected/unavailable evidence, and existing Research Idea navigation.

Do not invent a frontend "interestingness" score.

## 6. Experiment Lab

Build the smallest advanced research authoring surface over M10-A.

Only:

- `pair`;
- `fixed_basket`.

Use backend-described components/defaults from the minimal read projection. There must be no React capability registry or duplicated scientific combination table.

Support presentation must preserve independent backend truth:

- structure;
- capability;
- authority;
- readiness;
- fidelity;
- `runnable`;
- all reasons;
- suggestions.

The UI may choose friendly wording/ordering, but must not calculate a replacement scientific status or precedence.

Run eligibility is exactly `support.runnable` plus possession of the canonical `ResearchRecipeV1` returned by Check support.

No arbitrary Python, dynamic plugins, paper-to-code interpretation, Copula implementation, or automatic adaptation.

## 7. Operation/result navigation

Extend current operation presentation for `run_research_recipe` without creating another operation authority.

When complete:

- read `compilation_sha256` and `run_ids[]` from backend operation result;
- link each exact run to existing experiment/economic/pair surfaces as appropriate;
- preserve Activity as the durable operational-status authority;
- present a concise immediate result/sibling summary in Pair Research/Experiment Lab when useful.

Do not infer run IDs from hashes or filesystem paths in React.

## 8. History / experiment disclosure

Improve existing evidence presentation without manufacturing new scientific entities.

Required behavior:

- manual/unowned recipe experiment runs may be grouped by existing `research_family_id` for learning/navigation;
- they do **not** become scanner Research Ideas merely because they share a family;
- advanced provenance may expose M10-A recipe/compilation lineage through the backend-owned read projection;
- exact recipe hash, compilation hash, family, data role, manifest hash, immutable generation/provenance details stay behind progressive disclosure.

Prefer extending existing History/Experiment read/presentation rather than adding a new result database.

## 9. Small guidance/copy update only

Update only the guidance needed to match the new workflow, primarily:

- `ScreenGuide`;
- `HomeWorkspace`;
- directly affected Research copy.

Do not turn M10-B into another global copy rewrite.

Help should describe user intent/action/example/next step while keeping audit terminology secondary.

## Scientific and authority boundaries

Preserve all of these:

- M10-A remains sole recipe/preflight/compiler authority;
- only `pair | fixed_basket` compile;
- Universal Scan remains scanner-owned;
- Focus Scan remains deferred;
- `SupportReportV1` axes/reasons are independent backend truth;
- exact recipe hash and stable `research_family_id` semantics are unchanged;
- final-OOS selection/family rules are unchanged;
- `basket_graph` remains development-only under current basket authority;
- strict PIT remains Advanced/scanner authority;
- ExperimentManifest/runner/economics/controls/provenance/final-OOS machinery remain unchanged except a tiny read/presentation seam if genuinely necessary;
- no live/private trading authority.

## Likely ownership map

Expect the smallest coherent changes around:

- `web/src/api/types.ts`
- `web/src/api/client.ts`
- `web/src/api/queries.ts`
- one shared asset-selector component/helper
- `web/src/features/home/ResearchUniverse.tsx`
- `web/src/features/discovery/ResearchHome.tsx`
- `web/src/features/discovery/ProductResearch.tsx` only where scanner presentation reuse requires it
- new Pair Research Product component(s)
- new Experiment Lab Product component(s)
- operations presentation/detail
- History/Experiment advanced presentation
- `ScreenGuide.tsx`
- `HomeWorkspace.tsx`
- route wiring only as needed
- the smallest backend read DTO/route/view needed for recipe descriptors/defaults/lineage, if current public reads are insufficient
- generated OpenAPI/schema synchronization if that backend read seam is added

This is an ownership guide, not permission for broad refactors.

## Observable success conditions

M10-B is complete only when direct non-test evidence demonstrates:

1. typing exact `W` puts `W` before substring matches and the shared behavior is used in both Pair Research and Research Universe;
2. a user can select `W` + `BTC`, choose one Product timeframe, obtain the backend-owned default pair recipe and Check support without authoring scientific JSON;
3. a setup blocker is shown as the exact human task, the pair draft survives identity/admission/data actions, and support can be re-checked afterward;
4. a runnable Pair Research recipe launches through `/api/research-recipes/run`, follows the existing operation, and exposes the exact resulting `run_ids[]`;
5. ResearchHome presents Pair Research first and Universal Scan second, while strict PIT remains under Advanced Research;
6. Universal Scan still uses existing Product scanner authority and truthful backend funnel/evidence;
7. Experiment Lab choices come from backend-described capability/default metadata rather than a React scientific registry;
8. Experiment Lab renders all independent SupportReport axes/reasons and gates Run only on backend `runnable` + canonical recipe;
9. completed recipe operations link exact experiment runs and Activity remains operational authority;
10. History/Experiment can disclose recipe/compilation lineage under advanced provenance without manufacturing Research Ideas;
11. normal novice paths hide hashes/fingerprints/protocol IDs unless audit/provenance is deliberately expanded;
12. the Product can still state clearly that QAP does not recommend, authorize, or place live trades.

## Required validation

No tests.

Use direct rendered/manual fixture or bounded browser evidence only where it directly proves the M10-B user jobs, then one candidate-final non-test pass appropriate to changed surfaces. At minimum, if affected by the implementation:

- generated OpenAPI / TypeScript schema synchronization for API changes;
- TypeScript typecheck;
- Vite production build;
- focused Ruff/Pyright/import-contract checks only if Python API read surfaces change;
- `git diff --check`.

Do not run test suites or add tests.

## Out of scope

- new research methods;
- Copula or Palazzi implementation;
- Universal Scan/scanner scientific-policy changes;
- Focus Scan mechanics;
- custom strategy plugins/arbitrary Python;
- new backtester/economic engine;
- new result database;
- redefinition of Research Idea;
- final-OOS/scientific threshold changes;
- live/private exchange authority;
- broad Product IA redesign outside M10-B;
- M10-C proof or M10-D representative-user study.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and clean/dirty state;
3. exact Product flows delivered: Pair Research, Universal Scan reshaping, Experiment Lab, navigation/history disclosure;
4. exact API/client/read seams added or reused, especially descriptor/default/lineage reads;
5. confirmation that support/run eligibility remains backend-owned and no React scientific registry/precedence was added;
6. exact-first asset-search behavior and shared reuse location;
7. just-in-time setup behavior and how unfinished pair draft is preserved;
8. recipe-operation/result/history lineage behavior;
9. direct non-test evidence and final static/build checks actually run; explicitly state no tests were run;
10. protected scientific/scanner/final-OOS/live-trading boundaries confirmed unchanged;
11. M10-C handoff: stable user flows and evidence cases now available;
12. unresolved risks or deliberate non-scope.