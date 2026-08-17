# QAP Real-Alpha and Inventory-Compounding Research Integration

**Date:** 2026-08-17

**Status:** Approved research refinement for the remaining QAP implementation phases.

**Provenance:** Distilled from the user-supplied Deep Research report, *Finding Real Alpha in Long-Only Spot Crypto: A Rigorous QAP Research Blueprint* (2026-08-17), then reconciled against the existing protected QAP design. The report is research evidence and prioritization guidance; this document records only the parts admitted into QAP's plan corpus.

## 1. What did not change

The research reinforces rather than replaces the core QAP constitution:

- long-only, spot-only, actually owned inventory;
- self-financing tactical reallocations, with exogenous deposits/withdrawals modeled explicitly when present;
- no leverage, borrowing, derivatives, synthetic shorts, or interest/riba financing;
- one authoritative inventory/accounting truth;
- matched-passive-HODL-relative portfolio wealth is the primary economic objective;
- coin-unit accumulation is secondary attribution and may not justify destroying wealth;
- causal decision/fill timing and realistic explicit costs are mandatory;
- research-family lineage, chronological evaluation, one-time final-OOS consumption, and honest negative results remain mandatory;
- fast exploratory scans may reject candidates, but only deterministic QAP replay may establish economic results;
- no result authorizes live-capital operation.

## 2. Operational meaning of real alpha

QAP uses three evidence labels, without creating a promotion bureaucracy:

1. **Promising candidate** — positive development/validation economics after costs, causal replay green, and no obvious single-parameter pathology.
2. **Research alpha** — positive predeclared historical final-OOS economics, appropriate multiplicity-aware evidence when selection reused evaluation information, and credible cost/regime/parameter robustness.
3. **Deployment candidate** — research alpha plus a genuinely prospective `forward_paper` period after the rule is frozen, operational/capacity review, and explicit Phase-12 readiness review.

The labels describe evidence quality. They do not mutate runtime policy automatically.

For QAP, "alpha" is not a high Sharpe ratio or a statistically elegant relationship fit. The primary economic object remains:

```text
strategy net wealth / matched passive HODL net wealth - 1
```

under identical starting inventory, valuation marks, admissible exogenous flows, data availability, and feasible execution assumptions.

## 3. Distinguish four economically useful mechanisms

Research and UI language should separate:

- **accumulation alpha** — better deployment of newly contributed admissible inventory when an explicit external-flow stream exists;
- **holding alpha** — correctly choosing not to rebalance when action is worse than holding;
- **rebalancing alpha** — changing owned weights only when the expected economic benefit exceeds the cost of doing so;
- **execution/cost alpha** — reaching substantially the same desired portfolio transition with less implementation shortfall.

These mechanisms may coexist. A result must not attribute ordinary rebalancing return, lower turnover, beta/concentration changes, or execution assumptions to pair-specific relationship information.

## 4. Matched controls when external flows exist

The constitutional passive benchmark remains **strict inventory HODL**:

- same starting owned quantities;
- same exogenous asset deposits/withdrawals at the same effective timestamps;
- no tactical trading;
- same valuation marks.

When a run contains external contributions, one passive control is insufficient for an accumulation/timing claim. Add a mandatory **matched-contribution static HODL** control:

- receive the same exogenous contribution stream;
- mechanically deploy each contribution according to one predeclared static allocation using the same feasible execution semantics;
- hold purchased assets thereafter.

This prevents a strategy that merely converts newly arrived quote inventory into crypto market exposure from being mislabeled as smart accumulation.

The simple-control ladder therefore becomes, as applicable:

```text
strict inventory HODL
  -> matched-contribution static HODL        # mandatory when external flows exist
  -> periodic/fixed-weight rebalance
  -> cost-aware band/partial rebalance
  -> contribution-aware band                # when external flows exist
  -> pair-blind trend/cross-sectional control
  -> relationship-conditioned policy
```

Rung differences are counterfactual policy comparisons, not automatically orthogonal causal alpha components.

## 5. Search order: simple mechanisms before sophisticated models

The admitted priority order is:

1. periodic/fixed-weight and threshold/no-trade rebalancing;
2. contribution-aware threshold rebalancing when explicit external flows exist;
3. slow time-series momentum/trend gating;
4. relative momentum among admissible owned assets;
5. volatility-aware deployment/bands;
6. transparent ratio/log-ratio relationship state and mean-reversion hypotheses;
7. pair-blind common-mode/cross-sectional controls;
8. richer relationship models such as Student-t Copula only after transparent controls establish a specific remaining falsifiable question;
9. larger ensembles/network models only after individual mechanisms survive and the added search denominator is justified.

This ordering is research priority, not a claim that momentum or mean reversion is true. QAP must be able to discover that the correct action is to hold, follow strength, buy relative weakness, or reject the entire family.

## 6. First predictive pilot

After the mechanical replay/control stack is trustworthy, the first predictive family should be deliberately small:

> Can contribution-aware threshold rebalancing, optionally gated by a slow completed-bar momentum signal, create more net owned-portfolio wealth than matched static contribution HODL and ordinary cost-aware rebalancing without enough additional turnover to erase the benefit?

For a minimal pilot, use a small declared basket (for example BTC, ETH, and one explicitly admitted quote/stable asset), one weekly/daily decision schedule, a small predeclared band family, and a small predeclared momentum-lookback family. The exact assets/thresholds/lookbacks are experiment choices, not constitutional defaults.

When no external flow stream is present, test the same slow momentum evidence as a bounded gate/tilt on ordinary rebalancing rather than inventing synthetic contributions.

## 7. Candidate-killing tests

A serious candidate declares its falsifier before final OOS. At minimum:

- **smart rebalancing:** reject incremental-intelligence claims when a fixed band or contribution-aware fixed-weight control matches/beats it;
- **momentum:** reject when a small causal delay, nearby lookback, or independent equivalent venue destroys the effect;
- **mean reversion:** reject when gross reversion exists but realistic costs eliminate the net wealth advantage;
- **volatility timing:** do not call lower drawdown alpha when matched-HODL-relative wealth falls outside the predeclared acceptable trade-off;
- **execution improvement:** hold target portfolios constant and reject when the timing advantage disappears under realistic spread/latency/impact assumptions;
- **pair-specific intelligence:** reject the pair-specific label when common-mode/cross-sectional or broader momentum/beta exposure explains the result.

A narrow regime-specific result may survive, but the claim must remain conditional rather than being generalized.

## 8. Minimum robustness/admission funnel

```text
immutable admitted data
 -> descriptive/model-free diagnostics
 -> cheap whole-family exploratory scan
 -> freeze candidate/family parameters
 -> authoritative deterministic QAP replay
 -> strict HODL + applicable matched/simple controls
 -> baseline and adverse cost stress
 -> chronological development/walk-forward evaluation
 -> parameter/regime/concentration/delay diagnostics
 -> family-level inference only when selection pressure requires it
 -> one committed/frozen historical final OOS
 -> no historical retuning after inspection
 -> genuinely prospective forward-paper evidence
```

Negative outcomes remain first-class artifacts. Do not consume additional holdouts merely to rescue a favored hypothesis.

## 9. Metrics and attribution

Keep terminal HODL-relative wealth primary. Add/report where applicable:

- full relative-wealth and incremental log-relative paths;
- time below HODL/control;
- per-asset quantity delta/ratio versus the matched passive inventory;
- same-mark value of inventory deltas;
- external-flow-adjusted/unitized returns when deposits/withdrawals exist;
- turnover, fees, slippage/shortfall, trade count, and no-action frequency;
- asset exposure/concentration and largest-contributor concentration;
- results by declared regime/subperiod;
- decision-to-inventory flow trace sufficient to explain how holdings changed;
- gross-versus-net result under the same target sequence when testing execution/cost alpha.

More units of one coin are not success when the common-mark total wealth result is materially worse.

## 10. Stablecoin and quote-asset treatment

A stablecoin is inventory, not magically risk-free USD. If the reporting numeraire differs from the stablecoin, value it from an admitted market price rather than hard-coding one dollar. Stress relevant depeg regimes when a research claim materially relies on stablecoin residence.

Using a stablecoin as the declared numeraire still defines a coordinate system; it does not make stablecoin purchasing power or credit/liquidity risk disappear from broader claims.

## 11. Multiplicity without cargo cult

Preserve the existing minimum method-selection rule:

- one truly predeclared candidate versus one predeclared control on untouched final OOS does not automatically require a family-level Reality Check/SPA/PBO/DSR ceremony;
- when a winner is selected from a searched family using the same information supporting the superiority claim, family-level inference is required;
- use dependence-aware block/bootstrap procedures on aligned candidate-minus-control performance;
- use PBO as a search-overfitting diagnostic for genuinely large structured search matrices, not as a substitute for chronological OOS;
- use DSR only when Sharpe itself was materially optimized/selected or advertised;
- all failed siblings remain in the search denominator.

Prefer `arch` for admitted bootstrap/SPA machinery rather than reimplementing it.

## 12. Phase integration

- **Phase 05:** keep policy/rebalance primitives generic enough for scheduled, banded, partial, contribution-aware, and later signal-conditioned targets; do not constitutionalize mean reversion or momentum.
- **Phase 06:** admit explicit exogenous inventory-flow events as a second audited state-change source beside fills, with deterministic ordering/idempotency and identical flow streams across strategy/controls.
- **Phase 07:** implement the expanded passive/simple-control ladder, optional flow schedule in manifests, same-flow invariants, flow-aware artifacts/metrics, and falsifiable research-family bookkeeping.
- **Phase 09:** make strict HODL, matched-contribution HODL, simple controls, inventory accumulation, external-flow context, and incremental policy value visually distinguishable.
- **Phase 10:** run the first small slow-momentum/trend-gated family before richer relationship models; then test transparent relationship and pair-blind controls before any admitted Copula. Add robustness/falsification evidence before strong alpha language.
- **Phase 11:** collect prospective `forward_paper` evidence for frozen survivors and harden realistic execution/reconciliation; do not retune on forward-paper observations and still call the same period prospective.
- **Phase 12:** a deployment-candidate/GO discussion requires genuinely prospective forward-paper evidence, not merely another historical split.

## 13. Non-goals

This integration does **not** authorize:

- a generic strategy DSL;
- automatic hyperparameter optimization;
- large technical-indicator mining;
- a factor-research platform before a surviving candidate makes attribution material;
- neural-network/ensemble complexity before simple controls are difficult to beat;
- historical order-book precision QAP does not possess;
- live order placement;
- automatic policy promotion from a positive experiment.

The objective is to make false alpha difficult to survive, not to maximize the number of strategies tested.
