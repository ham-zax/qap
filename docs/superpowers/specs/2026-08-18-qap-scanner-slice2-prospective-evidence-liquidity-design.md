# QAP Scanner Slice 2 Design — Prospective Evidence and Liquidity Qualification

**Date:** 2026-08-18

**Status:** User-approved design. Implementation is authorized by the 2026-08-18 `implementation_prompt.md` mission update; a detailed implementation plan must be written before code if one does not already exist.

**Depends on:** `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`

**Scope:** Turn Slice-1 historical survivors into immutable prospective research cohorts and collect enough current microstructure evidence to classify hypothetical actionability without pretending historical OHLCV proves executable capacity.

## 1. Goal

Slice 2 answers two questions that Slice 1 intentionally cannot:

> After a candidate was selected and frozen using only past information, what happened on genuinely later data?

and:

> At a specified hypothetical capital size, does current captured spread/depth evidence support `tradable_now`, only `small_capacity`, or `research_only`?

The slice does **not** build live trading, a scheduler platform, a portfolio optimizer, or a new backtester.

## 2. Protected semantics

- Historical search/replay remains development evidence.
- Prospective status requires selection/freeze before outcome observations exist.
- Prospective evaluation uses existing QAP policy/execution/inventory/evaluation authority.
- `forward_paper` remains operational paper/dry-run evidence and cannot be relabeled scanner prospective-alpha evidence.
- Reserved final OOS remains sealed.
- Candidate pair P&Ls are never summed into a fictional portfolio.
- Liquidity evidence may restrict actionability but cannot create alpha.
- Missing historical order-book evidence remains unknown rather than imputed.
- No live credentials, order placement, capital authority, borrowing, leverage, derivatives, or unowned shorts.

## 3. Architecture

```text
Slice-1 deep_replay_survivor
        |
        v
qap.scanner forward registry
  freeze + cohort identity
        |
        v
future admitted bars arrive
        |
        v
qap.experiment prospective replay adapter
        |
        v
existing QAP replay/evaluation
        |
        v
append-only candidate evidence checkpoints

promoted/pinned venue instruments
        |
        v
qap.market microstructure capture
  L1/book ticker + shallow depth
        |
        v
qap.scanner liquidity qualification
        |
        v
research_only / small_capacity / tradable_now
```

`qap.scanner` still must not own fills, balances, official HODL/control economics, or exchange execution truth.

`qap.market` owns admitted public market observations and provenance. Slice 2 may add current microstructure observation types there, but not a generic private exchange client.

## 4. Two evidence layers

### 4.1 Candidate prospective evidence

Candidate evidence asks what happened after one exact frozen pair/model/orientation/template hypothesis was selected. It is evaluated through authoritative QAP replay over a future window.

### 4.2 Scanner-selection cohort evidence

A frozen automatic scan generation may produce several survivors. Slice 2 records prospective **selection quality**:

- candidate count;
- matured/partial/invalid count;
- distribution of candidate net wealth versus HODL/control;
- number/fraction passing both economic gates prospectively;
- model/family/horizon attribution;
- automatic/manual selection attribution.

Slice 2 must not add or average pair terminal wealth and call the result “Scanner portfolio return.” Several candidates may share assets and do not represent independent capital books.

A true scanner-policy portfolio wealth path requires the one-inventory basket resolver planned for Slice 3.

## 5. Prospective evidence identity

Introduce scanner-owned immutable artifacts conceptually equivalent to:

```text
CandidateFreeze
ForwardCohort
ForwardCheckpoint
ForwardOutcome
```

They reference QAP experiment/run artifacts rather than copying their accounting.

### 5.1 `CandidateFreeze`

Required fields:

```text
freeze_id
candidate_id
scan_id
scanner_protocol_version
automatic/manual selection facts
frozen_at
eligible_information_end
forward_start
forward_end
horizon
venue
pair_id
orientation
resolution
model_family
template_id
model_parameters
source/selection-slice fingerprints at freeze
universe_snapshot_id
cost_policy_reference
candidate_deep_replay_run_id
candidate_deep_replay_gate_status
```

`freeze_id` is deterministic from semantic content and excludes non-semantic creation timestamps.

Only a Slice-1 `deep_replay_survivor` may enter the canonical automatic prospective cohort. Manual/pinned survivors may also be frozen, but their lineage remains explicit and is excluded from automatic cohort summaries unless a later protocol explicitly changes that rule.

### 5.2 Freeze timing invariant

```text
frozen_at < forward_start
AND
eligible_information_end < first outcome observation used
```

The pair, orientation, model, thresholds, target policy, costs, and evaluation horizon are immutable after freeze. Changing them creates a new candidate/freeze generation; old prospective evidence does not transfer.

`forward_start` is candidate-specific: use the first model-resolution decision boundary strictly after `frozen_at`, and require the first outcome observation used to complete after that boundary. Cohort members do not need one shared bar boundary.

### 5.3 Forward horizons

Use one fixed maximum prospective window per research horizon:

```text
short  -> 48 hours
medium -> 10 days
swing  -> 28 days
```

These map to the already approved horizon definitions and are not optimized holding periods. Interim checkpoints may exist, but the completed endpoint is the canonical matured outcome.

## 6. Cohort enrollment

For each completed automatic Slice-1 scan/horizon:

1. take every automatic `deep_replay_survivor`;
2. create one `ForwardCohort` containing all such survivors;
3. freeze every new member before that candidate's own prospective start;
4. if the same semantic candidate already has an active unmatured freeze under the same protocol, record a reselection event instead of opening a duplicate overlapping freeze;
5. allow a zero-new-member cohort as a valid result;
6. preserve manual/pinned membership separately.

Do not ask the operator to cherry-pick one historical winner before prospective tracking. Active-freeze deduplication bounds repeated 4-hour/daily scans without pretending repeated overlapping selections are independent experiments. The deduplication key is the frozen semantic rule `(protocol, venue, pair, orientation, horizon, resolution, model_family, template_id, model_parameters, cost_policy)`, not the source scan ID. After a freeze matures, a later reselection may open a new prospective generation.

A cohort records:

```text
forward_cohort_id
scanner_protocol_version
source_scan_id
horizon
cohort_frozen_at
candidate_freeze_ids[]
reselected_active_freeze_ids[]
automatic_member_count
manual_member_count
```

If the ScannerProtocol changes, new cohorts use the new version. Old/new forward results remain visible but are not silently pooled.

## 7. Forward data and replay semantics

Future data enters only through normal QAP admission/fingerprinting.

At checkpoint time `through`:

- only bars with `observation_complete_at <= through` may be used;
- pre-forward warm-up rows may be used only if they were knowable at freeze;
- after `forward_start`, the frozen rolling rule may update causally from newly completed bars;
- no bar may earn the return of the signal it produced;
- existing next-observation execution/fill semantics remain authoritative.

### 7.1 Starting inventory

Candidate prospective evidence remains a two-asset research experiment, not the user's whole portfolio.

Use the same candidate research convention as Slice-1 deep replay:

```text
starting target = 50/50 pair inventory
matched HODL = exact same starting quantities
simple control = exact same starting quantities/window/cost semantics
```

Never merge separate candidate books into one portfolio claim.

### 7.2 Underlying experiment role

Do **not** reuse `DataRole.FORWARD_PAPER`.

Prospective status is proven by scanner freeze/cohort timing and immutable lineage. The underlying QAP replay may remain `DataRole.DEVELOPMENT` unless a later repository-wide design introduces a dedicated prospective-research role.

Reserved `FINAL_OOS` data is never used by this path.

## 8. Forward processing and checkpoints

Expose deterministic commands that advance frozen cohorts against newly admitted data. Do not build a daemon or scheduler.

```text
freeze cohort
  -> later ingest new public bars
  -> advance cohort --through <timestamp>
  -> append immutable checkpoints
  -> repeat
  -> finalize matured outcomes when forward_end is complete
```

A checkpoint records:

```text
checkpoint_id
freeze_id
through
market_slice_fingerprints
replay_run_id
status: pending | partial | matured | invalid
result_reference
created_at
```

Same freeze + same future slice must reproduce the same run/result identity or fail loudly. Published checkpoints are immutable; later checkpoints extend evidence rather than overwrite it.

### 8.1 No internal scheduler

Conceptual commands:

```text
python -m qap.scanner.forward_cli freeze ...
python -m qap.scanner.forward_cli advance --cohort <id> --through <UTC>
```

External/manual invocation may later follow the already chosen cadence: short roughly every four hours, medium roughly daily, swing daily/every few days, pinned investigations on demand. Slice 2 does not create cron/systemd/Celery/job-server machinery.

## 9. Prospective economic outcome

A matured candidate outcome references authoritative QAP economics and exposes separately:

```text
net wealth vs matched HODL
net wealth vs strongest simple admissible control
relative-wealth path
costs
turnover
fills/no-fills
drawdown/concentration diagnostics
```

A prospective candidate passes only when both economic gates remain positive over its frozen future window:

```text
QAP wealth > matched HODL
AND
QAP wealth > strongest simple admissible control
```

Historical pass followed by prospective failure is a normal result and must remain visible.

## 10. Prospective scoreboards

File/CLI scoreboards may group by:

```text
scanner_protocol_version
calendar week/month
horizon
model_family
venue
automatic/manual selection source
```

A July-style report means selections were frozen before their attributed July outcomes occurred. Never fit on all of July and call the best retrospective backtest “what worked in July.”

Because horizons overlap, do not treat every trade/candidate outcome as IID. Later formal inference may use time-indexed QAP wealth/P&L differentials with dependence-aware methods; Slice 2 does not build a statistical-governance service.

## 11. Microstructure capture boundary

Historical OHLCV is enough for discovery research but not for certifying executable capacity.

Slice 2 starts collecting current public evidence for promoted/pinned instruments so QAP can make defensible **current** actionability statements going forward. Do not attempt a giant historical L2 reconstruction project.

### 11.1 Public capture only

For Binance/Gate spot instruments capture public:

```text
L1/book ticker
  bid
  ask
  bid quantity
  ask quantity
  observed_at

shallow order book
  ordered bid levels
  ordered ask levels
  observed_at

instrument state
  two-way trading status
  order constraints needed by QAP execution rules
```

No private account data or credentials are required.

### 11.2 Capture cadence contract

For promoted/pinned instruments needing qualification:

```text
L1/book ticker snapshot: nominal every 60 seconds
shallow depth snapshot: nominal every 5 minutes
minimum qualification window: 14 calendar days
overall scheduled coverage: >=95%
each UTC day scheduled coverage: >=90%
```

These are conservative versioned engineering defaults, not profitability-tuned parameters.

The collector should be a one-shot/bounded command. External invocation supplies cadence; missing invocations remain missing data and reduce measured coverage.

If captured depth ends before a hypothetical order can be filled, record:

```text
capacity_unknown_at_that_size
```

Do not extrapolate unseen depth.

## 12. Liquidity evidence contract

For each instrument retain, where available:

```text
historical bar diagnostics
  rolling quote volume
  zero-volume fraction
  stale/no-change fraction
  missing-bar fraction
  trade count when supplied

L1 diagnostics
  bid/ask
  quoted spread
  bid/ask size

book diagnostics
  cumulative bid/ask notional by price distance
  simulated buy/sell VWAP for hypothetical quote notionals

instrument constraints
  current trade status
  min/max order rules
  price/quantity precision
```

Volume is corroborating evidence. Slice 2 does not invent `1% ADV`, `$10m/day`, or another universal liquidity threshold.

## 13. Direct book-sweep capacity

For hypothetical taker quote notional `q` at snapshot `t`, walk the captured book and compute separately for buys/sells:

```text
c_t(q) = abs(VWAP_t(q) - mid_t) / mid_t + configured_taker_fee
```

Across the qualified microstructure window use a conservative nearest-rank percentile (`ceil(0.95*n)-1` after sorting), with no interpolated quantile:

```text
C95(q) = max(
  95th_percentile(buy_cost_t(q)),
  95th_percentile(sell_cost_t(q))
)
```

A snapshot that belongs to the qualified window but cannot fill `q` from the captured book is **not omitted** from this calculation. That `q` is infeasible for the window and its capacity result is `capacity_unknown_at_that_size` / fail for qualification. The implementation may represent the missing side as `+infinity` internally, but publication must not compute a lower percentile from only the fillable snapshots.

`B_h` is not a new scanner-tuned parameter. The frozen candidate/scan `cost_policy_reference` must resolve to QAP's predeclared adverse `CostModel` for horizon `h`. Define:

```text
fee_h               = adverse_cost_model.fee_bps / 10_000
slippage_budget_h   = adverse_cost_model.slippage_bps / 10_000
B_h                 = fee_h + slippage_budget_h
```

The book-sweep cost uses that same fee exactly once:

```text
c_t(q) = book_price_impact_t(q) + fee_h
```

so the capacity condition is equivalent to `book_price_impact <= slippage_budget_h`. If the frozen cost policy has no adverse cost model, Slice 2 cannot infer a friction budget and the candidate remains `research_only`; it must not invent a horizon budget.

Then:

```text
q_star = max q such that every required snapshot is fillable at q
                     AND C95(q) <= B_h
q_safe = 0.5 * q_star
```

The `0.5` haircut belongs to `liquidity-policy-v1`; it is a conservative engineering factor and must not be tuned to candidate profitability.

Compute `q_star` deterministically with Decimal arithmetic/bisection over the executable quote-notional range, using venue quote/order precision as the stopping tolerance. If the captured book or venue precision cannot establish that range, capacity remains unknown. Use conservative taker/marketable execution only; maker queue/fill probability is future work.

## 14. Candidate capital ceiling

Capacity is based on the largest **one-way rebalance notional the frozen policy can actually require**, not the maximum deviation from neutral. The 40/60 and 60/40 target states alone permit a 20-percentage-point one-way transition, and `NO_ACTION` drift can make the next corrective rebalance larger.

For the direct candidate market, compute conservative direction-specific required trade fractions using exact Decimal weights. Let `w` be the current weight of the direct market's base asset and let `T={0.40,0.50,0.60}` be the frozen base-asset target states:

```text
r_structural_buy  = 0.20
r_structural_sell = 0.20

r_current_buy  = max(max(t - w, 0) for t in T)
r_current_sell = max(max(w - t, 0) for t in T)

r_required_buy  = max(r_structural_buy,  r_current_buy)
r_required_sell = max(r_structural_sell, r_current_sell)
```

The current weight `w` must come from the authoritative current prospective candidate state/valuation at the qualification timestamp; drift is not clipped at `0.20`. Let `q_safe_buy` and `q_safe_sell` be the independently qualified quote-notional capacities from the captured direct-market book. The candidate ceiling is the minimum defensible result:

```text
candidate_capital_ceiling = min(
  q_safe_buy  / r_required_buy,
  q_safe_sell / r_required_sell,
)
```

If the required fraction cannot be established from the frozen policy/current state, capacity is unknown. A `NO_ACTION` observation does not imply infinite capacity because the direction-specific `r_structural_*` terms still protect the next allowed extreme target transition.

Slice-1 authoritative survivors are restricted to real direct venue markets, so Slice 2 qualifies both buy and sell capacity on that direct instrument. Multi-leg bridge capacity belongs to a separately approved Slice 3 using the Phase-11 executor.

Do not persist a universal “tradable capital” for an asset. Capacity is time-, venue-, direction-, state-, and policy-dependent.

## 15. Three liquidity tiers

Tier classification is a function of:

```text
candidate/instrument
as_of timestamp
hypothetical requested capital
liquidity_policy_version
```

Slice 2 does not invent the user's actual capital. The operator must supply explicit hypothetical `requested_capital` for classification.

### 15.1 `tradable_now`

Require all of:

```text
current status permits required buys and sells
14d capture contract satisfied
book supports required order sizes
requested capital <= safe candidate capital ceiling
existing order constraints can be satisfied
candidate remains positive under declared empirical/adverse cost replay
```

Report:

```text
tradable_now
as_of=<timestamp>
at_capital=<explicit hypothetical capital>
estimated_capital_ceiling=<value>
```

It is never a permanent coin label.

### 15.2 `small_capacity`

Require:

```text
execution evidence contract satisfied
safe capital ceiling is positive/usable
requested capital > safe capital ceiling
candidate economic gates survive at a lower tested capital <= ceiling
```

Report the estimated ceiling explicitly.

### 15.3 `research_only`

Any one is sufficient:

```text
only OHLCV exists
historical/current eligibility unresolved for the claim
microstructure coverage insufficient
book depth insufficient to establish required size
instrument not currently two-way tradable
safe capacity below usable venue/order size
reasonable empirical/adverse cost destroys the candidate edge
```

An obscure Gate candidate may remain valuable research while staying `research_only` indefinitely.

## 16. Historical versus current liquidity claims

If a historical candidate has clean candles but QAP did not capture contemporaneous spread/depth:

```text
historical relationship/economic backtest evidence: may exist
historical executable capacity: unknown
```

Current microstructure collection may qualify the candidate **now** if the relationship remains relevant. It does not retroactively prove historical trades were executable at that capacity.

## 17. Cost-policy integration

Liquidity qualification consumes the existing QAP cost-policy boundary rather than inventing a second profit model.

The scanner may derive an empirical conservative one-way friction observation from captured book data, but any “still profitable after this cost” claim must be established by ordinary QAP replay/evaluation with that declared cost scenario.

Do not directly subtract depth cost from scanner results and call it authoritative terminal wealth.

## 18. Storage and atomicity

Keep file-oriented append-only artifacts.

```text
runs/scanner-forward/<cohort_id>/
  cohort.json
  freezes.parquet
  checkpoints.parquet
  outcomes.parquet

market/microstructure/<venue>/<instrument>/<UTC-date>/
  l1.parquet
  depth.parquet
  metadata.json
```

Published cohort/freeze records are immutable. Checkpoints/outcomes append new immutable records.

Market capture partitions retain provenance fingerprints and reject conflicting duplicate observations rather than silently overwrite them.

No database is required.

## 19. Failure handling

### Candidate-specific failure: record and continue

- future bar gap invalidates one replay;
- one instrument loses two-way tradability;
- one candidate cannot satisfy order constraints;
- one liquidity window has insufficient coverage;
- one book snapshot cannot price the requested notional.

### Abort/deny publication

- freeze timestamp is not before first outcome information;
- frozen candidate/protocol fingerprint changed;
- reserved final-OOS data would be consumed;
- future market slice cannot be reproduced;
- cohort membership mutates after freeze;
- artifact/checkpoint identities collide or hashes fail reconciliation.

A delisting/suspension during the prospective period is real prospective evidence and must be represented through normal execution/no-fill/eligibility semantics, not removed because it hurts performance.

## 20. Testing strategy

### Freeze/prospective contracts

- only eligible historical survivors enter automatic cohorts;
- all automatic survivors are enrolled or explicitly linked to an already-active identical freeze; zero-new-member cohorts are valid;
- manual lineage remains separate;
- outcome observations cannot predate freeze;
- changed candidate/protocol creates new freeze identity;
- appended future data creates new checkpoints without altering older checkpoints;
- same freeze + same future slice reproduces the same replay result;
- reserved final OOS is rejected;
- `forward_paper` cannot satisfy scanner prospective evidence.

### Economic contracts

- prospective replay uses exact matched starting quantities;
- both HODL and simple-control gates remain mandatory;
- overlapping candidates are not summed into scanner portfolio P&L;
- negative prospective results remain visible/immutable.

### Microstructure contracts

- L1/depth timestamps and venue instruments are exact;
- coverage uses expected cadence without fill/interpolation;
- insufficient depth yields `capacity_unknown_at_that_size` and the unfillable snapshot never disappears from the `C95(q)` denominator;
- buy/sell VWAP walk is deterministic;
- `B_h` resolves only from the frozen QAP adverse `CostModel`, with fee counted once and book impact consuming the adverse slippage allowance;
- `C95`, `q_star`, `q_safe` follow frozen policy;
- capital ceiling uses the conservative actual/structural rebalance fraction rather than a fixed `0.10` divisor;
- 14d/95%/90%-daily rules fail closed;
- tier classification requires explicit hypothetical capital;
- historical OHLCV alone cannot produce `small_capacity`/`tradable_now`;
- empirical-cost qualification routes back through QAP replay.

## 21. Operator surface

No web workbench is required in Slice 2.

Expose narrow deterministic argparse commands for:

```text
freeze automatic survivors into a cohort
advance a cohort through admitted future data
show candidate/cohort prospective evidence
capture one L1 snapshot
capture one shallow-depth snapshot
qualify liquidity at explicit hypothetical capital
```

Do not hide a persistent loop inside these commands. Scheduling remains external infrastructure.

## 22. Explicit non-goals

Do not build in Slice 2:

- broad asset-native momentum;
- basket resolver or combined portfolio P&L;
- automatic graph-to-portfolio construction;
- predictive model router;
- multiple-testing dashboard/service;
- SPA/RC as automatic daily gates;
- historical L2 reconstruction;
- maker/limit-order queue simulator;
- live/private exchange execution;
- scheduler/job server/database/distributed workers;
- automatic scanner-policy changes from forward scoreboards;
- scanner UI mutation workflow.

## 23. Acceptance boundary

Slice 2 succeeds when QAP can:

1. take every bounded automatic Slice-1 historical survivor and either freeze it before future outcomes or explicitly link a reselection to an identical already-active freeze;
2. replay that immutable hypothesis causally as new admitted bars arrive;
3. retain immutable prospective checkpoints/outcomes without confusing them with `forward_paper` or final OOS;
4. report cohort selection evidence without adding overlapping pair P&Ls;
5. collect the specified forward L1/depth evidence for promoted/pinned instruments;
6. derive direct book-sweep capacity from the existing adverse-cost budget;
7. classify `research_only`, `small_capacity`, or `tradable_now` only at an explicit timestamp and hypothetical capital;
8. fail closed when execution evidence is insufficient;
9. preserve that missing historical depth cannot be reconstructed from candles.

Slice 2 does not need a profitable prospective candidate to succeed. A cohort where all historical survivors fail prospectively is a valid and important result.

After Slice 2 implementation evidence exists, Slice 3 may design the broader asset-native momentum and manual basket workbench. No automatic portfolio discovery is implied.
