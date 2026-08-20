# Agent A — M11-D Integrated Pair Research Completion

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed Product/read composition
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m11d-pair-research-completion`
**Isolation reason:** `main` contains protected live-session `catalog.json` and `product-market-data/` state, while this mission requires writable Product code plus a headed end-to-end browser/runtime proof. No concurrent production writer is authorized.
**Can start:** immediately after this coordination package is integrated
**Depends on:** M11-A integrated through `2f055d1`; M11-B at `9890431`; M11-C integrated through `3095c98`
**Execution lifetime:** `persistent-agent-loop` required
**Wake strategy:** Terminal + event wait when durable API/web processes are needed; bounded Dev commands otherwise
**Developer visibility:** headless by default; headed browser evidence is required before completion

## Read first

- `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md` — authoritative research-question → evidence → experiment → economics contract
- `docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md` — M11-D is Section 7
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — current dependency/ownership map
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-a-m11c-pair-bridge-economics.md` — integrated economic-expression handoff
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/m10d-representative-user-acceptance.md` — final human acceptance context; do not simulate participant acceptance

Inspect the integrated repository before deciding details. M11-D should compose existing authoritative reads, not recreate economics or relationship logic.

## Objective

Let a normal user begin with the question `W / PIXEL · Medium-term` and finish the current development research cycle on the same Research surface with a truthful, understandable conclusion:

```text
QUESTION
  W / PIXEL · Medium-term

RELATIONSHIP
  exact Pair Study evidence

EXPERIMENT
  exact default/predeclared variant(s) actually run

ECONOMICS
  strategy, strict HODL, primary control, costs and drawdown

CONCLUSION
  positive / neutral / negative development evidence,
  or final-OOS status when that is what the existing artifact says

LIMITATIONS
  what this result does not establish

EXACT RUNS / PROVENANCE
  existing run and recipe-lineage links
```

A negative result is a completed research result. Development evidence must never be presented as final OOS, and multiple predeclared development variants must never be silently collapsed into a selected winner.

## Current state

The integrated M11 path now provides all scientific/economic authority needed for this mission:

- M11-A: Pair Study context/series with exact selected venue, cutoff, immutable generations, ratio/log-ratio/normalized paths and relationship observations;
- M11-B: study-first Research task, one `Research this pair` action, scoped preparation, relationship results, existing M10-A support/run continuation;
- M11-C: direct-first Product pair recipe selection, honest two-leg `multi_asset_bridge` fallback through exact same-venue `ASSET/USDT` legs, explicit transient USDT research authority, and ordinary M10-A compilation/run lineage.

The existing read APIs already expose the completion facts:

- completed operation result contains exact `run_ids[]` and compilation identity;
- `GET /api/experiments/{run_id}` returns `ExperimentDetailDto`, including exact manifest, provenance, `ExperimentResult`, data role, final-OOS consumption, result status, HODL/control comparisons, role terminal values/costs/turnover and maximum relative drawdown;
- `GET /api/research-recipes/runs/{run_id}/lineage` returns the exact recipe/compilation lineage;
- existing frontend presentation helpers under `features/experiments` already map backend result status and data role to user language.

Therefore **no new backend economic aggregation or verdict API is expected for M11-D**. If the current public reads genuinely lack one required authoritative fact, identify that concrete projection gap before broadening scope and add only the smallest read-only projection needed. Do not add backend arithmetic or a second result model.

The real M11-C W/PIXEL development proof produced two default/predeclared runs. Both were negative against HODL and the primary control. M11-D must be able to present that outcome honestly rather than treating completion as success.

## Ownership

You own:

- Product composition that turns completed Pair Research run IDs into inline research-completion evidence on the Research surface;
- consumption of existing experiment and recipe-lineage reads for each exact run;
- clear grouping of question, relationship evidence, experiment variant/method, economic expression, benchmark economics, conclusion, limitations and technical lineage;
- preservation of Pair Study evidence while economic results load or fail independently;
- presentation of multiple default development variants without automatic winner selection;
- reuse of existing experiment/result presentation semantics wherever possible;
- the headed end-to-end `W / PIXEL · Medium-term` completion proof.

Neighboring ownership remains:

- relationship formulas/Pair Study truth: existing backend owners;
- recipe support/compiler/manifest/bridge authority: M10-A + M11-C owners;
- fills, fees, slippage, turnover, accounting, HODL, controls, drawdown and result status: existing experiment authorities;
- final-OOS reservation/selection/consumption semantics: existing M10-A/final-OOS owners;
- explicit method/parameter authoring and future family selection: Experiment Lab;
- formal cointegration and Student-t Copula implementation: separate future method-admission work;
- representative-user acceptance: human-led M10-D after this mission integrates.

## Coordination contract

### Reuse authoritative results

Do not calculate research/economic truth in React.

React may format and arrange exact backend fields, but must not derive:

- relationship values or z-scores;
- strategy-vs-HODL/control economics;
- fees/slippage/turnover totals;
- drawdown;
- result status;
- development/final-OOS classification;
- execution validity;
- a cross-variant winner or promotion decision.

Prefer existing `ExperimentDetailDto`, recipe-lineage reads and existing experiment presentation helpers over a new frontend verdict registry.

### Preserve variant honesty

The canonical Pair Research development recipe currently runs two predeclared variants:

- rolling log-ratio z-score;
- Residual / OLS mean-reversion.

When both complete, show them as sibling development results. Do not choose the best result automatically, call one "the strategy", or imply that trying both creates final-OOS evidence.

If the current operation contains one run, present one. If it contains multiple exact runs, present each exact result with its method/variant identity.

### Preserve research-layer separation

The normal completion flow must remain understandable as:

```text
relationship evidence
    ≠ economic result
    ≠ final-OOS claim
```

A relationship can be valid while economics are negative. A development result can be positive while still not final OOS. An economic run can be blocked/unavailable without invalidating the Pair Study.

### Economic expression is backend truth

For each run, describe execution from the exact manifest:

- direct market when `execution.mode=direct`;
- real two-leg bridge when `execution.mode=multi_asset_bridge`, including the declared bridge asset and exact real instruments.

Do not infer an execution route from ticker text and never imply a synthetic pair market.

### Completion does not mean promotion

M11-D is presentation/composition only. Do not add a Product promotion state machine, automatic variant selection, final-OOS button flow, or new research lifecycle database.

Experiment Lab remains the advanced surface for explicit recipe/family work. Pair Research may link users to exact run evidence and explain that development evidence is not final OOS.

## Success conditions

### 1. Same-screen completion

After the existing Pair Research recipe operation completes, the Research page loads and presents the exact completed run result(s) without requiring the user to leave the research question merely to understand the outcome.

Existing links to detailed Experiment/Activity evidence remain available.

### 2. Question and relationship stay visible

The completion state retains the selected pair, orientation, timeframe, venue, data-through cutoff and Pair Study relationship evidence already shown by M11-B.

Running economics must not replace or erase the relationship evidence.

### 3. Exact experiment identity

For every returned run, show enough backend-owned identity to understand what was tested:

- relationship method/component and variant identity;
- relevant declared method parameters from the exact manifest/config in user language;
- execution mode and bridge/direct expression;
- development versus final-OOS role from the exact result/provenance;
- exact run link.

Technical hashes remain progressive disclosure rather than primary copy.

### 4. Economics are complete and benchmarked

For every completed run, show authoritative backend values sufficient to answer whether the economic expression helped:

- strategy terminal value;
- strict inventory HODL terminal value;
- declared primary-control terminal value when present;
- strategy vs HODL;
- strategy vs primary control when present;
- strategy fill count, fees, slippage and turnover from the strategy role;
- maximum relative drawdown versus HODL;
- predeclared result status/success threshold where useful.

Do not recompute these values in React.

### 5. Truthful conclusion language

Use existing result-status/data-role semantics to make the result understandable.

Required behavior:

- negative backend status is presented as completed negative research, not application failure;
- neutral remains neutral;
- positive development is described as development evidence, not final proof;
- `data_role=final_oos` is shown as final OOS only when the existing artifact says so and holdout consumption semantics are satisfied;
- if multiple sibling development variants differ, show the separate outcomes rather than synthesizing one overall verdict.

For the known W/PIXEL M11-C evidence, both default development variants must truthfully render as negative relative to their benchmark evidence.

### 6. Limitations remain explicit

The completion state must make clear that a development historical replay does not establish, unless an existing artifact explicitly does:

- final-OOS confirmation;
- live-trading authority;
- current capacity/tradability;
- formal cointegration;
- Student-t Copula evidence;
- causal attribution to one asset or relationship merely from terminal wealth differences.

Do not overload the primary result with internal governance language; use concise plain-language limitations with technical detail behind disclosure when useful.

### 7. Exact lineage remains inspectable

For each run, preserve links/access to:

- run ID;
- recipe/compilation lineage;
- manifest/execution identity;
- existing Experiment detail page;
- existing Activity operation.

Do not create parallel lineage identifiers.

### 8. Observable W / PIXEL completion proof

Using a headed browser against an isolated/safe Local Market Product workspace, demonstrate the full current development journey:

```text
Research a pair
→ W / PIXEL · Medium-term
→ Pair Study relationship ready
→ direct market unavailable
→ explicit temporary USDT research authority if not already granted
→ M10-A support runnable
→ run exact recipe
→ completed default development variants
→ inline research conclusions
```

The rendered result must show the actual backend outcomes for the two W/PIXEL development variants and make clear that they are completed negative development evidence, not final OOS and not a failed application.

If the exact historical data used in M11-C is reused, the visible economics should reconcile with the authoritative run artifacts rather than being hard-coded.

## Required validation

Testing remains opt-in and is **not authorized** for this mission. Do not create, modify, or run unit, integration, Vitest, Playwright-test, pytest, regression or TDD tests.

Required non-test evidence:

- `pnpm typecheck` for changed frontend/read consumption;
- `pnpm build` once at candidate final state;
- headed end-to-end `W / PIXEL · Medium-term` browser walkthrough through completed inline results;
- inspect exact experiment/run-lineage API values behind the rendered result and confirm the UI does not recompute verdict/economics;
- `git diff --check` once at candidate final state.

If an OpenAPI-visible backend read contract unexpectedly changes, regenerate/check `web/openapi.json` and `web/src/api/schema.d.ts` through the existing deterministic flow and explain the demonstrated projection gap. Do not run broad Python/static suites merely for confidence if backend code is unchanged.

## Out of scope

- new relationship/economic formulas;
- new backend verdict or aggregation engine;
- changes to `ExperimentResult`, HODL/control/cost/drawdown semantics unless a concrete read projection defect makes the requested presentation impossible;
- manifest/compiler/relationship-instrument changes;
- transient bridge authority changes;
- Scanner semantics;
- automatic variant selection or promotion;
- final-OOS orchestration/reservation/consumption changes;
- formal Engle-Granger/ADF, half-life or Hurst implementation;
- Student-t Copula implementation;
- live/private trading;
- Pair Study persistence or new History database;
- representative-user M10-D acceptance.

## Working style

Before the first source mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Use Persistent Agent Loop for execution lifetime. Status/progress questions and compatible steering are in-mission steering events, not stop commands. Preserve valid runtime/wait state and continue unless explicitly stopped/replaced or completion is verified.

Trace the existing completed operation → experiment read → result/roles → recipe lineage path before adding code. Reuse current Product/Experiment presentation primitives and formatting helpers. Avoid a new research-result abstraction unless it materially reduces duplicated current logic.

Keep all connected WSL repository/filesystem/Git/process/browser-runtime work through the harness. Do not substitute ChatGPT container/Python for connected WSL operations.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git status;
3. exact same-screen research-completion behavior delivered;
4. existing API/read contracts consumed and any contract change, if one was truly required;
5. exact variant/result/conclusion semantics presented;
6. headed `W / PIXEL · Medium-term` completion evidence with actual backend economics;
7. required non-test validation actually performed;
8. deviations/limitations and exact facts needed for the final M10-D human acceptance rerun.
