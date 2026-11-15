# Preregistration H1–H3 — 2026-10-27

```text
Update context — 2026-10-27
Trigger: Hamza approved B3 decisions (30 trials per hypothesis, Holm at alpha 0.05, 180-day shadow, coins only, 2x cost gate).
Purpose: Fix hypotheses, trial budgets, correction, fixed settings, and trial log format before running Stage B studies.
Impact: Preregistration record only. No code, cost, benchmark, or data-role change.
Evidence: docs/plans/20-earning-roadmap-proposal.md, docs/plans/20-earning-roadmap-tasks.md.
```

## Hypotheses

| id | Mechanism | Rule family | Falsifier |
|----|-----------|-------------|-----------|
| H1 | Rebalancing premium | Threshold or calendar rebalance of 2–4 alts with weak correlation | Does not beat HODL at 2× costs over 3 of 4 subperiods |
| H2 | Slow relative reversion | z-score rotation on 1h/4h within one sector (L1s, exchange tokens, memes) | Edge disappears with a one-bar delay or at 2× costs |
| H3 | Relative trend | Rotate toward the stronger coin of a pair (fast/slow ratio trend) | Does not beat the control in the forward shadow run |

## Trial budget

- H1: 30 trials. A trial is one study request.
- H2: 30 trials. A trial is one study request.
- H3: 30 trials. A trial is one study request.
- Total: 90 trials across H1–H3. Every run counts, including failed, cost-gated, and abandoned runs.

## Correction

Each study already corrects across its own settings (Bonferroni, see `lab_proof.py` correction text). Across the trials of one hypothesis, apply Holm at α = 0.05 to the studies' corrected p-values. A hypothesis is supported only if at least one trial survives Holm and passes every other proof condition.

## Fixed settings

- Bar list: `1h`, `4h` for H2.
- Costs: `LabSettings` defaults (fee 10 bps, slippage 5 bps, impact 10 bps).
- Proof: 8 folds, at least 5 passing, at least 10 trades, cost gate 2× (B2).
- Rule: no setting changes after the first result.

## Robustness set for a surviving trial

- Baseline and 2× costs, nearby settings, subperiods, a one-bar delay, and a second pair from the same sector.

## Out of scope

- USDT cash (coins only, decision 1).
- Point-in-time discovery (stage C, decision 2 open).
- Maker or BNB-discount cost models (decision 5 open).
- Live orders (Phase 12 gate).

## Trial log

| # | hypothesis | pair | bar | method | study_id | call | corrected p | Holm survives |
|---|---|---|---|---|---|---|---|---|
