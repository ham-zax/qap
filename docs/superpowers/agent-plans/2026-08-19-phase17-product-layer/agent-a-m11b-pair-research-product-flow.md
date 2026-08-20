# Agent A — M11-B Pair Research Product Flow

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed Product/browser/API consumption
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m11b-pair-research-product`
**Isolation reason:** `main` contains protected live-session `catalog.json` and `product-market-data/` state, while this mission requires writable Product code plus browser/runtime evidence. No concurrent production writer is authorized.
**Can start:** immediately after this coordination package is integrated
**Depends on:** M11-A integrated on `main` through `2f055d1`
**Execution lifetime:** `persistent-agent-loop` required
**Wake strategy:** Terminal + event wait when a persistent API/web process is needed; otherwise bounded Dev commands
**Developer visibility:** headless by default; headed browser evidence is required before completion and may be presented on request

## Read first

- `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md` — authoritative Pair Study contract
- `docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md` — M11 sequence; M11-B is Section 5
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — current dependency and ownership map
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/m10d-representative-user-acceptance.md` — final human task context; do not simulate participant acceptance

Inspect the integrated implementation before deciding details. M11-A changed the public API, so stale M10-B assumptions are not authoritative.

## Objective

Make ordinary Pair Research follow the researcher's question rather than an executable-recipe prerequisite.

A user selecting `W / PIXEL · Medium-term` must be able to click one obvious research action, remain on the Research surface, prepare only the selected pair when needed, and see backend-owned relationship evidence even though no real direct `W/PIXEL` market exists.

Pair Study readiness and economic-recipe readiness are independent facts. Direct-market absence must never be presented as Pair Research failure.

## Current state

M11-A is integrated through `2f055d1` and provides:

- optional pair-scoped Product preparation through the existing market-data owner using `asset_ids` and optional `analysis_reference_ids`;
- `GET /api/product-pair-study/context`;
- `GET /api/product-pair-study/series`;
- exact same-venue Pair Study selection with fail-closed unique current paths;
- one common selected-pair safe cutoff;
- immutable generation/provenance identities and source fingerprints;
- backend raw ratio, log ratio, normalized paths, `rolling_log_ratio_zscore`, and `rolling_log_price_ols_residual_zscore` observations;
- optional descriptive analysis-reference data;
- direct-market/economic-expression status kept separate from relationship readiness;
- generated OpenAPI and TypeScript contracts synchronized on `main`.

The real M11-A acceptance case used Gate `W_USDT + PIXEL_USDT`. The Pair Study was ready with no direct `W/PIXEL` market.

The current React flow is still M10-B-shaped:

- `ResearchHome.tsx` vertically stacks Pair Research, Universal Scan, and Experiment Lab;
- `PairResearch.tsx` asks for a default executable recipe before presenting the relationship study;
- pair preparation is still invoked from the old recipe issue path rather than from Pair Study context;
- Pair Study context/series are not yet consumed by the browser.

## Ownership

You own:

- the normal Research task-mode composition needed to make one active task primary;
- Pair Research orchestration over the integrated Pair Study context/series APIs;
- scoped preparation for the exact selected pair/timeframe;
- presentation of backend-owned Pair Study relationship values and chart data;
- preservation of the selected pair/timeframe/orientation across bounded identity/admission/data setup;
- the smallest frontend API client/query/type wiring required to consume the already-generated M11-A contract;
- a focused Pair Study result/chart component if that keeps `PairResearch.tsx` understandable;
- plain-language separation of relationship evidence from economic replay status.

Neighboring ownership remains:

- Universal Scan / current-approved scanner semantics: existing Product/scanner owners;
- Experiment Lab recipe authoring and M10-A support truth: existing recipe owners;
- two-leg Pair Research economics, manifest roles, transient USDT authority, bridge execution: **M11-C**;
- formal Engle-Granger/ADF cointegration: later method-admission work;
- Student-t Copula implementation: not this mission;
- final integrated economic conclusion presentation: M11-D;
- representative-user acceptance: human-led M10-D after M11 completes.

## Coordination contract

Treat the M11-A public contract at `2f055d1` as stable unless direct evidence shows a projection gap that prevents the required Product behavior.

Do not move relationship calculations into React. React may format and graph values returned by the backend but may not derive ratio, log ratio, normalized relationship truth, OLS coefficients, z-scores, readiness, or economic verdicts.

Do not reinterpret `economic_expression.direct_status=unavailable` as `data.status=needs_setup` or Pair Study failure.

Do not add bridge permission, `relationship_instrument_ids`, `multi_asset_bridge` pair compilation, or any execution/economic formula. If ordinary Pair Study presentation cannot be completed without such a change, stop and report the concrete M11-C dependency instead of absorbing it.

Universal Scan continues to use unscoped Product preparation. Pair Research must pass the exact selected pair to scoped preparation. Do not make the scanner inherit Pair Study scope.

Known-unimplemented method presentation must come from existing M10-A backend capability truth; do not create a React method registry. Residual / OLS remains Residual / OLS, not formal cointegration.

## Success conditions

### 1. One active Research job

The normal Research surface offers clear task choices equivalent to:

```text
Research a pair | Scan my universe | Experiment Lab
```

Only the active task's primary workflow dominates the page. Pair Research is the normal/default manual research task. Universal Scan and Experiment Lab remain accessible without being vertically stacked as simultaneous primary workflows.

Previous research / advanced strict-PIT evidence may remain available as secondary/history/advanced content without competing with the active task.

### 2. Small pair question first

Normal Pair Research input is centered on:

```text
Asset A
Asset B
Timeframe
[ Research this pair ]
```

Exact-first asset search remains intact. Genuine unresolved identity and explicit economic-asset approval remain fail-closed one-time interruptions, but the selected pair and timeframe stay intact.

Do not require the user to understand recipe hashes, dataset IDs, identity versions, or generation paths during routine successful research.

### 3. One Pair Study action

For a resolved/approved selected pair, `Research this pair`:

1. reads Pair Study context;
2. if selected-pair data needs setup, invokes existing Product preparation with the exact two `asset_ids` and selected horizon;
3. refreshes Pair Study context;
4. reads series when relationship data is ready;
5. checks M10-A default recipe support only when the backend can truthfully declare a default recipe.

The user remains on the Research screen throughout routine preparation.

Unrelated approved assets must not enter the pair-scoped preparation request.

### 4. Relationship evidence is the primary result

When Pair Study is ready, show the backend-owned facts needed to understand the selected relationship, including:

- pair/orientation;
- Product timeframe and selected venue;
- common safe cutoff/data-through time;
- exact selected `ASSET/USDT` path readiness in user language;
- current raw ratio and log ratio;
- rolling log-ratio model ID/version, status, window/required/coverage observations, and current score when valid;
- Residual / OLS model ID/version, orientation, status, alpha, beta, current residual z-score, and coverage when valid;
- ratio/log-ratio/normalized-path chart data from the Pair Study series endpoint;
- method-invalid/insufficient-history/variance states as evidence states rather than application failures.

Technical generation/fingerprint/path provenance remains available through progressive disclosure rather than primary copy.

### 5. Economic replay is clearly downstream

For the accepted `W / PIXEL` case:

- relationship research is shown as ready/valid when the backend says so;
- no direct `W/PIXEL` market is shown as a separate economic limitation;
- the page does not say the pair failed or that research is unavailable;
- no fake or synthetic `W/PIXEL` execution market is implied;
- because M11-C is not implemented yet, two-leg bridge economics remain explicitly unavailable/not-yet-admitted rather than guessed in React.

If a real direct market exists and the backend can declare the existing default recipe, Pair Research may continue into the existing M10-A support/run flow after the study. Do not make that flow a prerequisite for seeing the study.

### 6. Known method truth remains visible without false implementation

The normal Pair Research result can explain known method capability using existing backend capability descriptors. At minimum:

- rolling log-ratio relationship evidence: supported;
- Residual / OLS relationship evidence: supported;
- Student-t Copula: known but unimplemented;
- do not label Residual / OLS as cointegration.

Do not add formal cointegration, ADF, half-life, Hurst, or Copula computation in this mission.

### 7. Optional BTC/reference lens stays descriptive

If the existing M11-A `analysis_reference` path can be wired with a small Product-only change, expose a bounded analysis lens such as:

```text
Relationship | Relative to BTC
```

It must use `analysis_reference_ids` during scoped preparation and Pair Study reference-series data. It must not approve BTC as an economic target, change basket membership, imply BTC execution, or infer identity by ticker equality.

If current UX state cannot represent the reference safely without expanding identity/admission authority, leave the lens unavailable and report the concrete limitation. Do not broaden scope to solve it.

### 8. Observable W / PIXEL acceptance

Using a headed browser against an isolated/safe Local Market Product workspace, demonstrate:

```text
W / PIXEL · Medium-term
```

with one `Research this pair` action. The final rendered state must show actual backend Pair Study relationship values while direct pair economic replay remains unavailable separately.

The headed run must demonstrate that no unrelated BTC generation is required merely because BTC exists elsewhere in the approved universe.

## Required validation

Testing remains opt-in and is **not authorized** for this mission. Do not create, modify, or run unit, integration, Vitest, Playwright-test, or pytest tests.

Required non-test evidence:

- `pnpm typecheck` for the changed frontend/API consumption boundary;
- `pnpm build` once at candidate final state;
- a real headed browser walkthrough of `W / PIXEL · Medium-term` using the integrated Pair Study backend, capturing the observable success conditions above;
- `git diff --check`;
- if this mission must change an OpenAPI-visible backend contract despite the expected stable M11-A API, regenerate/check `web/openapi.json` and `web/src/api/schema.d.ts`, explain why the backend change was required, and keep it to the demonstrated projection gap.

Do not run broad Python/repository test suites. Do not run additional static gates merely for confidence.

## Out of scope

- `relationship_instrument_ids` or any manifest/compiler role amendment;
- transient USDT execution permission;
- `multi_asset_bridge` pair recipe compilation or replay;
- changes to fills, costs, ledger, HODL, controls, or final-OOS;
- Scanner Slice-1 search/promotion/direct-replay semantics;
- Universal/Focus scanner redesign;
- formal cointegration/ADF/half-life/Hurst implementation;
- Student-t Copula implementation;
- Pair Study persistence/History object design;
- M11-D final research-conclusion aggregation;
- human representative-user acceptance.

## Working style

Before the first source mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Use Persistent Agent Loop for execution lifetime. Status/progress questions and compatible steering are in-mission steering events, not stop commands. Preserve valid runtime/wait state and continue unless explicitly stopped/replaced or completion is verified.

Explore the integrated code before deciding implementation details. Prefer existing React/query/chart primitives and current Pair Study APIs over new abstractions. Do not create another Product workflow engine or frontend scientific registry.

Keep all WSL repository/filesystem/Git/process/browser-runtime work through the connected harness. Do not substitute ChatGPT container/Python for connected WSL operations.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git status;
3. exact user-visible Pair Research behavior delivered;
4. frontend/API interfaces consumed or changed;
5. required non-test validation actually performed;
6. exact headed `W / PIXEL · Medium-term` evidence and observed backend values/state;
7. deviations from this mission;
8. concrete blockers/contract facts that M11-C needs to know.
