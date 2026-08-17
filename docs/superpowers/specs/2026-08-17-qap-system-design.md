# QAP System Design

**Date:** 2026-08-17

**Status:** Approved design baseline; implementation authorized phase-by-phase under `docs/plans/` sequencing and stop conditions.

**Product:** QAP — crypto wealth-compounding and relative-rebalancing system

## Update context — 2026-08-17

Trigger: Replay/experiment implementation review exposed a post-fill marking mismatch and fail-open final-OOS entry points.
Purpose: Clarify existing timing and research-integrity contracts without changing the approved economic objective.
Impact: Decisions remain completed-data-only; post-decision accounting uses same-boundary marks, and final-OOS computation requires durable precommitment. Relationship claims are classified relative to their predeclared primary control.
Evidence: Phase 06 and Phase 07 regression suites and plans.

## Update context — 2026-08-17 (Phase 09 evidence workbench)

- **Trigger:** end-to-end API and rendered-browser validation connected the relationship, experiment, portfolio, and UI layers for the first time and exposed one real compatibility defect: a declared common quote could not act as an explicit relationship coordinate.
- **Purpose:** preserve one authoritative analytical chain from admitted data and immutable artifacts through typed read-only projections to browser evidence, including honest negative and invalid states.
- **Impact:** a unique common reference may be represented only as a labeled deterministic all-ones identity coordinate, never as market observations. API DTOs identify those assets explicitly. Portfolio compounding diagnostics, time below control, benchmark ladders, inventory attribution, costs, and audit records remain backend-owned. The React workbench consumes generated contracts, stores analytical selection in the URL, performs no financial recomputation, and keeps final-OOS/research-family boundaries visible.
- **Evidence:** relationship/API contracts, strict Python and TypeScript checks, deterministic generation, component interaction tests, production build, and rendered desktop/mobile WCAG verification cover the integrated contract.

## 1. Product definition

QAP is a **spot-only crypto wealth-compounding system whose economic state is owned inventory**.

It manages a curated ecosystem of assets the operator is willing to own, continuously measures their relative relationships, and uses economically justified reallocations to improve the portfolio.

Its primary purpose is to **compound portfolio wealth relative to matched passive ownership after realistic costs**. Coin-unit accumulation is a secondary outcome and attribution lens. QAP does not require broad market-direction prediction, and it does not treat any reporting numeraire as the economic objective.

The canonical economic question is:

> Starting from the same frozen basket, over the same window, after realistic costs, did QAP create more portfolio wealth than passive HODL and than simpler admissible rebalancing rules?

Pair relationships are evidence and execution atoms. **Portfolio inventory is the economic state/object being transformed; matched-HODL-relative wealth is the primary success objective.** Statistical models are replaceable instruments whose authority must be earned empirically.

## 2. Design hierarchy

The architecture follows this hierarchy:

```text
Portfolio / Inventory Objective
    -> Relationship Evidence
    -> Economic Opportunity / Policy
    -> Target Allocation
    -> Rebalancing
    -> Execution
    -> Accounting
    -> Matched HODL / Simple-Baseline Comparison
```

Models such as Copulas, cointegration, residual models, or future techniques live inside **Relationship Evidence**. They do not define the system above them.

The central state transition is:

```text
portfolio ownership vector
    -> relationship evidence changes
    -> desired ownership vector changes
    -> economically useful rebalance
    -> fills
    -> new ownership vector
```

A "trade" is an execution consequence. It is not the primary domain object, and there is no requirement that a useful lifecycle end in a fully "closed position."

## 3. Historical reference constitution

`docs/REFERENCE_BOUNDARY.md` is normative.

QAP v1 and QAP v2 at `/home/hamza/repo/tradingview_ratio` are read-only historical evidence corpora. They are not architecture templates, runtime dependencies, or automatic authorities.

The clean QAP must never import runtime code from that repository. Any reused concept must pass the admission protocol in `docs/REFERENCE_BOUNDARY.md`.

This rule exists because the two historical generations failed in opposite ways:

```text
v1: mechanism/feature accretion + mixed ownership + experiments becoming architecture
v2: governance/evidence accretion + object narrowing + research process becoming product
```

Clean QAP must be disciplined enough to avoid v1 without becoming bureaucratic enough to recreate v2.

## 4. Economic object and success metrics

### 4.1 Curated basket

A QAP portfolio declares a curated basket of assets the operator is willing to own. Basket admission is explicit; the engine does not infer religious, investment, or ownership suitability from ticker metadata.

The first implementation will use a manually declared basket. Automatic universe discovery is out of scope until the inventory engine is correct.

Research must distinguish two different universe claims:

- **declared-fixed-basket retrospective** — "given these assets that I explicitly selected, how would this policy have behaved historically?" This is the initial supported mode and must not be described as historical discovery performance;
- **point-in-time investable universe** — "could QAP have selected these assets using only what was actually listed/eligible/liquid at that historical time?" Any later discovery/generalization claim requires point-in-time listing/eligibility semantics and fails closed when those records are unavailable.

An asset's economic identity is not identical to a venue ticker string. Clean QAP uses a stable project-level `AssetId`; venue symbols/instruments are time-bounded market mappings owned by `qap.market`.

### 4.2 Anchor

A portfolio may declare an **analysis/discovery anchor**, commonly BTC, but the anchor is not automatically the final accumulation target and is not model authority.

The anchor may organize:

- discovery families;
- relative decomposition (`X/A`, `Y/A`);
- stress/context views;
- diagnostics and attribution.

It must not silently redefine the basket objective into single-asset accumulation.

### 4.3 Pair

A pair is one canonical relationship between two assets. `X/Y` and `Y/X` are orientations of the same relationship identity, not two independent discoveries.

Orientation is explicit everywhere. `X/Y` means **Y units per one X unit** (base `X`, quote `Y`), matching direct spot-market convention.

### 4.4 Primary economic metric

Simple summation of heterogeneous coin quantities is meaningless. Raw standalone USD P&L can confuse market beta with strategy value. Clean QAP therefore measures **portfolio wealth relative to matched passive ownership**, using one declared numeraire only to aggregate heterogeneous holdings consistently.

For a frozen starting basket `q0`, strategy ending quantities `qS(T)`, passive HODL ending quantities `qH(T)=q0` when there are no external flows, and one consistent terminal cross-price vector `p(T)`:

```text
strategy_value(T) = value(qS(T), p(T))
hodl_value(T)     = value(qH(T), p(T))

HODL-relative portfolio wealth growth
    = strategy_value(T) / hodl_value(T) - 1
```

The ratio is the primary scalar score. A valuation numeraire is a coordinate for aggregation, not the product objective; when conversion prices are internally consistent at the same timestamp, the strategy/HODL ratio is invariant to the chosen common numeraire. Per-asset coin accumulation remains secondary attribution and may not override a negative primary wealth result.

A strategy cannot claim success when this matched HODL-relative result is negative merely because one coin count increased.

When a run contains explicit external deposits or withdrawals, every compared portfolio receives the same exogenous flow stream at the same effective timestamps before tactical policy differences are evaluated. **Strict inventory HODL** remains the primary passive counterfactual: it receives those same asset flows and never tactically trades them. An accumulation/timing claim additionally requires a **matched-contribution static HODL** control that mechanically deploys each contribution according to one predeclared static allocation using the same feasible execution semantics. This prevents simple crypto-market exposure from being mislabeled as smart accumulation.

### 4.5 Secondary economic diagnostics

Every result also reports:

- per-asset quantity ratio vs HODL (the primary coin-accumulation diagnostic);
- per-asset contribution to terminal relative value;
- concentration and contributor-share concentration;
- turnover;
- fee drag;
- slippage drag;
- rebalance count and notional;
- anchor-relative diagnostics;
- drawdown of QAP relative to HODL;
- comparison against a simple admissible rebalance baseline where applicable;
- time below HODL/the declared primary incremental control;
- flow-adjusted or unitized return diagnostics when external deposits/withdrawals exist;
- explicit inventory-flow trace sufficient to explain how quantities changed.

## 5. Shariah/action-space boundary

QAP's initial executable action space is intentionally narrow:

- actual spot ownership only;
- long-only inventory;
- no shorting an unowned asset;
- no leverage or margin;
- no borrowing for trading;
- no futures, perpetuals, options, CFDs, or synthetic derivative exposure;
- no interest/riba-based financing;
- no yield-bearing cash or lending feature inside QAP;
- ambiguous instrument types fail closed.

Asset-level Shariah suitability remains an explicit operator admission decision; QAP enforces the mechanical action-space boundary and does not claim to replace scholarly review.

A stablecoin or quote asset may later be allowed as a **transient execution bridge** for explicit two-leg spot conversion when the operator explicitly admits transient ownership of that asset. That must be modeled as two real fills with two costs and must never become hidden synthetic execution. Any residual bridge quantity remains real portfolio inventory and is included in valuation/accounting even when it is not part of the target basket. A third-party fee token is treated the same way: if a venue charges a fee in an asset, that asset must be explicitly admitted/accounted and its balance change cannot be hidden. The first deterministic vertical slice uses direct spot conversion only.

## 6. System architecture

The recommended architecture is one repository, one Python modular monolith, one thin API, and one React web client.

```text
Historical/market observations
        |
        v
qap.market
        |
        v
qap.relationship
        |
        v
qap.policy
        |
        v
qap.portfolio / qap.execution
        |
        v
qap.evaluation
        |
        +------> qap.experiment
        |
        +------> qap.api ------> web/
```

There is no service mesh, plugin framework, message bus, database platform, or strategy registry in the initial architecture.

### 6.1 Planned Python package boundaries

```text
src/qap/
  market/         immutable observations, price snapshots, alignment, source adapters
  portfolio/      assets, quantities, inventory state, target allocations
  relationship/   pair identity, ratio evidence, model evidence
  policy/         evidence -> target allocation/rebalance plan; pure planning logic
  execution/      deterministic spot fill/routing/cost semantics
  evaluation/     valuation, HODL, attribution, baseline comparison
  experiment/     manifests, run orchestration, provenance/results/reconciliation
  api/            thin FastAPI presentation boundary
```

The exact internal file splits are specified phase-by-phase in `docs/plans/` and should not be pre-created before their phase.

### 6.2 Web boundary

```text
Python financial truth
    -> typed API DTO
    -> FastAPI/OpenAPI
    -> generated TypeScript types/client
    -> React view state
    -> chart pixels
```

The browser never owns wallet state, accounting truth, fill simulation, or experiment results.

## 7. Ownership rules

### 7.1 One state, one owner

- Market observations are immutable facts after admission.
- `PortfolioState` is the sole owner of actual simulated holdings.
- Policy is pure: it reads evidence/state and emits an allocation target; it cannot mutate holdings.
- Execution converts an accepted rebalance into fills; it does not independently own a second wallet.
- Portfolio applies fills exactly once.
- Evaluation derives metrics; it does not mutate portfolio state.
- Experiment manifests own frozen run inputs; research outputs cannot silently modify policy defaults.
- API and web layers are presentation/interaction boundaries only.

### 7.2 Configuration

Business state must not hide in environment variables.

Environment variables are permitted for operational concerns such as secrets, host/port, or filesystem roots. Portfolio composition, fees, slippage, interval, model parameters, policy thresholds, benchmark definition, and experiment semantics are explicit typed inputs/configuration passed into the owning component.

## 8. Numeric and temporal semantics

### 8.1 Numeric split

- Wallet quantities, fees, fill prices used for accounting, and notional arithmetic use `Decimal` with explicit market precision/rounding.
- Statistical/relationship computation may use `float64`/NumPy-style arrays.
- Crossing from model output into executable quantities is explicit and tested.

This prevents statistical convenience from becoming accounting truth.

### 8.2 Time

- Canonical timezone: UTC.
- Internally, historical bars use candle-open timestamps plus an exclusive interval boundary `bar_end_exclusive = open_time + interval`; raw venue close timestamps are preserved separately when supplied by the source.
- Only bars with `bar_end_exclusive <= decision_time` are admissible to a decision.
- For contiguous bars, a decision computed immediately after bar `t` completes has `decision_time = bar_t.open_time + interval`, which equals the next bar's open boundary; execution may use that next-bar open **as a causal reference price** but never any later value from that bar.

### 8.3 Default historical timing

For bar-based deterministic replay:

1. Observe completed bar `t` and all prior admitted data.
2. Compute relationship evidence.
3. Compute target allocation.
4. Convert it to a rebalance intent.
5. Use the **next bar open as the deterministic execution reference**, then derive the modeled fill from explicit direction-aware slippage/fee/quantization semantics. QAP does not claim that the observed bar open was a guaranteed executable market price.
6. Mark every role's post-decision inventory at that same causal boundary using the next contiguous opens of admitted direct numeraire markets. Keep this accounting snapshot separate from the completed-close snapshot shown to policy; a zero-cost conversion must not manufacture gap P&L.
7. If there is no next bar, record the intent as unfilled and use the final completed close only as the terminal valuation mark; do not backfill an execution.

Any model requiring a different timing contract must declare it explicitly in its experiment manifest.

## 9. Market-data semantics

An admitted observation carries at least:

```text
venue
instrument
venue_symbol
base_asset
quote_asset
instrument_valid_from / instrument_valid_to (when known)
interval
candle_open_time_utc
source_close_time_utc (when supplied)
open
high
low
close
volume (when available)
source/provenance
```

Rules:

- instrument orientation is explicit;
- `AssetId` is stable economic identity; venue symbols/instrument mappings are source-specific and may have validity windows;
- inverse markets are not silently substituted;
- synthetic cross-rates are labeled as analytical constructs, not executable markets;
- gaps and duplicates are detected;
- requested windows use explicit inclusive/exclusive endpoints;
- raw source data and derived relationship series have independent fingerprints;
- point-in-time data used by historical decisions must be reproducible;
- a fixed-current-basket retrospective cannot be relabeled as evidence that the same basket was historically discoverable/investable;
- source-native timestamps are preserved while internal completion semantics remain venue-independent.

Initial persistence should be local and file-oriented (Parquet plus small JSON manifests). A database is not justified until an actual concurrency/querying requirement appears.

## 10. Relationship evidence

### 10.1 First relationship primitive

The first real relationship evidence is intentionally model-free and uses **completed-bar close prices** by default:

```text
canonical pair
raw X/Y ratio
log ratio
normalized X and Y price paths
optional anchor decomposition X/A and Y/A
```

For synchronized prices:

```text
X/Y = (X/A) / (Y/A)
log(X/Y) = log(X/A) - log(Y/A)
```

The anchor view therefore decomposes the relationship; it does not create a second truth.

### 10.2 Model interface

A relationship model consumes admitted point-in-time observations and emits a typed `RelationshipObservation` containing:

- canonical pair identity;
- orientation;
- as-of timestamp;
- model identifier/version;
- model-specific evidence values;
- validity/coverage status;
- provenance/fingerprint.

Every model also declares its reciprocal-orientation behavior:

```text
exact_transform       # one fit can be transformed exactly for inverse orientation
directional_transform # an explicit model-specific transform exists
refit_required        # the inverse orientation requires an independent fit
```

The raw price relationship still has one canonical identity, but Clean QAP does not assume that every fitted statistical model is reciprocal by simple sign/inversion.

No model output directly mutates inventory.

### 10.3 Model authority

Student-t Copula, cointegration, residual z-score, tail measures, topology, or any future method are hypotheses/models. None is constitutional.

Historical importance is not an admission criterion by itself. A historical model may be rejected at its admission review without reimplementation when there is no specific current falsifiable question worth testing.

A model earns expanded authority only through economic evidence relative to controls and OOS data.

## 11. Policy, allocation, and rebalancing

The policy boundary converts evidence into a **desired portfolio state**, not OPEN/CLOSE trade labels.

```text
PolicyInput:
  current inventory
  current relationship evidence
  declared basket
  costs / execution constraints visible to policy

PolicyOutput:
  target allocation
  reason/evidence references
  no-action or rebalance decision
```

Target allocations are long-only and sum to 1 within declared tolerance for the mutable portfolio value.

The core policy/rebalance contract is deliberately agnostic about why a target was requested. Scheduled fixed targets, threshold/no-trade rules, contribution-aware rules, slow trend/momentum gates, volatility-aware rules, and relationship-conditioned rules must all pass through the same target/no-action boundary. Momentum and mean reversion are research hypotheses, not policy-layer truths.

### 11.1 Dummy policy first

The first vertical slice uses a deterministic policy with no statistical claims. Example: at predefined evidence states, request a known 50/50 or 70/30 target.

This proves allocation, costs, wallet conservation, replay, accounting, and HODL comparison **before** a real model can contaminate those semantics.

### 11.2 Economic no-trade threshold

A policy may propose a target, but rebalancing occurs only when the change is economically useful under explicit minimum-notional and estimated-cost rules. "No action" is a first-class valid result.

Partial rebalancing is first-class. Full liquidation is a special case, not the default lifecycle assumption.

## 12. Execution semantics

Initial execution is deterministic historical/paper execution only.

A fill contains:

```text
fill_id
decision_id
timestamp
venue
instrument
side
base_quantity
quote_quantity
price
fee
slippage
pre/post balances or reconciliation reference
```

Rules:

- fills are idempotently applied exactly once;
- balances cannot become negative;
- costs are explicit and applied exactly once;
- rounding/lot-size effects are explicit;
- unsupported market routes fail closed;
- direct-market execution is implemented before bridge routing;
- two-leg routing, when introduced, produces two fills and two cost events.

Live order placement is outside the initial product phases and requires a later explicit go/no-go decision.

## 13. Evaluation and benchmarks

Every executable experiment starts from one frozen ownership vector and produces at least:

- QAP terminal holdings;
- matched HODL terminal holdings;
- HODL-relative portfolio wealth growth;
- simple-baseline result where the experiment calls for one;
- per-asset inventory deltas;
- cost/turnover attribution;
- concentration diagnostics;
- run/data/config/code fingerprints.

The benchmark ladder is an economic contract:

```text
strict inventory HODL
  -> matched-contribution static HODL when external flows exist
  -> one predeclared periodic/fixed-weight rebalance control
  -> one predeclared cost-aware band/partial-rebalance control
  -> one predeclared contribution-aware band control when external flows exist
  -> one predeclared pair-blind predictive/common-mode control when the claim requires it
  -> relationship-conditioned policy
```

The controls use the same starting inventory, exogenous flow stream when present, prices, timing, costs, and execution model as QAP. A research family must predeclare which simple control is the **primary incremental benchmark** before final OOS evaluation; researchers may not search many simple controls and report whichever is easiest to beat. Relationship intelligence may be described as adding economic value only when it improves on that predeclared simple control after costs.

Research language distinguishes evidence strength without creating a promotion state machine:

- **promising candidate** — positive development/validation economics after costs with causal replay and no obvious parameter pathology;
- **research alpha** — positive predeclared historical final-OOS economics with appropriate selection-pressure treatment and credible robustness;
- **deployment candidate** — research alpha plus a genuinely prospective `forward_paper` period after the rule is frozen, operational/capacity evidence, and explicit readiness review.

## 14. Research protocol

Research serves QAP; it is not the product identity.

A research experiment declares:

```text
hypothesis
research_family_id
parent_run_id (optional)
frozen basket
universe_mode: declared_fixed_basket | point_in_time_investable
anchor (if any)
data window and source
relationship model
policy
execution/cost contract
baseline(s)
data role: exploratory | development | final_oos | forward_paper
train/validation split when model fitting occurs
metrics
predeclared success/rejection conditions
```

Rules:

- failed and neutral experiments remain recorded;
- attempted variants in the same research family remain discoverable, including failures;
- `final_oos` is an information-state claim, not merely a date label: once its result or chart is inspected and used to adapt code, parameters, pair selection, or the hypothesis, that window is consumed and becomes development evidence for subsequent work;
- a final-OOS run must be committed/frozen before its holdout is evaluated; public in-memory execution paths fail closed, and a completed result is authoritative only with its matching consumed commitment;
- model quality and economic quality are separate claims;
- multiple searches/features/models require selection-pressure awareness;
- formal family-level multiplicity methods (for example SPA/Reality Check style tests) are introduced only when the breadth of a serious claim warrants them; exploratory work is not forced through heavy governance;
- concentrated edge is reported as concentrated, not generalized;
- no research result silently changes default production policy;
- one research result is not promoted to constitutional invariant.

The default search order is intentionally simple-first: mechanical fixed/band rebalancing; contribution-aware rebalancing when explicit flows exist; slow time-series momentum/trend gating; relative-momentum/volatility controls when justified; transparent ratio/log-ratio relationship hypotheses; pair-blind common-mode/cross-sectional controls; and only then richer dependence models such as Student-t Copulas when a specific remaining falsifiable question justifies the added search denominator.

The repository will not recreate v2's candidate/promotion bureaucracy. Reproducibility is achieved with small manifests, fingerprints, deterministic runners, and concise result records.


## Companion design

Sections covering the web product, API, storage/provenance, testing, failure handling, security/deployment, autonomous-agent boundary, rejected approaches, invariants, anti-bloat rules, phase map, and first shippable QAP are intentionally split into `docs/superpowers/specs/2026-08-17-qap-web-operations-design.md` so neither hand-written design file becomes a documentation God object. The two files form one design and must be reviewed together.
