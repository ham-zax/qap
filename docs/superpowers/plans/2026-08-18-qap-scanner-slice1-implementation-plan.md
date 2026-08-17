# QAP Scanner Slice 1 Implementation Plan

> **For the implementation lead:** REQUIRED SUB-SKILL: use `superpowers:executing-plans` in the single authorized implementation thread. Do not dispatch secondary coding/review agents; the repository mission explicitly requires direct sequential implementation.

**Goal:** Implement the approved bounded Scanner-V1 Slice-1 pair-discovery foundation so one frozen point-in-time scan can produce deterministic venue-local pair hypotheses, rank fixed mean-reversion trials with a non-authoritative scout, spend at most ten automatic authoritative QAP replays per horizon, and preserve complete search provenance without creating a second economic engine.

**Architecture:** Add a new inner research-orchestration package, `qap.scanner`, above admitted `qap.market` data and `qap.relationship` evidence. `qap.scanner` owns point-in-time admission, exact evaluated-slice identity, SSD graph construction, fixed trial/scout ranking, promotion policy, scan artifacts, and CLI orchestration only. Promoted immutable candidates cross into `qap.experiment` through a narrow adapter; authoritative replay continues through QAP policy, direct execution, inventory, benchmark, and evaluation code. Slice-1 deep replay is deliberately narrower than discovery: only a real same-venue direct spot market with admitted historical direct-market data may be replayed; unsupported crosses remain searched scout evidence and are never silently bridged.

> **Update context — 2026-08-18**
> **Trigger:** Pre-rearchitecture audit remediation commits `619fc5c` and `30adfb7`, plus user confirmation that all ten audit findings are resolved.
> **Purpose:** Reconcile this plan with the now-authoritative direct-market-only Slice-1 replay boundary, durable replay-attempt denominator, resolved authorization state, and conservative Slice-2 liquidity contracts.
> **Impact:** Remove the stale bridge-routing/shared multi-fill replay expansion, synthetic-capital approval gate, and historical-precision requirement. Add direct-market eligibility, evidence-only relationship inputs, durable replay-attempt rows, and fail-closed unsupported-cross semantics. Slice 2 remains authorized but separate; Slice 3 remains a design gate.
> **Evidence:** `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`; `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`; `docs/reviews/2026-08-18-pre-rearchitecture-hardening.md`; `docs/superpowers/plans/2026-08-18-pre-rearchitecture-audit-final-remediation.md`.

**Tech Stack:** Python 3.14, NumPy, PyArrow/Parquet, Pydantic for persisted current-schema specifications, existing QAP market/relationship/policy/execution/evaluation/experiment primitives, pytest/Hypothesis, argparse. No new runtime/research dependency is planned initially; Polars/DuckDB may be admitted only if the required 500/1,000-asset benchmark identifies a measured bottleneck they materially remove.

## Global Constraints

- The authoritative requirements are `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`, then `docs/plans/15-research-scanner-and-candidate-workbench.md`, then the master plan. More-specific Slice-1 wording wins.
- Preserve long-only, spot-only, owned-inventory, self-financing, no-leverage/no-borrowing/no-derivatives/no-riba boundaries.
- `PortfolioState` remains the only mutable economic inventory truth. Scanner artifacts never own balances, fills, terminal wealth, HODL, control wealth, or final-OOS authority.
- `qap.scanner` may import `qap.market`, `qap.relationship`, and stable portfolio identity/value types. It must not import `qap.policy`, `qap.execution`, `qap.evaluation`, or `qap.experiment`.
- Existing `qap.experiment` remains the scanner-to-authoritative-replay boundary. Any reusable execution generalization lives in `qap.execution`/`qap.experiment`, not inside `qap.scanner`.
- Official scans use three-valued historical eligibility and admit only `known_eligible`. Current exchange survivor metadata may not backfill historical eligibility.
- Separate Binance-USDT and Gate-USDT graphs. No cross-venue synthetic history or arbitrage behavior.
- Scanner V1 Slice 1 has exactly one automatic generator: normalized-log-price SSD, `k=8`, with frozen short/medium/swing horizon mappings.
- Scanner V1 Slice 1 has only `log_ratio_mean_reversion` and `residual_mean_reversion`; ratio reciprocity is exact-transform, while residual orientations are separate refits and separate trial identities.
- Three fixed templates per family/horizon; neutral/NO_ACTION/entry semantics must match `EvidenceTiltPolicy`, including quantity preservation during NO_ACTION.
- Valid negative scout proxies remain rankable. Zero is not an admission gate.
- Automatic authoritative replay is capped at 10 per horizon, 2 promoted trials involving one asset per horizon, and 1 promoted trial per unordered pair/model family per horizon.
- Same-sample scanner search/replay remains development evidence; scanner code may not consume reserved `final_oos` automatically.
- Manual pins preserve independent `automatic_neighbor_selected` and `manual_pinned` lineage and must not duplicate semantic trials.
- Partial scan directories are recovery state only. Final publication requires reconciled counts/hashes and an atomic rename to a manifest-bearing final directory.
- Every promoted deep-replay attempt is durably enumerated in `replay_attempts.parquet` before experiment preparation/data admission; setup failures remain in the search denominator even when no experiment run exists.
- Authoritative Slice-1 replay requires a real same-venue direct spot instrument for the candidate pair plus admitted historical bars for that direct instrument. Relationship/scout evidence may exist for unsupported USDT-derived crosses, but those candidates fail deep-replay setup as `unsupported_direct_market`; no USDT bridge is synthesized.
- Slice-1 historical replay establishes research economics only. Missing historical venue precision, MARKET-filter reference prices, spread/depth, and capacity remain unknown and are not invented from current state.
- Scanner historical economics use a scale-free research normalization: equal-value 50/50 starting holdings with total direct-quote value normalized to `1`, `minimum_rebalance_notional=0`, and no synthetic venue quantization unless contemporaneous evidence is actually part of the admitted direct-market contract. This normalization is research accounting, never user capital or capacity.
- The frozen Scanner-V1 historical cost reference uses the existing QAP baseline/adverse convention: ordinary `fee_bps=10`, `slippage_bps=5`; adverse `fee_bps=20`, `slippage_bps=10`. The baseline cost model drives Slice-1 economics; the adverse model is bound for robustness/provenance and Slice-2 capacity authority.
- The frozen Scanner-V1 primary simple control is `band-5pct-half`: target the starting 50/50 weights, act only when maximum weight drift exceeds `0.05`, and correct `0.5` of the drift through the same replay/cost path. Strict HODL remains separately mandatory. This avoids searching several baselines inside the scan.
- No scanner UI, scheduler, database, queue, generic strategy DSL, adaptive router, parameter optimizer, Copulas, broad momentum, automatic basket discovery, private exchange access, or live-capital authority in Slice 1.
- No external/subagent coding or review model is used for this mission.
- Work stays in `/home/hamza/repo/qap/.worktrees/qap-implementation-20260818` on branch `qap-implementation-20260818`.
- User steering gate: after this implementation plan is complete and self-reviewed, stop before any Slice-1 code changes and wait for user review.

## Resolved pre-implementation audit boundaries

The 2026-08-18 audit is closed before Slice-1 code begins. Do not reopen or duplicate its fixes inside scanner work:

- authoritative experiment integrity requires the physical file set to match `integrity.json`;
- malformed paper-operation directories are isolated invalid entries;
- autonomous Git scope checks fail closed on unexpected HEAD/branch movement;
- Slice 1 deep-replays only real direct venue markets; bridge execution is deferred to a separately approved Slice 3;
- Slices 1 and 2 are implementation-authorized, while Slice 3 remains a design gate;
- Slice-2 capacity uses the conservative policy transition/drift requirement, not `q_safe / 0.10`;
- Slice-2 friction authority comes from the frozen adverse QAP `CostModel`, with fees counted exactly once;
- unfillable required shallow-book snapshots make a tested size infeasible rather than disappearing from `C95(q)`;
- a post-registry final-OOS crash is an identifiable fail-closed safe-stop requiring operator investigation, not an automatic resume/abandon/reuse path;
- the nine obsolete Phase-10 run directories remain archived historical evidence and are intentionally unreadable by current sealed-artifact readers.

The only Slice-1 replay normalization added by this plan is the scale-free unit-value research portfolio described in Global Constraints. It exists solely so proportional historical economics do not depend on an invented user-capital number. It does not claim historical venue feasibility.

## File Structure

### Market-domain extensions

- Create `src/qap/market/lifecycle.py` — immutable historical lifecycle event model, evidence source priority, and point-in-time eligibility state derivation inputs.
- Modify `src/qap/market/__init__.py` — export lifecycle types/helpers only.
- Create `tests/unit/market/test_lifecycle.py` — event validation, rename/migration continuity, and three-state evidence examples.

### Relationship evidence

- Create `src/qap/relationship/models/rolling_residual.py` — deterministic rolling log-price OLS residual observation with refit-required reciprocity.
- Modify `src/qap/relationship/models/__init__.py` and `src/qap/relationship/__init__.py` — export the admitted residual model.
- Create `tests/unit/relationship/models/test_rolling_residual.py` — orientation/refit, sign, causality, degeneracy, and deterministic fingerprint tests.

### Scanner package

- Create `src/qap/scanner/__init__.py` — narrow public scanner API.
- Create `src/qap/scanner/protocol.py` — frozen protocol/version, horizon/resolution/template mappings, quality thresholds, promotion caps, and deterministic duration-to-bar conversion.
- Create `src/qap/scanner/models.py` — immutable current-schema scan definition, source records, evaluated series identity, pair/trial/candidate/promotion records, statuses, and canonical IDs.
- Create `src/qap/scanner/catalog.py` — explicit local scanner input catalog resolution below `--data-root`; safe relative paths, admitted Parquet identity, lifecycle evidence references, and venue-local direct-pair historical source lookup used only to determine authoritative replay eligibility.
- Create `src/qap/scanner/slices.py` — exact causal row selection, source-vs-selection fingerprinting, expected-grid coverage, missing-run metrics, and canonical row serialization.
- Create `src/qap/scanner/universe.py` — venue-local PIT USDT admission and exclusion reasons.
- Create `src/qap/scanner/graph.py` — normalized-log SSD, full valid-pair digest, deterministic `k=8` neighbor union/canonicalization, and manual-pin merge.
- Create `src/qap/scanner/trials.py` — fixed trial enumeration, orientation identity, template/window mapping, and candidate IDs.
- Create `src/qap/scanner/scout.py` — approximate two-asset holdings simulation with exact neutral/NO_ACTION/entry state semantics, next-observation action timing, turnover, one-way friction proxy, and rankable/invalid status.
- Create `src/qap/scanner/promotion.py` — deterministic ranking and fixed automatic promotion/diversity caps.
- Create `src/qap/scanner/artifacts.py` — explicit PyArrow schemas for eligibility/neighbors/scout/promotions/replay attempts, staging writes, table hashes/counts, durable attempt-state updates, resume validation, manifest reconciliation, and atomic final publication.
- Create `src/qap/scanner/run.py` — one sequential generation orchestrator from frozen definition through graph/trials/scout/promotions/authoritative replay references.
- Create `src/qap/scanner/cli.py` — required argparse operator entry point and bounded summary output.

### Authoritative experiment/replay adapter

- Create `src/qap/experiment/scanner_adapter.py` — convert one promoted immutable `ScannerCandidate` into a development-role direct-market experiment when a real same-venue candidate-pair spot instrument and admitted historical direct-market source exist; otherwise return `unsupported_direct_market` without fabricating an experiment run.
- Modify `src/qap/experiment/manifest.py` — minimally add an optional `evaluation_window` inside `data_window` plus explicit evidence-only instrument IDs. Existing manifests default to full-window evaluation and no evidence-only instruments. Evidence-only instruments may support model observations but can never be the execution instrument, numeraire, target basket member, or valuation authority.
- Modify `src/qap/experiment/data.py` — preserve exact fingerprint admission for all declared datasets while exposing deterministic instrument/source lookup for evidence-only relationship legs. Do not create a second loader.
- Modify `src/qap/experiment/model_policies.py` — admit `residual_mean_reversion` and allow scanner pair policies to name the exact two admitted evidence source instruments used for relationship computation, avoiding ambiguity when the direct execution instrument is also present.
- Modify `src/qap/experiment/runner.py` / `src/qap/execution/replay.py` only for the evaluation-start boundary needed to load causal warm-up before economic measurement begins. Do not add bridge execution, multi-fill replay, routing modes, or scanner-specific accounting.
- Modify `src/qap/experiment/__init__.py` only for the narrow scanner adapter export if a public import is needed.
- Regenerate `web/openapi.json` and `web/src/api/schema.d.ts` only if the manifest schema change is exposed through current API contracts; no scanner route is added.

### Tests and fixtures

- Create `tests/unit/scanner/test_protocol.py`
- Create `tests/unit/scanner/test_slices.py`
- Create `tests/unit/scanner/test_universe.py`
- Create `tests/unit/scanner/test_graph.py`
- Create `tests/unit/scanner/test_trials.py`
- Create `tests/unit/scanner/test_scout.py`
- Create `tests/unit/scanner/test_promotion.py`
- Create `tests/unit/scanner/test_artifacts.py`
- Create `tests/unit/scanner/test_cli.py`
- Create `tests/unit/experiment/test_scanner_adapter.py`
- Extend focused experiment/replay tests for evidence-only inputs and evaluation-window warm-up without changing direct execution behavior.
- Create `tests/scenarios/test_scanner_slice1.py` — end-to-end synthetic scanner generation through ordinary QAP deep replay and economic gates.
- Create `tests/fixtures/scanner/` — small deterministic Binance/Gate-style admitted Parquet/lifecycle/catalog/metadata fixtures only; no network dependency.

### Architecture/docs

- Modify `.importlinter` — add explicit scanner-boundary contracts: scanner may depend on relationship/market/portfolio value types but not policy/execution/evaluation/experiment; relationship/market/portfolio/policy/execution/evaluation may not import scanner; `qap.experiment.scanner_adapter` is the intentional outer adapter allowed to consume scanner candidate value objects.
- Modify `docs/plans/15-research-scanner-and-candidate-workbench.md` only to mark Slice-1 implementation status/results after verification, not to rewrite the approved design.
- Modify `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md` only if implementation evidence exposes a non-protected factual correction; do not reopen architecture.
- Add a concise Slice-1 implementation/result record under `docs/research/` after completion with performance numbers, survivor/negative outcome summary, search denominator, and known limitations.

## Task 1: Add historical lifecycle evidence and three-state eligibility primitives

**Files:**
- Create: `src/qap/market/lifecycle.py`
- Modify: `src/qap/market/__init__.py`
- Test: `tests/unit/market/test_lifecycle.py`

**Interfaces:**
- Consumes: `AssetId`, `VenueInstrument` identity, UTC timestamps.
- Produces: `InstrumentLifecycleEvent`, lifecycle event/source/confidence enums, stable event IDs, and an evidence bundle that scanner universe code can evaluate without consulting current exchange state.

**Steps:**
- [ ] Add failing examples for required event types: trading started, suspended/resumed, delisting announced/delisted, symbol renamed, token/contract migrated.
- [ ] Add validation that `effective_at` and `observed_at` are timezone-aware UTC, venue/symbol/quote/source IDs are non-empty, and the event binds a stable asset identity/version.
- [ ] Encode source priority as data/enum ordering only; do not turn it into a mutable global registry.
- [ ] Require explicit continuity mapping for rename/migration. A rename/migration event without recorded continuity cannot silently concatenate bar history under one scanner identity.
- [ ] Add examples proving absence of bars is not negative lifecycle evidence and current status is only current-state evidence.
- [ ] Run `uv run pytest -q tests/unit/market/test_lifecycle.py`.

**Acceptance criteria:** lifecycle evidence is immutable, causal, source-attributed, and sufficient for scanner code to distinguish known eligibility, known ineligibility, and unknown without reading live/current exchange state.

## Task 2: Freeze Scanner-V1 protocol, identities, local source catalog, and exact slice fingerprints

**Files:**
- Create: `src/qap/scanner/__init__.py`
- Create: `src/qap/scanner/protocol.py`
- Create: `src/qap/scanner/models.py`
- Create: `src/qap/scanner/catalog.py`
- Create: `src/qap/scanner/slices.py`
- Test: `tests/unit/scanner/test_protocol.py`
- Test: `tests/unit/scanner/test_slices.py`
- Fixture: `tests/fixtures/scanner/`

**Interfaces:**
- Consumes: admitted `ValidatedBarSeries`/Parquet artifacts, lifecycle references, the frozen protocol, `as_of`, `eligible_information_end`, and optional manual pins.
- Produces: immutable scan definition/source records and `EvaluatedSeries` records carrying both `source_artifact_fingerprint` and exact `selection_slice_fingerprint`.

**Steps:**
- [ ] Encode `scanner-v1-s1`, 365-day automatic history, project 730-day ceiling as documentation-only/non-automatic, venues Binance/Gate, quote USDT, `k=8`, replay/diversity caps, quality rules, and exact horizon mappings. For the canonical Slice-1 CLI, set `eligible_information_end = as_of`; every interval independently admits only observations complete by that shared cutoff.
- [ ] Encode short=`1h/30d` graph with model resolutions `15m,1h`; medium=`4h/90d` with `1h,4h`; swing=`1d/180d` with `4h,1d`; each horizon uses the same common scout/deep evaluation window for all templates.
- [ ] Encode fast/base/slow windows and fixed `0.5/1.5` neutral/entry bands with deterministic duration-to-bars conversion.
- [ ] Freeze `scanner-v1-historical-costs-v1` in protocol data with ordinary `CostModel(fee_bps=10, slippage_bps=5)` and adverse `CostModel(fee_bps=20, slippage_bps=10)`. Freeze `scanner-v1-band-control-v1` as one `band_partial` simple control with `band_width=0.05` and `partial_correction_fraction=0.5`, and freeze `scanner-v1-unit-value-normalization-v1` as equal-value 50/50 starting holdings with total direct-quote value `1`, zero minimum-rebalance notional, and no synthetic quantization. These are protocol constants, not CLI/search dimensions.
- [ ] Make protocol identity a canonical hash/version payload that changes if graph windows, `k`, thresholds, orientation enumeration, template windows, promotion caps, historical cost-policy reference, benchmark-control reference, research-normalization policy, or other search-bearing rules change. Define `scan_id` as a semantic hash of protocol, `as_of`/information cutoff, requested horizons/venues, frozen source/slice identities, and normalized manual inputs; exclude `created_at` and filesystem paths from semantic identity.
- [ ] Define current-schema `catalog.json` below `--data-root` with `schema_version`, one append-only lifecycle-evidence file reference, and `sources[]` records containing `dataset_id`, safe relative Parquet path, venue, venue symbol, base asset, quote asset, interval, expected semantic/source fingerprint, lifecycle evidence IDs, plus optional direct-pair dataset linkage fields used only to resolve a real venue execution instrument in Task 9. Do not require or invent historical precision/MARKET-filter metadata for Slice 1. Validate every relative path against root escape, read Parquet through existing market storage, and verify catalog identity against Parquet metadata/fingerprint rather than trusting filename text.
- [ ] Select only bars with `bar_end_exclusive <= eligible_information_end`; enforce the requested interval/instrument/venue and exact automatic lookback bounds before model computation.
- [ ] Hash canonical selected rows including venue, instrument, interval, candle open, bar end, observation-complete boundary, OHLCV/source row semantics used by current admission. Use deterministic float serialization (`float.hex`) where float bytes participate in identity.
- [ ] Add a property/regression showing appending future rows changes whole-source identity but not an older evaluated-slice fingerprint or candidate identity.
- [ ] Compute expected-grid coverage and longest missing run without forward fill/interpolation.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_protocol.py tests/unit/scanner/test_slices.py`.

**Acceptance criteria:** identical protocol + causal selected rows produce identical IDs/hashes; future-row append cannot mutate historical selection identity; no incomplete/future observation can enter hash or computation.

## Task 3: Build the official point-in-time venue-local universe

**Files:**
- Create: `src/qap/scanner/universe.py`
- Test: `tests/unit/scanner/test_universe.py`

**Interfaces:**
- Consumes: scanner source records, lifecycle event bundles, horizon graph interval/window, `eligible_information_end`.
- Produces: one `EligibleAssetRecord` per candidate asset/horizon/venue with state/reason/evidence refs, slice fingerprints, bar coverage, and longest missing run.

**Steps:**
- [ ] Implement `known_eligible`, `known_ineligible`, and `historical_eligibility_unknown` as explicit states.
- [ ] Official automatic universe admits only known-eligible USDT spot instruments whose lifecycle evidence covers the required formation/evaluation period and whose graph slice passes fixed quality rules.
- [ ] Keep Binance and Gate records/graphs separate even for the same stable `AssetId`.
- [ ] Exclude USDT as an automatic candidate base asset; keep it as the venue quote/evidence coordinate for Slice-1 discovery. Authoritative execution uses only a real direct candidate-pair market.
- [ ] Make source conflicts fail closed using the approved evidence priority; do not infer a listing date from the first available bar.
- [ ] Permit unknown eligibility only through an explicitly forensic/manual path and mark those records ineligible for official automatic scoreboards. Derive a deterministic `universe_snapshot_id` from the canonically ordered venue/horizon admission records, lifecycle evidence refs, and exact slice identities.
- [ ] Add tests for current-survivor metadata failing to establish historical eligibility, suspension windows, delisting, rename/migration discontinuity, and identical asset names on two venues remaining distinct universe entries.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_universe.py`.

**Acceptance criteria:** official automatic graphs cannot contain unknown/ineligible assets or cross-venue edges; every exclusion is explicit and attributable.

## Task 4: Implement the single normalized-log SSD candidate graph and manual-pin merge

**Files:**
- Create: `src/qap/scanner/graph.py`
- Test: `tests/unit/scanner/test_graph.py`

**Interfaces:**
- Consumes: one official venue/horizon eligible universe and its graph-interval evaluated slices; optional validated same-venue manual pins.
- Produces: deterministic valid-pair comparison digest and retained `NeighborRecord` set with ranks/selection flags/pin lineage.

**Steps:**
- [ ] Reindex each graph series to the expected timestamp grid without filling missing values; require asset coverage >=95%, pair common coverage >=95%, longest missing run <=2 graph bars, and positive finite closes.
- [ ] Compute `x_i(t)=log(P_i(t))-log(P_i(t0))` and mean squared path distance over common valid bars.
- [ ] Exclude invalid/insufficient pair comparisons rather than assigning sentinel distances.
- [ ] For every eligible asset rank peers by `(distance, canonical_pair_id)`, retain nearest `k=8`, union directed choices, canonicalize to one unordered `PairId`, and deduplicate.
- [ ] Compute `distance_digest` as SHA-256 over canonically sorted `(venue,horizon,pair_id,float.hex(distance))` for every valid comparison, not only retained edges.
- [ ] Merge same-venue manual pins after admission. A pin bypasses only the `k=8` cutoff; it must still pass identity/PIT/data-quality rules.
- [ ] Preserve both `automatic_neighbor_selected` and `manual_pinned` when automatic and manual selection overlap; emit one semantic pair record.
- [ ] Add Hypothesis/property coverage for SSD symmetry and invariance to multiplying either raw price path by a positive constant, plus deterministic tie handling.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_graph.py`.

**Acceptance criteria:** graph generation is deterministic and bounded; no cross-venue or duplicate semantic pair can appear; a manual pin cannot erase or impersonate automatic lineage.

## Task 5: Add the residual-MR relationship model and freeze trial enumeration/orientation semantics

**Files:**
- Create: `src/qap/relationship/models/rolling_residual.py`
- Modify: `src/qap/relationship/models/__init__.py`
- Modify: `src/qap/relationship/__init__.py`
- Create: `src/qap/scanner/trials.py`
- Test: `tests/unit/relationship/models/test_rolling_residual.py`
- Test: `tests/unit/scanner/test_trials.py`

**Interfaces:**
- Consumes: aligned completed A/USDT and B/USDT bars, `PairOrientation`, source fingerprints, fixed template bars.
- Produces: causal residual observations with `fit_reciprocity=refit_required`, `evidence_reciprocity=model_specific`, and deterministic fixed scanner trial identities.

**Steps:**
- [ ] Implement deterministic OLS using NumPy linear-algebra primitives over `log(P_numerator/USDT) = alpha + beta*log(P_denominator/USDT) + residual`; do not implement a generic regression framework.
- [ ] For each observation boundary use only fully completed common bars inside the declared rolling window; standardize the latest residual over that same fit window.
- [ ] For every retained pair/resolution/template, resolve the exact model-resolution A/USDT and B/USDT slices separately from the graph slice, enforce >=95% required warm-up/common coverage with no interpolation, and bind those model-resolution selection fingerprints into the trial/candidate identity.
- [ ] Return insufficient-history/variance rather than fabricating a score when the fit or residual scale is degenerate/non-finite.
- [ ] Persist deterministic model input fingerprint from orientation, timestamps, exact selected source fingerprints, and float-hex values used by the fit.
- [ ] Verify reversing residual orientation performs a fresh fit and may yield a materially different score; never derive it by negation.
- [ ] Reuse existing `rolling_log_ratio_observation` for log-ratio MR. Verify inverse orientation is an exact score negation/semantic transform and enumerate only the canonical log-ratio orientation as one trial.
- [ ] Enumerate, per retained pair, every allowed resolution x family x fast/base/slow template; residual produces both orientations, log-ratio one canonical orientation.
- [ ] Candidate/trial ID binds scan/protocol, venue, pair, orientation, horizon, resolution, model family/template, model parameters, source/slice fingerprints, and lineage facts; creation timestamp must not affect semantic ID.
- [ ] Verify preference sign is `-z` for both families and distinguish venue quote USDT from relationship numerator/denominator terminology.
- [ ] Run `uv run pytest -q tests/unit/relationship/models/test_rolling_residual.py tests/unit/scanner/test_trials.py`.

**Acceptance criteria:** model/orientation semantics match the approved design exactly; residual orientations are independent trials; log-ratio reciprocity is exact-transform; no arbitrary lexical orientation is presented as model truth.

## Task 6: Implement the non-authoritative scout with exact policy-state parity

**Files:**
- Create: `src/qap/scanner/scout.py`
- Test: `tests/unit/scanner/test_scout.py`

**Interfaces:**
- Consumes: one fixed trial, causal model observations, common evaluation start/end, two admitted asset price paths, and a declared QAP cost-policy reference reduced to a documented one-way friction proxy.
- Produces: `ScoutTrialRecord` with status/failure reason, `scout_relative_wealth_proxy`, turnover proxy, signal count, and lineage.

**Steps:**
- [ ] Start synthetic holdings as same-value 50/50 quantities at the common evaluation boundary and construct passive comparison from those same starting quantities.
- [ ] On `|z| <= 0.5`, emit neutral 50/50 target; on `0.5 < |z| < 1.5`, emit NO_ACTION and leave quantities unchanged while weights drift; on entry extremes, target 60/40 or 40/60 according to `preference_score=-z`.
- [ ] Make each decision causal: evidence from a completed observation can affect only the next observation rebalance approximation; it cannot earn the bar that produced the signal.
- [ ] Rebalance approximate float quantities only when a target exists. Define scout one-way turnover as `0.5 * sum(abs(target_weight - pretrade_weight))`; define the one-way friction rate directly from the referenced QAP cost policy as `(fee_bps + slippage_bps) / 10_000`; subtract `pretrade_proxy_wealth * turnover * friction_rate` exactly once per approximate rebalance. This is a ranking proxy only and must not model precision, minimums, bridge routes, fee assets, or fills.
- [ ] Score all templates for one horizon over the identical declared evaluation start/end; earlier data is warm-up only.
- [ ] Mark insufficient warm-up/common observations, non-finite evidence, zero active signals, impossible causal target path, or non-finite proxy wealth invalid/unrankable.
- [ ] Keep finite negative proxy results valid/rankable.
- [ ] Add a parity test that feeds representative scores/current holdings through both scout state mapping and the existing `EvidenceTiltPolicy` contract and compares target/no-action semantics without importing policy from production scanner code (test-only comparison is allowed).
- [ ] Add a regression where NO_ACTION between two targets preserves quantities and therefore produces drifted weights, not a hidden reset to 50/50.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_scout.py`.

**Acceptance criteria:** the scout is explicitly approximate, causal, and stateful; it never becomes a fill/accounting engine; negative valid proxies remain eligible for ranking.

## Task 7: Apply the frozen promotion policy and deterministic automatic replay budget

**Files:**
- Create: `src/qap/scanner/promotion.py`
- Test: `tests/unit/scanner/test_promotion.py`

**Interfaces:**
- Consumes: all valid automatic scout trials for one horizon plus manual replay requests.
- Produces: deterministic automatic promotion decisions/ranks/reasons and separate manual promotion lineage.

**Steps:**
- [ ] Sort automatic valid trials by descending proxy, ascending turnover, then canonical venue/pair/model/orientation/resolution/template ID.
- [ ] Greedily admit at most 10 automatic promotions per horizon, at most 2 promoted trials involving one asset per horizon, and at most 1 promoted trial per unordered pair/model family per horizon.
- [ ] Record every valid but non-promoted trial with a precise budget/diversity exclusion reason.
- [ ] Ensure both residual orientations compete for the same pair/family slot and only the higher-ranked one can consume that slot.
- [ ] Deep-replay the highest-ranked valid trial even when all valid proxies are negative; replay fewer than ten if diversity/validity leaves fewer candidates and never create filler trials.
- [ ] Keep manual deep-replay requests outside the automatic 10/horizon denominator while preserving whether the underlying semantic trial also appeared automatically.
- [ ] Add deterministic tie/cap tests and a negative-all-candidates scenario.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_promotion.py`.

**Acceptance criteria:** automatic deep-replay count is bounded independently of universe size and search ranking never uses a positive-zero gate.

## Task 8: Persist recoverable scan generations and complete search denominator atomically

**Files:**
- Create: `src/qap/scanner/artifacts.py`
- Test: `tests/unit/scanner/test_artifacts.py`

**Interfaces:**
- Consumes: frozen definition and completed eligible-assets/neighbors/scout/promotions records plus deterministic replay-attempt transitions.
- Produces: `runs/scans/<scan_id>.partial/` during execution and an atomically renamed `runs/scans/<scan_id>/` only after final reconciliation.

**Steps:**
- [ ] Write immutable `definition.json` first with protocol, `as_of`, information cutoff, venues/horizons, source/slice fingerprints, cost policy reference, manual pins/forensic mode, and semantic scan ID.
- [ ] Define explicit versioned PyArrow schemas for `eligible_assets.parquet`, `neighbors.parquet`, `scout_trials.parquet`, `promotions.parquet`, and `replay_attempts.parquet` matching the approved minimum fields; store strings for exact IDs/statuses and float columns only for explicitly approximate scanner metrics.
- [ ] Write each table atomically within staging; compute deterministic semantic/table hashes and record row counts. For every promoted candidate, persist an `enumerated` replay-attempt row before experiment preparation begins; later update that same deterministic attempt to `setup_failed`, `replay_failed`, or `completed`.
- [ ] Write `manifest.json` last inside staging with all counts/hashes, protocol identity, replay-attempt reconciliation, and referenced authoritative QAP run IDs/statuses.
- [ ] Before final rename, re-read staged definition/tables/manifest and reconcile counts, hashes, IDs, frozen source/slice fingerprints, and exactly one replay-attempt row for every promoted deep-replay request, including setup failures with no run ID.
- [ ] Resume an existing `.partial` only when the requested semantic scan definition, frozen source-artifact fingerprints, and frozen selection-slice fingerprints all match exactly; otherwise abort rather than mutating the old generation. A future-row append may leave an old completed candidate identity unchanged when its evaluated slice is unchanged, but it must still invalidate resume of a partial generation whose frozen whole-source identity changed.
- [ ] Treat a final directory with valid manifest as immutable completed evidence; reject duplicate final publication/collision.
- [ ] Test interrupted writes, mismatched future-appended source artifacts with unchanged slice vs genuinely changed slice, malformed definitions, deterministic ID collision, and no completed-evidence discovery from `.partial`.
- [ ] Run `uv run pytest -q tests/unit/scanner/test_artifacts.py`.

**Acceptance criteria:** a scan is either recoverable-incomplete or atomically complete; partial artifacts can never masquerade as completed research evidence.

## Task 9: Adapt promoted candidates into authoritative direct-market QAP replay

**Files:**
- Create: `src/qap/experiment/scanner_adapter.py`
- Modify: `src/qap/experiment/manifest.py`
- Modify: `src/qap/experiment/data.py`
- Modify: `src/qap/experiment/model_policies.py`
- Modify: `src/qap/experiment/runner.py`
- Modify: `src/qap/execution/replay.py` only for the shared evaluation-start boundary if needed.
- Modify: `src/qap/experiment/__init__.py` if needed.
- Test: `tests/unit/experiment/test_scanner_adapter.py`
- Test: focused existing experiment/replay/model-policy tests affected by evidence-only inputs/evaluation windows.
- Regenerate: `web/openapi.json`, `web/src/api/schema.d.ts` only if the manifest schema exported by OpenAPI changes.

**Interfaces:**
- Consumes: one promoted `ScannerCandidate`, its exact admitted relationship slices, the frozen ScannerProtocol historical cost/control/normalization references, and scanner catalog lookup for a same-venue direct pair instrument/dataset.
- Produces: either `(deep_replay_run_id, completed/economic-gate status)` from an ordinary development QAP run, or a fail-closed setup result such as `unsupported_direct_market`; scanner artifacts never copy financial truth.

**Steps:**
- [ ] Add RED adapter tests for both paths: a real `A/B` direct venue market proceeds to manifest preparation; an `A/B` candidate represented only by `A/USDT` + `B/USDT` records `unsupported_direct_market` and produces no experiment run or bridge route.
- [ ] Resolve the direct execution instrument by exact venue + unordered candidate assets + historical interval/window. Accept either venue orientation (`A/B` or `B/A`) but record the exact `direct_execution_instrument_id`; require admitted historical bars covering warm-up/evaluation needs. Never synthesize a cross from USDT legs.
- [ ] Extend `ExperimentManifest` with `evaluation_window` and a narrow `evidence_instrument_ids` declaration. Keep existing manifests unchanged by default. Evidence-only instruments may contain the USDT relationship legs but are prohibited from being the execution instrument, numeraire, target basket, external-flow asset, or valuation authority.
- [ ] Update manifest validation so the economic basket remains exactly the two candidate assets and the direct execution instrument's base/quote are exactly those assets. Permit explicitly declared evidence-only instruments to reference a third quote coordinate such as USDT without making that coordinate owned inventory.
- [ ] Update experiment data/model-policy composition so scanner relationship configs name the exact two evidence instruments. Compute log-ratio/residual evidence from those admitted legs, while the direct `A/B` venue series alone supplies execution reference/valuation in the existing replay. Reject ambiguous/missing evidence source IDs.
- [ ] Add `residual_mean_reversion` composition using the new relationship residual observation and existing `EvidenceTiltPolicy`; keep log-ratio MR on the existing relationship implementation. Both use the candidate's frozen orientation/template and the same 50/50 neutral +/-0.10 target semantics as the scout.
- [ ] Add `evaluation_window` as a strict subwindow of `data_window`. Warm-up rows may affect the first model observation but strategy/HODL/control economic measurement and decisions begin exactly at `evaluation_window.start`. Add a regression proving warm-up changes the first evidence score without changing starting wealth or matched evaluation duration.
- [ ] Use the frozen scale-free research normalization: at evaluation start, value the direct pair in the direct execution quote asset and derive exact equal-value starting quantities whose total quote value is `1`. Set historical research `minimum_rebalance_notional=0` and no synthetic base-step quantization unless contemporaneous admitted precision evidence exists. Bind normalization policy ID and resulting quantities into the experiment commitment; never label this as user capital or capacity.
- [ ] Bind the frozen `scanner-v1-historical-costs-v1` baseline/adverse costs (`10/5` bps ordinary; `20/10` bps adverse) and the single predeclared `band-5pct-half` control (`band_width=0.05`, `partial_correction_fraction=0.5`). Strict HODL remains mandatory; the scanner does not search alternative controls.
- [ ] Build candidate manifests with `data_role=development`, full causal warm-up `data_window`, exact common `evaluation_window`, relationship evidence source fingerprints, direct execution dataset fingerprint, `50/50` starting target, QAP cost model, strict HODL, and the frozen band control as primary incremental benchmark.
- [ ] Prevent scanner adapter creation of `final_oos` manifests or any run whose evidence/execution window exceeds the candidate's frozen information/evaluation boundary.
- [ ] Before any adapter/data/manifest operation, require the scanner artifact layer to have durably persisted the deterministic replay attempt as `enumerated`. Convert missing direct market/data or manifest/data admission failures to `setup_failed`; execution failures become `replay_failed`; successful ordinary QAP artifact publication becomes `completed`.
- [ ] Execute eligible candidates through `run_experiment_to_artifacts`; scanner retains only immutable run ID/status references. Do not add bridge routing, multi-fill replay, scanner fills, copied wealth fields, or historical capacity/venue-feasibility claims.
- [ ] Classify `deep_replay_survivor` only when terminal strategy wealth is strictly greater than matched HODL and strictly greater than the frozen `band-5pct-half` control after baseline costs. Preserve adverse-cost results as robustness evidence without silently changing the survivor rule.
- [ ] Add architecture tests proving `qap.scanner` never imports experiment/execution/policy/evaluation and proving experiment's scanner adapter is the only allowed outer dependency on scanner value objects.
- [ ] Run `uv run pytest -q tests/unit/experiment/test_scanner_adapter.py` plus focused manifest/data/model-policy/replay tests and API contract generation checks if the schema is visible.

**Acceptance criteria:** every authoritative Slice-1 survivor comes from the ordinary direct-market QAP replay/ledger/evaluation path; unsupported crosses remain durably counted research attempts and are never bridged; evidence-only USDT legs cannot become inventory/execution state; historical economics are scale-free research comparisons and make no capacity claim.

## Task 10: Assemble one deterministic sequential scan orchestrator and CLI

**Files:**
- Create: `src/qap/scanner/run.py`
- Create: `src/qap/scanner/cli.py`
- Modify: `src/qap/scanner/__init__.py`
- Test: `tests/unit/scanner/test_cli.py`
- Scenario: `tests/scenarios/test_scanner_slice1.py`

**Interfaces:**
- Consumes: CLI `--as-of`, `--horizon`, `--data-root`, `--run-root`, optional `--pins-file`; explicit local scanner catalog/lifecycle/metadata inputs.
- Produces: completed/recoverable scan generation and bounded human-readable summary.

**Steps:**
- [ ] Parse only the approved arguments and require `--as-of` timezone-aware UTC; `--horizon` is one of short/medium/swing/all.
- [ ] Parse `--pins-file` as current-schema JSON with `schema_version` and `pins[]`; each pin declares venue, unordered asset pair, requested horizon(s), and `forensic` boolean. Reject cross-venue pins and duplicate normalized pins. Freeze the normalized pins/forensic requests into the definition before any search-bearing work.
- [ ] For each requested horizon and each venue, build PIT universe -> SSD graph -> fixed trials -> scout records -> promotion decisions sequentially from the frozen definition.
- [ ] Execute at most the selected automatic authoritative candidates and any explicitly requested manual deep replays through `qap.experiment.scanner_adapter`; every selected deep-replay request is first durably enumerated in `replay_attempts.parquet`; unsupported direct markets and other candidate-specific setup/replay failures are recorded and do not abort unrelated candidates.
- [ ] Abort generation on frozen input/slice mismatch, malformed protocol/definition, non-reproducible PIT snapshot, ID collision, or artifact reconciliation failure.
- [ ] Publish final scan only after all requested venues/horizons and replay references reconcile.
- [ ] Print admitted/excluded counts by venue/horizon, retained edges, enumerated/valid/invalid trials, automatic promotions/budget exclusions, replay survivors/failures, scan ID, and artifact path. Do not print success language for the scout proxy.
- [ ] Add a synthetic end-to-end scenario proving official PIT universe -> expected graph -> both family/orientation trial set -> deterministic approximate ranking -> <=10 promotions/horizon -> ordinary QAP replay -> HODL/simple-control gate.
- [ ] Add a negative scenario where an attractive scout fails authoritative replay and another negative scout is still replayed because it ranks inside budget.
- [ ] Add a direct-market boundary scenario: one promoted pair with admitted direct `A/B` bars completes ordinary QAP replay; one promoted USDT-derived cross with no direct pair bars becomes a durable `unsupported_direct_market` setup failure, and neither changes the automatic promotion denominator.
- [ ] Run `uv run pytest -q tests/unit/scanner tests/unit/experiment/test_scanner_adapter.py tests/scenarios/test_scanner_slice1.py`.

**Acceptance criteria:** `python -m qap.scanner.cli ...` produces the same logical candidate/ranking set for identical frozen inputs and never exceeds the fixed authoritative replay budget.

## Task 11: Lock architecture, research-integrity, and search-denominator contracts

**Files:**
- Modify: `.importlinter`
- Add/extend: scanner architecture/integrity tests under `tests/unit/scanner/` and `tests/scenarios/test_scanner_slice1.py`.

**Interfaces:**
- Consumes: completed Slice-1 implementation.
- Produces: executable guards against scanner ownership drift and research-label leakage.

**Steps:**
- [ ] Keep `qap.scanner` as research orchestration outside the financial kernel. Add explicit import-linter contracts: scanner may depend on relationship/market/portfolio value types but not policy/execution/evaluation/experiment; relationship/market/portfolio/policy/execution/evaluation may not depend on scanner; `qap.experiment.scanner_adapter` is the intentional outer adapter allowed to consume scanner candidate value objects. Do not rely on a simple layer ordering that would accidentally permit policy/execution to import scanner.
- [ ] Prove current survivor/current exchange state cannot backfill historical eligibility.
- [ ] Prove unknown eligibility cannot enter an official automatic scan.
- [ ] Prove changing any search-bearing frozen rule changes protocol identity and therefore candidate/scan identity.
- [ ] Prove source future-row append cannot mutate old slice/candidate identity.
- [ ] Prove manual pins cannot masquerade as automatic discovery or duplicate semantic trial IDs.
- [ ] Prove final-OOS rows/role cannot enter scanner warm-up/replay.
- [ ] Prove every enumerated loser/invalid trial remains in `scout_trials.parquet` so the automatic denominator is reconstructible.
- [ ] Prove completed scanner tables contain QAP run IDs/statuses but not copied terminal wealth/accounting fields.
- [ ] Prove every promoted candidate has a replay-attempt row before adapter preparation and that `unsupported_direct_market` remains a counted `setup_failed` attempt with no fabricated run ID.
- [ ] Prove relationship evidence-only instruments cannot become execution/valuation/inventory assets and no Slice-1 code path invokes Phase-11 bridge routing.
- [ ] Run `uv run lint-imports` and the focused research-integrity scenario tests.

**Acceptance criteria:** package imports and persisted artifacts enforce that scanner is a bounded search/orchestration layer, not an alternative economic authority.

## Task 12: Benchmark realistic scanner sizes and optimize only measured bottlenecks

**Files:**
- Create: `scripts/benchmark_scanner_slice1.py`
- Modify production scanner code only if benchmark evidence justifies it.
- Document results in the Slice-1 result record.

**Interfaces:**
- Consumes: deterministic synthetic/admitted-like 500-asset and 1,000-asset data matrices for the frozen horizon shapes.
- Produces: timing/memory counts for source slicing, SSD matrix/digest, retained graph, trial enumeration, and scout work; no performance claim about authoritative replay beyond its fixed <=30 all-horizon cap.

**Steps:**
- [ ] Generate deterministic benchmark inputs without network I/O and without changing scanner semantics.
- [ ] Measure 500 and 1,000 assets for the cheap SSD stage and bounded post-graph scout stage separately.
- [ ] Confirm work shape is consistent with one O(N^2*T) distance stage and O(N*k*fixed-trials) post-graph work; confirm automatic deep replay count is <=30 for all horizons combined regardless of N.
- [ ] If NumPy/PyArrow performance is adequate for local research use, add no dependency.
- [ ] If a measured bottleneck is material, compare the smallest Polars or DuckDB substitution that deletes custom work; admit it only with a dependency-boundary note and focused parity test. Do not add distributed compute or a generic acceleration layer.
- [ ] Keep benchmark artifacts out of tracked runtime data; persist only concise reproducible commands/results.

**Acceptance criteria:** implementation has evidence for the required 500/1,000-asset workload and no speculative performance framework is introduced.

## Task 13: Run Slice-1 integrated verification, self-review, documentation, and coherent commit

**Files:**
- Modify: `docs/plans/15-research-scanner-and-candidate-workbench.md` status/checklist with actual verified results.
- Create: `docs/research/2026-08-18-qap-scanner-slice1-results.md` with exact commands, synthetic/real-data scope, scout/promotion/replay-attempt denominator counts, survivor/setup-failure/negative outcomes, benchmark results, limitations, and explicit searched-development label.
- Modify: `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md` only if a factual implementation correction is required and does not change protected design.

**Interfaces:**
- Produces: a verified, reviewable Slice-1 checkpoint suitable for writing/executing the already-authorized Slice-2 implementation plan after Slice 1 is green; no second authorization is required unless a new protected decision appears.

**Steps:**
- [ ] Run focused scanner/relationship/experiment/execution tests first and repair all failures.
- [ ] Run full Python gate: `uv run pytest -q`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run pyright src tests scripts`, `uv run python scripts/check_source_size.py`, `uv run lint-imports`.
- [ ] If OpenAPI-visible manifest schema changed, run `uv run python scripts/export_openapi.py --output web/openapi.json`, `cd web && pnpm generate:api`, then frontend typecheck/tests/build and ensure no unrelated UI behavior changed.
- [ ] Run the Slice-1 CLI twice against identical deterministic fixtures in separate run roots and compare semantic definitions/tables/rankings while ignoring only explicitly non-semantic creation timestamps/paths.
- [ ] Inspect `git diff --check`, source-size warnings, import direction, and actual diff for accidental Slice-2/3/live/UI scope.
- [ ] Perform a fresh inline self-review against every Slice-1 design acceptance bullet, including exact slice identity, residual orientation, NO_ACTION quantities, negative promotion, caps, partial recovery, QAP authority, HODL/control gates, and searched-development labeling.
- [ ] Record honest negative/no-survivor results if that is what the authoritative replay produces; do not relax controls to make a winner.
- [ ] Update the durable Recovery Capsule with verified HEAD/checks/results and commit one or more coherent Slice-1 changes only after fresh verification is green.

**Acceptance criteria:** all approved Slice-1 acceptance contracts are proven by repository evidence; documentation states what was actually tested and found; Git state is understood; no Slice-2/3 implementation or live authority was introduced.

## Verification Matrix

| Risk / contract | Primary verification | Why this level is needed |
|---|---|---|
| Future/incomplete bars enter search | `test_slices.py`, `test_universe.py` | Pure causal selection invariant; unit/property tests give precise counterexamples. |
| Source append mutates old candidate identity | Hypothesis/regression in `test_slices.py` | Broad invariant over serialization/window boundaries. |
| PIT eligibility backfilled from current state | `test_universe.py` + scenario | Research-integrity boundary, not a UI concern. |
| Cross-venue pair leakage | `test_graph.py` | Deterministic graph invariant. |
| SSD math/ties/scale | property tests in `test_graph.py` | Invariant-heavy numerical transform benefits from generated inputs. |
| Residual orientation incorrectly negated | `test_rolling_residual.py` | Model semantic unit contract. |
| Log-ratio reciprocal semantics drift | existing rolling-log-ratio tests + `test_trials.py` | Reuse existing relationship evidence plus scanner enumeration proof. |
| Scout silently resets during NO_ACTION | `test_scout.py` | Stateful regression with hand-checkable holdings path. |
| Negative valid trial excluded | `test_promotion.py` | Frozen selection-policy regression. |
| 10/horizon or diversity caps exceeded | `test_promotion.py` + end-to-end scenario | Local algorithm plus integrated budget proof. |
| Manual/automatic duplicate candidate | `test_graph.py`, `test_trials.py` | Identity + lineage boundary. |
| Partial scan treated as complete | `test_artifacts.py` | Persistence/recovery contract. |
| Scanner becomes second backtester | `.importlinter`, artifact assertions, adapter scenario | Static dependency guard plus runtime evidence ownership. |
| Unsupported cross silently bridged | `test_scanner_adapter.py` + architecture grep/import tests | Slice 1 must require a real direct pair market and never invoke Phase-11 bridge routing. |
| Evidence-only USDT leg leaks into inventory/valuation | manifest/data/adapter regressions | Relationship evidence may use a third coordinate without making it economic state. |
| Replay attempt disappears before manifest creation | `test_artifacts.py` + adapter scenario | Every promoted attempt is durable before setup can fail. |
| Warm-up leaks into economic evaluation | experiment/scanner adapter regression | Must prove earlier rows affect evidence only, not starting wealth or benchmark period. |
| Candidate bypasses HODL/control gate | scanner end-to-end scenario | Must prove ordinary QAP benchmark roles are authoritative. |
| Research normalization changes silently | scanner adapter identity tests | Unit-value normalization is frozen/versioned and must remain separate from capital/capacity claims. |
| Final OOS consumed by scan | adapter/integrity tests | Protected data-role boundary. |
| Performance becomes unbounded after SSD | benchmark script + promotion-count assertions | Measures the only credible scale risk without speculative optimization. |

## Explicit Deferrals to Slice 2 or Later

- Prospective freeze/cohort/checkpoint registry.
- Forward scanner scoreboards.
- L1/book-ticker/shallow-depth capture and liquidity/capacity tiers.
- Historical/current capacity claims.
- Asset-native momentum.
- Manual 3–6 asset basket resolver.
- Scanner API/workbench/UI.
- Scheduler/platform/queue/database.
- Formal SPA/Reality Check/Romano-Wolf/DSR/PBO promotion gates.
- Copulas, alternate pair generators, adaptive diagnostics, Bayesian/continuous optimization, learned reliability weights, automatic portfolio discovery, or live trading.

## Slice-1 Completion Gate

Slice 1 is complete only when all of the following are freshly verified:

- official three-state PIT admission fails closed and keeps Binance/Gate graphs separate;
- exact evaluated-slice identity is stable under future-row append;
- one normalized-log SSD generator with deterministic `k=8` neighbor union produces bounded pairs;
- fixed ratio/residual trial enumeration implements exact-transform vs refit orientation semantics correctly;
- scout state transitions are causal and match neutral/NO_ACTION/entry behavior while preserving quantities through NO_ACTION;
- all valid negative/positive trials remain in the denominator and negative valid trials can be promoted;
- automatic authoritative replays cannot exceed 10 per horizon and obey per-asset/pair-family caps;
- the scale-free unit-value historical research normalization is frozen/versioned and never presented as actual user capital or capacity;
- warm-up rows influence evidence only; all candidates in one horizon measure strategy/HODL/control economics over the identical common evaluation window;
- every promoted candidate replays through ordinary QAP inventory/execution/evaluation with mandatory HODL + strongest simple-control gates;
- lack of a real direct same-venue pair market/historical direct dataset yields a counted `unsupported_direct_market` setup failure; missing historical precision/depth remains unknown and is never backfilled from present-day assumptions;
- every promoted candidate has a durable replay-attempt row before experiment setup and publication reconciles promotions against attempts;
- scan staging/resume/final publication is deterministic and atomic;
- manual pins preserve complete lineage without duplicate semantic candidates;
- same-sample results are explicitly searched development evidence, never prospective/final-OOS alpha;
- 500/1,000-asset performance is measured and no unearned infrastructure/dependency is introduced;
- full Python/architecture/source-size verification is green and any OpenAPI-visible manifest delta is regenerated/checked;
- Slice 2/3, scanner UI, private exchange actions, and live-capital authority remain absent.
