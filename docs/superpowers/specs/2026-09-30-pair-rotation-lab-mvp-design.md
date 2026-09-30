# Pair Rotation Lab — MVP Design

**Date:** 2026-09-30
**Status:** Accepted 2026-09-30. All [decisions](../../product/decisions-2026-09-30.md) settled.
**Vision:** [docs/product/vision.md](../../product/vision.md)
**Design direction:** [docs/product/design-direction.md](../../product/design-direction.md)
**Plan:** [Phase 19](../../plans/19-pair-rotation-lab-mvp.md)
**Baseline contracts kept:** [QAP system design](2026-08-17-qap-system-design.md)
(economic objective, benchmark ladder, cost and fill semantics, research integrity,
spot-only action space).

Update context — 2026-09-30
Trigger: design interview and reference dashboard.
Purpose: specify the MVP precisely enough to plan and accept it.
Impact: new product surface. Supersedes the Phase 18 M4–M7 experience direction.
No change to the economic objective, benchmark definitions, cost/fill semantics,
holdout roles or action-space boundary. Q9 (research any eligible coin without
admission) changes universe admission for research; Hamza approved it.
Evidence: decision record Q1–Q20.

## 1. Goal

A holder picks two coins and an anchor and, within seconds, sees:

1. **The call:** rotate now (and which way), or no reliable edge.
2. **The proof:** out-of-sample, after-cost results against HODL and simple
   rebalancing, with the testing protocol stated.
3. **The explanation:** the A/B ratio with the anchor behind it, the active signal,
   wealth over time and the chosen measurements.

They can change methods and settings and see everything recompute immediately.

## 2. Non-goals for the MVP

- Portfolios with entered holdings and multi-coin rotation.
- Scanning the whole market for pairs.
- Live streaming, alerts, paper trading, automation or any order placement.
- Accounts, hosting or sharing links.
- Manual asset admission, identity mapping or data preparation screens.

## 3. User flow

1. Open the app. The dashboard shows the last pair viewed (or a suggested pair on
   first run).
2. Type in coin A and coin B (name, ticker or market symbol, e.g. "Wormhole", "W",
   "W/USDT"). Ineligible listings never appear.
3. QAP suggests an anchor (§4.3); the user may change it.
4. If data is missing or stale, QAP downloads it. Progress appears in the call region;
   charts fill as soon as data is available.
5. The call, proof, charts and evidence render. Defaults: 15m bars, last 6 months,
   z-score signal with default settings.
6. The user toggles methods, drags settings, changes bar size or dates. Results
   recompute; the proof updates its "settings tried" count.
7. The view is autosaved. The user can pin it and reopen it exactly later.

There is no step between 2 and 5 that asks the user to approve, verify or prepare
anything.

## 4. Analysis content

### 4.1 Measurements (descriptive, shown in Evidence when switched on)

| Measurement | Output shown |
| --- | --- |
| Correlation of returns (Pearson, Spearman), Kendall's tau | Value over the window; rolling series on hover |
| Cointegration (Engle-Granger; Johansen optional) | p-value, pass or fail |
| Hedge ratio (OLS, TLS, Kalman) | Current ratio and its stability |
| Half-life (Ornstein-Uhlenbeck fit) | Hours or bars |
| Hurst exponent of the ratio | Value; reverting, random or trending |
| Copula tail dependence (lower, upper) | λL and λU with fitted family |
| Beta to anchor, for each coin | Values |
| Lead-lag to anchor | Lag of each coin behind the anchor (cross-correlation peak and Granger test) with stability flag |
| Regime | Volatility state; trending or ranging |
| Current ratio percentile | Percentile over the window |

### 4.2 Signals (can produce the call)

Each signal is a pure function from aligned bars and settings to a target weight
between the two coins, so strategies stay swappable and portable to a future live
engine.

| # | Signal | Core settings | Delivery |
| --- | --- | --- | --- |
| 1 | Ratio z-score mean reversion (variants: Bollinger, RSI on ratio) | Lookback, entry z, exit z, hedge method | First |
| 2 | Anchor lead-lag trigger | Anchor move threshold, lag window, follower choice | Second |
| 3 | Copula mispricing index | Window, family, entry and exit probability | Third |
| 4 | Ratio trend (MA direction, slope, crossover) | Fast and slow lengths, slope threshold | Fourth |

Common settings: rotation size (partial or full), minimum hold, cooldown, fee tier,
slippage model.

### 4.3 Anchor suggestion

For candidate anchors (BTC, ETH, BNB, SOL and any coin the user adds), compute each
coin's beta and lead-lag strength. Suggest the anchor that explains the most joint
variance. Show why ("BNB explains 61% of both coins' moves").

## 5. The call

| Status | When | Example headline |
| --- | --- | --- |
| Rotate A → B | The active signal fires now **and** its proof passes (§6.4) | "Rotate PIXEL → W" |
| Rotate B → A | Same, other direction | "Rotate W → PIXEL" |
| Hold | Proof passes but the signal is not firing | "Hold. No rotation signal right now." |
| No reliable edge | Proof fails | "No reliable edge right now. Holding is as good as rotating." |
| Not enough data | Below the method's minimum history | "Not enough history yet: 12 of 60 days downloaded." |

Under the headline: one plain-language reason (e.g. "Ratio 2.3σ above normal; BNB up
1.4% in the last hour") and a status chip. The call never uses in-sample results.

## 6. Proof and research integrity

### 6.1 Data split

The selected range splits chronologically into a **tuning** part (older) and a
**proof** part (newest, default 30%). Walk-forward additionally re-tunes on a
rolling window and tests on the next unseen block (default 8 folds).

### 6.2 Benchmarks

Measured from the same starting holdings (default 50/50 by value) with identical
costs:

1. **HODL of the starting mix.**
2. **Best simple rebalancing:** fixed schedule (daily, weekly) and drift threshold
   (±5%). The strongest over the tuning part is the control, chosen before looking
   at the proof part.
3. **Context lines:** hold-A-only and hold-B-only.

Results appear in USDT value and in coin units.

### 6.3 Overfitting control

Every distinct combination of method and settings evaluated for a pair is counted in
a per-pair **research family**. The proof reports the count and applies a
multiple-testing correction (White's Reality Check or SPA via `arch`, or a deflated
Sharpe ratio). Walk-forward fold pass counts are shown.

### 6.4 Pass criteria for "real edge"

A signal's proof passes when all hold:

- Out-of-sample terminal wealth beats HODL **and** the simple-rebalancing control,
  after costs.
- The corrected test is significant at the configured level (default 5%).
- At least 5 of 8 walk-forward folds beat the control.
- Enough trades out-of-sample to be meaningful (default ≥ 10).

The thresholds are shown on screen and changeable in advanced settings; changing
them counts as a new setting tried.

### 6.5 Costs and fills

Existing QAP semantics: decisions use completed bars only; fills at the next bar
with fee and slippage. Route through the direct A/B market when it exists; otherwise
two legs via USDT, each paying fee and slippage. Default fee is Binance spot 0.10%
per side (0.075% with the BNB-discount option). Slippage is volume-scaled with a
floor. Only held inventory can be sold.

## 7. Engine and verification

- **Judge:** QAP's existing replay, execution, cost and HODL evaluation modules.
- **Statistics:** `statsmodels`, `arch`, `pyvinecopulib` behind adapters, per
  [OSS_REUSE_BOUNDARY](../../OSS_REUSE_BOUNDARY.md).
- **Tuning speed:** `vectorbt` only if interactive recompute misses the latency target
  (§9), and only for exploration, never for the proof.
- **Independent verification:** `bt` runs the parity suite (§10, M0). If `bt` cannot
  be installed on Python 3.14, the fallback is a separate minimal pandas reference
  implementation written independently of QAP's engine, decided in M0.

## 8. Data

- Venue: Binance spot USDT markets first; Gate second.
- Bars: 15m (default), 1h, 4h, 1d from stored 15m or native bars; 1m added for
  lead-lag.
- History: as far back as the exchange provides; at least 12 months of 15m.
- Freshness: top up to the latest closed bar on open; a pair view older than two bars
  shows "refresh".
- Identity: resolved automatically by the M2 resolver; coins with unresolved identity
  are still viewable, labelled, but cannot make a call.

## 9. Performance targets

- First render of a cached pair: under 2 seconds.
- Recompute after a settings change (6 months of 15m bars, one signal, proof and
  walk-forward): under 1 second at the 95th percentile on Hamza's machine.
- First download of a new pair: progress visible within 1 second.

## 10. Acceptance criteria

1. **Engine parity:** HODL, periodic rebalancing, threshold rebalancing and one signal
   strategy agree between QAP and the independent engine on three recorded pairs to
   within 0.01% terminal value and identical trade counts. Five hand-computed cases
   match exactly. The report is committed.
2. **Search:** "Wormhole", "W", "W/USDT" and "W_USDT" find W; leveraged tokens and
   tokenized stocks do not appear.
3. **No ceremony:** from an empty workspace, choosing two coins reaches a rendered
   answer with no approval, identity or preparation screen.
4. **Honest call:** on a pair where the signal overfits (in-sample win, out-of-sample
   loss), the call reads "No reliable edge". A seeded synthetic pair with a real edge
   produces a rotate call.
5. **Recompute:** the §9 targets are met and measured.
6. **Benchmarks:** every result shows HODL mix, the rebalancing control and hold-A and
   hold-B, in value and coins.
7. **Design:** desktop and mobile screenshots in dark and light are reviewed and
   accepted by Hamza against the design direction.
8. **Repository gates:** Phase 00 verification commands and the web suite pass.
