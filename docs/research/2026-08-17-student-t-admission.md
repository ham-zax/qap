# Student-t Copula Admission Review

**Date:** 2026-08-17

**Decision:** `REJECT` for the current Phase-10 implementation branch.

**Scope:** Read-only inspection of the QAP v1/v2 historical repository at `/home/hamza/repo/tradingview_ratio`, under `docs/REFERENCE_BOUNDARY.md`. This decision rejects historical Student-t/Copula behavior as a current clean-QAP implementation requirement. It does not claim that every future tail-dependence hypothesis is false.

## 1. What historical statistic was computed?

The historical runtime modeled synchronized **log returns** of two assets. It transformed each marginal through an empirical rank transform `rank / (N + 1)`, estimated Kendall's tau, converted tau to the elliptical correlation parameter `rho = sin(pi * tau / 2)`, and evaluated a bivariate Student-t conditional h-function in both directions:

- `MI_1|2 = P(U1 <= u1 | U2 = u2)`
- `MI_2|1 = P(U2 <= u2 | U1 = u1)`

The same implementation also reported empirical/model-implied tail-dependence diagnostics. The historical code defaulted to a 2,000-bar window, `nu=4`, and a 100-bar Kendall-tau refresh interval. Those defaults are historical configuration choices, not clean-QAP truths.

Primary historical implementation inspected:

- `src/python/core/models/copula_model.py`
- `src/python/core/models/copula_math.py`
- `src/python/support/transforms.py`
- `src/python/core/constants.py`

## 2. What policy action did it drive?

Historical QAP elevated Copula MI to canonical signal authority. Dual-MI bands generated entry intent and Copula-fair normalization could drive exits. Z-score was explicitly made diagnostic-only. This is not compatible with clean QAP's model-neutral authority boundary, where evidence may request an allocation target but cannot become constitutional trading authority.

Relevant historical surfaces inspected:

- `src/python/core/signals.py`
- `README.md`
- `docs/INVARIANTS.md`

## 3. Which behaviors were technically validated?

The historical corpus contains direct validation of the numerical plumbing rather than only prose claims:

- PIT uses the open interval through `rank / (N + 1)` and handles ties by average rank;
- the Student-t h-function is tested against a closed-form reference grid;
- MI outputs are bounded probability values with explicit invalid/neutral paths;
- dual directional MI values and `nu` propagation are covered by tests;
- pair identity was later added to prevent cached tau/rho state from bleeding across pairs;
- a `prior_window` calibration mode was added to avoid using the current return in its own calibration set.

Representative historical tests inspected or located:

- `tests/unit/test_transforms_pit.py`
- `tests/core/models/test_copula_validations.py`
- `tests/core/test_copula_nu_propagation.py`
- `tests/unit/test_copula_network_cache_and_validation.py`

These technical checks support the formula implementation. They do **not** establish incremental long-only economic alpha.

## 4. What v2 evidence falsified or weakened the economic claim?

The v2 forensic chain is materially negative for the historical canonical MI thesis:

- entry MI did not distinguish winners from losers in-sample (`p=0.98`);
- entry MI remained useless out of sample (`rho=+0.016`, `p=0.72`);
- the Copula-fair exit path closed trades that had not generated enough gross edge to survive costs;
- stronger dependence structure was not monotonically better economically;
- `lambda_upper` and entry tau showed aggregate OOS predictive information, but the tail signal was not universal across pairs;
- the best reported lambda veto improved average PnL but the system still lost money after costs;
- a significant DOT/SOL counterexample reversed the aggregate lambda direction.

Primary negative-evidence source inspected:

- `docs/R6-R11_FORENSIC_CHAIN.md`, especially R8 through R11.

The clean-QAP research contract therefore cannot treat historical MI, `nu=4`, the 2,000-bar window, tail thresholds, BTC authority, or Copula-only policy as admitted behavior.

## 5. Is there a current falsifiable question that justifies Student-t code now?

No.

Phase 10 now has deliberately cheaper comparators available first:

- completed-bar slow momentum;
- transparent rolling log-ratio standardized deviation;
- pair-blind cross-sectional/common-mode relative return;
- bounded allocation mappings through the normal policy boundary.

The historical canonical MI question is already weakened by direct OOS evidence. The surviving historical tail-dependence observations are narrower and pair-dependent, and no current clean-QAP result has yet established a residual tail-specific economic question that survives the simple-control ladder.

A future Student-t experiment could be reconsidered only if a frozen simple/transparent candidate leaves a specific tail-dependence question material, for example whether a predeclared tail-dependence observation adds net wealth over the same policy with transparent/common-mode evidence removed. That would be a new experiment, not restoration of historical Copula authority.

## 6. Admission action

`REJECT`

For this Phase-10 branch:

- do not create `student_t_copula.py`;
- do not add SciPy or a Copula dependency for this hypothesis;
- do not copy the historical h-function, fixed `nu=4`, 2,000-bar minimum, MI bands, tau cache, or signal-authority rules;
- do not add a Student-t member to the current comparison family;
- preserve this rejection as a first-class research result.

If a future frozen experiment produces a genuinely tail-specific question, evaluate `pyvinecopulib` first as required by `docs/OSS_REUSE_BOUNDARY.md` and `docs/research/2026-08-17-quant-oss-integration.md`; third-party estimator types must remain behind `qap.relationship.models`.
