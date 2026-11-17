# QAP strategy, mathematics, portfolio, and product audit

Date: 2026-11-16. Source revision: `5dbcdbdbbe75a9127966235f91abd3affe1f7163`.

Trigger: Hamza requests a repository audit, profitability assessment, copula review, and improvement proposals.
Purpose: distinguish sound engineering, mathematical assumptions, economic evidence, and product potential.
Decision impact: proposals only. Existing objectives, benchmarks, costs, holdout roles, and action limits remain authoritative.
Evidence: current source, recorded research, the compiler gate, offline probes, and primary research listed below.

## Assessment

QAP has useful research infrastructure. The inspected evidence does not establish a repeatable net advantage over matched HODL and simple rebalancing.
Some historical results justify further investigation. They do not justify a profitability claim or capital deployment.
Passing software tests does not establish that a statistical model describes the market or predicts future returns.

The largest opportunities are execution fidelity, a statistically usable evaluation procedure, and stronger admission rules for relationships.
Adding more models before those repairs can increase the number of false discoveries.

| Area | Assessment | Basis and limit |
| --- | --- | --- |
| Inventory accounting | Strong inspected foundation | Immutable Decimal holdings, explicit fills, nonnegative inventory, matched passive holdings |
| Signal implementation | Useful causal foundation | Existing causality and scale tests pass. These tests do not prove predictive value |
| Statistical promotion | Material design gap | Bootstrap resolution cannot support the S4-A correction structure |
| Historical profitability | Unproven | No S4-A or S4-B proof passes. Some individual validation returns are positive |
| Copulas | Suitable research tool, incomplete trading case | Correct conditional-probability direction. Stationarity and future recovery need separate evidence |
| Forward paper | Execution prototype | Offline probes reproduce timing, cadence, metadata, and recovery gaps |
| Personal portfolio | Not assessed | No authoritative personal holdings, tax basis, cash flows, or risk budget were supplied |
| Mainstream use | Plausible as a research product | Customer demand, willingness to pay, and representative-user success remain unmeasured |

## Scope and method

The audit traces analysis → signals → proof → targets → fills → ledger → economic views.
It also inspects the current product vision, Phase 21 plan, TASKS, S4 records, advisor, paper API, and paper panel source.
“Maps” means relationship maps and the project roadmap here. No separate user portfolio map was supplied.

The graph index reports no recorded freshness issue for 13 checked source paths. Source reads support material findings.
The graph does not establish complete repository coverage. The audit does not claim a formal proof of every mathematical function.
The browser interface did not receive a rendered usability or accessibility assessment during this audit.
No new investment trials, live orders, or final-OOS evaluations ran.

Concurrent source and UI edits appeared after the compiler check.
The inspected diff moves signal builders into a registry and changes explicit-anchor error handling.
Those edits do not resolve the documented statistical and paper-execution findings.
The offline probes ran again against the updated working tree. Their results include source hashes.
The earlier nine-gate pass does not certify those concurrent edits.

Academic-research guidance supplies source appraisal. Probabilistic-thinking guidance prevents unsupported probability estimates.
Systematic-debugging guidance supplies reproducible diagnosis. UI/UX guidance limits product claims to inspected evidence.
This is a targeted research synthesis, not a systematic literature review or an independent multi-agent review.

## What the recorded economics show

| Research record | Declared rows | Economic proofs | Passing proofs | Main limit |
| --- | ---: | ---: | ---: | --- |
| October 27, 15m Lab | 10 | 10 | 0 | Earlier signal generation. Some cost coverage fails |
| November 15, S4-A | 24 | 24 | 0 | No Holm survivors. Bootstrap resolution also prevents a pass |
| November 15, S4-B | 12 | 8 | 0 | Four anchor-defense rows contain blocked results |

These are different research generations on overlapping data. Do not pool them as independent statistical trials.
The October record does not measure the repaired November copula implementation.

S4-B's strongest coins-only row is DOGE/XRP, 4h, BTC-anchored copula:

- Validation wealth is 16.50% above matched HODL and 16.22% above its selected simple control.
- Reported trading cost is 5.57% of starting validation capital. Five of eight folds beat the control.
- Its raw p-value is 0.02204. The first Holm threshold across 12 rows is 0.00417.
- Its tuning cost gate fails. The recorded proof does not pass.

LINK/ETH, 1d Kalman, reports 10.92% above HODL on 0.91% cost, with seven validation rotations.
Its corrected p-value is 0.3968, and its tuning cost gate fails.
Those gains describe historical relative wealth over the recorded validation window. They are not annual returns or expected future returns.

The inspected standard paper-session directories contain two sessions.
One contains zero decisions. The smoke session contains one decision and one rotation over about 37 seconds.
Neither record supplies a sustained forward profitability history. An `active` state file does not prove an operating collector or scheduler.

Sources: [S4-A](../2026-11-15-stage-s4-discovery-results.md), [S4-B](../2026-11-15-stage-s4b-discovery-results.md),
[October record](../2026-10-27-lab-earning-answer.md), and their linked raw records.

## Priority findings

### 1. High: S4-A cannot pass its statistical procedure

`corrected_spa` uses 499 bootstrap replicates and floors the raw p-value at `1/500 = 0.002`.
S4-A records at least three configurations per row. The smallest possible corrected p-value is therefore `0.006`.
Holm's first threshold across 24 rows is `0.05/24 = 0.0020833`.
No row can start the Holm step-down. Zero survivors is partly a property of the test configuration.

This does not make a rejected strategy profitable. DOGE/XRP's S4-A raw p-value, 0.02605, also exceeds the unlayered first threshold.
Costs and the other gates still fail. The evidence supports no promotion.

Proposal: preregister enough replicates for the complete correction structure and acceptable sampling error.
For a trial multiplier of 12 and 24 outer tests, the floor alone needs at least 5,759 replicates under an inclusive threshold.
Use a larger fixed count for confirmation and report Monte Carlo uncertainty near the decision boundary.
Check block-length sensitivity before freezing the procedure. Do not choose a block length because it produces significance.

Also define one experiment-wide hypothesis family. Per-pair configuration counts followed by outer Holm can count some searches twice.
Actor-scoped trial registries serve workspace isolation. They cannot record knowledge shared across actors or successive research waves.
Maintain a research ledger for pair, anchor, bar, method, and parameter selection across waves.
Any statistical contract change needs the repository's explicit escalation process.

Owner: [lab_proof.py](../../../src/qap/experiment/lab_proof.py), `corrected_spa`.
Evidence: [probe results](probe-results.json), `bootstrap_resolution`, and S4-A raw records.
Background: [arch SPA documentation](https://arch.readthedocs.io/en/latest/multiple-comparison/generated/arch.bootstrap.SPA.html),
[Bailey and López de Prado](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf).

### 2. High: paper decisions do not preserve historical candle timing

Each paper step appends a current book midpoint to close history.
The append function accepts no candle timestamp. The session's `bar` does not enforce a completed-bar boundary in this path.
The normal step API does not supply refreshed completed candles.
Three immediate calls increase a one-observation history to four observations.

A 4h backtest and a manually stepped paper session therefore consume different observation clocks.
Lookbacks, hold periods, cooldowns, and refit blocks lose their historical time meaning.
L2 depth can improve fill realism without correcting that signal mismatch.

Proposal: advance strategy state once per completed, timestamped candle.
Keep book sampling and execution events on their separate clock.
Make duplicate candle ingestion idempotent and reject missing or unordered candle evidence.
Compare historical replay and paper decisions over the same recorded candle sequence.

Owners: [live_paper_state.py](../../../src/qap/experiment/live_paper_state.py), `append_mid_closes`,
and [live_paper_runner.py](../../../src/qap/experiment/live_paper_runner.py), `step_session`.
Evidence: `step_cadence` probe and [step API](../../../src/qap/api/routes/live_paper.py).

### 3. High: partial rotations can leave the portfolio outside its intended target

The probe sells BTC successfully and rejects the ETH buy because its book is stale.
The strategy then owns 100 ETH and 6,487.0065 USDT.
The manager records the new signal preference after any strategy fill.
On the next fresh step, the signal remains `-1`, so preference comparison requests no further rotation.
The strategy holds the same USDT balance and reports `hold`.

Owned inventory remains correct. Execution progress does not match the intended target.
The problem is the state transition after a partially completed rebalance, not a Decimal accounting failure.

Proposal: track target completion independently from signal preference.
Reconcile remaining target differences after fills and explicit rejections.
Define retry, abandonment, cooldown, and crash-defense behavior for partial execution.
Add a stale-second-leg recovery case and a neighboring fully completed case.

Owners: [live_paper_runner.py](../../../src/qap/experiment/live_paper_runner.py), strategy-fill branch,
and [live_paper_execution.py](../../../src/qap/experiment/live_paper_execution.py), `sweep_rebalance`.
Evidence: `partial_rotation` probe. The probe uses temporary sessions and no network.

### 4. High: the normal paper API does not require venue filters

The manager accepts optional market metadata. The normal step route does not provide that metadata.
The sweep then accepts `None`, so quantity and notional filter checks do not run.
The probe fills a quantity of `0.0000001` without metadata.
With the supplied fixture metadata, the same order fails with `below_minimum_quantity`.

Proposal: resolve and persist observed venue constraints for every traded market before admitting a paper session.
Reject missing constraints at the product boundary. Preserve metadata provenance and its observation time.
Keep the low-level fixture mode explicit if tests need unconstrained books.

Owners: [live_paper.py](../../../src/qap/api/routes/live_paper.py),
[live_paper_runner.py](../../../src/qap/experiment/live_paper_runner.py), and
[l2_book_fill.py](../../../src/qap/execution/l2_book_fill.py).
Evidence: `optional_metadata` probe. Exchange context: [Binance filters](https://github.com/binance/binance-spot-api-docs/blob/master/filters.md).

### 5. High for latency claims: reported fill clocks can precede their books

The paper runner computes nominal fill times from decision time plus configured RTT.
It can then obtain a fresh book after that nominal time and use the later book for the fill.
The low-level probe uses a book received at 850 ms for a target fill at 75 ms.
The sweep fills and reports a book age of `-775 ms`.
An existing unit test explicitly permits this ordering.

Using a later book for a later actual fill can be valid forward simulation.
The recorded nominal timestamp does not describe that actual fill time.
The current record cannot establish execution at the displayed 75 ms latency.

Proposal: record configured delay and actual simulation availability separately.
Require the effective fill time to follow receipt of its supporting book.
Report connection, collection, and processing delay. Use a monotonic clock for elapsed durations.
Check injected late books, reconnects, and cross-leg clock ordering.

Owners: [live_paper_execution.py](../../../src/qap/experiment/live_paper_execution.py),
[live_paper_runner.py](../../../src/qap/experiment/live_paper_runner.py), and `sweep_l2_taker_order`.
Evidence: `late_book` probe. No wall-clock network latency measurement ran in this audit.

### 6. High for model interpretation: residual stationarity is an assumption

The anchor copula fits rolling regressions of log prices on the anchor.
It does not test whether either resulting residual has a stable distribution.
Independent random walks with anchor-cointegration p-values of 0.332 and 0.110 still produce 504 finite copula outputs.
The probe demonstrates missing admission checks. It does not estimate a false-discovery rate.

The direct path subtracts a moving average from each log price.
A fixed-window filter can make a random walk's filtered output stationary under stationary increments.
That mathematical property does not establish a relationship between the two assets or predict their future relative returns.
Two unrelated walks can both produce such filtered series.

Proposal: distinguish a filtered deviation from an admitted cointegrating residual.
For anchor-mediated models, admit each asset-anchor relationship on formation data and monitor subsequent breakdown.
For direct models, establish forward predictive value beyond a univariate deviation control.
Do not describe regression, detrending, or a bounded percentile as proof of recoverable mispricing.

Owner: [lab_copula.py](../../../src/qap/relationship/lab_copula.py).
Evidence: `independent_walks` probe and [Engle-Granger assumptions](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.coint.html).

### 7. Medium: descriptive measurements do not always describe the traded spread

The analysis computes half-life and Hurst on `log(A/B)`.
An OLS signal uses a spread of the form `log(A) - alpha - beta*log(B)`.
The two spreads coincide only under specific coefficients. Their reversion speeds need not match.
The advisor uses the ratio half-life to select a lookback for other hedge methods.

The displayed copula tail measurements fit log returns. The traded copula fits deviations or anchor residuals.
Their selected families and tails can differ.
The walk-forward proof also returns the final selected candidate's full signal path for display.
The executed validation preferences can come from different candidates across folds.

Proposal: identify each measurement's variable, window, fit cutoff, and units.
Estimate half-life on the actual frozen residual. Display the stitched signal that generated the fills.
Label descriptive return dependence separately from the strategy's residual dependence.

Owners: [product_pair_rotation_analysis.py](../../../src/qap/product_pair_rotation_analysis.py),
[product_lab_advisor.py](../../../src/qap/product_lab_advisor.py),
[lab_proof.py](../../../src/qap/experiment/lab_proof.py), and
[product_lab_study.py](../../../src/qap/product_lab_study.py).
Basis: source inspection. No rendered chart comparison ran.

### 8. Medium: some research explanations overstate their arithmetic

`terminal strategy wealth + paid costs` is a cost add-back approximation.
It is not a separate zero-cost replay. Removed costs can change quantities, later wealth, impact, and drawdown-triggered decisions.
The tuning gate's monetary arithmetic is internally distinct from its displayed percentages.
`tuning_cost_pct` divides cost by starting wealth. `tuning_gross_vs_hodl_pct` divides the add-back gain by ending HODL wealth.
Those percentages cannot form a valid gross-to-cost ratio without a denominator conversion.

The S4-B report also says lower turnover cannot move the gate because both sides scale together.
That conclusion requires a proportionality assumption. Changing entry rules changes which trades occur and their expected gains.
S4-B establishes that its tested changes did not clear the gate. It does not establish a general impossibility law.

Proposal: retain the existing gate until an approved change.
Label add-back gross as approximate and report its denominator.
Use a separate zero-cost counterfactual for diagnosis, with its policy behavior declared.
Correct explanatory documents through the document-update method rather than silently changing historical records.

Owners: [lab_proof.py](../../../src/qap/experiment/lab_proof.py) and the S4-B research report.

## Mathematical interpretation and copula research

For prices `P_A` and `P_B`, define a fixed fitted log spread:

```text
s_t = log(P_A,t) - alpha - beta * log(P_B,t)
```

Here beta is a log-price coefficient. It is not a fixed number of B tokens per A token.
For a local hedged long-short construction, the B quantity magnitude is approximately `beta * q_A * P_A / P_B`.
That construction does not authorize a short position in QAP.
QAP can reduce an owned B allocation and increase A. Its total portfolio still carries long market exposure.

Cointegration means that a specified combination of integrated price series has a stable distribution under its assumptions.
Correlation describes co-movement. Neither property alone establishes a positive expected trading gain after costs.
Higher correlation is not the objective. It can leave too little relative movement to pay for trading.

For one period starting from equal wealth, a useful approximate active-return equation is:

```text
strategy return - HODL return
    ≈ (strategy weight in A - passive weight in A) * (return A - return B)
      - trading cost / starting wealth
```

The predictive task concerns the future relative return after the decision.
A high dependence score describes the relationship but does not estimate that future return.
Test expected gain over a declared horizon against the complete cost of entering and later changing the allocation.
With two routed legs each way and a 10-basis-point fee per leg, a full round trip costs about 40 basis points in fees.
Slippage and impact add further cost. Partial trades and direct routes have different portfolio-level costs.

For a continuously rebalanced two-asset diffusion without costs, the excess-growth term is:

```text
0.5 * w * (1-w) * (sigma_A^2 + sigma_B^2 - 2*rho*sigma_A*sigma_B)
```

That term compares portfolio log growth with weighted constituent log growth under the model.
It does not guarantee terminal outperformance of buy-and-hold.
Persistent relative trends, trading costs, jumps, and estimation errors can reverse the practical comparison.
Evaluate volatility harvesting through the actual benchmark ladder rather than presenting the formula as a profit guarantee.

For an AR(1) residual with coefficient `0 < phi < 1`, the implemented half-life formula is:

```text
half_life_in_bars = -log(2) / log(phi)
```

The formula is appropriate for that fitted process. The coefficient needs uncertainty estimates and stability checks.
A short sample that gives a finite half-life does not establish a persistent economic equilibrium.
Hurst's exponent is a scaling estimate. Its current threshold labels lack an uncertainty measure.
Use Hurst as supporting evidence rather than an independent permission to rotate.

A copula separates each variable's distribution from their joint dependence.
The inspected `hfunc2` call correctly represents `P(U_A <= u_A | U_B = u_B)`.
That value describes today's conditional rank. It is not `P(A will outperform B over the next H bars)`.
The independence copula returns A's marginal rank. It can still trigger the current strategy without any cross-asset dependence.

Source: [pyvinecopulib hfunc2](https://pyvinecopulib.readthedocs.io/en/latest/_generate/pyvinecopulib.core.Bicop.hfunc2.html).

The Student-t, Clayton, and Gumbel tail formulas inspected are consistent with their usual unrotated forms.
The code also handles the displayed same-tail effect of rotations.
That source check does not establish calibration, parameter stability, or predictive usefulness for any selected pair.
No new copula family is required before those questions receive evidence.

Recommended copula experiments, in order:

1. **Independence abstention.** If independence wins formation-period selection, produce no relationship tilt.
2. **Two-sided evidence.** Record both conditional ranks. Compare a joint divergence rule with the current single-rank rule.
3. **Formation admission.** Check integration order, residual stability, and breaks before fitting the trading copula.
4. **Margin calibration.** Compare the existing empirical margins with one declared conditional-volatility model on formation data.
5. **Out-of-sample calibration.** Check conditional-rank distributions, serial dependence, and predictive scores on untouched validation data.
6. **Incremental family value.** Compare independence, Gaussian, Student-t, and one asymmetric family with identical margins and execution rules.

GARCH means a model of changing conditional variance. Such a model can improve margin calibration without creating a return forecast.
Do not fit GARCH to stationary spread levels by default. Specify whether it models innovations or returns.
Extreme-value tails, dynamic copulas, and high-dimensional vines add estimation and selection burden. Defer them until simpler models add value.

The default 96-bar formation window contains only 1.92 expected observations in each nominal 2% marginal tail under uniform ranks.
Serial dependence reduces independent information further. A parametric copula can extrapolate, but the tail calibration remains weakly supported.
Report sample size, effective sample-size limits, and threshold sensitivity. A rarer threshold does not guarantee a better trade.

### What the research does and does not transfer

[Tadi and Witzany](https://arxiv.org/html/2305.06961v2) study cointegration-screened, anchor-mediated spread copulas and conditional trading signals.
Their long-short construction differs from QAP's owned long-only rotations.
Their results motivate a hypothesis. They do not establish QAP's returns or justify assuming stationary residuals without screening.
The cited arXiv version is dated 2023. The playbook's 2024 attribution needs a matching publication citation before reuse.

[Rad, Low, and Faff](https://randlow.github.io/2016_QF_PairsTrading.pdf) compare methods on US equities from 1962 to 2014.
They report monthly copula excess returns of 43 basis points before costs and 5 after costs.
Those equity results do not forecast crypto returns. They show that a more elaborate dependence model can lose much of its gain to execution costs.

[Liu and Tsyvinski](https://www.nber.org/papers/w24877) provide historical evidence for cryptocurrency momentum.
Their result supports keeping momentum as a falsification control. It does not override QAP's unsuccessful historical momentum tests.
[Boyd and colleagues](https://arxiv.org/abs/1705.00109) separate allocation, risk, and transaction-cost optimization from return forecasting.
Their framework motivates constrained sizing. It does not supply the missing forecast.

## Portfolio and relationship maps

The core ownership boundary is appropriate: policy supplies a target, execution supplies fills, and the ledger updates owned inventory.
Preserve that boundary when adding a basket or a map. Separate benchmark ledgers represent separate counterfactual portfolios.
Do not sum independent pair-backtest profits. Two pairs can require the same inventory at the same time.

For a future relationship map, use each asset as a node and each tested relationship as an edge.
Show horizon, sign, sample size, fit cutoff, stability, liquidity, cost estimate, and validation status for each edge.
Distinguish return correlation, residual stationarity, and tail dependence rather than combining them into one unexplained score.
Shared BTC exposure can create many correlated edges. More edges do not mean more independent opportunities.

Admit edges using formation data. Apply a declared multiple-testing procedure across the searched graph.
Keep direction consistent when the user reverses A and B. Display conflicting edge recommendations before resolving a portfolio target.
The existing graph-basket module is a useful reference for ownership and orientation. It does not prove a current profitable portfolio strategy.

For basket allocation, a possible research objective is:

```text
maximize expected relative return
         - risk penalty
         - expected trading cost

subject to weights >= 0, sum(weights) = 1,
           position limits, owned inventory, venue filters, and capacity limits
```

Estimate every input on information available at the decision time.
Keep the matched initial holdings and external cash flows identical across strategy and passive comparisons.
Report absolute drawdown alongside relative wealth. A strategy can beat HODL and still lose substantial capital.

## Proposed presets and new statistics

These are research specifications, not profitable settings or personal investment recommendations.
Freeze the entire family before testing on new evidence. Do not retrospectively register these proposals as preregistered trials.

| Proposal | Exact initial research settings | Status and purpose |
| --- | --- | --- |
| Passive reference | HODL. No signal or rotations | Existing benchmark. Measures whether any intervention helps |
| Simple control | Initial 50/50 allocation. Rebalance at five percentage points of weight drift | Existing replay control. Freeze the control selection rule before evaluation |
| Wide OLS test | 4h, lookback 180, entry 2.5, exit 0.5, minimum hold 12, cooldown 8, rotation size 0.5, coins_only, auto_tune=false | Current settings accept this tuple. Requires residual-admission research. Not tested by this audit |
| Restricted copula test | 4h, lookback 360, probability 0.05, exit band 0.15, minimum hold 12, cooldown 8, rotation size 0.5, coins_only, auto_tune=false | Current settings accept this tuple. Add independent-model abstention and formation admission before interpreting it as a relationship strategy |
| Trend control | 1d, fast 20, slow 80, deadband 0.005, minimum hold 3, cooldown 2, rotation size 0.5, coins_only, auto_tune=false | Current settings accept this tuple. Tests relative trend as a competitor to reversion. No claimed edge |
| Partial-rotation variant | Initial 50/50, targets 65/35 and 35/65, rotation size 0.15 | Backend settings permit it. The approved MVP defers granular sizing. Requires a plan decision before inclusion |

All examples retain the existing fee, slippage, impact, minimum-trade, fold, significance, and cost-gate defaults.
Keep defensive parking as a separate declared arm. Apply the same defensive rule to an additional simple control for attribution.
Continue to report the original HODL and control ladder. Extra attribution must not replace the objective.

The proposed windows and thresholds are hypotheses, not estimated optima.
A 360-bar 4h window covers 60 days. Historical coverage and adequate formation/proof samples still require a data check.
Use the existing 2% tail settings as already explored evidence, rather than repeatedly testing small variations on the same validation dates.

Statistics worth adding before more strategy families:

- Confidence intervals for net relative log wealth and each comparison against HODL and control.
- Predictive relative returns by signal bucket at a declared horizon, including adverse excursions and failed recoveries.
- Turnover, gross traded notional, per-leg cost, and a declared round-trip cost definition.
- Residual-break frequency, hedge-coefficient stability, and uncertainty around half-life.
- Conditional-rank calibration and a forecast-score comparison against independence.
- Downside dependence and expected shortfall for risk interpretation, with sample uncertainty.

Distance correlation or mutual information can detect dependence that ordinary correlation misses.
They still do not specify a trade direction or a profitable horizon.
A vector error-correction model can model adjustment toward a cointegrating relationship.
Admit it only after integration and rank assumptions pass, then compare its forecasts with the simple residual model.
Use change-point diagnostics to suspend unsupported reversion hypotheses rather than forcing every market into a regime label.

## Usefulness and mainstream potential

The clearest initial user is an existing crypto holder who wants to test whether a rotation helps after costs.
QAP can answer that question even when the answer is to hold.
Useful outputs are an honest comparison, a reproducible report, and a clear explanation of why a proposed rotation fails.

The present advisor ranks presets from descriptive measurements.
Descriptions such as “conservative” or “keeps gross spread well above spot fees” exceed the available economic evidence.
Label these outputs as research candidates until the complete test procedure supports a stronger claim.
Keep untested, failed, reused-validation, and prospectively supported states visibly distinct.

Mainstream acceptance needs observed user outcomes.
Test whether a novice can enter a pair, understand costs, identify the better benchmark, and explain an inconclusive result without help.
Measure completion, interpretation errors, time, and willingness to return or pay.
A cosmetic assessment or passing component tests cannot establish those outcomes.

Subscriber isolation by an actor header is not authentication or authorization.
The inspected application identifies itself as a local single-operator API.
Hosted use requires an explicit identity, authorization, job-isolation, storage, quota, and recovery design.
Those product requirements do not justify placing live orders.

Demand and distribution remain open questions. No customer interviews, pricing experiment, or market-size study ran here.
Research quality, transparent negative findings, and reproducible reports are plausible differentiators, not an established commercial moat.
Do not promise that relationship analysis beats passive holding.

## Recommended sequence and stop conditions

1. Repair paper cadence, partial execution, required metadata, and actual fill-clock evidence.
2. Approve and freeze a statistically resolvable confirmation procedure. Preserve the economic objective and realistic costs.
3. Align measurements and displays with the exact traded residual and executed signal path.
4. Run one small preregistered comparison on fresh evidence with a fixed pair universe and an experiment-wide ledger.
5. Require net gains against both benchmarks, uncertainty bounds, stability, and execution-cost stress before any promotion claim.
6. Use sustained forward paper evidence only after replay/paper equivalence passes.
7. Evaluate basket expansion and hosted distribution after the pair product answers its core question reliably.

For two required superiority claims, one possible preregistered test uses the larger of the two valid one-sided p-values.
That intersection requirement differs from searching for whichever benchmark is easiest to beat.
Preserve dependence with a suitable block method and a declared hypothesis family.
The statistical owner must specify the final procedure before the next confirmatory test.

Stop adding nearby presets when the new information is another view of already inspected validation data.
If a small fresh comparison fails, report the failure and revisit the predictive mechanism rather than weakening the cost gate.
Capital deployment remains subject to the separate readiness decision.

## Check record and reproducibility

The targeted compiler command exits zero. All nine gates pass in 53.20 seconds:
lint, format, source size, import boundaries, Python types, OpenAPI synchronization, web types, invariants, and targeted tests.

```bash
uv run python scripts/qap_gate.py --fail-fast --pytest \
  tests/unit/relationship tests/unit/portfolio tests/unit/evaluation \
  tests/unit/experiment/test_lab_proof.py \
  tests/unit/experiment/test_lab_replay.py \
  tests/unit/experiment/test_lab_crash_defense.py \
  tests/unit/experiment/test_live_paper_runner.py \
  tests/unit/execution/test_l2_book_fill.py \
  tests/unit/test_lab_advisor.py tests/unit/test_lab_store.py

uv run python docs/research/2026-11-16-audit/probes.py
```

The [offline script](probes.py) uses existing fixtures and temporary directories.
Its [recorded results](probe-results.json) include the audited source revision.
The script passes Ruff lint and formatting checks after one formatting correction.
The full release gate, rendered browser acceptance, live latency measurements, and a new performance study did not run.
The audit findings remain open. This audit changes only documentation and offline diagnostic artifacts.
Concurrent source and UI edits belong to another task and remain preserved.

Documentation drift needs attention: README still describes retired workbench flows, while TASKS and Phase 21 describe the current Lab.
TASKS records an anchor-metadata repair. S4-B's original report and raw rows still document four blocked executions.
Current input resolution includes the anchor metadata. Do not silently replace the historical blocked rows with assumed successful results.
Publish any later rerun as separately identified evidence with its code revision and research role.

## Brief retrospective

The green compiler gate did not cover observation-clock equivalence or partial-second-leg recovery.
Propose focused cross-layer checks at those boundaries.
The S4 research procedure did not expose its unattainable significance threshold before running trials.
Propose a preflight calculation of p-value resolution and the complete correction structure.
Some combined reads exceeded output bounds, and the web fetcher returned PDF bytes without usable text.
Use smaller evidence windows and a PDF parser for future audits. Proposals appear in the repository's future-improvements document.
