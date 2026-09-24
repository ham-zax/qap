# MFSM experiment patterns relevant to QAP

Read-only source review on 2026-09-24 of `/home/hamza/repo/My_Research_Model`,
including its staged working-tree implementation. No experiment/collection scripts
or tests from that repository were run, no data was acquired, and no holdout data
was inspected. Its working tree was left untouched.

## Useful now

- `src/mfsm_e001/readiness.py:80`: blockers carry evidence and a next action.
  QAP should explain a setup interruption within the unfinished study and preserve
  independent relationship results when downstream economic preparation fails.
- `readiness.py:250` and `scripts/run_e001_experiment.py:15`: readable report,
  machine result and hash manifest are distinct outputs. QAP should lead with the
  question/conclusion/comparisons and disclose reproducibility details separately.
- `src/mfsm_e001/evaluation.py:25`: paired candidates use the same observations
  and equal tuning budgets. Expose QAP's existing shared dates, starting holdings,
  costs and declared controls in the pre-run explanation and result comparisons.
- `docs/e001_exploratory_btc_result.md`: report the actual question, exclusions,
  baseline, limitations and negative conclusion. Do not label pipeline completion
  as empirical success or assume a small positive aggregate is useful.

## Future method-admission candidates, not implemented by this UX change

- `src/mfsm_e001/validation.py:59`: chronological fit/calibration/validation/test
  blocks with label-maturity checks. Useful for a separately admitted learned model;
  do not retrofit this classifier's partitions onto QAP's existing replay/holdouts.
- `src/mfsm_e001/exploratory.py:95`: fixed calendar splits and overlap checks.
- Per-period stability and feature-ablation views could strengthen a future research
  protocol, provided metrics and partitions are frozen before scoring. QAP currently
  marks generic walk-forward/parameter search unimplemented; this remains true.

## Limits

The original evaluator explicitly rejects `real_btc` at `evaluation.py:19`.
`readiness.py:180` reports the real dataset/evaluation stages as not run.
The separate observational report describes a tiny unstable Brier improvement and
states that both fitted models underperformed a simple historical-rate comparator.
These are reported results, not independently rerun findings. The exploratory study
has no fee/slippage/market-impact execution model. Predictive Brier scores cannot
replace QAP's wealth-versus-HODL-and-simple-control benchmark ladder.

No source is copied or imported. MFSM derivative-feed features, timing contracts,
and model/evaluation choices are not admitted to QAP by this product work.

## Application in this correction

QAP already owns experiment provenance, declared controls and backend support
reports. No parallel experiment framework is needed. The change makes that existing
authority easier to use: a saved question and attempts, setup/recovery in place,
an explicit pre-run explanation, a backend-owned economic conclusion, and expandable
test/reproducibility details. Support next-actions remain visible outside technical
disclosure. Relationship evidence survives an economic-preparation error.

The model-selection and chronological-partition ideas above remain proposals for
separate method admission, not implemented improvements or demonstrated alpha.
See the [implementation and verification record](../superpowers/plans/2026-09-24-research-study-workspace.md).
