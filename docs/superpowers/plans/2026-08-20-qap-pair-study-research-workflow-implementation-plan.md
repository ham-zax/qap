# QAP Pair Study Research Workflow Implementation Plan

**Status:** IMPLEMENTED — M11-0 is approved/frozen; M11-A is integrated through `2f055d1`, M11-B at `9890431`, M11-C through `3095c98`, and M11-D integrated research completion through `3528973`. The remaining Phase-17 gate is the human-led M10-D representative-user rerun.

**Phase:** 17 follow-on, proposed as M11 after the first M10-D human Pair Research session exposed an architecture gap.

**Goal:** Restore the researcher's primary job — select two assets, understand their relationship, form/test an economic hypothesis, and complete the research honestly — without restoring legacy synthetic execution, Copula authority, hidden identity assumptions, or a second research engine.

**Architecture:** Add a Product Pair Study read composition over existing immutable Product market data and `qap.relationship`. Pair Study is upstream of `ResearchRecipeV1`. Extend Product market-data preparation with selected-pair scope. Keep M10-A recipe/support/compiler/final-OOS authority unchanged. After Pair Study, use the existing direct replay when a real pair market exists or the existing Phase-11 `multi_asset_bridge` executor when exact same-venue quote legs and explicit transient bridge authority exist. Preserve Scanner-V1 as a separate automatic discovery owner.

## 1. Global constraints

- The Pair Study design is authoritative for this plan once approved.
- Preserve long-only, owned-inventory, Spot-only, no leverage/borrowing/derivatives/riba mechanics.
- Preserve QAP wealth versus matched HODL and the predeclared primary control as the economic claim boundary.
- Preserve strict historical PIT semantics and current-approved Product claim separation.
- Preserve explicit asset admission and fail-closed canonical identity.
- Preserve Scanner-V1 search, promotion, replay-attempt denominator, Research Idea, and prospective semantics.
- Preserve M10-A `ResearchRecipeV1`, `SupportReportV1`, stable `research_family_id`, compilation lineage, and final-OOS reservation/consumption semantics.
- Preserve existing `evidence_instrument_ids` as evidence-only for current direct/scanner runs.
- Do not synthesize `A/B` execution candles from `A/USDT` and `B/USDT`.
- Do not create a second backtester, second ledger, generic strategy DSL, plugin runtime, arbitrary Python execution, generic workflow engine, automatic route graph, or automatic portfolio optimizer.
- Do not calculate relationship/economic values in React.
- Formal cointegration and Student-t Copula are not part of the initial Pair Study implementation unless separately admitted.
- Testing is opt-in. This plan does not authorize creating, modifying, or running tests. Use direct runtime/browser evidence and the smallest relevant non-test static/build checks.

## 2. Execution shape

Use a sequential foundation-first implementation. The backend contracts are shared and later Product behavior depends on them.

```text
M11-0  Pair Study design freeze
          |
          v
M11-A  Pair-scoped data + Pair Study backend/API
          |
          v
M11-B  Pair Research Product flow + current relationship values
          |
          v
M11-C  Honest two-leg pair economics through existing bridge executor
          |
          v
M11-D  Integrated research-completion presentation/evidence
          |
          v
M10-D  representative-user acceptance rerun
```

Do not parallelize M11-A and M11-C. M11-C changes the experiment contract and must build on the exact Pair Study/data behavior proved by M11-A/B.

Formal cointegration recovery is a separate later method-admission wave and is not required to prove the Pair Study architecture.

## 3. M11-0 — Design approval

**Artifact type:** design/documentation.

**Deliverables:**

- `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md`
- this implementation plan;
- Phase-17 status/coordination updates showing M10-D blocked by the Pair Study redesign rather than a bounded UI-only patch.

**Acceptance:** the design explicitly separates relationship study from economic replay, freezes pair-scoped preparation, and resolves how real two-leg economics can reuse existing execution without synthetic markets.

No production code begins before approval.

## 4. M11-A — Pair-scoped preparation + Pair Study backend

### Mission

Make `W / PIXEL · Medium-term` a valid research question even when no direct `WPIXEL` market exists.

The backend must prepare only the selected question, bind exact same-venue immutable data, compute current admitted relationship evidence, and return one Pair Study context/series projection.

### Primary owners

Expected owner files include:

- `src/qap/product_market_data_prepare.py`
- the Product market-data request DTO and route under `src/qap/api/`
- `src/qap/product_universe.py` only if an exact selected/reference scope read is needed;
- new focused Product composition, preferably `src/qap/product_pair_study.py`;
- new Pair Study API DTOs/routes under `src/qap/api/`;
- existing `qap.relationship`, `qap.market`, and immutable generation readers as dependencies only.

Do not modify `qap.relationship` formulas merely to project them into Product.

### 4.1 Extend market-data preparation with optional selected scope

Current preparation accepts only horizons and iterates the entire resolved approved scope.

Extend the request conceptually to:

```text
horizons[]
asset_ids[]?                 # economic assets selected by Pair Study
analysis_reference_ids[]?   # optional descriptive references
```

Semantics:

- no `asset_ids` -> existing universe-wide behavior, preserving Universal Scan;
- exactly two `asset_ids` from Pair Research -> acquire only relevant resolved/current paths and real direct markets for those assets;
- an analysis reference is data-only/descriptive and must never become an economic target through this request.

The owner filters the resolved Product instrument scope before acquisition. Do not create a separate pair fetcher.

### 4.2 Preserve the bounded M10-D acquisition fixes

Carry forward the demonstrated operational corrections from remediation commit `6609a1c` after reviewing them against the approved design:

- if a Gate archive segment fails exact QAP bar validation, reject that archive candidate and use the existing official REST acquisition path for the required window;
- freeze one shared completed preparation cutoff for the selected operation so required 1h/4h or 4h/1d paths do not drift by a few hours merely because they were acquired sequentially.

Do not merge invalid archive rows or weaken contiguous-bar validation.

### 4.3 Resolve one venue-local Pair Study

Given pair, horizon, and optional venue:

1. require both economic assets to have resolved canonical identity and Product approval;
2. find same-venue `ASSET/USDT` paths satisfying the selected horizon after preparation;
3. never combine evidence legs across venues;
4. determine one common safe cutoff from the exact selected paths;
5. surface all valid venue options if more than one exists;
6. surface a real direct pair market separately when one exists;
7. do not require the direct market to build relationship evidence.

### 4.4 Build PairStudyContextV1

The new Product owner composes existing domain functions and returns at least:

```text
question
  asset_a / asset_b
  canonical pair
  orientation
  horizon
  venue
  coordinate asset
  safe cutoff

data
  ready / needs_setup
  exact path/generation references
  reasons
  direct-market availability
relationship
  current raw ratio
  current log ratio
  normalized path summary
  rolling-log-ratio observation
  residual/OLS observation
analysis lens availability
economic-expression availability summary
technical provenance
```

Do not invent one exclusive overall research status. Preserve independent data/method/execution facts.

### 4.5 Build bounded series read

Return chart-sized synchronized backend data for:

- oriented raw ratio;
- log ratio;
- normalized asset paths;
- optional analysis-reference paths when requested and valid.

Reuse `qap.relationship` ratio/anchor primitives. Do not duplicate formulas in API code.

### 4.6 Current method values

Use only admitted current methods:

- `rolling_log_ratio_observation()`;
- `rolling_residual_observation()`.

Expose their exact model IDs/versions, orientation, window/required/coverage observations, status, `as_of`, and values.

Do not add a cointegration p-value, Hurst, half-life, Copula statistic, or invented interpretation.

### M11-A acceptance

With an isolated Product workspace and real admitted public data, `W / PIXEL · Medium-term` can produce a Pair Study over exact same-venue W/USDT + PIXEL/USDT data even when the direct `WPIXEL` market is absent.

The read must show actual backend ratio/log-ratio and current rolling log-ratio/residual-OLS values when valid, plus exact safe cutoff/source provenance.

A failure in unrelated approved BTC data must not block the selected W/PIXEL preparation.

## 5. M11-B — Research Product flow

### Mission

Make the normal Research screen follow the researcher's task rather than expose three backend workflows simultaneously.

### Primary owners

Expected files:

- `web/src/features/discovery/ResearchHome.tsx`
- `web/src/features/discovery/PairResearch.tsx`
- a focused Pair Study results/chart component rather than growing `PairResearch.tsx` indefinitely;
- `web/src/features/discovery/ProductResearch.tsx` only for mode composition, not scanner semantics;
- `web/src/features/discovery/ExperimentLab.tsx` only for mode composition;
- `web/src/api/client.ts`, queries, and generated OpenAPI TypeScript types for the new backend reads;
- `web/src/components/ScreenGuide.tsx` for task guidance.

### 5.1 One active Research task

Replace the vertical stack with one active mode:

```text
Research a pair | Scan my universe | Experiment Lab
```

Default to Pair Research for the normal manual research job.

Do not alter Universal Scan ownership or Experiment Lab recipe semantics.

### 5.2 Small Pair Research form

Normal input:

```text
Asset A
Asset B
Timeframe
[ Research this pair ]
```

Preserve exact-first asset search and current bounded identity/admission interruption behavior.

Keep the unfinished pair/timeframe/orientation draft across setup.

Do not send ordinary selected-pair setup to Research Universe unless a genuine identity ambiguity cannot be resolved inline.

### 5.3 One preparation action

`Research this pair` performs:

1. exact Pair Study context read;
2. scoped Product preparation when needed;
3. context refresh;
4. relationship computation/read;
5. M10-A default recipe support check only when the backend can truthfully declare a default economic recipe.

The user remains on the same screen.

### 5.4 Immediate values

After success show:

- pair/orientation;
- selected venue;
- safe cutoff;
- W/USDT and PIXEL/USDT data state;
- current ratio/log ratio;
- rolling log-ratio z-score;
- Residual / OLS alpha, beta, residual z-score;
- window/coverage/status;
- direct-market availability as a separate economic fact;
- known-unimplemented methods such as Student-t Copula with M10-A truth.

No React scientific calculations.

### 5.5 Optional BTC lens

If the approved design's analysis-reference role can be implemented without weakening identity authority, expose a small optional lens:

```text
Relationship | Relative to BTC
```

When BTC reference identity/data is unavailable, show a bounded descriptive setup/unavailable state. Do not force BTC into the economic Research Universe and do not fabricate BTC execution markets.

If current Product identity/admission structures cannot represent this safely with a small explicit change, stop this subtask and report `DESIGN REVIEW REQUIRED`; do not silently approve BTC as an economic asset.

### M11-B acceptance

A headed browser walkthrough can select exact W, exact PIXEL, Medium-term, click one `Research this pair` action, stay on Research, and immediately see actual Pair Study values even though no direct W/PIXEL market exists.

The page clearly says that direct economic replay is a separate question.

## 6. M11-C — Two-leg pair economics through existing QAP execution

### Mission

Allow a manually selected two-asset Pair Research experiment to use existing real same-venue `ASSET/USDT` execution legs when no direct `A/B` market exists, without synthesizing an `A/B` market or weakening the evidence-only Scanner Slice-1 contract.

This is the only milestone in this plan that changes the experiment/manifest contract. Re-read the approved design before its first source mutation.

Current code already provides the relevant economic path: the generic replay accepts multiple declared execution instruments plus one bridge, and basket-specific manifest restrictions apply only to `basket_graph`. Do not rewrite that executor. The demonstrated seam is the current evidence-only relationship-input contract.

### Primary owners

Expected files:

- `src/qap/experiment/manifest.py`
- `src/qap/experiment/model_policies.py`
- `src/qap/research_recipe_compiler.py`
- `src/qap/research_recipe_product.py`
- Product state/universe owner for explicit transient bridge permission;
- API/Product presentation only as required to expose that permission/status.

The existing Phase-11 routing/replay/ledger/evaluation code is reused. Do not create pair-specific routing or accounting.

### 6.1 Add explicit relationship-input instrument role

Preserve `evidence_instrument_ids` as evidence-only.

Add one explicit manifest field, conceptually:

```text
relationship_instrument_ids
```

Rules:

- IDs reference declared exact instruments/data sources;
- relationship models consume these IDs when present;
- they may overlap execution IDs;
- overlap does not grant execution authority — execution IDs still come from `ExecutionSpec`;
- existing direct/scanner manifests without the field continue to use current evidence-only behavior;
- evidence-only IDs remain prohibited from execution.

Do not reinterpret old manifests silently.

### 6.2 Compiler mapping

For direct Pair Research:

```text
relationship inputs = A/USDT + B/USDT evidence bindings
execution            = real A/B direct binding
```

For two-leg Pair Research:

```text
relationship inputs = A/USDT + B/USDT
execution            = the same A/USDT + B/USDT declared real instruments
mode                 = multi_asset_bridge
bridge_asset         = USDT
```

Do not change `ResearchRecipeV1` merely to duplicate those IDs in another recipe field. For the bounded pair/bridge case, the compiler may derive `relationship_instrument_ids` only after validating that the exact two execution bindings are `A/USDT` and `B/USDT` for the selected pair and explicit bridge. Any additional/missing/ambiguous execution binding is a compile failure.

The compiler binds the exact dataset IDs. React does not select IDs or infer instrument roles.

### 6.3 Explicit transient USDT authority

Add one Product-owned persisted operator permission for transient research-execution bridge ownership.

Requirements:

- separate from economic asset approval;
- does not make USDT a target basket member or Research Idea;
- exact canonical identity remains required;
- bridge residue stays real inventory/accounting in replay;
- permission is research/paper execution only and creates no live-capital authority.

Normal UI copy should be plain:

> QAP can replay this pair using two real Spot conversions through USDT. Allow temporary USDT ownership inside research replays?

This is a bounded one-time authority step, not routine per-run plumbing.

### 6.4 Default pair recipe execution choice

The backend default product recipe chooses execution before results exist:

1. prefer a ready real direct pair market when one exists;
2. otherwise use `multi_asset_bridge` only when both exact same-venue quote legs are ready and transient bridge permission is present;
3. otherwise return relationship evidence plus an explicit economic-expression blocker.

No automatic route graph and no alternative hidden bridge.

### 6.5 Existing economics only

Once compiled, execute through existing:

- `qap.experiment.runner`;
- `qap.execution.replay` / multi-asset bridge execution;
- current cost model;
- current inventory/accounting;
- HODL and predeclared controls;
- current artifact/lineage/final-OOS authority.

No economic formula changes are in scope.

### M11-C acceptance

For a pair such as W/PIXEL with no direct market but two valid same-venue W/USDT + PIXEL/USDT legs and explicit transient USDT permission:

- M10-A support can report a canonical pair recipe runnable with `multi_asset_bridge`;
- compilation records the exact relationship and execution instruments;
- the existing replay produces real two-leg fills/costs rather than a synthetic pair fill;
- HODL/control economics and run artifacts are unchanged in authority;
- bridge residue remains explicit;
- Scanner Slice-1 direct replay behavior is unchanged.

If the existing two-leg executor cannot represent the required two-asset target without changing economic semantics, stop and return to design review rather than adding a second executor.

## 7. M11-D — Integrated research-completion experience

### Mission

Present the full research chain on one Pair Research flow without creating a new promotion state machine.

### Behavior

After a runnable default experiment completes, show in the Pair Research result:

```text
QUESTION
  W / PIXEL · Medium-term

RELATIONSHIP
  exact current Pair Study values

EXPERIMENT
  selected/default variant and parameters

ECONOMICS
  QAP
  HODL
  primary control
  difference vs HODL/control
  fees/turnover/drawdown where authoritative

CONCLUSION
  completed negative / promising development / final-OOS result

LIMITATIONS
  method/execution/live/capacity claims not established

EXACT RUNS
  run links

TECHNICAL PROVENANCE
  progressive disclosure
```

Use existing artifact semantics to describe development versus final OOS. Do not invent a new Product promotion state.

Experiment Lab remains the place for explicit method/parameter variant authoring. Pair Research may link into it while preserving the selected assets/timeframe.

### M11-D acceptance

The user can begin with "what is happening between W and PIXEL?" and finish with a truthful statement of:

- what relationship evidence exists;
- which method was used;
- what economic expression was tested;
- how it compared with HODL/control;
- whether the result was positive, negative, blocked, or not yet final OOS;
- what QAP still cannot claim.

## 8. Formal cointegration recovery — separate method-admission wave

Do not include formal cointegration in M11-A through M11-D merely to match legacy terminology.

After the Pair Study workflow is working, run a focused method design/recovery review for `engle_granger_cointegration`.

The review must compare the legacy implementation to current clean-QAP evidence semantics and freeze:

- exact estimator/transform;
- ADF/Engle-Granger procedure;
- deterministic terms/lag selection;
- p-value/critical-value source;
- causal window/refit policy;
- orientation semantics;
- half-life/Hurst definitions if retained;
- numerical dependency decision;
- `diagnostic_only` versus executable capability status.

A safe initial implementation should prefer `diagnostic_only`. Economic authority is a later hypothesis, not implied by a significant p-value.

Student-t Copula remains separately gated by the existing Phase-10 admission decision.

## 9. Direct evidence / validation policy

No tests are authorized by this plan.

At each candidate milestone use direct evidence that can falsify the behavior:

### M11-A

- inspect exact Product preparation scope before/after the selected-pair request;
- read Pair Study API output for W/PIXEL;
- confirm exact source generations/fingerprints and common safe cutoff;
- confirm no direct market is required for relationship observations.

### M11-B

- headed/visible browser walkthrough of W -> PIXEL -> Medium-term -> `Research this pair`;
- show actual backend ratio/z-score/OLS values;
- confirm Pair, Scan, and Experiment Lab are separate active modes rather than a vertical stack.

### M11-C

- inspect compiled manifest and exact instrument roles;
- run one isolated real-data historical pair experiment through the existing multi-asset bridge executor when the environment has the required public data;
- inspect fills/costs/inventory/HODL/control artifacts;
- confirm no synthetic `WPIXEL` instrument exists in execution lineage.

### M11-D

- headed end-to-end research-completion walkthrough;
- exact run links and existing technical provenance;
- negative result remains a completed research result.

Near each candidate final state, run only the smallest relevant non-test static/build checks required by the changed language/boundary. Do not run pytest/vitest/e2e or create tests unless the user separately authorizes testing.

## 10. Stop conditions

Stop and return to design review before:

- weakening canonical asset identity or ticker-equality rules;
- making analysis-reference BTC an economic asset by implication;
- making USDT an economic target merely because it is a measurement/execution coordinate;
- allowing bridge execution without explicit transient ownership authority;
- permitting synthetic A/B fills or synthetic direct-market candles to become execution truth;
- changing Scanner-V1 to use pair bridge execution;
- changing HODL/control/cost/timing/accounting semantics;
- changing final-OOS family/holdout semantics;
- changing `ResearchRecipeV1` schema merely to avoid an additive manifest role when the current recipe can already express the needed exact data;
- adding a new router/backtester/ledger;
- implementing cointegration or Copula without the separate method-admission decision;
- moving statistical/economic math into React.

## 11. Files that should remain untouched by default

Unless direct evidence proves a necessary contract seam, do not change:

- Scanner graph/trial/promotion/prospective modules;
- live-readiness/private-trading authority;
- final-OOS reservation/permit/consumption implementation;
- portfolio valuation/evaluation formulas;
- direct/multi-asset execution math;
- existing relationship model formulas;
- Product current-approved strict-PIT separation.

## 12. Phase-17 exit after this amendment

Phase 17 should not close merely because the M10-D user can click through the current Pair Research recipe form.

After this implementation, the final representative-user gate must establish that a non-developer user can:

1. select W and PIXEL and one Product timeframe;
2. start research with one obvious action;
3. understand that W/USDT + PIXEL/USDT can establish relationship evidence without a listed WPIXEL market;
4. read the actual rolling log-ratio and Residual / OLS values;
5. understand that Residual / OLS is not formal cointegration;
6. distinguish relationship evidence from economic replay;
7. understand direct versus two-real-leg USDT execution when applicable;
8. run an authorized economic experiment and compare it with HODL/control;
9. accept a negative result as completed research;
10. find advanced provenance without needing it to understand the result;
11. state correctly that QAP does not recommend or place live trades.

Only then should M10-D/Phase-17 representative-user closure be reconsidered.
