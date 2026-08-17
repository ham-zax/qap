# QAP Scanner Slice 1 Design — Bounded Pair Discovery Foundation

**Date:** 2026-08-18

**Status:** User-approved design. Implementation is authorized by the 2026-08-18 `implementation_prompt.md` mission update; a detailed implementation plan must be written before code if one does not already exist.

**Scope:** First implementation slice of the QAP research scanner. It creates bounded, reproducible pair hypotheses and spends a fixed authoritative replay budget without creating a second economic engine.

> **Update context — 2026-08-18**
> **Trigger:** User-approved option B after review of the first frozen Slice-1 spec (`aa2330c`) against the two Deep Research reports and the current QAP model/orientation contracts.
> **Purpose:** Correct residual-model orientation, exact data-slice identity, scout no-action semantics, promotion policy, manual-pin lineage, and interrupted-scan recovery; clarify that broad asset-native momentum remains future Scanner-V1 intent.
> **Impact:** Slice 1 remains the bounded pair-native foundation. The scanner still uses one SSD generator and at most ten automatic deep replays per horizon, but all valid candidates may reach that replay budget and residual-MR orientations are independent trials. Phase 15 is an umbrella plan; slice specs own detailed Scanner-V1 semantics.
> **Evidence:** Deep Research reviews supplied in the 2026-08-18 design session; QAP orientation behavior in `docs/plans/04-relationship-evidence-pairs-and-anchor-lens.md`; existing authoritative experiment/policy/accounting contracts.
## 1. Goal and protected boundary

Build the smallest scanner foundation that can answer:

> As of timestamp `t`, using only point-in-time-admissible Binance/Gate evidence, which recent pair-relative mean-reversion hypotheses deserve the fixed authoritative QAP replay budget?

The slice must make broad discovery possible without becoming a Cartesian `pair x model x parameter x timeframe` optimizer.

The following remain constitutional:

- owned spot inventory only; no leverage, margin, borrowing, derivatives, or unowned shorts;
- `PortfolioState` remains the only economic inventory owner;
- scanner output is a hypothesis, not financial truth;
- matched HODL and the strongest predeclared simple admissible control remain mandatory economic comparisons;
- only the existing QAP policy -> execution -> inventory -> evaluation path may establish economic performance;
- today's survivor list cannot establish a historical point-in-time discovery universe;
- scanner exploration is development/search evidence and cannot consume reserved final OOS automatically.
## 2. Scanner decomposition

The broader scanner program is intentionally split.
```text
Slice 1 — bounded pair discovery foundation
  PIT universe
  one SSD neighborhood generator
  residual-MR + ratio-MR scouts
  fixed deep-replay budget
  search ledger
  candidate -> existing QAP replay adapter

Slice 2 — prospective evidence + liquidity qualification
  immutable forward cohorts
  candidate prospective evidence
  lightweight L1 + shallow-depth capture
  capacity / research_only / small_capacity / tradable_now

Slice 3 — basket + broader Scanner-V1 research surface
  broad asset-native relative momentum discovery
  manual 3–6 asset baskets
  one active opinion per pair/horizon
  deterministic long-only resolver
  scanner API/workbench projections
```
Slice 1 must preserve interfaces for later slices without implementing them early.
## 3. Architectural ownership

Add `qap.scanner` for discovery semantics only.
```text
qap.market
  admitted bars + lifecycle evidence
      |
      v
qap.scanner
  PIT universe
  SSD graph
  pair-native scout
  ranking + search ledger
      |
      v
immutable ScannerCandidate
      |
      v
qap.experiment
  candidate replay adapter
      |
      v
existing relationship -> policy -> execution -> portfolio -> evaluation
```
`qap.scanner` may consume `qap.market`, `qap.relationship`, and stable portfolio identity/value types. It must not import `qap.policy`, `qap.execution`, `qap.evaluation`, or `qap.experiment`.

The candidate-to-replay adapter belongs in `qap.experiment`. This is the structural defense against the scanner becoming a second backtester.
### Scanner never owns

- balances or actual inventory;
- fill generation or venue precision;
- authoritative fee/slippage truth;
- matched-HODL or simple-control construction;
- official terminal/relative wealth;
- final-OOS authority.

The scout may calculate only a clearly named approximate ranking proxy.
## 4. Frozen Slice-1 protocol

Every canonical scan binds a protocol identity. Any meaningful rule change creates a new protocol version.
```text
protocol_id: scanner-v1-s1
normal_history: 365d
maximum_normal_discovery_history: 730d   # project ceiling, not used automatically by Slice 1
venues: BINANCE, GATE
quote_asset: USDT
candidate_generator: normalized-log-price-ssd-v1
neighbors_per_asset: 8
automatic_deep_replay_cap_per_horizon: 10
max_automatic_promotions_per_asset_per_horizon: 2
max_automatic_promotions_per_pair_family_per_horizon: 1
```
The automatic Slice-1 path uses the most recent 365 days only. The project's 730-day discovery ceiling remains documented future/manual intent; Slice 1 does not add a second automatic history mode merely to exercise it.
### 4.1 Horizons and common evaluation windows

| Horizon | Meaning | SSD graph bars/window | Allowed model resolutions | Common scout/deep evaluation window |
|---|---|---|---|---:|
| `short` | hours–2 days | `1h`, trailing `30d` | `15m`, `1h` | trailing `30d` |
| `medium` | 2–10 days | `4h`, trailing `90d` | `1h`, `4h` | trailing `90d` |
| `swing` | 1–4 weeks | `1d`, trailing `180d` | `4h`, `1d` | trailing `180d` |

All templates within one horizon are ranked over the same evaluation start/end. Earlier rows inside the 365-day history are warm-up only. This avoids comparing terminal wealth over different effective durations.

The longest Slice-1 warm-up plus evaluation requirement is the swing `slow` template: `180d + 180d = 360d`, which fits the normal 365-day history policy.

These mappings are frozen engineering defaults, not historically selected optima.
## 5. Storage, exact data identity, and recovery

Keep QAP file-oriented. Do not add a database, queue, distributed worker system, scheduler service, or plugin framework.

A scan uses only admitted local snapshots. Network/exchange ingestion is a separate market-data operation.
### 5.1 Source identity versus evaluated-slice identity

Whole-file/source identity is not enough. Every admitted series used by a scan records both:
```text
source_artifact_fingerprint
selection_slice_fingerprint
```
`source_artifact_fingerprint` identifies the admitted source artifact.

`selection_slice_fingerprint` identifies the exact canonical rows visible to the scan through `eligible_information_end`, after interval/venue/instrument selection and before any model computation. Appending future rows to the source file therefore does not change the historical selection slice.

Candidate/trial identity binds to the exact slice fingerprints, not merely to the mutable extent of a source artifact.

The slice hash must be deterministic over canonical row serialization, including at least:
```text
venue instrument interval
bar_open bar_end_exclusive observation_complete_at
OHLCV/source row identity needed by current admission semantics
```
No row whose observation was incomplete at the information cutoff may enter the slice hash or computation.
### 5.2 Generation layout and atomic completion

Use recoverable staging:
```text
runs/scans/<scan_id>.partial/
  definition.json          # written first; immutable scan intent
  eligible_assets.parquet
  neighbors.parquet
  scout_trials.parquet
  promotions.parquet
  replay_attempts.parquet
  manifest.json            # written last inside staging
```
After all artifact counts/hashes reconcile, atomically publish/rename the directory to:
```text
runs/scans/<scan_id>/
```
`definition.json` freezes protocol, `as_of`, information cutoff, input slice fingerprints, and manual pins before work begins. An interrupted `.partial` generation may resume only when those identities still match.

A completed `manifest.json` in the final directory is the evidence-completion marker. Partial state is recovery state, not completed research evidence.

Authoritative deep replays remain ordinary QAP run artifacts referenced by run ID. Scanner tables do not copy or become owners of their financial accounting.
## 6. Point-in-time universe contract

Historical admission is three-valued:
```text
known_eligible
known_ineligible
historical_eligibility_unknown
```
Only `known_eligible` instruments may enter an official automatic graph.

`historical_eligibility_unknown` may remain available to explicitly labeled forensic/manual research but cannot silently participate in official point-in-time discovery claims.
### 6.1 Lifecycle evidence

Extend `qap.market` with event-oriented lifecycle evidence rather than a mutable `listed=true/false` field.

Conceptual event:
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
Required event types:
```text
listing_or_trading_started
trading_suspended
trading_resumed
delisting_announced
delisted
symbol_renamed
contract_or_token_migrated
```
Do not concatenate histories across rename/migration unless official evidence establishes continuity and the mapping is recorded explicitly.
### 6.2 Evidence priority

When evidence conflicts, prefer:

1. QAP's own timestamped append-only venue snapshot;
2. official exchange lifecycle announcement with effective timestamp;
3. official exchange metadata referring to the historical lifecycle event;
4. official exchange-native historical trade/bar evidence as positive evidence trading occurred near that timestamp;
5. current survivor/status metadata for current state only;
6. third-party metadata as corroboration only.

Absence of a bar is not proof a market did not exist. One historical trade is not proof of uninterrupted eligibility across a formation window.
### 6.3 Venue-local graphs

Build independent USDT spot universes:
```text
BINANCE:<asset>/USDT
GATE:<asset>/USDT
```
Do not splice venues into synthetic execution histories and do not add cross-exchange arbitrage mechanics.

`USDT` is the venue quote coordinate, not an automatic candidate base asset. Scanner admission never invents a Shariah/stablecoin taxonomy from ticker text.
## 7. One frozen SSD candidate generator

For each venue/horizon, use normalized log-price path squared distance.

For asset `i`:
```text
x_i(t) = log(P_i(t)) - log(P_i(t0))
d(i,j) = mean_t((x_i(t) - x_j(t))^2)
```
Smaller distance means more similar recent normalized paths. It is a search-bearing selector, not a cointegration claim.
### 7.1 Data-quality rules

For each graph:

- use only fully completed bars available by `eligible_information_end`;
- reindex to the expected timestamp grid;
- no forward fill or interpolation;
- require positive finite prices;
- asset bar coverage >= 95%;
- pair common-bar coverage >= 95%;
- longest missing run <= two generator bars;
- invalid/insufficient distances are excluded rather than assigned artificial values.

These are fixed data-policy constants. Changing them requires a new policy version and prospective evidence; they are not tuned against P&L.
### 7.2 Neighbor selection

For every eligible asset:

1. rank same-venue peers by `(distance, canonical_pair_id)`;
2. retain nearest `k=8`;
3. union all directed selections;
4. canonicalize to one unordered `PairId`;
5. deduplicate.

A pair survives if either side selected the other.

The quadratic distance matrix is allowed because it is one cheap vector comparison per unordered pair. The expensive model layer is bounded by the retained graph rather than all `N(N-1)/2` pairs.

Persist:
```text
eligible_asset_count
total_valid_pair_comparisons
generator_version/config
input selection_slice_fingerprints
distance_digest
retained neighbor edges + ranks
```
`distance_digest` is SHA-256 over canonically sorted `(pair_id, float.hex(distance))` records for every valid pair comparison.

The full matrix need not become millions of permanent rows because it is deterministically reconstructible from the frozen inputs and digest.
## 8. Manual pins without duplicate trial identity

Manual intuition is allowed and must remain visible.

A pinned same-venue pair bypasses only the SSD `k=8` cutoff. It still needs official identity, point-in-time eligibility, and data-quality admission.

For every retained pair persist independent lineage facts:
```text
automatic_neighbor_selected: bool
manual_pinned: bool
```
If a pair is both automatically selected and manually pinned, it remains one pair/trial identity. Do not duplicate it and do not erase either provenance fact.

A derived display label may be:
```text
automatic
manual_pin
automatic_and_manual
```
Manual investigations that intentionally admit `historical_eligibility_unknown` run only in forensic mode and cannot contribute to official automatic scoreboards.

Manual deep replays are outside the canonical automatic `10/horizon` budget and are attributed separately.
## 9. Slice-1 model menu and orientation semantics

Slice 1 has only two pair-native families:
```text
A. residual_mean_reversion
B. log_ratio_mean_reversion
```
Broad relative momentum remains Scanner-V1 intent but is asset-native and deferred to Slice 3. It must not be forced through the SSD pair topology merely to reuse Slice-1 code.

No Copulas, learned router, regime classifier, nonlinear family search, or automatic family expansion is admitted here.
### 9.1 Canonical pair versus oriented model trial

`PairId` is one unordered economic relationship. Model trials may still be oriented.

Use `numerator_asset` / `denominator_asset` for relationship orientation; do not confuse those names with the venue's USDT quote asset.

**Log-ratio MR** has exact reciprocal evidence semantics:
```text
r_t = log(P_numerator(t) / P_denominator(t))
```
Reversing orientation negates the log ratio and standardized score. Evaluate only the canonical orientation as one scout trial; the inverse display/action semantics are an exact transform.

Declare:
```text
fit_reciprocity = exact_transform
evidence_reciprocity = exact_transform
```
**Residual MR** is directional and must refit:
```text
log(P_numerator/USDT)
  = alpha + beta * log(P_denominator/USDT) + residual
```
`X~Y` and `Y~X` are not assumed equivalent. For every retained unordered pair, enumerate both residual orientations as separate scout trials under the same pair/research family.

Declare:
```text
fit_reciprocity = refit_required
evidence_reciprocity = model_specific
```
Trial identity includes orientation. The scanner must never choose orientation from lexical asset ordering and then present that arbitrary choice as model truth.
### 9.2 Mean-reversion preference sign

For log ratio:
```text
z > 0 -> numerator relatively expensive -> prefer denominator
z < 0 -> numerator relatively cheap     -> prefer numerator
preference_score = -z
```
For residual MR, fit deterministic OLS on completed common bars inside the declared rolling window and standardize the latest residual over that same fit window:
```text
z_residual > 0 -> numerator expensive relative to fitted relation -> prefer denominator
z_residual < 0 -> numerator cheap relative to fitted relation     -> prefer numerator
preference_score = -z_residual
```
The family is deliberately named `residual_mean_reversion`, not `cointegration_alpha`. ADF/cointegration diagnostics may be recorded later but cannot become hidden Slice-1 admission/router rules.
### 9.3 Fixed templates

Both families use three predeclared rolling windows per horizon:

| Horizon | fast | base | slow | neutral band | entry band |
|---|---:|---:|---:|---:|---:|
| short | 2d | 7d | 14d | `|z| <= 0.5` | `|z| >= 1.5` |
| medium | 14d | 30d | 60d | `|z| <= 0.5` | `|z| >= 1.5` |
| swing | 30d | 90d | 180d | `|z| <= 0.5` | `|z| >= 1.5` |

Durations convert deterministically to bars for each allowed resolution. Required warm-up coverage is >=95% with no interpolation.

`fast/base/slow`, `0.5`, and `1.5` are engineering defaults. Changing them creates a new protocol/template version and starts new prospective evidence.

Deep replay reuses the existing bounded two-asset target shape:
```text
neutral target: 50/50
maximum tilt: 10 percentage points
active extremes: 60/40 or 40/60
```
## 10. Cheap scout semantics

The scout is an approximate ranking mechanism, not a second fill/accounting system.

For each retained `pair x allowed resolution x family x template x required orientation`:

1. compute causal completed-bar evidence;
2. map evidence into the exact discrete policy states below;
3. maintain approximate float quantities for the two assets so `NO_ACTION` means holdings truly remain unchanged;
4. execute a simple next-observation target rebalance approximation only when a target is emitted;
5. compute target-weight turnover and subtract a one-way friction proxy derived from the declared QAP cost-policy reference;
6. compare against passive ownership from the same synthetic 50/50 starting quantities;
7. score every template over the horizon's common evaluation window.
### 10.1 Discrete state contract

The scout must match existing `EvidenceTiltPolicy` state semantics:
```text
|z| <= 0.5
  -> target 50/50

0.5 < |z| < 1.5
  -> NO_ACTION
  -> quantities remain unchanged; weights may drift

preference_score >= +1.5
  -> target 60/40 toward numerator

preference_score <= -1.5
  -> target 40/60 toward denominator
```
The signal cannot earn the return of the bar that produced it.

The ranking metric is named exactly:
```text
scout_relative_wealth_proxy
```
It must never be labeled QAP return, alpha, official economic success, or OOS performance.

The scanner owns no precision, min-notional, bridge, fill, fee-asset, or official benchmark calculation.
### 10.2 Rankable versus invalid

A trial is invalid/unrankable when:

- model warm-up/common observations are insufficient;
- fit/signal is non-finite;
- no active signal occurs during the common evaluation window;
- target/no-action path cannot be constructed causally;
- proxy wealth is invalid/non-finite.

A valid negative proxy remains a valid trial and remains rankable. Do not treat the proxy's zero line as an admission gate.
## 11. Promotion policy

For each horizon, sort automatic valid trials by:

1. `scout_relative_wealth_proxy` descending;
2. lower approximate turnover;
3. canonical venue/pair/model/orientation/resolution/template ID.

Then greedily apply:
```text
max automatic authoritative replays per horizon = 10
max automatic promoted trials involving one asset per horizon = 2
max automatic promoted trials for one pair/model-family per horizon = 1
```
The top valid trial may be negative. Slice 1 still deep-replays it if budget remains, because the scout is deliberately approximate and the fixed 30-replay all-horizon ceiling is the calibration cost of verifying that approximation.

If fewer than ten valid candidates survive diversity constraints, replay fewer. Never invent filler trials.

The pair/family cap prevents both residual orientations of one unordered pair from consuming duplicate authoritative budget; the higher-ranked orientation wins that family slot. The per-asset and pair/family caps are search-bearing selection policy even though their purpose is diversity/compute control. They are frozen/versioned and judged prospectively.

Do not add a 90-candidate tournament, Bayesian optimizer, Hyperband controller, significance gate, or learned routing rule.
## 12. Authoritative replay adapter and economic gates

`qap.experiment` converts each promoted immutable `ScannerCandidate` into an ordinary development-role QAP experiment.

Candidate identity includes at least:
```text
candidate_id
scan_id
scanner_protocol_version
automatic_neighbor_selected
manual_pinned
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
source_artifact_fingerprints
selection_slice_fingerprints
universe_snapshot_id
candidate_generator_version/rank
scout_relative_wealth_proxy
scout_turnover_proxy
```
The adapter supplies the existing experiment engine with:

- exact admitted market slices/fingerprints;
- declared relationship/model orientation behavior;
- frozen thresholds/window/template;
- `50/50` neutral target and `0.10` maximum tilt;
- authoritative `CostModel`;
- the existing deterministic historical replay/fill rules and any execution precision evidence that is actually present;
- matched HODL;
- strongest applicable predeclared simple admissible control.

The authoritative replay uses the same horizon evaluation start/end and information cutoff as the candidate. It may use earlier admitted rows only as causal warm-up and may not extend into reserved final OOS.

Slice 1 establishes **historical research economics**, not retroactive venue-capacity truth. If contemporaneous venue precision metadata or Binance/Gate MARKET notional-reference evidence was not captured for the historical timestamp, the replay must not invent it, backfill it from today's exchange state, or describe the result as historically executable at venue limits. OHLCV plus the frozen QAP cost model is sufficient for the Slice-1 research comparison because strategy, HODL, and the predeclared simple control share the same deterministic execution model.

Authoritative deep replay is deliberately narrower than relationship discovery. A promoted pair may enter `qap.experiment` only when the same venue has a **real direct spot instrument whose base/quote assets are exactly the candidate pair (either orientation)** and QAP has an admitted historical bar source for that direct instrument over the replay window. The adapter records that `direct_execution_instrument_id` in the replay lineage. If the discovered relationship is an indirect cross such as `ETH/SOL` represented only by `ETHUSDT` and `SOLUSDT`, Slice 1 may retain its scout/research evidence but must mark authoritative replay as ineligible/`unsupported_direct_market`; it must not synthesize an `ETHSOL` market, route through USDT, or silently feed bridge legs into the single-instrument historical replay engine.

Slice 2 owns prospective/current microstructure capture and the `research_only` / `small_capacity` / `tradable_now` qualification. Multi-asset bridge execution remains outside pair-native Slice 1 and becomes a Slice-3 concern only if that separate design is approved; an approved Slice 3 must reuse the Phase-11 multi-asset executor rather than creating scanner-owned routing.

A candidate becomes a historical `deep_replay_survivor` only when, after declared costs:
```text
terminal QAP wealth > matched HODL wealth
AND
terminal QAP wealth > strongest simple admissible control wealth
```
That remains searched development evidence. It is not confirmed alpha.
## 13. Search ledger and denominator

The ledger preserves the search procedure; it is not a multiple-testing correction.

`definition.json` / final `manifest.json` bind generation provenance:
```text
scan_id
scanner_protocol_version
as_of
eligible_information_end
created_at
universe_policy_version
candidate_generator_version
template_set_version
promotion_policy_version
cost_policy_reference
venues/horizons
source_artifact_fingerprints
selection_slice_fingerprints
manual pins / forensic mode
```

`cost_policy_reference` resolves to an immutable QAP execution-cost policy, not a scanner-local profitability knob. For every enabled horizon it must bind the exact ordinary and adverse `CostModel` inputs used by authoritative replay (`fee_bps` and `slippage_bps`, including the adverse pair). Slice 1 stores/replays that reference but does not invent horizon-specific friction budgets. Slice 2 derives any liquidity friction budget only from the referenced adverse `CostModel`; if an adverse model is absent, capacity qualification fails closed rather than substituting a number.

`eligible_assets.parquet` records at least:
```text
scan_id venue horizon asset_id venue_symbol
eligibility_state eligibility_reason lifecycle_evidence_refs
source_artifact_fingerprint selection_slice_fingerprint
bar_coverage longest_missing_run
```
`neighbors.parquet` records at least:
```text
scan_id venue horizon pair_id asset_a asset_b
ssd_distance rank_from_a rank_from_b
selected_by_a selected_by_b
automatic_neighbor_selected manual_pinned
```
`scout_trials.parquet` records every enumerated fixed trial, including losers and both residual orientations:
```text
candidate_id scan_id venue horizon pair_id orientation
resolution model_family template_id
trial_status failure_reason
scout_relative_wealth_proxy scout_turnover_proxy signal_count
automatic_neighbor_selected manual_pinned
```
`promotions.parquet` records:
```text
candidate_id promotion_rank promotion_status budget_reason
direct_execution_instrument_id
deep_replay_run_id deep_replay_status economic_gate_status
```

Before invoking `qap.experiment` for any promoted candidate, persist a replay-attempt row in `replay_attempts.parquet`:
```text
attempt_id scan_id candidate_id promotion_rank
attempt_status: enumerated | setup_failed | replay_failed | completed
failure_stage failure_reason
deep_replay_run_id
```
`attempt_id` is deterministic from the frozen scan/candidate/promotion identity. The `enumerated` row must exist durably before experiment preparation, data admission, manifest construction, or replay can fail. A setup failure updates that same attempt row to `setup_failed`; it does not disappear because no experiment `manifest.json` was produced. Publication must reconcile the enumerated promotion count against replay-attempt rows and promotion outcomes.

The automatic denominator is reconstructible from the PIT universe, deterministic SSD generator, fixed trial enumeration, complete trial table, promotion table, and pre-enumerated replay-attempt ledger. Manual additions remain visibly separate.
## 14. Statistical semantics

Slice 1 uses one simple rule:
```text
same historical data influences screening/ranking/replay
  -> search/development evidence

future observations unavailable when a rule/candidate was frozen
  -> possible prospective evidence (Slice 2)
```
SSD, model scores, orientation trials, template choice, proxy ranking, diversity caps, and deep-replay selection are all part of the search procedure.

Predeclaration improves reproducibility; it does not make price-derived selection statistically independent.

Do not use SPA, Reality Check, Romano-Wolf, DSR, PBO, or naive per-row p-values as Slice-1 promotion gates. Later formal tests may audit frozen comparable forward return series; prospective economics is the primary confirmation path.
## 15. Performance, failure handling, and dependencies

The permitted complexity shape is:
```text
SSD generation: O(H * N^2 * T) cheap vector comparisons
pair scout after k=8 graph: approximately O(H * N * k * F * R * P * O)
automatic authoritative replay: <= 30 per all-horizon scan
```
where `H=3`, `k=8`, `F=2`, `R=2`, `P=3`, and `O` is model-orientation multiplicity (`1` ratio, `2` residual).

Benchmark realistic 500- and 1,000-asset datasets during implementation and optimize only measured bottlenecks. PyArrow remains canonical storage; NumPy is sufficient for dense kernels; Polars/DuckDB are permitted only where they materially simplify/accelerate measured scanner work. No distributed compute.
### Exclude/record and continue

- one asset fails coverage;
- one pair lacks common observations;
- one trial fit/signal is invalid;
- one candidate lacks a real direct venue instrument/historical source for authoritative replay and is recorded as `unsupported_direct_market` rather than synthesized through a bridge;
- one promoted candidate fails experiment setup/data admission after its replay attempt has been durably enumerated;
- one promoted candidate fails authoritative replay for candidate-specific reasons.
### Abort the generation

- a frozen input slice fingerprint changes;
- `as_of`/information cutoff becomes inconsistent;
- PIT universe snapshot cannot be reproduced;
- frozen protocol/definition is malformed;
- deterministic IDs collide;
- staging/final artifact counts or hashes do not reconcile.
## 16. Operator surface

No scanner web UI in Slice 1.

Expose one deterministic argparse entry point consistent with the repository's module-CLI style:
```text
python -m qap.scanner.cli \
  --as-of <ISO-8601-UTC> \
  --horizon <short|medium|swing|all> \
  --data-root <path> \
  --run-root <path> \
  [--pins-file <json-path>]
```
The CLI reports:

- admitted/excluded counts by venue/horizon;
- retained SSD edges;
- enumerated/valid/invalid scout trials;
- automatic promotions and budget exclusions;
- authoritative replay survivors/failures;
- scan ID and artifact path.

`--pins-file` can add same-venue pair pins and explicit forensic-mode requests; it cannot mutate the automatic protocol.
## 17. Testing and acceptance
### Unit/property contracts

- normalized-log SSD symmetry and initial-price scale invariance;
- deterministic ties and `k=8` union/deduplication;
- no cross-venue edges;
- no incomplete/future bars;
- source fingerprint versus exact slice fingerprint behavior under future-row append;
- three-state PIT admission;
- manual/automatic overlap creates one trial identity with both lineage flags;
- log-ratio exact reciprocal transform;
- residual MR enumerates both orientations and refits;
- ratio/residual mean-reversion sign semantics;
- neutral/NO_ACTION/entry target-state parity with existing policy semantics;
- common horizon evaluation windows and deterministic warm-up mapping;
- candidate/protocol/hash determinism;
- ranking, pair/family + per-asset caps, and negative-valid-candidate promotion behavior.
- replay attempts are durably enumerated before experiment preparation and setup failures remain counted.
### Scenario contracts

One synthetic market proves:
```text
PIT universe
 -> expected SSD graph
 -> fixed oriented trial enumeration
 -> deterministic approximate ranking
 -> <=10 automatic promotions/horizon
 -> ordinary QAP deep replay
 -> HODL/simple-control gates
```
A negative scenario proves that an attractive scout can fail authoritative replay and that a negative scout can still be deep-replayed when it ranks inside the fixed budget.
### Research-integrity contracts

- current exchange state cannot silently backfill historical eligibility;
- `historical_eligibility_unknown` cannot enter official scans;
- changing graph windows, `k`, thresholds, orientation enumeration, or promotion caps changes protocol identity;
- final-OOS rows cannot enter scanner replay/warm-up;
- manual pins cannot masquerade as automatic discovery;
- historical OHLCV without contemporaneous venue execution evidence cannot produce a historical capacity/venue-feasibility claim;
- a discovered pair without a real direct venue market/historical direct-market dataset cannot enter authoritative deep replay and cannot be silently bridged;
- `qap.scanner` cannot import policy/execution/evaluation/experiment layers;
- interrupted `.partial` scans resume only against the exact frozen definition/slices.

Two scans with identical frozen definition, data slices, protocol, and manual inputs produce logically equivalent candidate sets/rankings, apart from explicitly non-semantic creation timestamps.
## 18. Explicit non-goals

Do not build in Slice 1:

- adaptive diagnostic routing;
- multiple pair generators/selector competition;
- parameter/Bayesian optimization;
- Copula/tail broad scans;
- broad asset-native momentum;
- automatic portfolio/basket discovery;
- learned edge weights or portfolio optimization;
- multi-horizon portfolio aggregation;
- prospective forward registry/scoreboards;
- L1/depth capture/capacity graduation;
- historical L2 reconstruction;
- scanner scheduler/platform;
- scanner web mutation UI;
- live/private exchange authority.
## 19. Future interface and acceptance boundary

Slice 2 may attach to a survivor without changing Slice-1 identity:
```text
freeze_id
forward_cohort_id
prospective evidence checkpoints
liquidity evidence/status
capacity estimate
```
Slice 3 may add a separate asset-native discovery stream and consume pair evidence for manually selected baskets:
```text
asset-native relative momentum
manual 3–6 asset basket
one active opinion per unordered pair/horizon
ternary {-1,0,+1} pair preference
fixed equal edge weight
degree-normalized/component-neutral resolver
one final long-only QAP target
```
Slice 1 succeeds when QAP can reproducibly take one admitted point-in-time Binance/Gate universe snapshot and one `as_of`, produce a bounded SSD graph, enumerate the fixed pair-native mean-reversion trials with correct orientation semantics, rank them using a clearly non-authoritative proxy, spend no more than ten automatic authoritative replays per horizon, and preserve exactly how each hypothesis arose.

It is not successful merely because it finds a profitable historical candidate. Alpha efficacy remains unresolved until prospective evidence exists.
