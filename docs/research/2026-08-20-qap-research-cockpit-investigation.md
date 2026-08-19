# QAP Research Cockpit Investigation

**Date:** 2026-08-20
**Status:** planning investigation; no runtime/scientific change authorized
**Trigger:** representative real-user walkthrough on iPhone after Phase-17 M9 closure
**Current implementation baseline:** `37ed0e8` on `main`
**Primary repositories inspected:** `/home/hamza/repo/qap`, `/home/hamza/repo/tradingview_ratio` (read-only legacy evidence)

## Executive conclusion

The Phase-17 Product Layer solved important prerequisites correctly—workspace identity, explicit asset admission, market-data preparation, current-approved versus historical-PIT claim separation, longitudinal evidence, persistent current evidence, Portfolio/History composition, and local lifecycle hardening—but it put too much of that machinery in front of the user's actual research job.

The real-user walkthrough exposed a product-level failure rather than a copy-only usability problem:

> A normal operator cannot begin with “research W against BTC/ETH” or “scan my approved universe and show me interesting relationships” without first understanding setup/admin concepts that should be secondary.

The correct Product center should be **research intent first**:

```text
Research
  -> Research a pair
  -> Scan my universe
  -> optionally focus one asset against the universe
```

Identity resolution, approval, data preparation, immutable lineage, protocol IDs, fingerprints, and physical generation paths remain necessary backend truth, but they should appear as bounded setup interruptions or advanced audit detail—not as the user's conceptual starting point.

This investigation does **not** recommend weakening identity, provenance, strict PIT, scientific promotion, HODL/control economics, or the Phase-12 live-capital `NO-GO`. It recommends changing which job the Product UI organizes around.

The most important implementation finding is that a large portion of the desired cockpit already exists in current QAP, but at the wrong boundary:

- the normal current-approved Product scan is already a universe scan over all approved+ready assets;
- the strict scanner already supports manually pinned pairs;
- Scanner V1 already evaluates two pair-model families under fixed horizons/templates;
- completed scan artifacts already retain model-family, template, replay, negative/unavailable, and economic evidence;
- the Product already has readiness, safe-cutoff, data preparation, claim identity, and durable operation ownership.

What is missing is a normal Product composition that turns these capabilities into **Pair Research** and an explicit **Universal Scan** experience.

A second, more important gap is **research-experiment machinery at the Product boundary**. The objective is not to make Copula special. The operator should be able to describe a research recipe, check it before execution, and receive a precise answer about what QAP can reproduce, what it can only adapt, and what is unsupported or constitutionally forbidden. Current Scanner V1's two pair families, momentum/cross-sectional research, the legacy Student-t Copula work, and published strategies such as Rafael Baptista Palazzi's 2025 crypto pairs-trading study should all be handled through the same support/preflight language. A method must never become a UI checkbox merely because a paper or legacy implementation exists.

## 1. Observed user failure

The iPhone walkthrough was not a hypothetical usability critique. The user attempted a concrete task:

```text
Find W
select W
research W against BTC/ETH
try different models/backtests
or scan the wider universe for interesting relationships
```

Instead the Product led into Research Universe identity administration.

### 1.1 Exact-symbol search behaves like substring search

`web/src/features/home/ResearchUniverse.tsx` currently filters unresolved venue asset codes with `includes(query)`. Typing the one-character exact symbol `W` therefore returns many unrelated codes containing W before/around the actual `W` record.

The intended interaction is asset lookup; the implemented interaction is raw substring matching over venue codes.

Required Product semantics:

```text
exact symbol matches
    before
prefix matches
    before
substring/other matches
```

An exact `W` match should be visually dominant. Leveraged/legacy/suffixed venue codes should not make the user hunt for a literal exact match.

### 1.2 Selection feedback occurs below the long result list

When an unresolved venue code is selected, the identity confirmation card is rendered after the matching-results grid. On mobile, clicking `W` can therefore appear to do nothing because the newly relevant form is far below a very long result list.

This is a direct interaction defect. Once an item is selected, the selected setup task should replace/collapse the result list or move immediately into view.

### 1.3 The user is asked to operate backend vocabulary

The current identity form asks for:

- canonical economic asset;
- identity version.

Those fields represent legitimate fail-closed identity state, but they are not the user's primary research language. A user who wants `W vs BTC` should encounter a bounded message such as:

> W needs one-time identity confirmation before QAP can research it.

The advanced identity fields and exact lineage can remain available when needed, but the normal path should preserve the research intent and return to it after setup.

### 1.4 More help text cannot fix the wrong task hierarchy

Commit `37ed0e8` added route-aware guidance with Intent / What to do / Example / What happens next / This does not mean. That is useful and should remain, but the walkthrough demonstrates that explanation is not a substitute for putting the correct primary task first.

The Product should not teach a novice to navigate an admin-first workflow when the desired workflow can be expressed directly.

## 2. Current QAP capability inventory

### 2.1 The normal Product scan is already a universe scan

`web/src/features/discovery/ProductResearch.tsx` presents one current-approved research action:

```text
choose horizon
check backend readiness
Find research ideas
```

It calls the Product endpoint with only:

```json
{
  "horizon": "short | medium | swing",
  "readiness_id": "<opaque binding>"
}
```

`CurrentApprovedResearch.run()` then derives every ready approved asset per venue from the bound readiness object and calls `run_scan_with_qap()` with that scope.

Therefore the Product does not lack a universe scanner engine. It lacks a user-facing **“Scan my universe”** research mode that plainly states:

- how many approved/ready assets will be scanned;
- which timeframe is selected;
- which admitted research methods are included;
- what “interesting” means;
- how the completed funnel should be interpreted.

This is primarily a Product-composition problem, not a new scanner-engine problem.

### 2.2 Strict Advanced Research already supports pair pins

`web/src/features/discovery/DiscoveryHome.tsx` exposes the strict historical-PIT scanner. Its request supports:

- explicit `as_of`;
- one or multiple horizons;
- manual pair pins;
- forensic mode;
- manual replay candidate IDs.

The backend scanner already has `ScannerPinSpec`, manual-pinned graph records, deterministic trials, and special forensic handling.

This proves that the scanner can preserve an explicitly requested pair through discovery/evaluation. However, the current pin contract belongs to the strict historical-PIT flow. It should not simply be exposed unchanged as the Product pair-research contract, because Product current-approved research has different scope/readiness semantics and must not pretend to be PIT.

### 2.3 Current Product does not have a pair-research request

`ProductRunScanRequestDto` currently extends only the current-approved horizon/readiness request. There is no Product field for:

- selected asset A/B;
- focus asset;
- model family selection;
- pair-only scope.

Likewise `CurrentApprovedResearch.run()` constructs `assets_by_venue` from the entire ready scope. This is the principal backend composition gap for a normal Pair Research cockpit.

### 2.4 Pair pages are read-only evidence views, not research launchers

Current `/pair/<run>/<assetX>/<assetY>` pages project relationship/model evidence from an already existing experiment. They are valuable after research exists, but they do not answer:

> “I picked W and BTC. Run research now.”

The desired Pair Research cockpit should therefore launch through Product research ownership and later link into the existing specialist pair evidence view when a concrete run exists.

### 2.5 Product market-data preparation is whole-scope today

`ProductMarketDataPreparation` consumes `ProductUniverse.resolved_scope()` and prepares the required intervals for all resolved approved/current instruments for the chosen horizons.

That is acceptable for universal scanning. For Pair Research it raises a design question:

- simplest V1: prepare the approved universe as today and then run only the selected pair;
- more efficient later option: prepare only the selected pair's required legs/direct market.

Pair-specific preparation should not be invented merely for UX neatness. It should be added only if whole-scope preparation creates a demonstrated latency/request burden for the pair workflow.

### 2.6 The low-level experiment engine exists, but the Product cannot author/check experiments

Current QAP already has a minimal CLI that loads one frozen `ExperimentManifest` and executes it to artifacts. The web/API experiment routes, however, are read-only list/detail artifact readers. There is no Product mutation/API that lets a researcher author a recipe, query supported components, preflight one methodology, or receive a structured explanation before execution.

This is an important scope correction: M10 does **not** need a generalized new backtesting engine. It needs a typed authoring/preflight/compiler boundary in front of the mature low-level experiment engine.

## 3. Current model and strategy inventory

The Product must present models truthfully. “Model” is currently not one uniform concept across QAP.

The architectural opportunity is that current QAP already has most of the **low-level experiment substrate** needed for a typed research-recipe layer:

- `ExperimentManifest` freezes basket, instruments, exact data sources/fingerprints, relationship component, policy component, execution, benchmarks, data role, primary metric, and family lineage;
- Pydantic rejects unknown manifest fields and invalid cross-field combinations;
- `compose_model_strategy_policy()` admits only explicit relationship/policy combinations and already fails on unsupported combinations;
- the experiment runner executes strategy, HODL, declared controls, adverse-cost roles, and preserves negative results through one replay/economic path;
- final-OOS reservation/consumption and research-family lineage already exist.

The missing Product capability is **pre-execution explainability**. Today unsupported research tends to fail late through `ExperimentSetupError`, and `ComponentSpec` is still a string ID plus opaque config at the manifest boundary. There is no queryable capability contract that can answer, before a run: `is this exact research recipe representable, executable, and claim-compatible in QAP, and if not, why?`.

### 3.1 Scanner-V1 admitted pair model families

`src/qap/scanner/trials.py` defines exactly:

```text
log_ratio_mean_reversion
residual_mean_reversion
```

Each admitted scanner pair is evaluated across the horizon's frozen model resolutions and Fast / Base / Slow templates. Residual mean reversion has orientation-specific fits; log-ratio reciprocity follows its frozen semantics.

These are the only model families that can honestly appear in an initial current Product **pair-model comparison** without a scientific expansion.

### 3.2 Other currently admitted research strategies are not equivalent pair models

`src/qap/experiment/model_policies.py` also admits compositions including:

- slow momentum tilt;
- cross-sectional relative-log-return tilt;
- rolling log-ratio evidence tilt;
- residual mean-reversion evidence tilt.

Scanner Slice 3 also contains asset-native / pair-blind relative momentum used by basket research.

Therefore a Product dropdown labeled simply `Momentum` beside pair mean-reversion models would be scientifically ambiguous. Before exposing momentum in `W / BTC` Pair Research, the design must answer what the unit of research is:

- W's standalone slow momentum?
- W versus BTC relative momentum?
- a pair-blind control/benchmark?
- a cross-sectional universe signal?

Until that is explicit, Momentum should be presented as a separate research capability or benchmark, not falsely relabeled as a pair model.

### 3.3 Copula is legacy-only today

The current QAP repository does not contain an admitted Copula model family in Scanner V1 or its current Product protocol.

The legacy `/home/hamza/repo/tradingview_ratio` repository does contain substantial Copula machinery, including:

- bivariate Student-t Copula implementation;
- Kendall-tau dependence estimation;
- Mispricing Index / conditional-probability logic;
- readiness/sufficiency evaluation;
- Copula observation and drift tracking;
- Copula-oriented backtesting and WAFO code;
- explicit old signal-authority rules.

This is enough evidence to treat Copula as a serious candidate for scientific recovery, not enough evidence to transplant it into current QAP.

A current-QAP Copula reintroduction would require its own design to define at minimum:

- relationship/evidence object and immutable artifact schema;
- calibration sample and minimum data contract;
- completed-bar and OOS/formation semantics;
- orientation and reciprocal semantics;
- Student-t parameter fitting and numerical dependency choice;
- discovery versus deep-replay role;
- economic policy and target-allocation mapping;
- cost/HODL/control comparison under current QAP economics;
- promotion/negative/unavailable semantics;
- current-approved and strict-PIT claim compatibility;
- prospective follow-up semantics;
- provenance and reproducibility requirements;
- whether adding SciPy or another numerical dependency is justified.

Copula must therefore be a **scientific design gate**, not a frontend option.

## 4. Required typed Research Recipe / capability-check machinery

The new machinery should sit **above** the existing `ExperimentManifest`, not replace the experiment engine and not become a generic plugin framework.

### 4.1 Research Recipe is the user's declared methodology

A recipe should separate concepts that are currently easy to collapse under the word `model`:

```text
research object
  pair | focus asset vs universe | universe | basket

relationship / evidence method
  log-ratio | residual/OLS | Student-t Copula | other declared method

signal / decision rule
  z-score rule | evidence tilt | Copula MI rule | momentum rule | other

allocation / rebalance policy
  long-only relative tilt | scheduled target | long-short spread | other

risk overlays
  volatility filter | trailing stop | none | other

selection / calibration protocol
  fixed parameters | train/test | grid search | walk-forward | other

execution + costs
  direct Spot | bridge | required market metadata | fee/slippage assumptions

benchmarks + evaluation
  HODL | simple control | momentum comparator | primary metric | data role
```

This is exactly the distinction needed to answer questions such as `does W/BTC support Student-t Copula?`, `what did this paper rebalance?`, or `can QAP faithfully reproduce Palazzi's method?` without pretending every difference is merely a model-name difference.

### 4.2 Check first, run second

The normal experiment lifecycle should be:

```text
Draft recipe
    -> structural/type check
    -> capability/authority check
    -> data/readiness preflight
    -> explicit support report
    -> compile to one or more frozen ExperimentManifest trials
    -> execute through existing QAP replay/economics
    -> persist exact recipe + compiled manifest lineage
```

The check operation is read-only. It must never download data, mutate admission, consume final OOS, or start a scientific run merely to explain support.

### 4.3 Support status must distinguish fidelity from availability

Recommended recipe-level states:

```text
runnable_exact
    QAP can execute the declared method without semantic substitution.

runnable_after_setup
    methodology is supported; identity/data/direct-market prerequisites are missing.

adaptation_possible
    QAP can run a related method, but it is not a faithful reproduction.
    User must explicitly create/accept a different adapted recipe.

diagnostic_only
    QAP can compute the evidence but has no admitted economic policy/claim for it.

unsupported
    a required method/risk/selection/execution component is not implemented/admitted.

blocked_by_constitution
    the declared methodology requires behavior QAP intentionally forbids
    (for example shorting, leverage, derivatives, or live-capital authority).

invalid
    the recipe itself is structurally contradictory or malformed.
```

`adaptation_possible` must never silently downgrade into `runnable_exact`.

### 4.4 Reasons must be typed and actionable

A bounded reason vocabulary is preferable to generic exception strings. Candidate reason codes include:

```text
unknown_method
known_method_not_implemented
method_not_admitted_for_replay
method_has_no_current_data_contract
unsupported_research_object
incompatible_component_combination
requires_short_position
requires_leverage_or_borrow
requires_derivative
requires_unimplemented_risk_overlay
requires_unimplemented_parameter_selection
requires_unimplemented_walk_forward_protocol
requires_unavailable_numerical_backend
requires_missing_identity_confirmation
requires_operator_asset_approval
requires_market_data
requires_real_direct_market
current_claim_incompatible
strict_pit_evidence_required
cannot_claim_faithful_replication
adaptation_available
```

Each reason should state:

- which recipe component caused it;
- whether it is missing implementation, missing data, or a protected authority boundary;
- what current QAP capability is nearest, if any;
- whether a scientifically different adaptation is possible;
- the exact owner/design milestone required to make it executable.

### 4.5 Explicit capability catalog, not a plugin system

Do not build a generic strategy registry, dynamic import system, workflow engine, or plugin platform.

Use one explicit, versioned capability catalog owned by the research/experiment boundary. For each known component ID it should declare enough static metadata to validate the request and explain support, for example:

```text
component kind
component ID + version
configuration schema/validator
implementation state
allowed research objects
required data semantics
allowed allocation/execution semantics
claim limitations
compiler/composition owner when executable
```

Unknown IDs remain representable at the draft envelope only long enough to return `unknown_method`; they never become executable through dynamic dispatch.

### 4.6 Compile downward into existing authority

The recipe layer should not become a second backtester. A supported recipe compiles to:

- one `ExperimentManifest`; or
- an explicit finite family of sibling manifests under one `research_family_id` when the recipe declares multiple precommitted variants.

Existing provenance, immutable data fingerprints, controls, replay, economics, final-OOS rules, and negative-result handling remain authoritative.

The compiler must fail if it would need to invent a semantic substitution. For example, a long-short paper cannot be silently compiled to a long-only QAP tilt while retaining a `faithful replication` label.

## 5. Palazzi paper as a preflight acceptance example

The likely paper referred to in the user walkthrough is Rafael Baptista Palazzi, **“Trading Games: Beating Passive Strategies in the Bullish Crypto Market,” Journal of Futures Markets (2025), DOI `10.1002/fut.70018`**.

Its methodology is a useful acceptance case precisely because current QAP should **not** claim full support. The paper uses cointegrated crypto pairs and spread z-scores, estimates parameters in-sample and applies them out-of-sample, optimizes lookback using in-sample Sharpe, uses long and short positions, adds volatility filtering and adaptive trailing stops, performs split/walk-forward/sensitivity checks, and benchmarks against momentum and buy-and-hold.

A correct current-QAP support report should look conceptually like:

```text
Palazzi 2025 exact reproduction
STATUS: blocked / not faithfully reproducible today

pair research object                         supported
Spot historical data/provenance             supported in QAP form
log-price OLS residual z-score               related capability exists
fixed IS cointegration fit -> OOS use        not the current rolling-residual contract
cointegration admission/test semantics       not an admitted exact Palazzi contract
long-short pair position                     BLOCKED BY QAP long-only Spot constitution
lookback grid search maximizing IS Sharpe    not implemented as an admitted selection protocol
adaptive volatility filter                   not implemented as this paper's rule
adaptive trailing stop                       not implemented as this paper's rule
walk-forward parameter re-estimation         no generic admitted paper-replication protocol
buy-and-hold/control comparison              QAP has its own stronger explicit control machinery

NEAREST ADAPTATION:
A separately named long-only rolling-residual QAP experiment may be possible,
but it is not “Palazzi replication” and must have its own recipe/family identity.
```

This is the kind of answer the user should be able to obtain **before writing code or launching a backtest**.

## 6. Student-t Copula as another capability-check example

Copula is useful here as a test of the machinery, not as the center of the Product.

A current support report should distinguish:

```text
Student-t Copula relationship / MI request

legacy evidence exists                       yes
current QAP implementation/admitted model    no
current QAP data sufficiency contract         not defined
current QAP artifact/model version            not defined
current QAP policy mapping                    not defined
current QAP numerical backend                 NumPy only; SciPy is not a current dependency
pair-specific incompatibility                 not established

STATUS: known method not implemented/admitted
```

The critical wording is the last distinction: QAP should not tell the user `W/BTC does not support Copula` when the truth is `QAP has not defined/admitted a current Student-t Copula experiment contract, so it cannot yet assess or execute that method for W/BTC.`

The old `/home/hamza/repo/tradingview_ratio` Student-t implementation, readiness evaluators, MI logic, and WAFO work are research evidence available to a future method-design pass. They do not themselves make current support `yes`.

## 7. Legacy QAP research-cockpit evidence

The earlier Phase-17 salvage report correctly rejected the legacy runtime architecture, but the latest walkthrough shows that it underweighted one valuable legacy asset: the **research task model**.

The legacy repository should continue to be used as product-intent evidence, not copied as architecture.

### 7.1 The old beginner workflow began with research phases, not provenance administration

`docs/user-guides/BEGINNER_WORKFLOW.md` framed the sequence as:

```text
Setup -> Data -> Discovery -> Validation -> Shadow -> Trading
```

Each stage said:

- the purpose;
- what it can/cannot decide;
- what the user should do;
- what the user learns;
- the next stage.

The useful salvage is not its old live/trading authority. It is that **Discovery and Validation were recognizable user jobs**.

### 7.2 Pair discovery and backtesting were explicit first-class jobs

`docs/user-guides/WORKFLOW_PAIR_DISCOVERY_BACKTEST.md` made the workflow recognizable:

```text
Find pairs -> rank candidates -> backtest one pair -> analyze metrics -> inspect why
```

Representative legacy commands included:

```text
qap discover discover --quick
qap validate validate AVAX SOL
qap validate validate AVAX SOL --wafo
qap validate compare AVAX SOL
qap validate inspect AVAX SOL
```

Regardless of which old scientific claims remain valid, this is substantially closer to the user's current mental model than “enter the identity/provenance subsystem first.”

### 7.3 Legacy target scan is particularly relevant

The old `qap discover screen` supported both:

```text
no base symbols -> full universe scan
named base symbols -> test those assets against the universe
```

The source even documents examples such as:

```text
qap discover screen LA W
qap discover screen LA W --quick
```

This suggests three useful Product research jobs rather than one opaque scan button:

1. **Research a pair** — W against BTC;
2. **Scan my universe** — all approved-ready assets;
3. **Focus scan** — W against the approved universe.

The Focus Scan is a strong legacy concept because it avoids forcing the user to choose between one pair and a potentially large all-pairs scan.

### 7.4 The legacy model-comparison mental model was richer

Historical CLI help offered multiple spread/model configurations and an `all` comparison mode. The exact old methods and their authority are not current-QAP contracts, but this is direct evidence that the intended product was not merely “run one hidden scanner protocol.” The user expected to investigate how a pair behaves under different hypotheses.

The Product should recover this mental model carefully:

> choose a research object first; compare only currently admitted methods; expand the scientific model set separately.

### 7.5 Old Copula should be treated as a research program, not a port

Legacy docs sometimes describe Copula as canonical signal authority and include old thresholds, readiness gates, Tethered Mesh assumptions, and trading-oriented semantics. Those do not automatically satisfy current QAP's economic/research contracts.

Useful salvage:

- Student-t Copula research implementation as evidence;
- MI/dependence concepts;
- sufficiency/readiness concerns;
- WAFO/OOS concerns;
- why Copula was central to the original product identity.

Rejected salvage:

- old live/trading authority;
- old thresholds as current policy;
- synthetic/tethered execution assumptions;
- old monolithic fetch/cache/runtime ownership;
- direct source-code transplant without current-QAP protocol design.

## 8. External product-pattern check

External products are not QAP authority, but they provide a useful usability sanity check.

### TradingView screeners

TradingView's official Crypto Pair/CEX Screener documentation describes the screener as a place to filter and sort large sets of crypto pairs by metrics, timeframe, indicators, symbol type, quote currency, and exchange, then choose pairs of interest for deeper analysis.

Relevant official sources:

- https://www.tradingview.com/support/solutions/43000476423-what-is-the-crypto-pair-screener/
- https://in.tradingview.com/support/solutions/43000746110/
- https://in.tradingview.com/support/solutions/43000689102-main-filters-in-crypto-pairs-screener/

The Product lesson is not to copy TradingView's market screener. It is that **screening is presented as a primary discovery action**, not hidden behind data-governance screens.

### QuantConnect research/backtest separation

QuantConnect's official Research Environment documentation recommends investigating a hypothesis in the Research Environment before backtesting and supports subsequent analysis of backtest results.

Relevant official sources:

- https://www.quantconnect.com/docs/v2/research-environment/key-concepts/getting-started
- https://www.quantconnect.com/docs/v2/research-environment/meta-analysis/backtest-analysis

The useful QAP lesson is the explicit hypothesis/research object -> backtest -> analysis flow.

### Composer strategy-to-backtest transition

Composer's official guides make the transition from creating/configuring a strategy to running a backtest a direct user action (`Insert & backtest` in its AI flow; explicit backtesting in its strategy tutorial).

Relevant official sources:

- https://help.composer.trade/article/108-create-with-ai
- https://help.composer.trade/article/54-create-tutorial
- https://help.composer.trade/article/67-backtest-basics

Again, QAP should not copy Composer's product or authority model. The useful pattern is that **the user's strategy/research intent remains visible when the system asks for prerequisites and when it produces backtest evidence**.

## 9. Corrected Product jobs-to-be-done

The normal Research surface should be designed around three direct Product jobs plus one advanced research job.

### Job A — Research a pair

User statement:

> “I want to compare W and BTC/ETH and see how their relationship behaves under QAP's admitted research methods.”

Minimum interaction:

```text
Asset A: W
Asset B: BTC
Timeframe: Short / Medium / Longer
Research methods: QAP admitted pair methods
Run pair research
```

Recommended initial method behavior:

**Run all currently admitted Scanner-V1 pair model families automatically for the selected pair.**

Why:

- it reuses the frozen Scanner-V1 scientific protocol;
- it avoids letting UI selection silently change trial enumeration/promotion policy;
- it reduces novice configuration;
- it lets the result page compare methods without cherry-picking one after seeing outcomes;
- it does not invent a new user-selectable scientific protocol.

The UI may allow presentation filters after completion, but filtering a completed result is not the same as changing what was run.

A future explicit “selected model families” experiment mode would require its own versioned research protocol and should not be smuggled into the initial cockpit.

### Job B — Scan my universe

This is primarily a re-presentation of current Product research, not a new engine.

Minimum interaction:

```text
Approved assets: 24
Ready assets: 22
Timeframe: Medium
Methods: QAP pair models
Scan my universe
```

Before launch, exclusions should be summarized without taking over the page.

Completed view should show the truthful backend stage funnel and a ranked/organized set of relationships. “Interesting” must mean a declared backend research state (for example retained relationship / valid rule / selected replay / surviving Research Idea), never a new browser score or trading recommendation.

### Job C — Focus scan

User statement:

> “I care about W. Show me which approved assets have interesting relationships with W.”

Conceptual interaction:

```text
Focus asset: W
Against: all approved-ready assets
Timeframe: Medium
Find relationships
```

This is strongly supported by the legacy target-scan mental model but is not currently a Product API contract. It should be considered a secondary cockpit mode after Pair Research + Universal Scan or implemented in the same backend scope mechanism if doing so remains small.

### Job D — Experiment Lab / research recipe

User statement:

> “I want to test a specific research method or paper on W/BTC, understand exactly what QAP supports, and see the correct reason before I write code or run a misleading backtest.”

Minimum interaction:

```text
Research object: W / BTC
Recipe: current QAP residual-zscore | Student-t Copula | Palazzi 2025 | custom catalogued recipe
Parameters / variants: declared before run
Data role: exploratory / development / final OOS where allowed
Check support
```

The first result is a support/fidelity report, not a backtest. Only `runnable_exact` or an explicitly resolved `runnable_after_setup` recipe can proceed unchanged. An adaptation requires a new recipe identity and explicit user choice.

This is the key correction from the follow-up user clarification: **the machinery to ask and validate the research question matters more than any one model such as Copula.**

## 10. Just-in-time setup instead of setup-first UX

The product must preserve fail-closed identity and admission while changing when the user experiences them.

### 10.1 Asset selector behavior

Research asset selection should search **researchable asset intent**, not expose the entire unresolved venue-code queue by default.

Recommended ordering:

```text
1. exact canonical/venue symbol match
2. exact known alias/current venue code
3. prefix matches
4. substring/other matches under a secondary heading
```

The selected item should remain visible and the result list should collapse.

### 10.2 Unresolved identity should interrupt the research task, not replace it

Example:

```text
W needs one-time setup

QAP found W on Binance and Gate, but this workspace has not yet
confirmed which canonical asset identity those venue codes represent.

[Confirm W]  [Why QAP asks this]
```

After confirmation, return to the same Pair Research form with `W` still selected.

The Product must not silently infer identity from ticker equality.

### 10.3 Approval is a separate decision

Identity means:

> “this venue code maps to this canonical asset identity.”

Approval means:

> “this operator allows QAP to include this asset in Product research.”

The Product can present those decisions in one bounded setup sequence, but persistence/authority must remain separate.

### 10.4 Independent identity evidence remains an open design decision

The current backend correctly requires explicit identity confirmation but leaves the human responsible for the actual independent evidence. A novice-friendly cockpit needs a safe answer to “how do I know this W is the intended W?”

Possible future evidence sources could include explicit venue metadata, contract/network identifiers, or a curated local identity registry, but none should be assumed or implemented until reviewed. The plan must preserve this as a named unresolved design question rather than pretending the UI can solve identity truth by itself.

## 11. Pair readiness and data preparation

Pair Research should answer readiness in the context of the selected pair:

```text
W / BTC
Identity: ready / needs setup
Approval: ready / needs approval
Historical data: ready / needs preparation
Direct market for deep replay: ready / unavailable
```

User-facing action when history is missing:

> Prepare data for this research

The first implementation can reuse current whole-approved-scope Product preparation if that is the smallest correct backend path. Pair-specific acquisition should be an optimization only when measured preparation cost makes it worthwhile.

The user should not have to navigate into a general Market Data workspace and understand immutable generations just to continue a pair hypothesis. Exact dataset lineage remains available under audit details.

## 12. Pair Research result design

A completed pair result should organize evidence by the question the user asked.

Suggested primary view:

```text
W / BTC
Current Approved Market Research
Data through <cutoff>

Method comparison
-------------------------------------------
Log-ratio mean reversion
  Fast / Base / Slow evidence
  selected/deep-replay state
  economic result or valid rejection

Residual mean reversion
  orientations + Fast / Base / Slow evidence
  selected/deep-replay state
  economic result or valid rejection
-------------------------------------------

Overall
  what survived
  what was rejected
  what was unavailable
  next valid action
```

Do not manufacture a single “winner” unless an authoritative current protocol defines one.

Advanced/audit disclosure can contain:

- candidate IDs;
- protocol identity;
- readiness/claim identity;
- semantic fingerprints;
- dataset IDs and exact physical generation paths;
- raw model parameters/evidence tables.

This reverses the current emphasis: audit truth remains present, but it is not the first thing a user must understand.

## 13. Universal Scan result design

The universal result should make the scanner visible as a scanner.

Before launch:

```text
22 ready approved assets
231 possible unordered relationships
Medium-term research
QAP pair-model protocol
```

The exact number of actual valid comparisons may differ by venue/eligibility and must come from backend truth.

After completion, use the already backend-composed stage counts rather than reconstructing them in React:

```text
relationships compared
retained relationships
rules evaluated
valid rules
selected for deep replay
completed / unavailable replay
rejected replay
Research Ideas
```

The result table should support practical organization/filtering such as:

- contains asset W;
- venue;
- model family;
- resolution/template;
- Research Idea / rejected / unavailable;

Those are view filters over completed evidence, not new research policy.

## 14. “Interesting” must remain a scientific state, not a UI score

The user naturally asks “which coins/pairs are interesting?” The Product must define this without introducing a hidden recommender.

Recommended language:

- `Relationship retained for deeper evaluation`
- `Selected for deep replay`
- `Research Idea — survived declared historical/economic checks`
- `Rejected research — valid negative evidence`
- `Replay evidence unavailable`

Avoid:

- “best coin”;
- “buy”;
- “recommended pair”;
- a frontend-generated 0–100 attractiveness score;
- ranking by mutable UI heuristics.

If ordering is required, use an existing authoritative scanner ordering/promotion state or neutral deterministic sorting. Any new ranking objective is a scientific-policy change.

## 15. Recommended API/composition direction for later implementation

This is a planning direction, not an implementation contract yet.

### Pair Research

The smallest plausible current-QAP-native seam is a Product pair-research launch that:

1. accepts two canonical Product assets + horizon + opaque readiness binding;
2. validates both assets against current approved readiness;
3. resolves common ready venue paths and exact M3 generation bindings;
4. requires the real direct market only where deep replay requires it;
5. builds a current-approved scan scope containing only the selected pair's assets;
6. preserves the pair as an explicit Product research focus/pin without invoking strict-PIT forensic semantics;
7. invokes the existing `RUN_SCAN` scientific operation / `run_scan_with_qap` path;
8. records a separately truthful Product pair/focus scope identity;
9. returns ordinary scanner artifacts so existing candidate, longitudinal, History, and Portfolio consumers continue to work.

The design should strongly prefer this composition over building a second pair backtester.

### Universal Scan

Keep the current Product scan engine and change presentation/entry semantics first. Only add API fields when required by genuine user choices.

### Focus Scan

If implemented, it can potentially reuse the same bounded Product scope concept with one focus asset plus all compatible approved-ready counterparts. It must not silently change the scientific graph/promotion policy without a versioned contract.

## 16. Research modes: simple Product defaults and explicit Experiment Lab

The user does need method choice, but not every research surface should have the same freedom.

### Simple Pair Research

The novice/default Product flow should use one versioned QAP pair-comparison recipe that evaluates the currently admitted Scanner-V1 pair families together and records the complete sibling family. This makes `W / BTC` immediately useful without requiring protocol design choices.

### Universal Scan

The normal scanner remains a versioned Product protocol over the approved-ready universe. It should not turn into an arbitrary method-builder because changing graph/trial enumeration changes the claim.

### Experiment Lab

Advanced research should expose the new recipe machinery directly:

```text
Choose research object
-> choose/define a method recipe
-> choose declared parameters / variants
-> choose data role and evaluation protocol
-> Check support
-> inspect exact blockers/adaptations
-> Run only if the recipe compiles to current QAP authority
```

Here user-selected methods are legitimate because they are **predeclared research variants**, not silently selected after outcomes. Sibling attempts remain linked under `research_family_id`, and exploratory/development/final-OOS semantics continue to control what can be claimed.

The Experiment Lab should expose both friendly forms for catalogued components and an advanced structured recipe view. It should not execute arbitrary Python or dynamically import strategies.

## 17. Revised Phase-17 M10 recommendation

The real-user walkthrough and follow-up clarification invalidate the assumption that M10 is only a final comprehension study or a one-off Pair Research UI repair.

M0-M9 remain complete. They should not be reopened.

M10 should be reframed as:

### M10-0 — Research Cockpit + Experiment Contract Design Amendment — CURRENT

Research, review, and freeze the corrected Product/experiment journey before implementation.

Outputs:

- this investigation;
- amended Phase-17 plan;
- approved Pair Research / Universal Scan / Focus Scan semantics;
- approved Experiment Lab / Research Recipe schema and fidelity states;
- approved read-only `Check support` behavior and typed reason vocabulary;
- approved compile-down boundary to existing `ExperimentManifest`/research-family authority;
- approved setup-interruption behavior;
- initial explicit capability catalog derived from current QAP, without a plugin framework.

No implementation until reviewed.

### M10-A — Typed Research Recipe + Capability Preflight

Implement the smallest backend domain/API owner that can answer whether a declared recipe is executable **before** starting a scientific run.

Required behavior:

- structurally parse a recipe envelope without treating unknown method IDs as executable;
- resolve each catalogued component through an explicit capability catalog;
- validate configuration using component-owned typed validators;
- distinguish `runnable_exact`, `runnable_after_setup`, `adaptation_possible`, `diagnostic_only`, `unsupported`, `blocked_by_constitution`, and `invalid`;
- return typed reasons rather than only `ExperimentSetupError` strings;
- separate method support from identity/data/direct-market readiness;
- compile only exact supported recipes to one or a finite family of current `ExperimentManifest` objects;
- preserve `research_family_id`, data role, controls, immutable fingerprints, code provenance, negative results, and final-OOS rules;
- never auto-convert an unsupported paper method into a QAP adaptation;
- remain read-only during check/preflight.

The initial catalog should describe **existing** QAP capabilities first: rolling log-ratio evidence, rolling residual evidence, slow momentum, cross-sectional relative return, scheduled targets, basket graph, existing controls, execution modes, and current data-role/economic constraints. This milestone is not permission to implement new research methods.

### M10-B — Research Cockpit + Experiment Lab Product Surface

Build the user-facing surface on top of M10-A:

- **Research a pair** — e.g. `W / BTC`, with the default QAP pair-comparison recipe;
- **Scan my universe** — the existing current-approved scanner presented explicitly as a scanner;
- **Focus scan** — one asset against approved-ready counterparts if the reviewed scope seam remains small;
- **Experiment Lab** — choose/inspect a research recipe, check support, see exact blockers/adaptations, and run supported recipes;
- exact-first asset search and selected-item mobile behavior;
- just-in-time identity/admission/data setup while preserving the draft;
- pair/universe readiness in user-task language;
- progressive disclosure of protocol IDs, fingerprints, physical generation paths, and other audit data.

Experiment Lab method selection is allowed because the recipe/family/data-role contract makes it explicit. The simple Product scanner remains versioned and bounded.

### M10-C — Capability/Fidelity Proof Using Real Methods

Before claiming the machinery works, exercise it with deliberately different recipes:

1. **Current QAP rolling residual pair recipe** — should reach `runnable_exact` or `runnable_after_setup` for a ready pair.
2. **Current slow-momentum recipe** — should explain that it is asset evidence/policy, not automatically a pair-relationship model.
3. **Student-t Copula recipe** — should report `known_method_not_implemented` / no current model contract, not falsely blame the selected pair.
4. **Palazzi 2025 exact-replication recipe** — should identify the related OLS/z-score capability while blocking faithful replication for long-short/selection/risk-method differences.
5. **Palazzi-inspired QAP adaptation** — only if manually declared as a different recipe; must never inherit an `exact replication` claim.
6. **Unknown method ID** — should return `unknown_method`, not attempt dynamic dispatch.

This is an acceptance proof of the **research machinery**, not a requirement to implement Copula or Palazzi's strategy.

### M10-D — Representative-user acceptance

Only after M10-A/B/C are integrated should actual/likely users repeat realistic tasks without developer coaching:

- find exact W;
- research W/BTC with the default QAP recipe;
- scan the approved universe;
- open Experiment Lab and check whether a named method/recipe is supported;
- understand the difference between `method unsupported`, `pair/data not ready`, `blocked by QAP constitution`, and `valid negative research`;
- inspect what a paper recipe actually declares about relationship, signal, rebalance, risk, tuning, benchmarks, and OOS evaluation;
- distinguish an exact replication from a QAP adaptation;
- distinguish Product current-approved research from strict historical PIT;
- confirm QAP does not recommend/authorize/place live trades.

## 18. Review decisions required before implementation

The following decisions are intentionally left for user/design review.

### D1 — Research Recipe envelope

**Recommendation:** a small first-class typed recipe above `ExperimentManifest`, explicitly separating research object, evidence/model, decision rule, allocation/rebalance, risk overlays, selection/calibration, execution/costs, and evaluation/benchmarks.

Do not make users author raw low-level experiment manifests for normal experiments, but keep the compiled manifest visible for audit.

### D2 — Capability catalog scope

**Recommendation:** one explicit in-code catalog of known QAP research components and known-but-unimplemented named methods used for explanation. No generic plugins, dynamic imports, or runtime strategy registration.

### D3 — Default Pair Research versus Experiment Lab

**Recommendation:** simple Pair Research runs a frozen versioned QAP pair-method family; advanced Experiment Lab permits declared method/parameter selection and records every sibling attempt under research-family/data-role semantics.

### D4 — Paper recipes

**Recommendation:** paper methodologies are manually curated recipe templates with source metadata. Do not attempt automatic paper-to-code interpretation in Phase 17. The support checker judges the declared recipe, not natural-language prose.

### D5 — Copula

**Recommendation:** Copula is only one known-unimplemented method in the initial catalog. It should not block M10 or Phase-17 closure. A later method-expansion design can implement it if/when it becomes a useful research hypothesis.

### D6 — Palazzi exact versus adapted

**Recommendation:** encode the paper as a fidelity test. Exact reproduction should remain blocked while it requires long-short positions and other undeclared current capabilities. A long-only QAP adaptation is a different recipe with a different claim.

### D7 — Momentum semantics

Do not label all momentum as one pair model. The capability checker should identify whether the requested recipe means slow single-asset evidence, cross-sectional relative return, pair-blind control, or a new method.

### D8 — Identity evidence UX

Decide what novice-facing independent evidence QAP may show when confirming a venue code. The backend must still fail closed and never infer identity from ticker equality alone.

### D9 — Pair-specific data preparation

**Recommendation:** initially reuse whole approved-scope preparation if it keeps implementation small; add pair-only preparation only when measured latency/request burden justifies it.

### D10 — Result ordering

**Recommendation:** use existing scanner stage/promotion truth and deterministic filters; do not create a new “interestingness” score during the cockpit redesign.

## 19. Explicit non-goals

This amendment does not authorize:

- weakening canonical identity rules;
- auto-approving venue listings;
- reclassifying current metadata as historical PIT evidence;
- changing Scanner-V1 thresholds/economics merely for UI convenience;
- inventing a new rank score;
- synthetic direct markets for authoritative replay;
- porting legacy Copula code merely because the support catalog knows the method name;
- automatically translating a paper or natural-language methodology into executable code;
- adding a generic strategy-plugin registry, dynamic imports, arbitrary user Python, or a second backtester;
- silently adapting an unsupported exact-replication recipe while retaining the original research claim;
- importing the legacy `DataFetcher`, APIGuardian, CCXT truth model, Tethered Mesh execution semantics, or live runtime;
- adding private exchange credentials or live orders;
- turning Portfolio into an optimizer;
- removing exact provenance/audit data.

## 20. Final assessment

The Product Layer is not a failed architecture. It is an **incomplete product composition**.

M0-M9 built the trustworthy operating substrate that a real research cockpit needs. The mistake was assuming that exposing readiness, lifecycle, and evidence clearly would automatically make the research job obvious.

The corrected product principle is:

> **Start from the research question. Type-check the declared methodology before execution. Interrupt only when setup is genuinely required. Keep audit truth available, but never make audit vocabulary the price of beginning research.**

For the user's concrete example, the target experience is therefore:

```text
Research a pair
W + BTC
Medium-term
Run QAP pair research

-> if W needs setup, resolve/approve it once without losing the draft
-> if data is missing, prepare it without abandoning the draft
-> run the existing current-approved scanner over the focused pair
-> compare current admitted pair methods
-> show economic replay/negative/unavailable evidence
-> expose exact protocol/data lineage only under audit details
```

And for discovery:

```text
Scan my universe
22 ready approved assets
Medium-term
Run

-> truthful stage funnel
-> relationships / Research Ideas
-> filter by W or model family
-> open one pair for deeper research
```

And for a researcher reproducing or exploring methods:

```text
Experiment Lab
W / BTC
Recipe: Palazzi 2025 exact reproduction
Check support

-> pair object: supported
-> related rolling OLS/z-score evidence: available but not identical
-> long-short position: blocked by QAP constitution
-> paper-specific tuning/risk mechanisms: not implemented
-> exact replication: not runnable
-> optional QAP adaptation: separate recipe, never silently substituted
```

That is the Product direction to review and freeze before implementation.
