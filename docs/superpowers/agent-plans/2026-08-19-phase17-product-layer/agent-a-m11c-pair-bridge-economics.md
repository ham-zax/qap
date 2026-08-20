# Agent A — M11-C Honest Two-Leg Pair Research Economics

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed experiment contract / Product authority / minimal Product UI
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m11c-pair-bridge-economics`
**Isolation reason:** `main` contains protected live-session `catalog.json` and `product-market-data/` state, while this mission changes the manifest/compiler/Product-authority boundary and must prove real historical economics. No concurrent production writer is authorized.
**Can start:** immediately after this coordination package is integrated
**Depends on:** M11-A integrated through `2f055d1`; M11-B integrated at `9890431`
**Execution lifetime:** `persistent-agent-loop` required
**Wake strategy:** Terminal + event wait for any durable API/runtime process; bounded Dev commands otherwise
**Developer visibility:** headless by default; use visible browser evidence only when needed for the one-time Product authority interaction

## Read first

- `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md` — authoritative Pair Study/economic-expression contract
- `docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md` — M11-C is Section 6
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — current dependency and ownership map
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-a-m11b-pair-research-product-flow.md` — integrated Product boundary that this mission must preserve

Inspect current code before deciding implementation details. The facts below are handoff observations, not permission to bypass the actual owners.

## Objective

Allow a manually selected pair such as `W / PIXEL · Medium-term` to proceed from valid Pair Study evidence into honest historical QAP economics even when no real direct `W/PIXEL` market exists, by using the existing real same-venue `W/USDT + PIXEL/USDT` Spot legs through QAP's existing `multi_asset_bridge` executor.

The economic replay must remain truthful:

- two real declared market legs, never a synthetic `W/PIXEL` fill or candle series;
- explicit operator authority for temporary USDT ownership inside research replay;
- exact immutable Pair Study generation/venue/cutoff binding;
- existing costs, inventory, accounting, HODL, controls, family/final-OOS and runner authority unchanged.

## Current state

M11-B is integrated at `9890431`. Its real W/PIXEL walkthrough proved:

- Gate `W_USDT + PIXEL_USDT` Pair Study ready at one exact 4h cutoff;
- relationship evidence valid without a direct pair market;
- `economic_expression.direct_status=unavailable` remains downstream of relationship readiness;
- no default direct-market recipe is declarable today;
- pair-scoped preparation excludes unrelated approved BTC.

Current implementation inspection also establishes:

- `ResearchExecutionV1` and `ExecutionSpec` already admit `multi_asset_bridge` with an explicit `bridge_asset`;
- the capability catalog already marks `multi_asset_bridge` executable;
- `run_deterministic_replay()` already accepts multiple execution instruments plus one bridge and the runner already delegates `multi_asset_bridge` manifests to it;
- Product fixed-basket defaults already use exact `ASSET/USDT` execution bindings with `bridge_asset="USDT"`;
- `ResearchGenerationBindingV1.purpose` is currently only `execution | evidence`;
- `ExperimentManifest.evidence_instrument_ids` are deliberately evidence-only and are forbidden from overlapping direct or multi-asset execution IDs;
- relationship model policies currently require their named pair inputs to be declared evidence-only;
- the compiler currently derives relationship input IDs only from `purpose="evidence"` bindings;
- Product `_pair_draft()` still requires a ready real direct market before it binds pair relationship legs;
- Product `_pair_draft()` is currently based on universe-wide `CurrentApprovedReadiness`, while M11-A Pair Study owns the exact selected venue, safe cutoff and immutable `A/USDT + B/USDT` generation references;
- M11-B permits the user to select a Pair Study venue, but the existing recipe Product-context request does not currently carry that venue.

The last two facts matter: M11-C must not reintroduce unrelated whole-universe readiness or silently change the user's selected study venue when it creates a bridge recipe.

## Ownership

You own the smallest complete vertical slice required for this new economic expression:

- additive manifest semantics for exact relationship-input instruments;
- relationship model consumption of that explicit role while preserving existing evidence-only behavior;
- compiler mapping for bounded pair + `multi_asset_bridge` recipes;
- Product-owned persisted transient research-bridge authority;
- canonical default pair-recipe selection after Pair Study;
- exact selected pair venue/cutoff/generation binding into the recipe/economic path;
- M10-A support/readiness/authority truth required so an unauthorized pair bridge cannot become runnable;
- Pair Study economic-expression projection and minimal Pair Research interaction needed to request/reuse the one-time bridge permission and continue through the existing support/run flow;
- OpenAPI/generated TypeScript synchronization if the Product/API contract changes;
- direct real-data proof through the existing runner and artifacts.

Neighboring ownership remains:

- Pair Study relationship formulas and series: M11-A / `qap.relationship`;
- study-first task composition and charts: M11-B, except the minimal bridge-authority/economic-state continuation required here;
- Scanner Slice-1 search, promotion and direct replay: unchanged;
- multi-asset fill routing, cost calculation, ledger/accounting, HODL and control formulas: existing owners, reuse only;
- final integrated research conclusion presentation: M11-D;
- formal cointegration and Student-t Copula implementation: later/separate method admission;
- live/private trading authority: out of scope and remains `NO-GO`.

## Coordination contract

### Preserve evidence-only semantics

Do not weaken or reinterpret existing `evidence_instrument_ids`.

Add an explicit relationship-input manifest role equivalent to `relationship_instrument_ids` with these semantics:

- references declared exact instruments/data sources;
- identifies what the relationship model consumes;
- may overlap execution IDs when the same real market series truthfully serves both roles;
- does not grant execution authority by itself;
- existing manifests without the new role retain current behavior;
- existing evidence-only IDs remain prohibited from execution.

For existing direct/scanner pair runs, compatibility may continue through the current evidence-only path. Do not rewrite historical manifests or duplicate one immutable dataset under fake identities.

### Compiler is the role authority

Do not add a redundant `ResearchRecipeV1` field merely to list the same market legs twice.

For the bounded new pair bridge case, the compiler may derive explicit relationship inputs only after establishing all of the following from the exact recipe/data bindings:

- `research_object=pair`;
- `execution.mode=multi_asset_bridge`;
- explicit bridge asset is the intended canonical bridge;
- exactly two execution generations exist;
- the two exact instruments are the selected `A/bridge` and `B/bridge` same-venue Spot legs;
- no extra, missing or ambiguous execution leg exists.

Ambiguity is a compile/support failure, not a guessed mapping.

### Pair Study remains the Product question owner

A bridge recipe created after Pair Study must bind the same selected pair question rather than falling back to unrelated universe-wide state.

For the Product default pair path, preserve:

- selected pair assets and orientation;
- selected Pair Study venue;
- Pair Study interval/horizon;
- exact immutable `A/USDT + B/USDT` generations;
- one compatible Pair Study safe cutoff/data window.

If the current recipe Product-context API cannot preserve the selected venue or exact Pair Study binding, make only the smallest explicit Product/API amendment needed. Do not silently choose another venue and do not make unrelated approved assets part of pair economic readiness.

### Direct execution remains preferred

Backend execution-mode choice remains pre-result and deterministic:

1. use the ready real direct pair market when the selected Pair Study/economic binding truthfully supports it;
2. otherwise use the exact same-venue two-leg bridge only when both pair legs are ready and transient bridge authority is present;
3. otherwise keep relationship research ready while economic replay reports the concrete blocker.

No route graph, hidden alternative bridge, outcome-dependent mode choice or synthetic pair instrument.

### Transient USDT authority is separate

Add one bounded persisted Product permission for temporary USDT ownership inside research/paper bridge replay.

It must:

- be separate from economic asset approval;
- not make USDT a target basket asset, Research Idea, scanner candidate or live-trading authorization;
- require canonical identity rather than ticker equality;
- be reusable after the operator grants it once;
- leave actual bridge residue as real replay inventory/accounting.

Normal Product wording should remain equivalent to:

> QAP can replay this pair using two real Spot conversions through USDT. Allow temporary USDT ownership inside research replays?

Do not create a generic permissions/settings framework for this single authority.

### M10-A remains final pre-execution truth

For the new pair bridge path, missing transient bridge authority must not result in `SupportReportV1.runnable=true`.

Expose the missing authority truth using the smallest semantically correct support/Product reason. Do not mislabel transient bridge permission as approval to economically own USDT.

Once authority and exact data are present, M10-A support must be able to report the canonical pair recipe runnable with `multi_asset_bridge` and compile it through the existing compiler/runner path.

Do not weaken existing fixed-basket or direct-pair behavior merely to implement the new Product pair path. If a broader authority change is genuinely required by an existing constitutional invariant, establish that from current code/design before expanding scope.

## Success conditions

### 1. W / PIXEL remains study-ready before permission

Starting from the integrated M11-B flow, `W / PIXEL · Medium-term` still displays the same valid Gate Pair Study evidence when no direct market exists.

Before transient USDT permission is granted, economic expression is blocked for the specific authority reason; Pair Study itself remains ready and its values do not disappear.

### 2. One bounded authority step

The normal Pair Research flow can grant the explicit temporary-USDT research replay permission without navigating away from the pair question or approving USDT as an economic asset.

After permission is granted, the state persists and Pair Research can refresh/re-evaluate economic expression without asking again on every run.

### 3. Canonical bridge recipe

For the selected W/PIXEL Gate study after permission:

- Product declares the existing default two-variant pair family (`rolling_log_ratio_zscore` and `residual_mean_reversion`);
- execution mode is `multi_asset_bridge`;
- bridge asset is USDT;
- the exact W_USDT and PIXEL_USDT immutable generations are the two real execution instruments and exact relationship inputs;
- the recipe uses the selected Pair Study venue/cutoff rather than unrelated universe readiness;
- no W/PIXEL synthetic generation/instrument exists.

### 4. Manifest role is explicit and backward-compatible

Compiled manifests record the exact relationship input role separately from evidence-only semantics.

The same W_USDT and PIXEL_USDT instrument IDs may be both relationship inputs and execution IDs for the new pair bridge run, while `evidence_instrument_ids` retains its historical evidence-only contract.

Existing direct pair/scanner manifests continue to validate under their existing semantics.

### 5. Existing executor performs the economics

Execute the admitted pair recipe through the existing `qap.experiment` runner and existing multi-asset bridge replay.

Direct artifact inspection must show:

- real W/USDT and PIXEL/USDT fills only;
- two-leg costs/fees/slippage from existing cost authority;
- no synthetic W/PIXEL execution fill;
- bridge inventory/residue represented by existing replay/accounting semantics;
- QAP, matched HODL and predeclared primary-control results produced by existing authorities;
- exact run/compilation lineage remains ordinary M10-A lineage.

Do not change economic formulas to make the run succeed.

### 6. Direct-market and scanner paths do not regress semantically

A pair with a ready real direct market still selects direct execution by the existing Product rule.

Scanner Slice-1 direct-replay/search/promotion semantics remain unchanged. M11-C does not teach Scanner automatic pair replay to use bridge execution.

### 7. Product/API truth is explicit

Pair Study/Pair Research can distinguish at least these economic states in user language:

- real direct replay ready;
- two-leg bridge available but transient authority needed;
- two-leg bridge admitted/ready;
- no honest economic expression available.

Relationship readiness remains independent from each state.

## Required validation

Testing remains opt-in and is **not authorized** for this mission. Do not create, modify, or run pytest, Vitest, Playwright-test, integration, regression or TDD tests.

Required non-test evidence:

- inspect the exact compiled W/PIXEL manifest(s) and verify declared instrument roles, execution IDs, bridge asset and absence of a synthetic pair instrument;
- run one isolated real-data W/PIXEL historical recipe through the existing experiment runner after explicit transient USDT authority is granted;
- inspect resulting fills, costs, inventory/bridge residue, HODL/control economics and ordinary run/compilation lineage;
- show that the same W/PIXEL Pair Study remains ready while permission is absent;
- verify a real-direct pair still chooses the existing direct path if a suitable admitted example is available without manufacturing state;
- if public API contracts change, regenerate/check `web/openapi.json` and `web/src/api/schema.d.ts` through the existing deterministic flow;
- run only the smallest relevant final Ruff/format/Pyright checks for changed Python boundaries, `pnpm typecheck`/`pnpm build` if frontend/API consumption changes, and `git diff --check` once at candidate final state.

Do not run broad repository suites or source-wide test collections merely for confidence.

## Stop conditions

Stop and return `NEEDS DESIGN REVIEW` rather than implementing around any of these:

- the existing multi-asset executor cannot represent the two-asset long-only target without changing economic semantics;
- honest bridge replay would require a synthetic W/PIXEL price/fill/candle series;
- canonical bridge permission cannot be represented without treating USDT as an economic target asset;
- preserving the selected Pair Study venue/cutoff would require silently weakening identity/PIT authority;
- the only apparent path is a second router, backtester, ledger, strategy engine or automatic route graph;
- Scanner Slice-1 would have to change its replay denominator/search semantics;
- HODL/control/cost/timing/accounting or final-OOS semantics would have to change;
- current residual/OLS would need to be relabeled formal cointegration or Copula implemented.

A narrow public Product/API contract amendment, new semantically correct support reason, or additive manifest field is not itself a stop condition when directly required by the approved M11-C design.

## Out of scope

- formal Engle-Granger/ADF, half-life or Hurst implementation;
- Student-t Copula implementation;
- new pair signal/model families or parameter search;
- M11-D final research-conclusion aggregation/presentation;
- automatic bridge/route discovery;
- live/private exchange execution;
- leverage, borrowing, shorting, derivatives or synthetic exposure;
- changing fixed-basket economics unless a demonstrated shared invariant requires a tiny compatibility adjustment;
- broad Product settings/permission architecture;
- Pair Study persistence/History design.

## Working style

Before the first source mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Use Persistent Agent Loop for execution lifetime. Status/progress questions and compatible steering are in-mission steering events, not stop commands. Preserve valid runtime/wait state and continue unless explicitly stopped/replaced or completion is verified.

Trace the actual pair draft -> support -> compiler -> manifest -> model policy -> runner -> multi-asset execution path before mutating. Reuse current fixed-basket bridge and Phase-11 execution/accounting behavior where it already solves the problem. Do not create a second execution path.

Keep all connected WSL repository/filesystem/Git/process/runtime work through the harness. Do not substitute ChatGPT container/Python for connected WSL operations.

## Finish report

Return:

1. status: complete / blocked / needs design review;
2. branch/worktree/commit and final Git status;
3. exact transient bridge authority semantics and persistence/API changes;
4. exact manifest/compiler/model-policy contract change and backward-compatibility behavior;
5. exact Product default-pair execution selection behavior;
6. M10-A support result before and after permission;
7. real W/PIXEL run evidence: manifests, instruments, fills/costs, bridge inventory/residue, HODL/control and run lineage;
8. required non-test validation actually performed;
9. deviations/limitations and exact M11-D handoff facts.
