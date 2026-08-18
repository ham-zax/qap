# QAP Scanner V1 Slice 3 — Asset-Native Momentum + Manual Basket Design

**Date:** 2026-08-18

**Status:** design complete for review; implementation remains separately gated until the user explicitly approves this design and its implementation plan.

**Depends on:**
- `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`
- `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`
- `docs/research/2026-08-18-qap-scanner-slice1-results.md`
- `docs/research/2026-08-18-qap-scanner-slice2-results.md`
- `docs/superpowers/specs/2026-08-17-qap-system-design.md`

> **Update context — 2026-08-18**
> **Trigger:** Slice 2 is complete and repository-verified; the remaining Phase-15 gap is the separately gated one-inventory basket surface and broad asset-native research stream.
> **Purpose:** freeze the mathematical, research-integrity, execution, artifact, module, API, and workbench contracts for Scanner-V1 Slice 3 before implementation begins.
> **Impact:** replace the umbrella phrase “degree-normalized/component-neutral basket resolver” with an exact deterministic rule; keep asset-native momentum bounded and pair-blind; integrate the existing Phase-11 multi-asset executor into ordinary QAP replay rather than creating a scanner backtester; preserve one portfolio/inventory authority.
> **Evidence:** current QAP repository at Slice-2 handoff; the research references in §22.

---

## 1. Core question

Slice 3 answers two related but distinct research questions:

> **Asset-native discovery:** As of timestamp `t`, which point-in-time eligible assets show the strongest or weakest simple relative trend under one frozen O(N) rule, without forcing the universe through an NxM pair graph?

and:

> **Manual basket research:** Given one explicitly selected same-venue 3–6 asset basket and one explicit candidate rule for each selected pair edge, what single long-only QAP target follows from the simultaneous pair opinions, and does one authoritative QAP inventory create more wealth than matched HODL, mechanical rebalancing, and a pair-blind relative-momentum control after costs?

Slice 3 does **not** ask QAP to discover an optimal basket automatically.

---

## 2. Authority and claim boundary

The constitutional ownership chain remains:

```text
market / relationship evidence
        ↓
policy-owned target allocation
        ↓
QAP rebalance plan
        ↓
existing multi-asset execution
        ↓
one PortfolioState
        ↓
QAP evaluation / HODL / controls
```

Slice 3 is not a new financial engine.

### 2.1 Scanner authority

`qap.scanner` may own:

- asset-native research observations and ranks;
- `BasketDefinition` identity and manual-selection lineage;
- selected candidate references and evidence-class projections;
- scanner/basket artifact persistence;
- thin orchestration callbacks that do not import financial-authority packages.

`qap.scanner` must not own:

- target-allocation mathematics that move capital;
- fills;
- routing;
- accounting;
- portfolio wealth;
- HODL/control economics;
- joint basket capacity.

### 2.2 Policy authority

The deterministic graph-to-target resolver belongs under `qap.policy`, not `qap.scanner`.

It consumes a neutral target plus signed pair opinions and emits one `AllocationTarget`. It does not know scanner P&L, qualification state, candidate rank, prospective pass rate, liquidity rank, or historical Sharpe.

### 2.3 Execution authority

Basket execution must reuse the existing Phase-11 `execute_multi_asset_rebalance()` path. Scanner code may not create a second bridge router, fill model, wallet, or accounting loop.

### 2.4 Economic claim

Slice-3 basket replay is searched/manual **development evidence** unless a later separately approved basket-level prospective protocol freezes the entire basket rule before future observations.

Pair-level Slice-2 prospective evidence remains useful input evidence, but it does not make a newly combined basket prospectively validated.

Reserved final OOS remains sealed.

---

## 3. Research rationale: informative, not protocol authority

The literature supports testing simple crypto momentum, but it does not support constitutionalizing one universal momentum sign across QAP's broad universe.

- Liu and Tsyvinski report strong cryptocurrency time-series momentum in *Risks and Returns of Cryptocurrency* (NBER Working Paper 24877; later RFS 2021).
- Liu, Tsyvinski, and Wu report a cryptocurrency momentum factor in the cross-section in *Common Risk Factors in Cryptocurrency* (NBER Working Paper 25882; later Journal of Finance 2022).
- Han, Kang, and Ryu, revised March 2026, report strong time-series momentum but almost no cross-sectional momentum once they impose more realistic assumptions in *Momentum in the Cryptocurrency Market: A Comprehensive Analysis under Realistic Assumptions* (SSRN 4675565).
- Fičura and Colak find weekly reversal concentrated in small/illiquid coins while large/liquid coins exhibit weekly momentum in *Impact of Size and Volume on Cryptocurrency Momentum and Reversal* (SSRN 4378429).
- Dobrynskaya finds short-horizon momentum up to roughly 2–4 weeks and reversal beyond roughly one month in *Cryptocurrency Momentum and Reversal* (Journal of Alternative Investments 2023; SSRN 3913263).
- Xu and Wu's 2026 *Size-Momentum Puzzle in Cryptocurrencies* (SSRN 6628860) reports another size-dependent split between small-coin reversal and large-coin momentum.

Therefore Scanner V1 uses **one deliberately small asset-native momentum hypothesis** as discovery evidence and as a pair-blind control. It does not add a momentum/reversal router, size-conditioned sign switch, or model grid.

For pair aggregation, graph-ranking research gives a useful representation without granting an optimizer authority:

- Jiang, Lim, Yao, and Ye represent pairwise rankings as graph edge flows and separate globally consistent from cyclic components in *Statistical Ranking and Combinatorial Hodge Theory* (arXiv:0811.1067).
- Šarić, Begušić, Merćep, and Kostanjčar apply preference-relation graphs to contradictory multi-pair trading signals in *Statistical Arbitrage Portfolio Construction Based on Preference Relations* (arXiv:2310.08284).

Slice 3 adopts the **edge-flow representation**, not their long-short/optimization machinery. Pure contradictory cycles should not manufacture long-only capital conviction.

For neutral allocation and search restraint:

- DeMiguel, Garlappi, and Uppal show that estimated optimization gains can be overwhelmed by estimation error relative to the simple `1/N` benchmark in *Optimal Versus Naive Diversification* (RFS 2009; SSRN 1376199).
- Bailey, Borwein, López de Prado, and Zhu formalize the probability of backtest overfitting when many configurations are tried in *The Probability of Backtest Overfitting* (Journal of Computational Finance; SSRN 2326253).

These references motivate a small deterministic rule and complete attempt lineage. They do not prove that the frozen Slice-3 rule is profitable.

---

## 4. Slice-3 scope

Slice 3 contains four product pieces:

```text
A. asset-native relative-momentum scan
B. immutable manual BasketDefinition
C. deterministic pair-opinion -> one-target policy
D. ordinary QAP multi-asset replay + read-only Candidate Workbench
```

### 4.1 Explicit non-goals

Do not build in Scanner V1 Slice 3:

- automatic graph-to-basket discovery;
- basket optimizer;
- mean-variance optimizer;
- Kelly sizing;
- learned edge/reliability weights;
- historical-P&L-weighted edges;
- prospective-pass-rate-weighted edges;
- capacity-weighted edges;
- cross-horizon authority weighting;
- adaptive momentum/reversal sign switching;
- regime classifier/router;
- generic strategy DSL/plugin registry;
- a second scanner backtester;
- cross-venue shared inventory;
- inter-venue transfer simulation;
- historical order-book reconstruction;
- basket-level `tradable_now` or capital capacity;
- browser-side target/accounting recomputation;
- private/live exchange actions.

---

## 5. Frozen Scanner-V1 basket protocol

The permanent runtime protocol is domain-named, not `slice3_*`.

```text
protocol_id: scanner-v1-basket-v1
source_pair_protocol: scanner-v1-s1
venues: BINANCE, GATE
quote / execution bridge: USDT
minimum economic basket size: 3
maximum economic basket size: 6
neutral allocation: equal weight across economic assets
maximum absolute asset tilt from neutral: 0.10
basket construction: manual only
one venue per basket: required
one horizon per basket: required
one decision resolution per basket: required
one selected candidate per unordered pair: maximum 1
pair edge weights: equal
cross-horizon combination: forbidden
cross-venue combination: forbidden
```

Changing any of those values creates a new basket protocol version and new basket research generation.

### 5.1 Horizon and resolution contract

A basket declares one Slice-1 horizon and one of that horizon's admitted model resolutions:

| Horizon | Allowed basket decision resolution |
|---|---|
| short | `15m` or `1h` |
| medium | `1h` or `4h` |
| swing | `4h` or `1d` |

Every selected pair candidate must use that exact resolution.

This avoids asynchronous multi-resolution opinion state, resampling, or a second timing engine in Scanner V1.

### 5.2 Same-venue execution contract

One basket is one venue.

All economic assets must have one admitted direct same-venue `ASSET/USDT` (or exact inverse where the market contract explicitly supports it) execution series at the basket decision resolution.

The execution instrument set contains only the required asset/USDT legs. Do not add alt/alt instruments merely because they exist; the basket policy is intentionally settled through one explicit USDT bridge.

A Binance basket and a Gate basket are separate experiments. QAP does not currently own venue-segregated balances or inter-venue transfers, so it must not pretend one USDT balance can teleport across venues.

---

## 6. Asset-native relative momentum

Contract family: `MOM-*`.

### MOM-01 — O(N), not NxM

Broad momentum is computed independently per admitted asset and then common-mode adjusted. It is not converted into pairwise combinations and does not use the SSD graph.

### MOM-02 — frozen horizon rule

Use exactly one formation duration and one canonical broad-scan resolution per horizon:

| Horizon | Broad momentum resolution | Formation duration |
|---|---:|---:|
| short | `1h` | `2d` |
| medium | `4h` | `10d` |
| swing | `1d` | `28d` |

These are Scanner-V1 engineering hypotheses, not universal crypto laws. No fast/base/slow momentum grid is admitted in Slice 3.

### MOM-03 — PIT universe and data quality

Reuse Slice 1's point-in-time universe policy and exact causal data-slice machinery.

For each eligible asset:

- only completed bars with `bar_end_exclusive <= as_of` are visible;
- no interpolation or forward fill;
- positive finite prices only;
- reuse the Slice-1 minimum asset coverage threshold;
- reuse the Slice-1 maximum missing-run rule over the declared momentum slice;
- preserve source-artifact and exact selected-slice fingerprints separately.

An eligible asset with insufficient/invalid data remains an explicit observation row with invalid status; it does not disappear from the research denominator.

### MOM-04 — score

For each valid asset `i`:

```text
own_momentum_i = log(P_i(t) / P_i(t - L_h))
```

where `L_h` is the frozen formation duration for the horizon.

For the valid admitted assets in that venue/horizon scope:

```text
common_mode = equal_weight_mean(own_momentum_i)
relative_momentum_i = own_momentum_i - common_mode
```

Persist both `own_momentum` and `relative_momentum`.

The common-mode membership and count are part of observation provenance. At least two valid assets are required for a valid relative-momentum scope.

### MOM-05 — ranking

Rank valid assets by:

```text
relative_momentum descending
asset key ascending as deterministic tie-break
```

All valid negative observations remain rankable. Rank is descriptive discovery evidence; it does not automatically select a basket, promote a model, or spend authoritative replay budget.

### MOM-06 — semantic identity

A momentum generation identity binds at least:

```text
basket/momentum protocol identity
venue
horizon
as_of
universe_snapshot_id
formation duration
momentum resolution
exact selected-slice fingerprints for admitted observation rows
```

Whole-source fingerprints remain physical provenance/admission evidence. Appending later source rows must not alter the semantic identity of an already frozen momentum generation when its exact evaluated slices are unchanged.

---

## 7. Manual BasketDefinition

Contract family: `BASK-*`.

### BASK-01 — one source scan generation

A Scanner-V1 `BasketDefinition` binds one completed Slice-1 source scan generation.

All selected pair candidates must come from that same scan, venue, horizon, and basket decision resolution.

This prevents a v1 basket from silently mixing rules selected at incompatible information cutoffs.

An optional asset-momentum generation may be referenced only when it has the same venue, horizon, and `as_of` cutoff.

### BASK-02 — basket assets

A basket contains exactly 3–6 distinct economic assets from the source scan's point-in-time admitted universe.

USDT is the execution-only bridge and valuation coordinate; it is not automatically an economic target asset.

Assets without a selected pair edge are allowed. They remain at neutral allocation unless another selected edge connects them.

### BASK-03 — selected edges

A `BasketEdge` binds exactly one Slice-1 `candidate_id` and therefore one immutable:

```text
unordered pair
candidate orientation
model family
model parameters/template
horizon
resolution
source scan/protocol identity
```

Requirements:

- both pair assets belong to the basket;
- candidate venue/horizon/resolution match the basket;
- candidate scout trial was valid;
- at most one selected candidate per unordered pair;
- at least one edge is selected;
- duplicate semantic edges are rejected.

If both ratio-MR and residual-MR candidates exist for the same pair, the user must explicitly choose one `candidate_id`. QAP must not choose whichever historical/prospective result is best.

### BASK-04 — evidence classes remain visible

A selected candidate may have different levels of supporting evidence. The basket artifact/API projects these facts separately; it does not collapse them into one quality score.

Examples include:

```text
historical direct deep-replay survivor
historical direct deep-replay rejection
prospective partial/matured outcome
manual/pinned lineage
valid scout-only indirect relationship
```

A valid relationship that Slice 1 could not authoritatively pair-replay solely because no direct alt/alt spot instrument existed may be selected for basket research **when every basket asset has its required same-venue asset/USDT execution leg**.

This does not rewrite the Slice-1 result. It means the first authoritative economics for that indirect relationship occur inside the one-inventory basket, where the actual execution consequence is asset→USDT and USDT→asset.

Candidate failures caused by integrity/provenance/data-admission violations are not upgraded into basket evidence merely because a bridge route exists.

### BASK-05 — forensic lineage

If any selected asset/candidate depends on Slice-1 forensic `historical_eligibility_unknown` admission, the whole basket is forensic research and cannot enter official automatic scoreboards or stronger evidence language.

### BASK-06 — semantic identity and family

`basket_id` binds all economically/search-bearing inputs, including:

```text
basket protocol identity
source scan id
optional source momentum generation id
venue
horizon
decision resolution
ordered economic asset set
selected candidate id per edge
neutral allocation rule
maximum asset tilt
execution bridge
cost policy reference
mechanical control reference
pair-blind momentum-control reference
```

Creation timestamp is provenance, not a reason to give an otherwise identical definition a different semantic identity.

All basket definitions created from the same:

```text
basket protocol + source scan + venue + horizon + resolution
```

share one deterministic basket research-family identity. Trying multiple asset/edge combinations is selection pressure and must remain attributable.

---

## 8. Pair-opinion state

Contract family: `EDGE-*`.

### EDGE-01 — canonical sign

Each unordered selected pair has one canonical `(asset_a, asset_b)` ordering stored by `BasketDefinition`.

Define:

```text
p_e = +1  => prefer asset_a over asset_b
p_e =  0  => neutral edge
p_e = -1  => prefer asset_b over asset_a
```

The selected candidate's own orientation/model score is explicitly mapped into that canonical sign. Residual orientations remain distinct fitted candidate rules; the mapping must not refit or invert them heuristically.

### EDGE-02 — reuse Slice-1 entry/neutral semantics

For the candidate's causal z-score at a basket decision boundary:

```text
|z| >= 1.5:
    set p_e to the current candidate preference sign

0.5 < |z| < 1.5:
    retain the previous p_e

|z| <= 0.5:
    set p_e = 0
```

Initial state is `0`.

The middle region is state retention, not neutralization. This preserves Slice-1's `NO_ACTION` hysteresis instead of changing model semantics when several edges are combined.

### EDGE-03 — missing evidence fails closed

If any selected edge cannot produce the required causal observation at a basket decision boundary because evidence is insufficient/invalid:

- emit basket-level `NO_ACTION` for that boundary;
- do not update any edge opinion state;
- preserve the missing/invalid evidence reason in the decision audit.

Scanner V1 does not add stale-signal TTLs or partial-edge authority.

---

## 9. Exact deterministic basket resolver

Contract family: `RES-*`.

The resolver is policy-owned and uses only:

- the frozen economic basket;
- one equal-weight neutral target;
- the frozen selected graph topology;
- current ternary edge opinions;
- the fixed maximum asset tilt.

It does not use returns, Sharpe, P&L rank, prospective pass fraction, liquidity rank, or capacity as edge weights.

### RES-01 — neutral target

For `N` economic assets:

```text
w0_i = 1 / N
```

USDT is not part of this neutral economic target.

### RES-02 — signed incidence pressure

For each selected edge `e=(a,b)`, use a row-incidence convention:

```text
B[e,a] = +1
B[e,b] = -1
```

and edge opinion `p_e ∈ {-1,0,+1}`.

Raw asset pressure is:

```text
v = Bᵀ p
```

Equivalently, each active edge contributes `+1` to its preferred asset and `-1` to its disfavored asset.

### RES-03 — declared-degree normalization

Let:

```text
d_i = number of selected BasketDefinition edges incident on asset i
```

Count the frozen selected graph topology, including edges whose current opinion is `0`.

Then:

```text
r_i = v_i / d_i   when d_i > 0
r_i = 0           when d_i = 0
```

Do **not** divide by only currently active edges. An unrelated edge changing from neutral to active must not mechanically change another edge's authority denominator.

### RES-04 — component neutrality

Find connected components from the frozen selected graph topology.

For each non-isolated component `C`:

```text
c_i = r_i - mean(r_j for j in C)
```

For isolated assets, `c_i = 0`.

Therefore:

```text
sum(c_i for i in C) = 0
```

inside every component.

A relationship component may redistribute its own neutral capital but cannot steal neutral weight from a disconnected component merely because it has more edges.

### RES-05 — one global fixed-scale tilt

Let:

```text
m = max_i |c_i|
```

If `m = 0`, emit the neutral target.

Otherwise:

```text
s_i = c_i / m
w_i = w0_i + 0.10 * s_i
```

Use exact `Decimal` arithmetic at the policy boundary.

Because Scanner V1 restricts the economic basket to 3–6 assets:

```text
min neutral weight = 1/6 ≈ 0.1667
maximum negative tilt = 0.10
```

so long-only weights remain positive without an optimizer or clipping rule.

Component centering ensures the final weights sum to exactly one within QAP's existing `AllocationTarget` arithmetic/tolerance contract.

### RES-06 — pair compatibility

Although Slice 3 admits only 3–6 asset baskets, the resolver's two-asset limiting case must reproduce the Slice-1 maximum pair target:

```text
50/50 -> 60/40 or 40/60
```

This is a useful invariant, not authorization for a second two-asset implementation path.

### RES-07 — cycles

A pure contradictory cycle such as:

```text
A > B
B > C
C > A
```

has zero net incidence pressure and therefore produces no portfolio tilt.

Scanner V1 does not implement Hodge decomposition, cycle scoring, or reliability weighting. A future workbench may display a separately designed inconsistency diagnostic, but it cannot affect v1 weights.

### 9.1 Worked examples

Three assets, consistent chain:

```text
A > B
B > C

v = (+1, 0, -1)
d = (1, 2, 1)
r = (+1, 0, -1)
c = (+1, 0, -1)

neutral = 33.33 / 33.33 / 33.33
final   = 43.33 / 33.33 / 23.33
```

Three assets, pure cycle:

```text
A > B
B > C
C > A

v = (0, 0, 0)
final = 33.33 / 33.33 / 33.33
```

Disconnected four-asset graph:

```text
A > B     C < D

Each pair redistributes only its own component-neutral capital.
No component gains weight merely because the other component is inactive.
```

---

## 10. Asset-native momentum as the pair-blind control

Contract family: `CTRL-*`.

### CTRL-01 — broad discovery and basket control are related but distinct

The broad asset-native momentum table is a scanner research surface over the PIT venue universe.

The authoritative basket comparator is computed only over the frozen 3–6 asset basket using ordinary QAP replay at the basket decision resolution.

### CTRL-02 — basket-relative momentum control

Reuse QAP's existing causal cross-sectional relative-return observation and long-only `CrossSectionalTiltPolicy` semantics where possible.

For the basket/horizon, use the same formation duration as `MOM-02`, converted exactly to the basket decision resolution.

At each valid decision boundary:

- compute trailing own-asset log returns over the declared basket;
- subtract the equal-weight basket common mode;
- transfer at most `0.10` weight from the lowest-scoring asset to the highest-scoring asset;
- use the same neutral equal-weight target;
- no score dispersion -> no action/neutral behavior according to the frozen control contract.

This control is pair-blind. It must not inspect selected pair edges.

### CTRL-03 — no momentum/reversal chooser

Even if recent or future evidence shows reversal among small/illiquid assets, Scanner V1 does not flip the control sign based on the same data being evaluated.

A reversal family would require a new version and a separately stated falsifiable question.

---

## 11. Historical basket replay

Contract family: `EXEC-*`.

### EXEC-01 — development-only historical role

Basket historical replay uses `DataRole.DEVELOPMENT`.

No Slice-3 path may consume reserved final OOS.

### EXEC-02 — common evaluation window

Use the Slice-1 horizon evaluation windows:

```text
short   30d
medium  90d
swing   180d
```

Warm-up begins early enough for the longest selected edge model window and the basket momentum-control formation window.

All strategy/control/HODL roles share the same evaluation boundaries.

### EXEC-03 — equal-value research normalization

At evaluation start, total economic basket value is normalized to `1` quote-value unit.

For `N` economic assets:

```text
starting value per asset = 1 / N
starting asset quantity  = (1 / N) / evaluation_start_price
starting USDT bridge quantity = 0
```

This is scale-free historical research normalization, not a claim about the user's capital.

### EXEC-04 — execution route set

Historical basket replay declares exactly the same-venue asset/USDT execution instruments needed for the economic assets.

It does not execute synthetic alt/alt crosses.

When the graph prefers XRP over NEO, the policy emits one portfolio target. The existing multi-asset executor may realize the resulting inventory change as real XRP/USDT and NEO/USDT legs.

### EXEC-05 — next-boundary execution references

Preserve QAP's default causal timing:

1. observe completed decision-resolution bars;
2. compute all selected edge evidence;
3. update edge opinions;
4. compute one policy target;
5. build one `RebalancePlan`;
6. use the next contiguous opens of the declared asset/USDT execution instruments as deterministic execution references;
7. execute sells to bridge before buys from bridge through `execute_multi_asset_rebalance()`;
8. apply every fill exactly once to one authoritative portfolio ledger;
9. mark the resulting inventory at the same causal boundary.

### EXEC-06 — 0..N fills per decision

Ordinary QAP replay must be generalized from a singular-fill assumption to a tuple of fills per decision.

Financial economics, turnover, fees, slippage, event serialization, reconciliation, and audit projections must iterate the authoritative fill tuple.

A singular `fill` convenience may remain for the direct-execution path only; no economics may depend on it once multi-asset replay is admitted.

### EXEC-07 — historical venue-metadata honesty

Slice 3 must not apply today's Binance/Gate precision/minimum/MARKET-notional metadata to old bars and call it historical venue truth.

Historical basket development replay therefore uses:

```text
recorded historical OHLCV
+ frozen QAP CostModel
+ deterministic bridge routing
+ research normalization
```

without claiming contemporaneous historical order constraints/capacity when those observations were not recorded.

The existing Phase-11 multi-asset/routing functions may be minimally generalized so historical research can omit `MarketMetadata`; when metadata is absent, direct fills use the existing unconstrained research quantization/cost semantics. Phase-11 operational callers that supply metadata remain strict and unchanged.

### EXEC-08 — cost policy

Use the exact source Scanner-V1 ordinary and adverse `CostModel` reference. Do not invent basket-specific fees/slippage to rescue a result.

---

## 12. Benchmark ladder and basket economic gate

Contract family: `EVAL-*`.

Every authoritative basket replay includes at least:

```text
1. strict matched-inventory HODL
2. equal-weight cost-aware band/partial-rebalance control
3. pair-blind relative-momentum control
4. relationship-conditioned graph basket strategy
```

The mechanical band uses the frozen Scanner-V1 `band-5pct-half` semantics around the equal-weight neutral target.

The pair-blind relative-momentum control is the **primary incremental benchmark for any pair-specific intelligence claim**.

A basket may be called a `basket_development_survivor` only when ordinary-cost strategy economics are positive versus all three required comparators:

```text
strategy_vs_hodl > 0
strategy_vs_band_control > 0
strategy_vs_pair_blind_relative_momentum > 0
```

Adverse-cost results remain separately visible robustness evidence; they do not authorize retuning inside the same generation.

A losing basket remains a complete valid research result.

Do not automatically promote a winning basket into prospective or deployment language.

---

## 13. Search pressure and lineage

Contract family: `RSCH-*`.

### RSCH-01 — manual is still search

Manual basket construction is search-bearing.

Trying:

```text
{XRP, NEO, SUI}
{XRP, NEO, SEI}
{XRP, NEO, SUI, SEI}
```

creates three basket siblings. Replacing a ratio candidate with a residual candidate after viewing basket economics creates another sibling.

Every attempted `BasketDefinition` remains attributable even when setup or replay fails.

### RSCH-02 — no hidden auto-selection

QAP does not:

- choose the best basket by historical P&L;
- choose the best edge model by historical P&L;
- choose edge weights from historical/prospective quality;
- choose a momentum/reversal sign from downstream performance.

### RSCH-03 — family-level inference remains conditional

If a later research claim relies on searching many basket siblings and reporting the winner, use the existing research-governance boundary for appropriate family-level selection-pressure treatment.

Scanner V1 does not make PBO/SPA/Reality-Check a per-basket promotion gate.

### RSCH-04 — pair prospective evidence does not transfer

A basket containing several pair-level prospective winners is still a newly combined policy.

Slice 3 does not call that combined policy prospective unless a later approved basket-level freeze-before-outcome protocol evaluates the whole frozen basket rule on genuinely later data.

No speculative `BasketFreeze` implementation is added in Scanner V1 Slice 3.

---

## 14. Basket capacity and actionability boundary

Contract family: `CAP-*`.

### CAP-01 — pair qualification remains pair evidence

Slice-2 candidate qualifications may be displayed beside selected edges.

They are not algebraically combined into one basket capacity.

### CAP-02 — no basket `tradable_now`

The actual basket rebalance produces several state-dependent asset/USDT order sizes competing for one bridge balance.

Therefore none of these are valid Scanner-V1 formulas:

```text
min(pair ceilings)
sum(pair ceilings)
average(pair ceilings)
```

as a basket capital limit.

Basket capacity remains `unknown / not evaluated` until a separate approved design consumes the actual multi-asset `RebalancePlan` and captured directional depth for every required execution leg.

Slice 3 grants no live-capital authority.

---

## 15. Artifact families

Contract family: `ART-*`.

Use the existing neutral exact-file integrity primitive for completed Slice-3 evidence. Do not create another integrity algorithm.

### 15.1 Asset-momentum generation

Suggested durable layout:

```text
runs/asset-momentum/<momentum_scan_id>.partial/
  definition.json
  eligible_assets.parquet
  observations.parquet
  manifest.json
  integrity.json
```

Publish atomically to:

```text
runs/asset-momentum/<momentum_scan_id>/
```

The observation table contains every admitted asset row, including invalid/insufficient rows.

### 15.2 Basket research generation

Suggested durable layout:

```text
runs/baskets/<basket_id>.partial/
  definition.json
  replay_attempt.json
  manifest.json
  integrity.json
```

`replay_attempt.json` is durably enumerated before ordinary QAP experiment preparation and transitions within the unpublished generation through the finite states:

```text
enumerated
setup_failed
replay_failed
completed
```

A completed attempt references the authoritative QAP `run_id`; it does not copy QAP economics into a second source of truth.

Interrupted `.partial` state may support deterministic recovery. A completed basket artifact is immutable.

### ART-01 — no pair-P&L portfolio artifact

No artifact sums candidate pair wealth/P&L into a basket result. Only the one-inventory QAP run is authoritative basket economics.

---

## 16. Read-only API and Candidate Workbench

Contract family: `UI-*`.

Slice 3 may add the first scanner browser surface only after backend artifact contracts are proven.

### UI-01 — API remains presentation authority only

The API may project:

- active Scanner-V1 pair/basket protocol values;
- completed Slice-1 scan/candidate summaries;
- matching Slice-2 prospective/qualification evidence;
- completed asset-momentum generations;
- completed basket definitions/attempts;
- per-decision edge opinions and resolver audit from the authoritative QAP run;
- links to existing experiment/portfolio/pair evidence routes.

It must not reconstruct financial truth from browser inputs.

### UI-02 — Candidate Workbench

The first workbench should support bounded inspection:

```text
select venue / horizon / completed scan
inspect asset-native momentum table
inspect 3–6 assets
inspect available pair candidates and evidence classes
inspect persisted BasketDefinitions
inspect edge-opinion -> node-pressure -> target audit
open the authoritative QAP portfolio result
```

The browser does not need to persist/run baskets in Scanner V1. Basket creation/execution remains an explicit local operator command.

A future browser mutation path requires a separate explicit trust-boundary decision; do not smuggle POST execution into the read-only workbench.

### UI-03 — frontend never recomputes resolver math

React receives backend-projected:

```text
edge opinion
raw incidence pressure
declared degree
degree-normalized pressure
component-centered pressure
final target weight
```

and explains them. It does not recalculate weights independently.

### UI-04 — reuse existing Portfolio UI

Combined financial truth already belongs on the existing Portfolio page:

- wealth vs HODL;
- benchmark ladder;
- allocation history;
- inventory attribution;
- costs/turnover;
- drawdown;
- rebalance/fill audit.

Candidate Workbench links there instead of rebuilding those views.

---

## 17. Operator surface

Keep the local mutation surface narrow.

Conceptually:

```text
python -m qap.scanner.basket_cli momentum ...
python -m qap.scanner.basket_cli create ...
python -m qap.scanner.basket_cli run ...
python -m qap.scanner.basket_cli show ...
```

Exact CLI spelling is implementation detail, but the responsibilities are fixed:

- `momentum`: create one asset-native generation;
- `create`: persist one immutable manual basket definition/attempt lineage;
- `run`: route that definition through ordinary QAP development replay;
- `show`: inspect completed definition/attempt/evidence references.

No scheduler is introduced.

---

## 18. Module design

Runtime modules use domain names rather than delivery labels such as `slice3_*`.

### 18.1 Scanner modules

```text
qap.scanner.basket_protocol
    typed Scanner-V1 basket/momentum protocol constants and identity

qap.scanner.asset_momentum
    PIT asset-native momentum observations/ranking only

qap.scanner.asset_momentum_artifacts
    immutable momentum generation persistence/readback

qap.scanner.basket
    BasketDefinition / BasketEdge identity and validation

qap.scanner.basket_artifacts
    basket definition + replay-attempt persistence/readback

qap.scanner.basket_cli
    thin local operator CLI; may route outward through qap.scanner_entry
```

`qap.scanner` continues to forbid imports from:

```text
qap.policy
qap.execution
qap.evaluation
qap.experiment
```

### 18.2 Policy module

```text
qap.policy.graph_basket
```

Owns the pure `RES-*` graph-to-`AllocationTarget` calculation.

It accepts generic pair orientations/opinions and an `AllocationTarget`; it imports no scanner types.

### 18.3 Experiment modules

```text
qap.experiment.basket_policy
    causal selected-edge model evaluation + ternary hysteresis state;
    delegates target construction to qap.policy.graph_basket

qap.experiment.relative_momentum_control
    narrow reusable pair-blind control composition if extraction from the
    current large model_policies module is needed for a second real use

qap.experiment.basket_scanner_adapter
    intentional outer adapter from BasketDefinition/scanner artifacts to
    ordinary QAP manifests/replay/artifacts
```

Only the dedicated basket scanner adapter may import `qap.scanner` from `qap.experiment`; update Import Linter narrowly for that edge.

### 18.4 Existing financial modules to generalize, not replace

```text
qap.experiment.manifest
    explicit direct vs multi-asset-bridge execution configuration;
    economic basket remains distinct from execution-only USDT bridge

qap.execution.replay
    one causal replay loop with 0..N fills per decision

qap.execution.multi_asset
qap.execution.routing
    existing Phase-11 authority; minimally admit metadata-free historical
    research while preserving strict metadata behavior for operational callers

qap.experiment.runner
qap.experiment.economics
qap.experiment.events
    ordinary role execution/economics/event output generalized over fill tuples
```

Do not create `scanner_backtest.py`, `basket_wallet.py`, or another portfolio ledger.

### 18.5 API/web modules

Prefer one focused read-only scanner artifact reader/projection family rather than teaching the existing experiment reader to parse unrelated scanner layouts.

Expected surface:

```text
qap.api scanner/basket DTOs + read-only routes
web/src/features/scanner/*
web/src/routes/scanner*
```

Use generated OpenAPI/TypeScript contracts and existing chart/UI primitives.

---

## 19. Architecture invariants

Contract family: `ARCH-*`.

### ARCH-01 — package direction

Preserve the existing financial-core dependency direction. Scanner does not become a policy/execution/evaluation owner.

### ARCH-02 — only outer adapters cross scanner -> experiment authority

Intentional edges are limited to outer composition/adapters such as:

```text
qap.experiment.scanner_adapter
qap.experiment.prospective_scanner_adapter
qap.experiment.basket_scanner_adapter
```

No financial inner package imports scanner.

### ARCH-03 — one ledger

Every basket role owns one `PortfolioLedger`/`PortfolioState` path. Multi-asset fills are applied exactly once. Bridge residue remains owned inventory and is valued, never discarded.

### ARCH-04 — source-size discipline

Current files near the repository review threshold must not become dumping grounds. In particular, avoid growing the existing large `model_policies.py` or `prospective_run.py` with Slice-3 responsibilities when a second real owner/use justifies a focused module.

---

## 20. Required behavioral evidence for implementation

The implementation plan may refine file placement but must prove these contracts.

### Momentum

- future source append does not mutate an older momentum semantic identity;
- one invalid asset remains visible instead of disappearing;
- no pairwise/NxM enumeration occurs;
- deterministic ranks/ties;
- no automatic basket selection.

### Basket identity/admission

- reject fewer than 3 or more than 6 economic assets;
- reject mixed venue/horizon/resolution/source scan;
- reject duplicate candidate for one unordered pair;
- reject selected edge whose assets are outside the basket;
- allow a valid scout-only indirect alt/alt candidate when all required same-venue asset/USDT execution legs exist;
- reject integrity/data-admission failure disguised as an indirect candidate;
- forensic lineage makes the whole basket forensic.

### Resolver

- two-asset limiting invariant gives 60/40 or 40/60;
- consistent three-asset chain produces the hand-calculated target;
- pure cycle produces neutral target;
- disconnected components preserve component-neutral capital;
- graph hub degree does not gain extra authority merely from more incident edges;
- all 3–6 asset outputs are long-only and sum to one;
- missing edge evidence causes basket-level no-action and preserves edge state;
- middle-band evidence preserves previous edge opinion.

### Replay/economics

- a four-asset historical basket produces multiple fills in one replay decision through the existing Phase-11 executor;
- every fill contributes once to fees/slippage/turnover/events;
- one ledger ending state reconciles to the multi-asset result;
- execution-only USDT bridge need not be an economic target and any residue remains owned/valued;
- historical basket replay does not require or fabricate current venue metadata;
- operational Phase-11 callers that do supply metadata retain their strict precision/notional behavior;
- HODL, band, momentum-control, and relationship strategy share identical starting inventory, timing, prices, cost model, and evaluation window.

### Research claims

- pair prospective evidence is visible but cannot mark the basket prospective;
- all basket siblings remain attributable;
- no basket capacity/tradable-now label is produced.

### API/workbench

- browser receives resolver audit fields from backend rather than recomputing them;
- combined economics link to the existing QAP portfolio result;
- no scanner browser mutation/live execution path exists.

---

## 21. Slice-3 completion criteria

Slice 3 succeeds when QAP can reproducibly:

1. create one PIT asset-native momentum table per venue/horizon using O(N) work and one frozen formation rule;
2. persist a manual same-venue 3–6 asset `BasketDefinition` with complete candidate/search lineage;
3. evaluate one causal ternary opinion per selected unordered pair at one common decision resolution;
4. resolve simultaneous opinions through the exact `RES-*` rule into one long-only target;
5. replay that target through the existing Phase-11 multi-asset execution authority and one QAP inventory;
6. compare the resulting strategy against matched HODL, the frozen mechanical band control, and the pair-blind relative-momentum control under identical costs/timing;
7. retain negative/failed basket generations as valid search evidence;
8. expose completed scanner/basket evidence through a read-only Candidate Workbench without recomputing financial truth in React;
9. preserve historical execution/capacity honesty and never derive basket `tradable_now` from pair ceilings;
10. leave reserved final OOS and live-capital authority untouched.

A profitable basket is not required for Slice-3 implementation success.

---

## 22. Research references

Primary papers used to inform the bounded design:

1. Yukun Liu and Aleh Tsyvinski, **“Risks and Returns of Cryptocurrency,”** NBER Working Paper 24877 (2018), later *Review of Financial Studies* 34(6), 2021. DOI: `10.3386/w24877`.
2. Yukun Liu, Aleh Tsyvinski, and Xi Wu, **“Common Risk Factors in Cryptocurrency,”** NBER Working Paper 25882 (2019), later *Journal of Finance* 77(2), 2022. DOI: `10.3386/w25882`.
3. Chulwoo Han, Byeongguk Kang, and Jehyeon Ryu, **“Momentum in the Cryptocurrency Market: A Comprehensive Analysis under Realistic Assumptions,”** SSRN 4675565, revised 2026-03-26. DOI: `10.2139/ssrn.4675565`.
4. Milan Fičura and Gonul Colak, **“Impact of Size and Volume on Cryptocurrency Momentum and Reversal,”** SSRN 4378429, revised 2024-04-03. DOI: `10.2139/ssrn.4378429`.
5. Victoria Dobrynskaya, **“Cryptocurrency Momentum and Reversal,”** *Journal of Alternative Investments* 26(1), 2023. DOI: `10.3905/jai.2023.1.189`; SSRN 3913263.
6. Zezhou Xu and Fenglin Wu, **“Size-Momentum Puzzle in Cryptocurrencies,”** SSRN 6628860, posted 2026-04-22. DOI: `10.2139/ssrn.6628860`.
7. Xiaoye Jiang, Lek-Heng Lim, Yuan Yao, and Yinyu Ye, **“Statistical Ranking and Combinatorial Hodge Theory,”** arXiv:0811.1067.
8. Fredi Šarić, Stjepan Begušić, Andro Merćep, and Zvonko Kostanjčar, **“Statistical Arbitrage Portfolio Construction Based on Preference Relations,”** arXiv:2310.08284.
9. Victor DeMiguel, Lorenzo Garlappi, and Raman Uppal, **“Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?”** *Review of Financial Studies* 22(5), 2009; SSRN 1376199.
10. David H. Bailey, Jonathan Borwein, Marcos López de Prado, and Qiji Jim Zhu, **“The Probability of Backtest Overfitting,”** *Journal of Computational Finance*; SSRN 2326253. DOI: `10.21314/JCF.2016.322`.

The research references motivate falsifiable hypotheses and restraint. QAP's normative authority remains this repository's frozen protocol, causal replay, economic controls, and prospective/holdout discipline.
