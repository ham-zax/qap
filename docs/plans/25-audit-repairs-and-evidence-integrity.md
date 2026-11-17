# Plan 25 — Audit repairs and evidence integrity

Date: 2026-11-16.
Status: ready for the current editing AI after its existing task.
Execution owner: the AI that completes the current terminal/strategy integration.

Update context — 2026-11-16
Trigger: Hamza requests an executable handoff for the audit recommendations.
Purpose: repair execution and evidence defects before further strategy expansion.
Impact: schedules the repairs below. Economic objectives and capital authority remain unchanged.
Evidence: [audit](../research/2026-11-16-audit/README.md), [offline probes](../research/2026-11-16-audit/probes.py), and [recorded results](../research/2026-11-16-audit/probe-results.json).

## Start here

Finish your current task first. Preserve its source, UI, tests, and integration decisions.
Then read this plan and claim `AR-0` in [TASKS.md](../../TASKS.md).
Execute `AR-0` through `AR-8` in order. Update the same task rows after each slice.
Do not start another worker for this handoff unless the current execution workflow requires one.

Suggested continuation instruction:

> After completing your current task, execute Plan 25 in docs/plans/25-audit-repairs-and-evidence-integrity.md.
> Reproduce the findings against your completed baseline. Preserve your existing work and historical research artifacts.
> Complete the ordered repairs and checks. Keep economic rules unchanged except for the explicitly specified numerical-resolution repair.
> Record unresolved research-policy decisions. Do not replace them with guessed thresholds or claim those decisions are complete.

The audit summary overemphasized copulas. This repair sequence covers the complete evidence pipeline.
The broader audit remains queued in the final section. Copula research is one part of that work.

## Scope, authority, and boundaries

Required outcomes:

1. Paper signals use the same completed-candle clock as historical replay.
2. Partial rotations recover without losing actual inventory or recording false completion.
3. Every product paper fill uses observed venue constraints.
4. Fill timestamps describe the books and execution that support them.
5. Statistical testing has sufficient numerical resolution for its declared correction structure.
6. Measurements and charts identify their actual variables and executed signal path.
7. Historical reports retain their evidence and receive explicit corrections where needed.
8. API, CLI, and web users receive consistent results and recovery states.

Preserve `PortfolioState` and `PortfolioLedger` as the inventory owners.
Preserve matched HODL, the declared simple-control selection rule, costs, next-open historical fills, and the tuning cost gate.
Preserve spot-only owned inventory, existing admissible assets, immutable artifacts, and consumed-holdout discipline.
Do not place live orders, consume `final_oos`, run a strategy search, or promote a candidate during these repairs.
Do not relax significance, trade counts, fold requirements, cost coverage, or the cost-budget multiple to make a result pass.

Hamza authorizes the recommended repairs. Routine implementation does not require another permission question.
Changes to benchmark definitions, cost formulas, historical fill semantics, universe eligibility, or holdout roles need a separate explicit decision.
Changes to model-admission thresholds and the experiment-wide correction structure belong to `RD-1`, below.

Change necessity: documentation alone cannot repair the reproduced execution and numerical-resolution defects.
The minimum code boundary is the existing paper manager, execution helpers, proof calculation, and their shared interface projections.
No second accounting engine, strategy engine, exchange adapter, or trial registry is needed.

TDD Route: mode `off`, decision `skipped`, authority: no explicit test-first request.
Use the existing reproductions and meaningful regression tests. Strict RED/GREEN sequencing is not required.
Never weaken or delete laws in `tests/invariants/test_quant_compiler_laws.py`.

## Baseline and implementation rules

Audit baseline: `5dbcdbdbbe75a9127966235f91abd3affe1f7163`.
The audit saw concurrent edits after its nine-gate check. That check does not certify your completed task.
Use your completed task's current source as the implementation baseline. Do not restore the audit revision over newer source.
During plan preparation, the editor committed `2667425` for benchmark, marker, comparison-label, and strategy-registry repairs.
Reconcile that commit and any later work in AR-0. A commit alone does not prove that the current editing task is complete.

Read these before changing the relevant owner:

- [Phase 21](21-pair-mvp-fundamentals-and-l2-paper-plan.md), the current task checkpoint, and repository AGENTS.md.
- [Document update method](../research/document-update-method.md) before changing historical interpretations or plans.
- `src/qap/experiment/live_paper_runner.py`, `live_paper_execution.py`, and `live_paper_state.py`.
- `src/qap/execution/l2_book_fill.py`, `src/qap/api/routes/live_paper.py`, and `src/qap/lab_cli_paper.py`.
- `src/qap/product_lab_inputs.py`, `product_lab_metadata.py`, `product_lab_study.py`, and `product_lab_store.py`.
- `src/qap/experiment/lab_proof.py`, `src/qap/policy/lab_signals.py`, and the current strategy registry.
- `src/qap/relationship/lab_copula.py`, `lab_features.py`, and `pair_measurements.py`.

Facts that constrain the design:

- The API currently imports CLI warmup logic. Replace that responsibility with one shared product-level resolver.
- `load_lab_inputs` resolves immutable datasets and observed metadata. Reuse those owners.
- Paper state currently stores untimed close arrays and a 1,999-observation cap.
- Recomputing a model after shifting its history origin can shift copula refit blocks and Kalman state.
- The manager marks a preference after any fill, even if the second leg fails.
- The normal step API supplies no venue metadata.
- Nominal fill timestamps currently precede some supporting book receipts.
- `corrected_spa` uses 499 replicates. S4-A's recorded trial multipliers are 3, 6, 9, and 12.
- The advisor and analysis use descriptive measurements that need not describe the traded residual.

The code graph transport failed during plan preparation. Known-file source reads support this plan.
Refresh the graph when available. Use source reads when coverage is unavailable or stale.

Keep hand-written files below 500 lines where possible. The paper manager and execution helper already approach that limit.
Put candle validation in a focused helper. Keep file I/O, policy decisions, and fill mechanics separate.
If additional decomposition is necessary, name its responsibility and consumers before creating a file.
Do not move every helper into a new mixed-purpose module to satisfy a line count.

## AR-0 — Establish the completed baseline

Dependencies: current editing task completed or explicitly handed off.
Files: TASKS.md and the completion evidence note for this plan.

1. Record HEAD, dirty paths, current task status, and the current strategy registry location.
2. Attribute existing edits. Do not stage, revert, or overwrite another task's files as part of this slice.
3. Read the audit and run its offline probes into a new temporary output file.
4. Classify each finding as reproduced, already repaired with evidence, or changed and needing a new reproduction.
5. Preserve the original probe output as historical evidence. Its numeric values are not permanent acceptance targets.
6. Record the implementation baseline and any changed owner paths in the completion note.

Check: the probe script exits successfully and creates only temporary fixture sessions.
Do not run a live paper session or network benchmark during this slice.

## AR-1 — Use timestamped completed candles in paper sessions

Dependencies: AR-0.
Owners: existing paper manager and state helpers.
Edit: `live_paper_runner.py`, `live_paper_state.py`, `lab_cli_paper.py`, and `api/routes/live_paper.py`.
Create: `src/qap/product_paper_inputs.py` for shared product input resolution.
Create if needed: `src/qap/experiment/live_paper_candles.py` for pure candle validation and ingestion.
Contracts: `api/live_paper_schemas.py`, `web/src/features/lab/labPaperApi.ts`, and the current paper hook/panel.

Design:

- The product resolver returns authoritative `LabInputs` with timestamps, aligned bars, datasets, and metadata.
- Reuse `PairRotationAnalysis` and `load_lab_inputs`. Do not derive execution history from sampled wealth or chart arrays.
- Resolve the anchor once when creating a session. Persist its identity and never silently replace it during refresh.
- API and CLI use the same resolver at create and step boundaries. Inject inputs in deterministic tests.
- Read prepared immutable data. Missing preparation returns an explicit recoverable error through existing error conventions.
- Distinguish an explicit no-anchor selection from automatic anchor selection when resolving inputs.

Persist completed candle identities and the last consumed decision boundary.
Reject unordered, incomplete, nonpositive, misaligned, or noncontiguous new bars before changing strategy state.
For timestamps that already exist, equal content is idempotent. Different content requires an explicit correction error.
Never append a book midpoint as a completed candle.

A step with no new candle can mark portfolio value and retry a pending execution.
That step must not advance model fitting, minimum-hold bars, cooldown bars, or signal-decision counts.
Use a separate observation/attempt count for book sampling if the product needs one.
Persist the original model history origin. Do not shift the refit grid by truncating close history.
Do not implement a second streaming estimator in this repair.

If multiple new candles arrive, process them causally in order to update model state.
Do not execute missed historical trades against a current book. Submit only the latest current target.
Distinguish this catch-up case from a continuously observed forward track record.

Compatibility:

- Write a new paper-session schema version for timestamped state.
- Preserve v1 files and integrity records. Keep existing read, list, and stop operations available.
- Refuse v1 stepping with a clear “start a new session” recovery message. Do not invent historical candle timestamps.
- Expose whether a session can step. The web panel must not offer a working-looking step action for incompatible sessions.
- Preserve old studies and old paper results as historical evidence. Do not migrate them in place.

Acceptance:

- Three steps inside one 4h candle cause zero additional signal observations.
- One new completed candle advances the signal exactly once. Repeating it changes no signal state.
- Future-bar mutation does not change earlier signals.
- For every supported strategy, replay and paper signals agree over the same candle prefix and settings.
- Include z-score ratio/OLS/TLS/Kalman, copula direct/anchored, trend, and anchor lead-lag.
- A session restart preserves decision boundaries and model origin.
- Missing warmup data and incompatible legacy sessions have clear API, CLI, and web recovery states.

Tests: extend `tests/unit/experiment/test_live_paper_runner.py` and `tests/contract/api/test_live_paper.py`.
New focused tests may use `tests/unit/experiment/test_live_paper_candles.py`.
Check:

```bash
uv run python scripts/qap_gate.py --pytest tests/unit/experiment/test_live_paper_runner.py tests/contract/api/test_live_paper.py
```

## AR-2 — Reconcile partial target execution

Dependencies: AR-1.
Owners: `live_paper_runner.py`, `live_paper_execution.py`, and state projections.

Persist the desired target separately from the last signal preference and actual holdings.
After every fill, calculate the remaining target from the authoritative ledger and current prices.
Classify each attempt as complete, partial, rejected, or below tradable precision/notional limits.
Do not equate “one fill occurred” with “target completed”.

Retry a pending remainder on the next explicit step using fresh books and current owned inventory.
A retry without a new candle must not refit the signal or create another signal decision.
Give every attempt and fill a unique identifier. Restarts must not apply an existing fill twice.
If a newer candle creates another target, supersede the pending target explicitly and record the reason.

Keep the current sell-then-buy order and existing depth rejection semantics.
Do not borrow, fabricate a buy fill, undo a successful sale, or silently liquidate remaining inventory.
Treat venue dust explicitly. Preserve a material unfilled remainder as pending.
Advance completed-rotation and defensive-parking state only after reconciling the intended target.
Keep the simple-control ledger independent and give it the same execution-completion discipline.

Acceptance: reproduce the successful-sell/stale-buy case, then complete the remainder on a fresh step with an unchanged signal.
Also cover a rejected first leg, repeated stale books, restart during partial execution, changed target, and a fully completed rotation.
The interface shows partial execution and the remaining owned assets without presenting a completed swap.

Tests: extend `test_live_paper_runner.py` and `test_live_paper.py` at their existing paths.
Check: use the AR-1 targeted gate command.

## AR-3 — Require observed venue constraints

Dependencies: AR-1 and AR-2.
Owners: shared product resolver, paper manager, and `l2_book_fill.py`.

Resolve metadata for every market that can trade, including a third-asset defensive anchor.
Persist its instrument identity, fingerprint, and observation time in the new session contract.
Before a product fill, require matching observed metadata and apply existing `MarketPrecision` rules.
The shared resolver owns metadata loading. The manager must not bypass a missing map with an empty dictionary.
Keep historical and current metadata limitations explicit. Do not claim that today's filters describe all historical dates.

The low-level sweep can retain explicit metadata-free fixture use.
Product API and CLI paths must never select that mode implicitly.
Use the existing metadata capture/read owners. Missing evidence produces a preparation error, not invented default filters.
Do not add a second market-metadata cache or change notional-reference semantics.

Acceptance: missing metadata blocks trading through both interfaces.
Also cover wrong-market metadata, below-minimum quantity, quantity step, market notional filters, and third-anchor parking.
Existing hand-computed accounting cases must still pass.

Tests: `tests/unit/execution/test_l2_book_fill.py`, `tests/unit/experiment/test_live_paper_runner.py`, and `tests/contract/api/test_live_paper.py`.
Check:

```bash
uv run python scripts/qap_gate.py --pytest tests/unit/execution/test_l2_book_fill.py tests/unit/experiment/test_live_paper_runner.py tests/contract/api/test_live_paper.py
```

## AR-4 — Record actual supporting fill times

Dependencies: AR-1 through AR-3.
Owners: `l2_book_fill.py`, `live_paper_execution.py`, manager latency projections, and typed interfaces.

Preserve configured RTT as a declared delay assumption.
Record requested execution time separately from the effective time supported by a received book.
For each executed leg, effective time must follow its decision, configured delay boundary, and supporting book receipt.
The second leg must also follow completion of the funding sale and its declared subsequent delay.
Do not reuse a cached second-leg book that predates the newly required execution boundary.

Evaluate staleness against effective execution time. Book age must never be negative.
Expose actual per-leg timing when fills occur. Represent absent fills as absent actual times.
Use one declared epoch clock for comparable event timestamps. Use a monotonic clock for local elapsed waits.
Do not subtract timestamps from different clock domains.

Keep legacy nominal clocks labelled as legacy when reading older records.
Update web labels to distinguish configured delay from measured simulation delay.
Do not imply that a reconnecting snapshot collector achieved the configured RTT.

Acceptance: the 850 ms book cannot support a claimed 75 ms actual fill.
Use that book only at a later effective fill time, subject to the existing depth, precision, and staleness checks.
Also check delayed collection, no fill, stale book, second-leg ordering, and ordinary on-time execution.
Keep the existing future-book regression's economic case while correcting its timestamp assertions.
No locked quant invariant needs modification.

Tests: use the AR-3 test paths and add interface assertions for nullable actual timings.
Check: use the AR-3 targeted gate command.

## AR-5 — Repair numerical resolution without weakening statistical rules

Dependencies: AR-0. Execute after the paper slices to avoid shared validation work.
Owners: `src/qap/experiment/lab_proof.py`, `scripts/run_lab_trials.py`, and their tests.
Create if needed: `src/qap/experiment/lab_statistics.py` for the existing statistical calculation and preflight arithmetic.

Use a fixed default of 9,999 SPA bootstrap replicates for new proofs.
Keep the deterministic seed, existing loss series, block rule, SPA variant, and Bonferroni calculation unchanged in this repair.
Derive the nonzero p-value floor from the configured replicate count. Do not retain a hard-coded `1/500` floor.
Persist the replicate count, seed, block size, correction description, and proof protocol version with new results.
Register new studies under a new proof protocol identifier. Do not reuse the v1 label for changed calculations.

Before a declared family runs, calculate whether its smallest attainable corrected p-value can meet the first Holm threshold.
The calculation uses the declared outer family size and a conservative bound on cumulative per-pair configuration counts.
Include existing actor-family registrations and all proposed settings, bars, anchors, and methods that share that pair family.
Reject an impossible family before preparation requests or study mutations. Report the inputs and the required resolution.
Keep the family size fixed when rows block or fail.
If the count exceeds this preflight's capacity, require a revised declared protocol instead of adjusting replicates after seeing outcomes.

Do not remove a correction layer, reset actor history, pool actors, or rerun S4-A/S4-B as fresh confirmation.
The experiment-wide ledger and possible duplicate corrections belong to RD-1.
Finite resolution does not guarantee enough statistical power or establish profitability.

Acceptance: the 499-replicate, multiplier-3, family-24 example is rejected by preflight.
The 9,999-replicate, multiplier-12, family-24 example is numerically resolvable.
Nonpositive advantage still returns p=1. Corrected p-values stay in [0,1] and remain at least their raw values.
Update the ordinary unit test that assumes a 499-replicate floor. Do not alter invariant tests.
Use injected small replicate counts or stubs for unrelated test cases. Run a real seeded statistical case for repeatability.

Tests: `tests/unit/experiment/test_lab_proof.py` and `tests/unit/test_run_lab_trials.py`.
Check:

```bash
uv run python scripts/qap_gate.py --pytest tests/unit/experiment/test_lab_proof.py tests/unit/test_run_lab_trials.py
```

## AR-6 — Align measurements, executed signals, and claims across methods

Dependencies: AR-0 and the completed current strategy-registry refactor.
Owners: `lab_features.py`, `pair_measurements.py`, `product_pair_rotation_analysis.py`, `product_lab_advisor.py`, `lab_proof.py`, and `product_lab_study.py`.
Consumers: Lab signal/evidence views and API schemas.

Keep ratio measurements explicitly labelled as ratio measurements.
Do not use ratio half-life as the measured half-life of an OLS, TLS, Kalman, or anchor-residual strategy.
The immediate advisor repair stops that unsupported substitution. Use its declared fixed fallback lookback instead.
Any new strategy-residual half-life field must identify hedge method, fit window, cutoff, variable, and units.
An adaptive Kalman residual must not be labelled a fixed-equilibrium spread without separate evidence.

Keep return-copula tail diagnostics distinct from the traded spread-copula probability.
Identify the measured variable in each view. Do not claim that regression guarantees residual stationarity.
Describe a conditional rank as a conditional rank, rather than a forecast probability of recovery.
Treat correlation, cointegration, Hurst, and Granger readings as evidence with assumptions and limits.
Remove unsupported advisor promises about “conservative” presets or gains staying above fees.

Persist the stitched walk-forward signal values and preferences that actually generated the validation targets.
Keep fold settings and refit provenance. Do not plot the final candidate's whole history as the executed strategy.
Preserve one signal builder per method in the current registry. Do not reintroduce the retired switch implementation.

Acceptance: a synthetic beta-not-equal-to-one example distinguishes ratio and hedge-residual measurements.
A fold-switching example displays the executed candidate at each boundary and aligns with recorded decisions and fills.
Saved older results retain their original interpretation and display missing provenance honestly.
Tests cover all strategy families, not only copula.

Tests: `tests/unit/relationship/test_pair_measurements.py`, `tests/unit/relationship/test_dependence_measurements.py`,
`tests/unit/experiment/test_lab_proof.py`, `tests/unit/test_lab_advisor.py`, and `tests/contract/api/test_lab_studies.py`.
Check:

```bash
uv run python scripts/qap_gate.py --pytest tests/unit/relationship tests/unit/experiment/test_lab_proof.py tests/unit/test_lab_advisor.py tests/contract/api/test_lab_studies.py
```

Numerical stationarity admission, independence abstention, alternative margins, and new copula families require RD-1.
Default copula lookback is 96, while the existing cointegration function needs 100 observations.
Do not add a mandatory 100-bar test to a 96-bar path and then weaken locked tests to hide the conflict.
This slice corrects interpretation and signal provenance. It does not claim to establish predictive validity.

## AR-7 — Correct economic explanations and research provenance

Dependencies: AR-5 and AR-6.
Owners: `lab_proof.py` metadata, advisor/readout wording, README, TASKS, and the cited research reports.

Label `terminal wealth + paid costs` as a cost add-back approximation.
Keep the existing monetary cost-gate calculation unchanged.
Identify the denominator of every displayed percentage.
Do not divide a starting-wealth cost percentage into an ending-HODL gain percentage without conversion.
Do not describe lower turnover as mathematically incapable of improving net economics.

Add dated corrections to S4-A and S4-B under the document-update method.
Preserve raw JSONL, original outcomes, family sizes, timestamps, and blocked rows.
Explain S4-A's numerical-resolution limit without implying that its rejected strategies therefore pass.
Link any later anchor-defense rerun to its actual saved result, code revision, and research role.
If that evidence cannot be found, qualify the completion claim. Do not invent a rerun or overwrite the original rows.

Replace stale current-product instructions in README with the current Lab entry points.
Preserve historical milestones as historical. Use one current tracker and links to detailed evidence.
Document that actor isolation is not hosted authentication and that the product remains local research software.

Acceptance: each new economic label matches its source calculation and denominator.
Historical artifacts remain byte-for-byte unchanged. Their interpretations carry explicit dated corrections.
The index, TASKS, README, and completion note agree about repair status and unresolved research decisions.

Checks: affected contract/readout tests, local Markdown links, `git diff --check`, and raw-artifact hashes from AR-0.

## AR-8 — Check integration and hand back complete evidence

Dependencies: AR-1 through AR-7.

Regenerate shared contracts after DTO changes, in this order:

```bash
uv run python scripts/export_openapi.py web/openapi.json
pnpm --pm-on-fail=ignore --dir web generate:api
```

Run the targeted compiler gate for each slice. The gate serializes heavy checks through `/tmp/qap-gate-heavy.lock`.
Run one full gate after integration. Repeat only when new changes or failures justify it.

```bash
uv run python scripts/qap_gate.py --full --fail-fast
```

Harden `scripts/qap_gate.py` alongside the repairs (`tests/unit/scripts/test_qap_gate.py`):

1. Add mandatory `regression_checks` covering partial-fill recovery, neutral-signal cancellation, tradable remainders, metadata round-trips, candle timing, and declared-versus-executed research settings while preserving `tests/invariants/test_quant_compiler_laws.py`.
2. Add `research_protocol` to verify `DEFAULT_SPA_REPLICATES >= 9_999`, `PROOF_PROTOCOL_VERSION`, `check_family_resolution`, `STRATEGY_REGISTRY`, and required `RD-1` sections once `Status: approved`.
3. Reject `--skip-invariants`, `--skip-openapi`, and `--skip-web` when `--full` is set.
4. Print `[LOCK]` wait times, `[RUN ]` active step names, per-step elapsed seconds, and `--durations=15` on `pytest_full`.

Add focused web tests for duplicate-candle observation, partial execution, legacy-session recovery, actual timing, and signal provenance.
Use the existing current frontend test structure. Do not add tests that only restate component markup.
Check the repaired flows in the browser with injected deterministic backend evidence.
Cover desktop and mobile, the normal case, and each material recovery state.
Do not claim representative-user acceptance from those technical checks.

Create `docs/reviews/2026-11-16-audit-repair-completion.md` or a correctly dated equivalent.
Include baseline revision, final revision, finding-to-test mapping, test results, remaining decisions, and artifact preservation evidence.
A gate pass establishes software checks. It does not establish profitability, market fit, or live readiness.
Mark TASKS rows done only with their specific acceptance evidence.
Commit only files owned by this repair after checking the staged diff. Preserve unrelated edits and running paper sessions.

## RD-1 — Resolve research-policy decisions before changing strategy admission

Dependencies: AR-5 through AR-7.
Deliverable: a dated decision proposal linked from the completion note. No new trial runs in this card.

Specify formation-only selection, model assumptions, residual variables, and treatment of structural breaks for every method.
Resolve whether a direct filtered-deviation strategy claims cross-asset dependence or only a univariate deviation effect.
Specify anchor-residual stationarity admission, independence abstention, sample sufficiency, and diagnostic uncertainty.
Evaluate both HODL and the simple control with a declared family and sufficient numerical resolution.
Separate actor storage isolation from experiment-wide research history and knowledge reused across waves.
Assess possible duplicated corrections before proposing any change to the existing procedure.

Preserve existing controls while proposing any additional risk-matched attribution control.
Label zero-cost diagnostics separately from add-back gross. Declare whether a zero-cost replay freezes trades or reruns policy decisions.
Predeclare cost stress, parameter sensitivity, and the next evidence window without inspecting that window first.
Carry the audit's proposed presets as hypotheses. Do not call them profitable or retrospectively preregister them.

The proposal must name the exact changes to research contracts and the evidence needed for approval.
The current repair authorization does not permit weakening those contracts to obtain a passing result.
Continue independent repair work while a genuinely new research decision remains open.
Report this card as a proposal delivered, rather than an implemented or validated strategy improvement.

## Queued broader audit — preserve the original request

After repair evidence is complete, continue the overall audit with equal coverage of these areas:

| Area | Required next evidence |
| --- | --- |
| All strategy mathematics | OLS/TLS/Kalman, ratio, trend, lead-lag, and copula assumptions, units, orientation, causality, and forward usefulness |
| Portfolio economics | Multi-asset conservation, shared-coin conflicts, cash-flow matching, cost attribution, concentration, absolute drawdown, and control fairness |
| Relationship maps | Formation-only edge selection, shared-factor redundancy, multiple testing, capacity, and conflicting target resolution |
| Repository boundaries | Current ownership, artifact integrity, restart/recovery behavior, dependency direction, and source/test size |
| Product usefulness | Novice understanding, end-to-end task completion, truthful uncertainty, and clear recovery |
| Profitability | A small approved comparison on fresh evidence after RD-1, with both benchmarks and cost stress |
| Mainstream potential | Observed customer demand, willingness to return/pay, distribution, and explicit hosted-security requirements |

Do not make personal allocation recommendations without actual holdings and constraints.
The repository's simulated portfolio engine can still receive a complete code and economic audit without that personal data.
New copula families, basket expansion, partial-sizing presets, and hosted deployment remain separate follow-on work.

## Plan preparation checks

The plan's local links resolve. Eleven test paths were checked against the repository.
One test path is explicitly new. Three proposed helper paths do not exist at the checked baseline.
TASKS contains all nine repair rows, the research-policy row, and the wider-audit row.
`git diff --check` passes for the documentation changes.
No repair code or application tests ran as part of writing this handoff.
