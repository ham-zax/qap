# QAP System Design

**Date:** 2026-08-17

**Status:** Review draft; not implementation authorization

**Product:** QAP — crypto wealth-compounding and relative-rebalancing system

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

For a frozen starting basket `q0`, strategy ending quantities `qS(T)`, passive HODL ending quantities `qH(T)=q0`, and one consistent terminal cross-price vector `p(T)`:

```text
strategy_value(T) = value(qS(T), p(T))
hodl_value(T)     = value(qH(T), p(T))

HODL-relative portfolio wealth growth
    = strategy_value(T) / hodl_value(T) - 1
```

The ratio is the primary scalar score. A valuation numeraire is a coordinate for aggregation, not the product objective; when conversion prices are internally consistent at the same timestamp, the strategy/HODL ratio is invariant to the chosen common numeraire. Per-asset coin accumulation remains secondary attribution and may not override a negative primary wealth result.

A strategy cannot claim success when this matched HODL-relative result is negative merely because one coin count increased.

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
- comparison against a simple admissible rebalance baseline where applicable.

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

A stablecoin or quote asset may later be allowed as a **transient execution bridge** for explicit two-leg spot conversion when the operator explicitly admits transient ownership of that asset. That must be modeled as two real fills with two costs and must never become hidden synthetic execution. Any residual bridge quantity remains real portfolio inventory and is included in valuation/accounting even when it is not part of the target basket. The first deterministic vertical slice uses direct spot conversion only.

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
  market/         immutable market observations, alignment, source adapters
  portfolio/      assets, quantities, inventory state, target allocations
  relationship/   pair identity, ratio evidence, model evidence
  policy/         evidence -> target allocation; pure economic policy
  execution/      deterministic spot fill/routing/cost semantics
  evaluation/     valuation, HODL, attribution, baseline comparison
  experiment/     frozen manifests, deterministic runs, provenance/results
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
- Historical bars use candle-open timestamps and have `close_time = open_time + interval`.
- Only bars with `close_time <= decision_time` are admissible to a decision.
- For contiguous bars, a decision computed immediately after bar `t` completes has `decision_time = bar_t.open_time + interval`, which equals the next bar's open; execution may use that next-bar open but never any later value from that bar.

### 8.3 Default historical timing

For bar-based deterministic replay:

1. Observe completed bar `t` and all prior admitted data.
2. Compute relationship evidence.
3. Compute target allocation.
4. Convert it to a rebalance intent.
5. Fill at the **next bar open** using declared cost/slippage semantics.
6. If there is no next bar, record the intent as unfilled; do not backfill at the last close.

Any model requiring a different timing contract must declare it explicitly in its experiment manifest.

## 9. Market-data semantics

An admitted observation carries at least:

```text
venue
instrument
base_asset
quote_asset
interval
candle_open_time_utc
open
high
low
close
volume (when available)
source/provenance
```

Rules:

- instrument orientation is explicit;
- inverse markets are not silently substituted;
- synthetic cross-rates are labeled as analytical constructs, not executable markets;
- gaps and duplicates are detected;
- requested windows use explicit inclusive/exclusive endpoints;
- raw source data and derived relationship series have independent fingerprints;
- point-in-time data used by historical decisions must be reproducible.

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

The first simple baseline is a deterministic periodic or threshold rebalance rule that is admissible under the same spot-only/cost contract. Model-driven logic must demonstrate incremental value over this simpler mechanism before being called useful.

## 14. Research protocol

Research serves QAP; it is not the product identity.

A research experiment declares:

```text
hypothesis
frozen basket
anchor (if any)
data window and source
relationship model
policy
execution/cost contract
baseline(s)
train/validation/OOS split when model fitting occurs
metrics
predeclared success/rejection conditions
```

Rules:

- failed and neutral experiments remain recorded;
- in-sample and OOS labels cannot be mixed;
- model quality and economic quality are separate claims;
- multiple searches/features/models require selection-pressure awareness;
- concentrated edge is reported as concentrated, not generalized;
- no research result silently changes default production policy;
- one research result is not promoted to constitutional invariant.

The repository will not recreate v2's candidate/promotion bureaucracy. Reproducibility is achieved with small manifests, fingerprints, deterministic runners, and concise result records.


## Companion design

Sections covering the web product, API, storage/provenance, testing, failure handling, security/deployment, autonomous-agent boundary, rejected approaches, invariants, anti-bloat rules, phase map, and first shippable QAP are intentionally split into `docs/superpowers/specs/2026-08-17-qap-web-operations-design.md` so neither hand-written design file becomes a documentation God object. The two files form one design and must be reviewed together.
