# QAP Scanner Slice 1 Design — Bounded Pair Discovery Foundation

**Date:** 2026-08-18

**Status:** Design frozen for written-spec review. Implementation is not yet authorized; the next step after review is a separate implementation plan.

**Scope:** First implementation slice of the QAP adaptive research scanner. This slice creates bounded, reproducible pair hypotheses and replays only a fixed number through the existing authoritative QAP economic kernel.

## 1. Goal

Build the smallest scanner foundation that can answer:

> As of timestamp `t`, using only point-in-time-admissible Binance/Gate market evidence, which recent pair-relative mean-reversion hypotheses are worth spending authoritative QAP replay budget on?

The slice must make broad discovery possible without turning QAP into a Cartesian `pair x model x parameter x timeframe` optimizer.

It must preserve the existing economic constitution:

- spot-only, long-only owned inventory;
- portfolio/inventory remains the economic owner;
- matched HODL and the strongest predeclared simple admissible rebalance/control remain the economic benchmarks;
- scanner results are hypotheses, not financial truth;
- only existing QAP policy/execution/accounting/evaluation may determine economic success;
- no historical point-in-time discovery claim may be made from today's survivor list;
- no automatic final-OOS consumption.

## 2. Scope decomposition

The overall scanner effort is intentionally split into three implementation slices.

```text
Slice 1 — bounded pair discovery foundation
  PIT universe
  SSD candidate graph
  fixed pair-native scouts
  hard deep-replay budget
  search ledger
  candidate -> existing QAP replay adapter

Slice 2 — prospective evidence and liquidity
  forward cohorts / scanner-policy evidence
  lightweight L1 + shallow-depth capture
  research_only / small_capacity / tradable_now

Slice 3 — manual basket research workbench
  3–6 asset user-selected baskets
  asset-native relative momentum
  one ternary opinion per pair/horizon
  simple component-neutral resolver
  scanner API/workbench projections
```

Slice 1 must leave clean interfaces for Slices 2 and 3, but it must not implement their machinery early.

## 3. Architectural boundary

Add one package, `qap.scanner`, for discovery semantics only.

```text
market data / lifecycle evidence
          |
          v
      qap.market
          |
          v
     qap.scanner
  universe / SSD graph
  scout / ranking / ledger
          |
          v
 immutable scanner candidate
          |
          v
    qap.experiment
  candidate replay adapter
          |
          v
existing relationship -> policy -> execution -> inventory -> evaluation
```

The import direction becomes:

```text
qap.api
qap.experiment
qap.evaluation
qap.execution
qap.policy
qap.scanner
qap.relationship
qap.market
qap.portfolio
```

`qap.scanner` may consume `qap.relationship`, `qap.market`, and stable portfolio identity/value types below it. It may not import `qap.policy`, `qap.execution`, `qap.evaluation`, or `qap.experiment`.

The candidate-to-economic-replay adapter belongs in `qap.experiment`, not in `qap.scanner`. This prevents the scanner from becoming a second backtester.

### Scanner must never own

- portfolio cash/inventory balances;
- fill generation;
- fee/slippage truth;
- matched-HODL construction;
- simple-control economics;
- terminal wealth or official relative-wealth claims;
- final-OOS authority.

The scout may calculate an explicitly approximate ranking proxy. That value must be named and typed as a proxy and must never be exposed as authoritative QAP performance.

## 4. Storage and execution model

Keep the existing file-oriented architecture. Do not add a database, queue, worker platform, scheduler service, or plugin registry.

Canonical admitted market observations remain Parquet with source fingerprints. Scanner outputs are compact JSON manifests plus Parquet tables.

One scan generation writes:

```text
runs/scans/<scan_id>/
  manifest.json
  eligible_assets.parquet
  neighbors.parquet
  scout_trials.parquet
  promotions.parquet
```

Authoritative deep replays remain normal QAP experiment/run artifacts and are referenced by run ID from `promotions.parquet`; their economics are not copied into scanner-owned accounting tables.

Write a generation atomically: temporary files first, then publish the complete manifest last. A scan with no complete manifest is incomplete evidence.

The scan command consumes only admitted local snapshots. It must not call an exchange during candidate computation. Exchange/network ingestion is a separate market-data operation so the same scan can be reproduced later.

## 5. Scanner protocol v1-s1

Every canonical scan is governed by a frozen protocol object. Meaningful rule changes create a new protocol version rather than silently rewriting historical evidence.

```text
protocol_id: scanner-v1-s1
normal_history: 365d
maximum_normal_history: 730d
venues: BINANCE, GATE
quote: USDT
candidate_generator: normalized-log-price-ssd-v1
neighbors_per_asset: 8
automatic_deep_replay_cap_per_horizon: 10
max_automatic_promotions_per_asset_per_horizon: 2
```

The last two values are engineering research-budget limits, not empirically optimized alpha parameters.

### 5.1 Horizons

The product supports three distinct research horizons. Slice 1 keeps them separate.

| Horizon | Meaning | Candidate-graph bars | Candidate-graph window | Allowed model resolutions |
|---|---|---|---:|---|
| `short` | hours–2 days | `1h` | trailing 30 days | `15m`, `1h` |
| `medium` | 2–10 days | `4h` | trailing 90 days | `1h`, `4h` |
| `swing` | 1–4 weeks | `1d` | trailing 180 days | `4h`, `1d` |

These are frozen engineering defaults. Do not search alternative graph windows or horizon-resolution mappings inside the same research generation.

### 5.2 Recency

Normal discovery uses at most the most recent 365 days available through `eligible_information_end`. A model may consume less history.

A deliberately requested extended discovery run may use at most 730 days and must be labeled as such. Older history remains stress/regime material and is outside canonical scanner selection.

## 6. Point-in-time universe contract

Historical universe admission is three-valued:

```text
known_eligible
known_ineligible
historical_eligibility_unknown
```

Only `known_eligible` instruments enter an official point-in-time scan.

`historical_eligibility_unknown` remains queryable for forensic/manual research but may not silently enter the official candidate graph.

### 6.1 Minimal lifecycle evidence

Extend `qap.market` with event-oriented lifecycle evidence rather than one mutable `listed` boolean.

Conceptual record:

```text
InstrumentLifecycleEvent
  canonical_asset_id
  asset_identity_version
  venue
  venue_symbol
  quote_asset
  event_type
  effective_at
  observed_at
  source_type
  source_id
  confidence
```

Required event types for Slice 1:

```text
listing_or_trading_started
trading_suspended
trading_resumed
delisting_announced
delisted
symbol_renamed
contract_or_token_migrated
```

Do not join price histories across a rename/migration unless official evidence establishes continuity and QAP records the identity mapping explicitly.

### 6.2 Source priority

Use this evidence order when sources conflict:

1. QAP's own timestamped append-only venue snapshot.
2. Official exchange lifecycle/listing/delisting/suspension announcement with effective time.
3. Official exchange lifecycle metadata field referring to the historical event.
4. Official exchange-native historical trade/bar evidence as positive evidence that trading occurred near that timestamp.
5. Current survivor/current-status metadata only for current state.
6. Third-party metadata only as corroboration; never sufficient by itself for official historical eligibility.

Absence of a bar/file does not prove that a market did not exist. Presence of one historical trade does not prove uninterrupted eligibility for an entire formation window.

### 6.3 Venue-local universe

Build two independent USDT spot universes:

```text
BINANCE:<base>/USDT
GATE:<base>/USDT
```

Do not splice Gate and Binance observations into one synthetic execution history. Do not perform cross-exchange arbitrage research in Slice 1.

The quote asset `USDT` is a coordinate/venue quote and is not itself inserted as a candidate base asset. Other base assets enter only when the operator/project admission metadata marks them scanner-eligible; QAP does not invent an automatic Shariah/stablecoin taxonomy from ticker text.

## 7. Candidate graph: one frozen SSD generator

Slice 1 uses exactly one automatic pair-neighborhood generator: normalized log-price path squared distance. It is chosen for transparency and auditability, not because QAP claims it is the optimal 2026 crypto pair selector.

For asset `i` with completed close prices on the generator grid:

```text
x_i(t) = log(P_i(t)) - log(P_i(t0))

d(i,j) = mean_t((x_i(t) - x_j(t))^2)
```

Smaller `d(i,j)` means more similar recent normalized paths.

The SSD score is search-bearing selection input. It is not evidence that the pair is cointegrated and must never be labeled as such.

### 7.1 Data-quality semantics

For each asset/horizon graph:

- use only fully completed bars known by `as_of`;
- reindex to the expected timestamp grid;
- no forward fill;
- no interpolation;
- prices must be positive and finite;
- asset coverage must be at least 95%;
- pair common-bar coverage must be at least 95%;
- longest missing run may not exceed two generator bars;
- invalid/insufficient distances are excluded rather than assigned artificial values.

The 95% and two-bar limits are conservative data-policy constants. They may be changed only by versioning the universe/generator policy, not by choosing whichever values improve historical P&L.

### 7.2 Neighbor selection

For each eligible asset:

1. rank every other eligible asset on the same venue by `(distance, canonical_pair_id)`;
2. keep the nearest `k=8`;
3. take the union of all directed selections;
4. canonicalize to one unordered `PairId`;
5. deduplicate.

A pair survives when either asset selected the other as a nearest neighbor.

The implementation may compute a quadratic distance matrix because this is one cheap vector operation per pair, not an economic replay. The expensive model layer remains bounded approximately by `N * k` retained edges rather than all `N(N-1)/2` edges.

The full distance matrix does not need to become millions of persistent ledger rows. Persist:

- eligible asset count;
- total valid pair comparisons;
- data fingerprint;
- generator version/configuration;
- `distance_digest`: SHA-256 over canonically sorted `(pair_id, float.hex(distance))` records for every valid comparison;
- retained neighbor edges and ranks.

## 8. Manual pins

Manual intuition is allowed without pretending it was automatic discovery.

A scan request may contain explicit pinned same-venue pairs. A pinned pair:

- bypasses only the SSD `k=8` neighbor cutoff;
- must still satisfy instrument identity, point-in-time eligibility, and required data-quality rules for an official scan;
- is marked `selection_source=manual_pin`;
- remains part of the search ledger;
- does not change the automatic nearest-neighbor algorithm.

Manual forced research that intentionally accepts `historical_eligibility_unknown` must run in a separate forensic mode and cannot contribute to official point-in-time discovery scoreboards.

Manual deep-replay investigations are separate from the canonical automatic `10/horizon` budget so they cannot silently alter the automatic policy's forward record.

## 9. Slice-1 model menu

Slice 1 implements only the pair-native mean-reversion vertical slice:

```text
A. residual mean reversion
B. log-ratio mean reversion
```

Asset-native relative momentum remains part of the overall Scanner V1 intent, but is deferred to Slice 3 because forcing an asset-native mechanism into the pair-candidate topology would create a second discovery topology before the pair scanner is proven. Existing momentum research remains evidence/reference, not scanner machinery.

Copulas, learned routing, regime classifiers, automatic strategy-family expansion, and nonlinear family search are not Slice-1 features.

### 9.1 Ratio mean reversion

Use the existing log-ratio evidence semantics:

```text
r_t = log(P_base(t) / P_quote(t))
z_t = (r_t - rolling_mean(r)) / rolling_std(r)
```

The economic preference is mean-reverting:

```text
z_t > 0  -> base relatively expensive -> prefer quote
z_t < 0  -> base relatively cheap     -> prefer base
```

Therefore the preference signal passed into the existing evidence-tilt policy is `-z_t`, not the raw deviation sign.

### 9.2 Residual mean reversion

Fit, on completed common bars inside the declared rolling window:

```text
log(P_base) = alpha + beta * log(P_quote) + residual
```

The scout uses deterministic ordinary least squares and standardizes the latest residual over the same rolling fit window.

```text
z_residual > 0 -> base expensive relative to fitted relation -> prefer quote
z_residual < 0 -> base cheap relative to fitted relation     -> prefer base
```

The preference signal is `-z_residual`.

The family name is deliberately `residual_mean_reversion`, not `cointegration_alpha`. Formal cointegration/ADF statistics may be added later as recorded diagnostics; they are not required to route or admit this Slice-1 model and must not be smuggled in as a hidden selector.

### 9.3 Fixed template set

Both pair-native families use the same three rolling-window templates per horizon. Thresholds do not vary across templates.

| Horizon | `fast` | `base` | `slow` | neutral band | entry band |
|---|---:|---:|---:|---:|---:|
| short | 2 days | 7 days | 14 days | `|z| <= 0.5` | `|z| >= 1.5` |
| medium | 14 days | 30 days | 60 days | `|z| <= 0.5` | `|z| >= 1.5` |
| swing | 30 days | 90 days | 180 days | `|z| <= 0.5` | `|z| >= 1.5` |

Durations convert deterministically to bars for each allowed resolution. Minimum observations are 95% of the expected window and the existing no-interpolation rule remains in force.

`fast/base/slow`, `0.5`, and `1.5` are engineering defaults chosen to create a small coarse neighborhood. They are not claimed optimal and must not be tuned against the same historical scanner results. Changing them creates a new template/protocol version requiring new prospective evidence.

Deep replay uses the existing two-asset neutral target and bounded policy shape:

```text
neutral target: 50% / 50%
maximum pair tilt: 10 percentage points
```

so an active preference can request at most `60/40` or `40/60`. This reuses the existing QAP bounded-tilt semantics instead of adding a new sizing model.

## 10. Cheap scout: approximate ranking, not a second backtester

The scout may use NumPy/Polars/DuckDB-style vectorized computation, but it must not reproduce QAP fills/accounting.

For each retained pair x allowed resolution x family x template:

1. compute the causal completed-bar model signal;
2. convert it to the same fixed `50/50`, `60/40`, `40/60` target states used by deep replay;
3. shift decisions so a signal cannot earn the return of the bar that produced it;
4. calculate an approximate float-based two-asset target-weight wealth path;
5. subtract a simple one-way turnover friction proxy supplied by the orchestration layer from the declared QAP cost policy;
6. compare the proxy path to the same starting `50/50` passive ownership path.

The output metric is named:

```text
scout_relative_wealth_proxy
```

It must not be named `QAP return`, `alpha`, `economic success`, or `OOS`.

The scanner owns no fill model, precision rules, bridge routing, minimum notional handling, or official HODL/control calculation. Those remain deep-replay responsibilities.

### 10.1 Deterministic scout failure rules

A trial is not rankable when any of these holds:

- model window has insufficient valid common observations;
- fitted values/signals are non-finite;
- no active signal occurs in the evaluated formation window;
- target path cannot be constructed causally;
- the proxy wealth path is invalid/non-finite.

A valid but negative proxy remains recorded. It simply cannot consume automatic deep-replay budget while positive candidates exist.

Do not create an additional adaptive diagnostic router or statistical significance gate in the scout.

## 11. Promotion policy

For each horizon, rank automatic valid trials by:

1. `scout_relative_wealth_proxy` descending;
2. lower approximate turnover;
3. canonical venue/pair/model/resolution/template identifier.

Apply these deterministic budgets:

```text
max automatic authoritative replays per horizon = 10
max automatic promoted trials involving one asset per horizon = 2
```

Only trials with positive `scout_relative_wealth_proxy` are automatically promoted. If fewer than ten qualify, promote fewer; do not fill the budget with negative trials.

The per-asset cap is a diversity/compute rule intended to prevent one hub asset from consuming the entire deep-replay budget. It is not an alpha parameter and must be versioned if changed.

No separate 90-candidate robustness tournament, Bayesian optimizer, Hyperband controller, or learned racing policy is implemented in Slice 1.

## 12. Authoritative QAP replay adapter

`qap.experiment` converts a promoted `ScannerCandidate` into an ordinary development-role QAP experiment specification.

The candidate must contain enough immutable information to reconstruct the replay:

```text
candidate_id
scan_id
scanner_protocol_version
selection_source
as_of
eligible_information_end
venue
pair_id
orientation
horizon
resolution
model_family
template_id
model_parameters
source_data_fingerprints
universe_snapshot_id
candidate_generator_version
candidate_generator_rank
scout_relative_wealth_proxy
scout_turnover_proxy
```

The adapter then supplies the existing QAP machinery with:

- the pair's admitted market observations and exact fingerprints;
- the declared relationship model semantics;
- the fixed neutral/entry thresholds;
- `50/50` neutral target and `0.10` maximum tilt;
- the declared authoritative `CostModel`;
- the existing execution/fill/precision contract;
- matched HODL;
- the strongest applicable predeclared simple admissible rebalance/control.

The authoritative deep replay must use the same information cutoff as the scanner candidate. It may not extend into a sealed final-OOS region merely because that data exists locally.

### 12.1 Economic gates

A promoted historical candidate becomes a `deep_replay_survivor` only when authoritative QAP replay shows, after declared costs:

```text
terminal QAP wealth > matched HODL wealth
AND
terminal QAP wealth > strongest simple admissible control wealth
```

This remains development/formation evidence. Slice 1 must not call it confirmed alpha.

The later Slice-2 freeze/forward registry is what turns surviving hypotheses into genuinely prospective evidence.

## 13. Search ledger and denominator

The search ledger preserves the procedure that produced a candidate; it is not itself a multiple-testing correction.

`manifest.json` records generation-level provenance:

```text
scan_id
scanner_protocol_version
as_of
eligible_information_end
created_at
data_snapshot_ids
universe_policy_version
candidate_generator_version
template_set_version
promotion_policy_version
cost_policy_reference
venues
horizons requested
manual pins / forensic flags
```

`eligible_assets.parquet` records at least:

```text
scan_id
venue
horizon
asset_id
venue_symbol
eligibility_state
eligibility_reason
lifecycle_evidence_refs
data_fingerprint
bar_coverage
longest_missing_run
```

`neighbors.parquet` records at least:

```text
scan_id
venue
horizon
pair_id
asset_a
asset_b
ssd_distance
rank_from_a
rank_from_b
selected_by_a
selected_by_b
selection_source
```

`scout_trials.parquet` records every enumerated fixed trial, including losers:

```text
candidate_id
scan_id
venue
horizon
pair_id
resolution
model_family
template_id
trial_status
failure_reason
scout_relative_wealth_proxy
scout_turnover_proxy
signal_count
selection_source
```

`promotions.parquet` records:

```text
candidate_id
promotion_rank
promotion_status
budget_reason
deep_replay_run_id
deep_replay_status
```

The automatic search denominator for one generation is reconstructible from the eligible universe, deterministic SSD generator, fixed model/template enumeration, and full scout-trial table. Manual pins/forced investigations remain visibly separate.

## 14. Statistical semantics

Slice 1 follows a deliberately simple rule:

```text
same historical data used for screening + ranking + replay
    -> development/search evidence

future observations unavailable at freeze time
    -> potential confirmatory evidence
```

SSD distance, residual statistics, ratio z-scores, template choice, and scout ranking are all search-bearing when computed from the same formation history.

Predeclaring them improves reproducibility but does not make them statistically independent.

Do not use SPA, White Reality Check, Romano-Wolf, DSR, or PBO as per-row promotion gates in Slice 1. Those are optional later research-review tools over frozen comparable return series. Causal prospective performance remains the primary confirmation mechanism.

## 15. Dependencies and performance

The architecture permits DuckDB and Polars for research scanning as already anticipated by QAP's OSS integration review, but the implementation must not build wrappers/frameworks around them.

Use the smallest stack that benchmarks adequately:

- PyArrow/Parquet remains canonical storage;
- NumPy handles dense numerical kernels where sufficient;
- Polars may handle vectorized reshaping/features;
- DuckDB may handle Parquet window/universe pruning.

Do not add distributed compute.

The required complexity shape is:

```text
SSD candidate generation: O(H * N^2 * T) cheap vector comparisons
pair model trials after k=8 graph: approximately O(H * N * k * F * R * P)
authoritative automatic deep replay: O(30) max per canonical all-horizon scan
```

where `H=3`, `k=8`, `F=2` pair-native families, `R=2` allowed resolutions/horizon, and `P=3` templates.

The important invariant is that expensive deep replay does not grow with the universe size.

Benchmark realistic 500- and 1,000-asset synthetic/admitted universes during implementation. Optimize only measured bottlenecks; do not pre-build a compute platform.

## 16. Failure handling

Fail closed on research-integrity boundaries, but do not let one bad asset destroy an otherwise valid generation.

### Exclude and record, continue scan

- one asset has insufficient coverage;
- one pair has insufficient common observations;
- one model trial has an invalid fit/no signal;
- one promoted candidate fails authoritative QAP replay for candidate-specific reasons.

### Abort the whole generation

- admitted source fingerprint changes during the run;
- `as_of`/information cutoff is inconsistent;
- universe snapshot cannot be reproduced;
- scanner protocol/config is malformed;
- deterministic candidate IDs collide;
- published artifact counts/hashes do not reconcile.

Unknown historical eligibility is not an exception: it is an explicit state that is excluded from official scanning.

## 17. Testing strategy

### Unit/property tests

- normalized log-path SSD symmetry;
- scale invariance from initial-price normalization;
- deterministic tie handling;
- `k=8` union/deduplication;
- no cross-venue edges;
- no use of incomplete/future bars;
- coverage/gap fail-closed rules;
- three-state eligibility resolution;
- manual pin attribution;
- ratio-MR sign inversion;
- residual-MR sign inversion;
- template-duration-to-bars mapping;
- candidate ID/protocol hash determinism;
- ranking and per-asset promotion caps.

### Scenario tests

A small synthetic market must prove end to end:

```text
PIT universe
 -> expected SSD graph
 -> fixed trial enumeration
 -> deterministic scout ranking
 -> <=10 promotions/horizon
 -> normal QAP deep replay
 -> HODL/simple-control economic gates
```

A negative scenario must prove that an attractive scout candidate can fail authoritative QAP replay without the scanner rewriting or hiding the negative result.

### Research-integrity tests

- today's current exchange metadata cannot backfill historical eligibility;
- `historical_eligibility_unknown` cannot enter an official scan;
- changing `k`, graph windows, thresholds, or promotion caps changes the protocol/version identity;
- final-OOS data is not consumed by scanner deep replay;
- manual pins cannot be mislabeled as automatic discovery;
- scanner package cannot import policy/execution/evaluation/experiment layers.

### Reproducibility

Two runs with identical admitted data fingerprints, protocol version, as-of timestamp, and manual inputs must produce byte/logically equivalent candidate sets and rankings, apart from explicitly non-semantic creation timestamps.

## 18. Slice-1 user/operator surface

No scanner web UI is built in this slice.

Expose one deterministic argparse entry point matching the repository's existing module-CLI style:

```text
python -m qap.scanner.cli \
  --as-of <ISO-8601-UTC> \
  --horizon <short|medium|swing|all> \
  --data-root <path> \
  --run-root <path> \
  [--pins-file <json-path>]
```

`--pins-file` contains only explicit same-venue pair pins and optional forensic-mode flags; it does not override the frozen automatic protocol. Reuse `argparse`; do not add a CLI framework merely for scanning.

The output should report:

- admitted/excluded asset counts by venue/horizon;
- retained SSD edge counts;
- enumerated/valid scout-trial counts;
- automatic promotions and budget exclusions;
- deep replay survivors/failures;
- artifact path/scan ID.

## 19. Explicit non-goals

Do not build in Slice 1:

- predictive diagnostic routing;
- multiple pair generators or selector competition;
- parameter optimization/Bayesian optimization;
- Copulas/tail-family broad scanning;
- asset-native momentum broad scanning;
- automatic 3–6 asset basket discovery;
- learned pair/edge quality weights;
- portfolio optimizer;
- multi-horizon portfolio aggregation;
- prospective forward-result registry/scoreboards;
- automated L1/depth capture or capacity graduation;
- full historical L2 reconstruction;
- live trading;
- scanner scheduler/platform;
- scanner mutation UI;
- statistical-governance service.

## 20. Future interfaces intentionally preserved

Slice 1 artifacts must be sufficient for later work without designing that work prematurely.

Slice 2 can attach to a surviving candidate:

```text
freeze_id
forward_cohort_id
liquidity_state
capacity_estimate
prospective outcome
```

Slice 3 can consume admitted pair candidates and add:

```text
manual basket of 3–6 assets
asset-native momentum evidence
one active opinion per pair/horizon
ternary {-1,0,+1} preference
fixed equal edge weight
degree-normalized/component-neutral allocation resolver
one final long-only QAP target
```

No Slice-1 data model should require future routing, optimizer, Copula, or graph-clustering fields.

## 21. Acceptance boundary

Slice 1 is successful when QAP can reproducibly take one point-in-time Binance/Gate universe snapshot and one `as_of`, produce a bounded SSD pair graph, enumerate the fixed pair-native mean-reversion family, rank it with a clearly non-authoritative proxy, spend no more than ten automatic authoritative replays per horizon, and preserve exactly how every promoted hypothesis was produced.

It is **not** successful merely because the scanner finds a profitable historical candidate.

The architecture earns the next slice when it demonstrates that broad discovery is computationally manageable and that scanner/QAP boundaries remain intact. Alpha efficacy remains intentionally unresolved until later prospective evidence exists.
