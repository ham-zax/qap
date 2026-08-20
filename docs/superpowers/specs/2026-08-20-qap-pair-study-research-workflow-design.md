# QAP Pair Study Research Workflow Design

**Status:** APPROVED / FROZEN — integrated on `main` with the M11-A backend foundation through `2f055d1`.

**Phase:** 17 — Product Layer follow-on after the first M10-D representative-user Pair Research walkthrough.

**Authority:** The user explicitly reopened Pair Research after the `W / PIXEL` walkthrough showed that QAP was asking downstream execution/setup questions before answering the upstream research question.

**Primary rule:** A researcher must be able to study a relationship before QAP asks whether one particular economic expression can be replayed.

**Canonical inputs:**

- `docs/superpowers/specs/2026-08-17-qap-system-design.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/04-relationship-evidence-pairs-and-anchor-lens.md`
- `docs/plans/10-first-real-relationship-model-experiments.md`
- `docs/plans/11-paper-operation-hardening.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
- `docs/research/2026-08-20-qap-m10c-capability-fidelity-proof.md`

## 1. Why this design exists

The first M10-D Pair Research walkthrough attempted `W / PIXEL · Medium-term` and exposed two different problems.

The operational problem was real but bounded: Product market-data preparation could fail on an invalid Gate archive segment and could prepare required resolutions to slightly different cutoffs. The bounded remediation branch `6609a1c` demonstrated that those failures can be corrected without weakening market-data truth.

The larger problem was architectural. Pair Research currently tries to build an executable default `ResearchRecipeV1` before it exposes the relationship evidence QAP already knows how to compute. The default pair recipe therefore asks for a real direct `W/PIXEL` market before it collects the ready `W/USDT` and `PIXEL/USDT` evidence paths.

That ordering contradicts the clean-QAP architecture:

```text
market observations
    -> relationship evidence
    -> policy hypothesis
    -> economic execution
    -> accounting / HODL / controls
```

It also contradicts the Phase-17 Product design, which already says that relationship evidence may survive when stricter direct-market replay is unavailable.

The Product must therefore stop treating "research a pair" as shorthand for "author an executable pair replay".

## 2. What the legacy QAP got right and wrong

The legacy `tradingview_ratio` QAP had serious runtime and authority problems, but its user task model was useful.

A user could ask for two economic assets and the system would obtain their common-coordinate price histories, align them, inspect ratio/spread/OLS/cointegration statistics, and only later decide whether the relationship justified economic validation.

For bare assets such as `W` and `PIXEL`, legacy `DataFetcher.fetch_pair_data()` mechanically fetched `WUSDT` and `PIXELUSDT`. Its cointegration path then aligned those series and could calculate OLS, residuals, Engle-Granger/ADF statistics, z-score, half-life, and Hurst diagnostics.

The legacy BTC Tethered Mesh also allowed a missing main pair to be described through anchor legs. That was useful analytically but became unsafe when synthetic relationship construction, model authority, and tradeability were allowed to blur together.

Clean QAP correctly rejected those unsafe parts:

- no model is constitutional authority;
- no synthetic direct market is an execution instrument;
- execution uses real fills only;
- relationship evidence, policy, execution, accounting, and promotion authority stay separate;
- historical importance alone does not re-admit Copula or another method.

This design restores the **research task**, not the legacy runtime.

## 3. Product mental model

The normal Pair Research journey becomes:

```text
Research question
W / PIXEL · Medium-term
        |
        v
Prepare exact question data
        |
        v
Pair Study
  ratio / log ratio / normalized paths
  current admitted relationship models
  optional analysis-anchor lens
        |
        v
What hypothesis is worth testing?
        |
        v
Check economic expression
  direct real market, or
  explicitly admitted real two-leg bridge
        |
        v
ResearchRecipeV1
        |
        v
existing QAP experiment / HODL / controls
        |
        v
interpret / compare variants
        |
        v
freeze one variant
        |
        v
final OOS when intentionally requested
```

The researcher can finish at any truthful layer. A study does not become invalid merely because a later method or economic expression is unavailable.

## 4. Research Question and Pair Study are upstream of ResearchRecipeV1

### 4.1 Research Question

A Pair Research question contains only what is needed to ask the question:

```text
asset_a
asset_b
orientation
Product timeframe
study venue / venue options
measurement coordinate
optional analysis reference
```

The default measurement coordinate for current Product pair work is the real same-venue `ASSET/USDT` paths already prepared by Phase 17.

The question is not itself an experiment, does not consume final OOS, and does not imply a trading policy.

### 4.2 Pair Study

A Pair Study is a backend-owned, reconstructible read composition over exact immutable market-data generations and existing `qap.relationship` functions.

It is **not** a second experiment engine and does not need a new persisted run artifact in V1.

The backend response carries the exact immutable generation bindings and source fingerprints needed to reconstruct the displayed evidence. If later product evidence shows that users need saved non-executable studies in History, persistence can be designed separately.

### 4.3 ResearchRecipeV1 remains the executable experiment boundary

`ResearchRecipeV1` keeps its M10-A meaning:

- declared method/decision/allocation/execution semantics;
- capability/authority/readiness/fidelity preflight;
- family continuity;
- compilation lineage;
- final-OOS selection and reservation rules.

Pair Study does not weaken or replace this contract. It gives the researcher useful evidence **before** a recipe is appropriate.

## 5. Pair-scoped market-data preparation

Whole-approved-universe preparation was an intentional M10 simplification. The `W / PIXEL` walkthrough has now provided the concrete burden that justifies a scoped path.

When the active question is `W / PIXEL · Medium-term`, Product preparation must be scoped to that question.

It prepares only the relevant resolved/current instruments needed for the selected timeframe:

```text
W/USDT
PIXEL/USDT
real W/PIXEL or PIXEL/W when one exists
optional reference/USDT path when an analysis lens is explicitly requested
```

It must not fail the W/PIXEL task because another approved asset, such as BTC, has unrelated readiness or acquisition problems.

Universal Scan continues to use universe-scoped preparation. Pair-scoped preparation does not change scanner scope or Scanner-V1 authority.

### 5.1 Same market-data authority

Do not create a Pair Research fetcher.

Extend the existing Product market-data preparation owner with an optional selected-asset scope. The same Binance/Gate acquisition, immutable generation, provenance, extension, and maintenance contracts remain authoritative.

### 5.2 Common cutoff

All required resolutions prepared in one Pair Research operation use one shared completed cutoff appropriate to their interval requirements. A 1h and 4h path must not become mutually unready merely because each request independently sampled a slightly different current time.

### 5.3 Archive fallback

If an exchange archive candidate violates QAP's exact contiguous-bar contract, reject that archive candidate and use the existing official public REST acquisition path for the required interval/window. Do not publish invalid archive rows and do not weaken gap validation.

This preserves the bounded acquisition fix demonstrated on branch `6609a1c`.

## 6. Venue, coordinate, and orientation semantics

### 6.1 Venue-local study

Pair Study remains venue-local. It does not mix `W/USDT` from one venue with `PIXEL/USDT` from another in one ordinary study.

If exactly one supported venue has both required paths, select it mechanically.

If multiple venues are valid, the backend returns the available venue choices and a deterministic Product default. The selected venue remains visible in the study header and can be changed without pretending that two venue histories are one dataset.

### 6.2 USDT is a measurement coordinate

For synchronized same-venue observations:

```text
W/PIXEL = (W/USDT) / (PIXEL/USDT)

log(W/PIXEL)
  = log(W/USDT) - log(PIXEL/USDT)
```

This is analytical relationship evidence. It is not a claim that a `WPIXEL` exchange market exists.

### 6.3 Orientation is explicit

The selected order is the default orientation.

`W / PIXEL` and `PIXEL / W` remain one canonical relationship identity with two orientations.

Raw ratio/log-ratio reversal is an exact transform. Residual/OLS models are directional and require the existing refit-required semantics. The UI must not imply that changing orientation is merely changing a sign.

## 7. Pair Study backend read model

Introduce one focused Product read model, conceptually:

```text
PairStudyContextV1
  question
    asset_a
    asset_b
    orientation
    horizon
    venue
    coordinate_asset
    safe_cutoff

  data
    status
    reasons[]
    asset_a_path
    asset_b_path
    exact generation/fingerprint references
    direct_market status

  relationship
    raw_ratio_current
    log_ratio_current
    normalized path summary
    methods[]

  analysis_lenses[]

  economic_expression
    direct
    bridge
    reasons[]
    default_recipe?       # only when one can be truthfully declared
    support?              # M10-A result when a default recipe exists

  technical_provenance
```

A separate bounded series read returns aligned chart data for ratio/log-ratio/normalized paths and optional anchor views. Do not overload the context response with large bar series.

The Product read model composes existing owners. It does not own statistical formulas, economic results, or support truth.

## 8. Relationship evidence available in Pair Study V1

Pair Study V1 exposes methods that current clean QAP already implements.

### 8.1 Transparent relationship series

Use existing `qap.relationship` primitives for:

- raw oriented ratio;
- log ratio;
- normalized price paths;
- reciprocal orientation;
- exact source/provenance fingerprints.

### 8.2 Rolling log-ratio z-score

Use `rolling_log_ratio_observation()`.

Display backend-owned values such as:

```text
method/model
window_bars
required observations
coverage observations
current score
status
as_of
```

### 8.3 Residual / OLS z-score

Use `rolling_residual_observation()`.

The current clean-QAP model is a rolling log-price OLS residual model:

```text
log(asset_a)
  = alpha + beta * log(asset_b) + residual
```

Display backend-owned:

```text
orientation
alpha
beta
current residual z-score
window/coverage
model ID/version
status
as_of
```

Do not call this formal cointegration.

### 8.4 Current known-unimplemented methods

Pair Study and Experiment Lab may display known methods such as Student-t Copula as non-runnable when the M10-A capability catalog says they are unimplemented.

A known method entry does not dispatch code.

## 9. BTC analysis lens

BTC is an optional **analysis reference**, not automatically an economic target and not automatically an execution bridge.

For a study with exact same-venue `W/USDT`, `PIXEL/USDT`, and `BTC/USDT` observations:

```text
W/BTC     = (W/USDT) / (BTC/USDT)
PIXEL/BTC = (PIXEL/USDT) / (BTC/USDT)
```

The lens may show how each selected asset moved relative to BTC and how the pair relationship decomposes under that reference.

The lens must never claim that a real `W/BTC` or `PIXEL/BTC` market was executed when those markets do not exist.

### 9.1 Analysis-reference authority

An analysis reference is not the same as Product asset admission.

Economic assets still require explicit approval as assets the operator is willing to own. A reference asset may be used only for descriptive analysis when its canonical identity is resolved and its exact market-data path is available.

The reference role must not make BTC part of the economic basket, scanner candidate universe, execution inventory, or live authority.

If introducing this separate reference role would require weakening the existing identity/admission contract, stop and return to design review rather than silently treating ticker equality as proof.

## 10. Economic expression is a second question

Pair Study answers "what is the relationship?"

Economic replay answers "does one declared long-only spot expression of that relationship add economic value after costs?"

Those answers must remain separate on screen and in backend contracts.

### 10.1 Direct execution

When a real same-venue direct `A/B` or `B/A` Spot instrument with admitted immutable history exists, the existing direct pair recipe/replay remains valid.

Do not remove or weaken Slice-1 direct replay.

### 10.2 Real two-leg bridge execution

Clean QAP already has an explicit real two-leg execution engine from Phase 11 and uses `multi_asset_bridge` for basket economics.

Current implementation inspection shows that this is not blocked by a basket-only replay rule: `run_deterministic_replay()` accepts generic multi-asset execution instruments plus one explicit bridge, and `validate_basket_manifest_contract()` returns without basket-specific restrictions when the policy is not `basket_graph`. The present pair blocker is the evidence-only instrument-role contract, not the absence of a two-leg executor.

For `W` and `PIXEL`, an honest two-leg rebalance may use real same-venue Spot instruments:

```text
W -> USDT
USDT -> PIXEL
```

or the reverse as required by the target rebalance.

This is not a synthetic `WPIXEL` fill.

The replay must preserve existing bridge rules:

- one declared bridge asset;
- every leg is a real declared Spot instrument;
- both legs are preflighted;
- each leg has its own fee/slippage/cost event;
- only actually received bridge inventory is available to the second leg;
- bridge residue remains real portfolio inventory and is valued/accounted;
- unsupported/missing legs fail closed;
- no graph search or automatic fallback bridge.

### 10.3 Explicit transient bridge admission

The system constitution requires explicit operator permission for transient ownership of the execution bridge.

Do not force USDT into the economic Research Universe merely to satisfy this rule.

Product should own a separate bounded persisted permission such as "allow USDT as a temporary research-execution bridge". This permission does not make USDT a target asset, research idea, scanner candidate, or live-trading authorization.

The normal workflow may ask for this permission once when a two-leg experiment first needs it, then reuse the persisted authority.

Known quote identity should be reused mechanically. Genuine identity ambiguity remains a bounded inline setup step.

## 11. Additive experiment contract for dual-use market instruments

The current `ExperimentManifest.evidence_instrument_ids` contract was deliberately introduced for Scanner Slice 1 to mean **evidence-only**. Those instruments cannot become execution state.

That safety invariant should remain true for existing direct scanner experiments.

Two-leg Pair Research creates a different legitimate case: `W/USDT` and `PIXEL/USDT` are both relationship inputs **and** real execution-reference instruments.

Do not weaken `evidence_instrument_ids` globally and do not duplicate the same immutable dataset under fake identities.

Add one explicit manifest concept for the relationship inputs used by the model, for example:

```text
relationship_instrument_ids
```

Semantics:

- identifies the exact declared instruments consumed by the relationship model;
- may overlap execution instruments when the same real market series truthfully serves both roles;
- does not itself grant execution authority;
- existing direct/scanner manifests may continue to derive relationship inputs from `evidence_instrument_ids` for compatibility;
- existing `evidence_instrument_ids` retain evidence-only semantics and remain forbidden from execution.

The recipe compiler, not React, maps exact recipe data bindings to this manifest field.

For the new two-asset `multi_asset_bridge` case, do not add a new `ResearchRecipeV1` schema field merely to name the same two market legs twice. The compiler can derive the relationship inputs only after verifying that the recipe is a `pair`, execution mode is `multi_asset_bridge`, the bridge is explicit, and the exact two execution bindings are the selected `A/bridge` and `B/bridge` instruments. It then writes those exact IDs into `relationship_instrument_ids`. Any ambiguity fails compilation.

This is the smallest contract amendment that allows dual-use real market data without erasing the historical evidence-only safety boundary.

## 12. Pair Research recipe selection after Pair Study

After relationship evidence is available, Product may declare the existing versioned default pair-method family.

The default family remains bounded and explicit:

```text
rolling_log_ratio_zscore
residual_mean_reversion
```

with existing `evidence_tilt` / `long_only_relative_tilt`, predeclared variants, costs, controls, and M10-A family semantics.

Execution is selected by backend truth:

```text
real direct market available
    -> direct execution recipe

otherwise exact same-venue A/USDT + B/USDT available
and transient USDT bridge is explicitly admitted
    -> multi_asset_bridge recipe

otherwise
    -> relationship study remains available;
       economic replay unavailable with explicit reason
```

Do not make execution-mode choice outcome-dependent. It is determined by declared market/authority availability before economic results exist.

`SupportReportV1` remains the final pre-execution owner of capability, authority, readiness, fidelity, and `runnable`.

## 13. Research page interaction model

The Research page should stop vertically stacking three complete workflows as equal-weight primary content.

Use one task switcher with one active workflow:

```text
Research a pair | Scan my universe | Experiment Lab
```

`Research a pair` is the default normal task.

`Scan my universe` remains Scanner-V1 Product discovery.

`Experiment Lab` remains the advanced typed recipe authoring surface.

No Focus Scan is introduced by this design.

### 13.1 Pair Research start

The primary form is intentionally small:

```text
Asset A        [ W ]
Asset B        [ PIXEL ]
Timeframe      [ Medium-term ]

[ Research this pair ]
```

If exactly one study venue is available, no venue question is required before the first result. When more than one valid venue exists, show the selected venue transparently and allow a bounded change without exposing directory internals.

### 13.2 One preparation action

`Research this pair` orchestrates existing Product authorities:

1. preserve the selected pair/timeframe/orientation draft;
2. reuse known identity/admission state;
3. ask only for genuine unresolved identity or missing economic admission;
4. prepare pair-scoped market-data requirements;
5. refresh Pair Study context;
6. compute backend relationship evidence;
7. when a default economic recipe can be declared, call M10-A Check support.

The user remains on the Research screen.

### 13.3 Immediate result hierarchy

After preparation, show:

```text
W / PIXEL · Medium-term
Gate
Data through <safe cutoff>

RELATIONSHIP
  W/USDT ready
  PIXEL/USDT ready
  current ratio / log ratio
  rolling log-ratio z-score
  Residual / OLS alpha, beta, z-score
  orientation control
  optional BTC lens

WHAT QAP CAN TEST
  supported default experiments
  known unimplemented methods

ECONOMIC REPLAY
  direct or real two-leg mode
  support status / blockers
  Run experiment when runnable

TECHNICAL PROVENANCE
  collapsed by default
```

No relationship value is calculated in React.

### 13.4 After an experiment

Stay in the same Pair Research flow and show existing authoritative artifact values immediately:

- exact method/model;
- window/lookback and thresholds;
- relationship value used by the run when exposed by authoritative artifacts;
- QAP economic result;
- HODL comparison;
- predeclared primary-control comparison;
- fees/turnover/drawdown where already authoritative;
- exact run links.

Recipe SHA, compilation SHA, manifest hashes, dataset fingerprints, compiler/catalog versions, and code provenance remain under Technical provenance.

## 14. Research completion semantics

A Pair Study may finish truthfully at different evidence layers.

Examples:

```text
Relationship complete
  "Residual / OLS evidence is valid at this cutoff."

Diagnostic blocked
  "Formal cointegration is not implemented in current QAP."

Economic expression unavailable
  "Relationship evidence is available, but no admitted real execution route is available."

Economic negative
  "The declared policy underperformed HODL/control after costs."

Development promising
  "One predeclared development variant improved on the primary control."

Final OOS negative
  "The frozen selected variant failed on untouched final-OOS data."

Research alpha
  "The frozen selected variant produced positive predeclared final-OOS economics under current QAP criteria."
```

Completion never means "QAP found a positive trade."

The UI should summarize what was learned, what was not established, and which layer blocked or failed.

## 15. Universal Scan and Experiment Lab remain distinct

Pair Study does not become a new scanner.

Universal Scan still owns automatic current-approved relationship discovery, candidate search, replay-attempt denominators, Research Ideas, and strict Scanner-V1 semantics.

Pair Study is manually selected fixed-pair research.

Experiment Lab still owns explicit recipe authoring, method/component selection, support/fidelity inspection, and manual finite variant declarations.

Manual Pair Study runs do not become scanner Research Ideas.

## 16. Formal cointegration recovery is a separate method-admission milestone

Legacy QAP implemented formal Engle-Granger/ADF, half-life, and Hurst diagnostics. Current clean QAP does not.

Do not rename current Residual / OLS z-score as "cointegration".

A later explicit method recovery may add a bounded relationship diagnostic such as:

```text
engle_granger_cointegration
```

Initial authority should be `diagnostic_only` unless a separately predeclared economic hypothesis justifies executable policy use.

The method design must freeze:

- price transform (raw or log; current likely candidate is log-price OLS for consistency with clean residual evidence);
- orientation/refit semantics;
- regression specification;
- stationarity test and deterministic terms;
- lag selection;
- p-value/critical-value implementation;
- diagnostic window versus rolling/refit schedule;
- half-life definition if included;
- Hurst definition if included;
- numerical dependency/provenance;
- causal completed-bar timing;
- how negative/invalid/insufficient-history outcomes are represented.

No implementation should begin merely by copying legacy `CointegrationTester`.

## 17. Student-t Copula remains a separately gated hypothesis

The Pair Study redesign does not re-admit Student-t Copula.

M10-A may continue to show it as known-unimplemented with a truthful nearest capability.

A future Copula implementation requires a specific current falsifiable research question and the Phase-10 admission discipline. Historical importance alone is insufficient.

## 18. API shape

Prefer the smallest explicit Product surface.

### 18.1 Extend existing market-data preparation

Conceptually extend the existing request with optional scope:

```text
MarketDataPreparationRequestDto
  horizons[]
  asset_ids[]?                 # selected economic assets only
  analysis_reference_ids[]?   # optional descriptive references
```

No `asset_ids` means existing universe-wide behavior.

Pair Research supplies exactly two economic assets. Universal Scan continues to omit the scope.

### 18.2 Pair Study reads

Add focused read endpoints such as:

```text
GET /api/product-pair-study/context
GET /api/product-pair-study/series
```

Inputs are pair, orientation, horizon, optional venue, and optional analysis reference.

The context endpoint owns small current facts and current model observations. The series endpoint owns chart-sized synchronized relationship series.

Do not add a generic research workflow API.

### 18.3 Existing experiment APIs remain

Continue to use:

```text
POST /api/research-recipes/check-support
POST /api/research-recipes/run
GET  /api/research-recipes/runs/{run_id}/lineage
```

Pair Study does not duplicate experiment launch or lineage APIs.

## 19. Persistence and provenance

V1 does not introduce a persisted Pair Study artifact.

The Pair Study response is reconstructible from:

- canonical asset identities;
- venue/instrument identities;
- horizon/interval;
- exact immutable generation IDs and semantic fingerprints;
- safe cutoff/as-of;
- explicit orientation;
- model IDs/versions/configuration;
- existing relationship observation input fingerprints.

Completed economic runs continue to persist through existing recipe compilation and experiment artifacts.

If users later need to save a non-executable Pair Study as a first-class History object, that is a separate persistence design based on demonstrated use.

## 20. Error and recovery behavior

Pair Research must distinguish:

```text
identity needs confirmation
asset not approved
selected pair data needs preparation
one selected path acquisition failed
relationship model has insufficient history/variance
method is not implemented
economic bridge permission missing
real execution route unavailable
support checker blocks the recipe
experiment completed with negative economics
```

Do not collapse these into `Data failed` or `Not runnable` without the specific layer/reason.

A market-data operational failure is not negative research.

A method being unimplemented is not evidence that the pair is unsuitable.

A missing direct market is not evidence that the relationship cannot be studied.

## 21. Protected boundaries

This design does not authorize:

- live/private trading;
- leverage, borrowing, shorting, derivatives, or synthetic exposure;
- a synthetic `A/B` execution market built from quote legs;
- automatic bridge selection or route graph search;
- automatic asset admission;
- ticker-equality identity proof;
- weakening strict historical PIT;
- changing Scanner-V1 search/promotion semantics;
- changing HODL/control/economic objective semantics;
- changing final-OOS family/reservation/consumption rules;
- moving scientific/economic calculations into React;
- a plugin runtime, arbitrary Python strategies, generic workflow engine, or second backtester;
- automatic portfolio discovery/optimization;
- calling current residual z-score formal cointegration;
- reimplementing Copula merely because legacy code exists.

## 22. Acceptance examples

### 22.1 W / PIXEL · Medium-term

The normal user can select W, PIXEL, Medium-term and click one `Research this pair` action.

The Product then shows, on the same screen:

- exact pair/timeframe/venue;
- W/USDT and PIXEL/USDT readiness;
- one common safe cutoff;
- current ratio/log-ratio evidence;
- rolling log-ratio z-score when valid;
- Residual / OLS alpha, beta, residual z-score when valid;
- Student-t Copula as unimplemented, not as pair-incompatible;
- optional BTC lens when exact BTC reference data is available;
- direct-market status separately from relationship status;
- real two-leg bridge economic availability only when exact same-venue legs and explicit transient bridge authority exist;
- M10-A support result for any default runnable recipe;
- post-run QAP/HODL/control values and exact run links when an experiment runs.

The absence of a `WPIXEL` venue symbol does not erase the relationship study.

### 22.2 Pair with a real direct market

The same flow uses direct economic execution when that real market is ready. Relationship evidence still comes first and remains separately visible.

### 22.3 Unsupported method

Selecting or inspecting Student-t Copula returns known-unimplemented support truth without changing relationship/data readiness.

### 22.4 Negative economics

A completed run that loses to HODL/control is presented as completed negative research, not an application error.

## 23. Design decisions frozen by this candidate

1. Pair Research starts from a Research Question / Pair Study, not an executable recipe.
2. Pair Study is a backend read composition over immutable data and `qap.relationship`, not another engine.
3. Pair market-data preparation becomes selected-pair scoped while Universal Scan remains universe scoped.
4. USDT common-coordinate relationship evidence is valid without a real direct A/B market.
5. BTC is an optional descriptive analysis reference, not automatically an economic target or execution bridge.
6. Current rolling log-ratio and Residual / OLS evidence appears before economic replay.
7. Direct-market absence gates direct economic replay only.
8. Pair economics may use existing real two-leg `multi_asset_bridge` execution when exact legs and explicit transient bridge authority exist.
9. Existing evidence-only semantics remain protected; a separate explicit relationship-input instrument role enables legitimate overlap with execution instruments.
10. M10-A recipe/support/family/final-OOS authority remains the executable experiment boundary.
11. Research page shows one active task at a time instead of vertically stacking Pair, Scan, and Experiment Lab workflows.
12. Formal cointegration and Student-t Copula remain separate method-admission work, not labels applied to current residual evidence.

## 24. Implementation gate

Do not start production implementation until this design is accepted as the Pair Research-specific amendment to the Phase-17 Product design.

The implementation plan is:

`docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md`
