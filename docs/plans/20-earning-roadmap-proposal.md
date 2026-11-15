# Phase 20 (proposal) — From Lab to earning, end to end

```text
Update context — 2026-10-27
Trigger: Hamza: "the main goal is to earn via altcoin. How can we make it earn?"
Purpose: one end-to-end path from today's Lab to a possible small live allocation.
Impact: proposal only. Not approved. Decisions marked ESCALATE need Hamza.
Evidence: Phase 19 plan, master plan Waves 5–6, TASKS.md L4 trial set.
```

Status: **draft for Hamza's review**. It authorizes no code, no data-role change and
no live order. Phase 19 acceptance (M3–M8) stays the current work.

## 1. The goal as a checkable claim

"Over a forward period of at least 6 months, a predeclared QAP policy ends with
more USDT value than matched HODL **and** than the predeclared rebalancing control,
after realistic fees and slippage, on Binance spot, with no leverage, no shorts and
no borrowing."

Earning means beating both rungs of the ladder. Ending with more USDT alone is not
earning: in a rising market, HODL also gains. In a falling market, a long-only
policy can lose less than HODL and still lose money. QAP measures the relative
result, and this plan keeps that objective.

## 2. Honest starting point

- **Base rate.** Most published and retail pair-trading and rotation rules lose
  their edge after costs and after correction for the number of rules tried.
  Prior for "a given simple, predeclared rule beats HODL and the control after
  costs on forward data": about 5–15%. Prior for "at least one of 10 trials
  passes in a backtest by chance": high, about 40% at p 0.05 with no correction.
  The study store corrects for the trial family, which lowers this.
- **Costs dominate at short bars (measured).** Trial 1 (SOL/ETH, z-score, 15m)
  made 102 trades in a 54-day check period. Fees were 268 USDT and slippage 241 USDT:
  5.1% of the 10,000 USDT start. The rule ended 424 USDT below HODL, so before costs
  it was about 85 USDT (0.85%) ahead. The gross signal is small. Costs are about
  6× larger.
- **What can be real.** Three mechanisms have some independent support in crypto:
  1. Rebalancing premium: two volatile coins with weak correlation and similar
     long-run growth can gain from periodic rebalancing. The control already
     measures this.
  2. Relative mean reversion within one sector, on slower bars (1h–1d), where cost
     per trade is small relative to the moves.
  3. Trend persistence: altcoins trend more than large caps. Rotation toward the
     stronger coin of a pair captures part of this without shorting.
- **What is not real.** A low cointegration p-value on one past window. A Granger
  lead that a cost of one bar removes. A single passing trial out of many.

Today's L4 trial set (10 predeclared studies) is the first evidence row for
section 5. Results go in [the trial record](../research/2026-10-27-lab-earning-trials.json).

## 3. The bottleneck

Research speed limits progress before any model does. One analysis takes 16–50 s,
a first open of a new pair takes minutes, and a study takes longer. At this speed
a disciplined research program of 50–100 trials takes days of wall time. Fix
speed first (stage A), because every later stage multiplies trial count.

## 4. Stages

Durations are rough guesses for one developer with agents, not estimates from data.
Each stage has an exit test. A failed exit stops the path or returns to an
earlier stage. No stage skips the benchmark ladder.

### Stage A — Fast, trusted research loop (1–2 weeks)

- Warm analysis below 8 s. Cache registry and catalog parsing. Cap the copula fit
  window. Reuse loaded series across requests (TASKS.md L6).
- Batch studies: one command runs a predeclared list and writes one record,
  with the trial family recorded before the first result.
- Exit: 10 studies finish in under 15 min. Same values as the slow path.

### Stage B — Preregistered research program (2–4 weeks)

- Write hypotheses H1–H3 (section 5) with falsifiers before any run.
- Fix a trial budget per hypothesis (for example 30) and one correction method
  for the family. Every run counts, including failed and abandoned runs.
- Prefer slower bars (1h, 4h) and fewer, larger rotations. Report turnover and
  cost paid as first-class numbers next to the result.
- Cost budget rule: a candidate's gross excess over HODL must be at least 2× the
  cost it paid on the tuning period. Otherwise the proof fails with the call
  `cost_budget_failed`. The trial still counts in the family budget (card B2).
- Robustness set for any candidate: baseline and 2× costs, nearby settings,
  subperiods, a one-bar delay, and a second pair from the same sector.
- Exit: at least one candidate passes the walk-forward proof, beats both rungs at
  2× costs, and survives the robustness set. Otherwise record `no_edge` and stop
  or revise the hypotheses once.

### Stage C — Point-in-time universe (2–3 weeks, ESCALATE)

- Fixed-basket results must not be described as discovery performance. A pair
  chosen today because it looks good is survivorship bias.
- Build a point-in-time pair selector: at each month start, choose pairs from
  coins that were listed, liquid and identity-resolved **at that time**.
- ESCALATE: universe eligibility rules change here.
- Exit: the candidate rule still beats both rungs when the selector chooses its
  pairs point in time.

### Stage D — Forward shadow run (minimum 90 days, target 180)

- `final_oos` is consumed once inspected. Forward data is the only clean test left.
- Run the frozen candidate on live public data with paper execution only
  (Phase 11 semantics). No setting changes during the run. Record every decision
  and every would-be fill with its timestamp.
- Exit: after 90 days, forward excess vs HODL and vs the control is positive, and
  the backtest's expected range contains it. A forward result outside the range in
  the bad direction stops the path.

### Stage E — Live-readiness gate (Phase 12, ESCALATE)

- A separate design and Hamza's approval. Secrets, kill switch, venue limits,
  reconciliation, Shariah/action-space review.
- Exit: documented GO with a capital limit (for example 1–5% of intended capital),
  or NO-GO with reasons.

### Stage F — Small live allocation (only after E)

- Start with the capital limit from E. Compare live fills with shadow fills each
  week. Stop on a predeclared drawdown versus HODL or on fill divergence.

## 5. Hypotheses for stage B

| id | Mechanism | Rule family | Falsifier |
|----|-----------|-------------|-----------|
| H1 | Rebalancing premium | Threshold or calendar rebalance of 2–4 alts with weak correlation | Does not beat HODL at 2× costs over 3 of 4 subperiods |
| H2 | Slow relative reversion | z-score rotation on 1h/4h within one sector (L1s, exchange tokens, memes) | Edge disappears with a one-bar delay or at 2× costs |
| H3 | Relative trend | Rotate toward the stronger coin of a pair (fast/slow ratio trend) | Does not beat the control in the forward shadow run |

H1 is the most likely to be real and the least exciting. It also tests whether
the control itself is the product. If the control beats every relationship rule,
QAP's honest answer is "rebalance and do not rotate".

## 6. Product path (the Lab)

The Lab stays the honest front door. Every stage adds one plain-language surface:

- A: "Test many pairs" with a queue and a progress line.
- B: a "Research log" that shows every trial, including failures, and the
  corrected verdict. A teenager reads "1 of 30 ideas worked, and that is about
  what luck gives" instead of a p-value.
- D: a "Live paper run" page: days run, money vs just holding, decisions made.
- E/F: no UI work before the gate decision.

## 7. Decisions for Hamza

Answered 2026-10-27: 1 = No, coins only. 3 = 30 trials per hypothesis, Holm. 4 = 180 days.
Cost gate (stage B rule) approved at 2×. Still open: 2 and 5.

1. ESCALATE — Is USDT (stablecoin cash) an allowed holding for a trend rule that
   steps out of both coins? Today the action space rotates between owned coins only.
2. ESCALATE — Approve the point-in-time universe rule in stage C.
3. Approve a trial budget per hypothesis and the correction method.
4. Approve the forward shadow length (90 or 180 days) before any live gate.
5. ESCALATE — Cost model levers. Binance spot charges less with a BNB fee discount
   and with maker (limit) orders. Modeling either changes cost/fill semantics, and
   maker fills are not guaranteed. Keep today's taker model unless Hamza approves a
   separate, conservative maker model with fill-probability evidence.

## 8. Stop conditions

- Stage B finds no candidate after the revised hypotheses: record `no_edge`,
  keep the Lab as an honest analysis tool, and do not continue to D.
- Any stage needs a change to costs, benchmarks or data roles to pass: stop and
  escalate. Changing the test to pass it is not evidence.
