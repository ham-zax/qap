# QAP Product Vision

**Date:** 2026-09-30
**Status:** Accepted by Hamza on 2026-09-30. This is the product north star; specs,
plans and UI work must trace back to it.
**Decision record:** [decisions-2026-09-30.md](decisions-2026-09-30.md)
**Design direction:** [design-direction.md](design-direction.md)
**MVP spec:** [Pair Rotation Lab MVP design](../superpowers/specs/2026-09-30-pair-rotation-lab-mvp-design.md)

Update context — 2026-09-30
Trigger: Hamza rejected the current research UI as overwhelming and asked to agree
on direction and intent before more building.
Purpose: state in one place what QAP is for, who it serves, what "real edge" means
and what the MVP is, in plain language.
Impact: reframes the product surface and roadmap. The economic objective in the
[system design](../superpowers/specs/2026-08-17-qap-system-design.md) §1 is unchanged.
Evidence: design interview on 2026-09-30 (Q1–Q20), the v2 corpus
(`tradingview_ratio`: PROJECT_INTENT, BULL_RUN_ACCUMULATION_JOURNEY, features doc)
and the reference dashboard image.

## 1. Why QAP exists

Hamza has traded crypto by rotating between coins he believes in for years, reading
ratio charts by eye and deciding manually when to swap one coin for another. It
works sometimes, but it is slow, emotional and impossible to verify. QAP replaces
that manual judgement with measured, honestly tested evidence, first as a research
tool and later as automation.

**In one sentence:** QAP shows how two coins move against each other and against the
coin that drives them, and tells you, with proof, whether rotating between them
would leave you better off than simply holding.

## 2. Who it is for, and the goal

QAP is **for Hamza's personal use**. It is not a product for sale, a service or a
stakeholder report. Its purpose is to **make Hamza money**, a lot of it, and only on
the strength of evidence he can trust enough to act on and eventually automate.

That shapes every trade-off: real, verified edge beats features; honest "no edge"
answers beat flattering charts; speed of insight beats polish for its own sake.
Screens stay plain enough to read at a glance, with every statistic one click away.

## 3. The core idea

Altcoins do not move independently. Most of their movement comes from an **anchor**:
BTC for the whole market, BNB for BNB-chain coins, ETH for Ethereum-ecosystem coins,
and so on. Two coins that share an anchor react to it differently and at different
speeds. One BNB-chain coin might follow BNB within 5 minutes while another follows
45 minutes later.

Those differences create **temporary mispricings between coins you already own**.
If the ratio between two coins stretches unusually far, or one has not yet caught up
with its anchor, shifting some holdings from one to the other and back can grow
total wealth over time. This is rebalancing-driven wealth creation, sometimes called
harvesting relative volatility. It is not directional trading.

QAP studies these relationships with several complementary methods:

| Family | Question it answers |
| --- | --- |
| Correlation and rank dependence | Do they move together, and how tightly? |
| Cointegration and hedge ratio (OLS, TLS, Kalman) | Is there a stable long-run ratio to revert to? |
| Ratio z-score, half-life, Hurst | How stretched is the ratio now, and how fast does it snap back? |
| Copula tail dependence and mispricing | Do they crash or pump together, and is one mispriced given the other? |
| Lead-lag off an anchor | Who follows the anchor, and how quickly? |
| Trend (moving-average direction and slope) | Is the ratio trending rather than reverting? |

New research methods can be added as the field moves on. The method list is open;
the testing standard in §5 is not.

## 4. What winning means

The user starts **holding coins**. Winning means ending with **more wealth than simply
holding the same starting coins**, after real fees and slippage. It is shown both in
USDT value and in coin units, because accumulating the coins you believe in is what
Hamza cares about emotionally, while value relative to holding is the honest test.

A strategy only counts as working if it climbs the whole benchmark ladder:

1. **HODL:** the starting coins untouched.
2. **Simple rebalancing:** reset to the starting split on a fixed schedule or at a
   drift threshold.
3. **The relationship strategy:** it must beat both of the above.

Beating HODL alone is not enough. A simple rebalancing rule often does that for free.

## 5. What "real edge" means

Hamza wants to act with confidence and eventually automate. So the product must be
harder to fool than a chart.

- **Out-of-sample proof.** Settings are tuned on older data and proven on data they
  never saw, with walk-forward re-testing. The headline call uses proof results only.
- **Overfitting is counted.** Every setting tried is a test. QAP records how many
  were tried and applies a statistical correction for trying many.
- **Real costs.** Exchange fees, slippage estimated from volume, and two legs when
  there is no direct market between the coins.
- **An engine that is itself verified.** QAP's backtest engine is checked against an
  independent open-source engine and hand-computed cases before its results are
  trusted.
- **"No edge" is a valid, prominent answer.** When nothing survives, the screen says
  so plainly: holding is as good.

## 6. The product, in horizons

| Horizon | What it is |
| --- | --- |
| **MVP: Pair Rotation Lab** | Pick two coins and an anchor. See the ratio, the anchor's influence, the call, the proof and the statistics on one dashboard. Tune settings and methods live. |
| **Next: portfolio** | Enter the coins you hold and their amounts. Analyse rotations across the whole basket, not only pairs. |
| **Later: automation** | Live data streaming, signal alerts, then paper trading, then (only after a separate readiness gate) automated rotation. |

## 7. What QAP is not

- Not a trading terminal and not a signal-selling service.
- No leverage, margin, borrowing, shorting, derivatives or interest. Spot holdings
  the user owns only, consistent with Shariah constraints.
- No live order placement until a separate live-readiness gate is passed.
- Not a black box: every call can be traced to its data, method, settings and test.
- Not a wall of process: no manual "approve", "verify identity" or "prepare data"
  steps before the user sees an answer. QAP does that work itself.

## 8. Experience principles

1. **Answer first.** The top of the screen says what to do now, or that there is no
   edge.
2. **Proof beside the answer.** How it was tested, on which data, against which
   benchmarks.
3. **Charts are the hero.** The ratio, the anchor behind it and wealth over time
   explain the answer at a glance.
4. **Controls close at hand.** Methods and tuning live beside the chart and update
   it instantly.
5. **Honest by construction.** Out-of-sample results only, costs always on, and "no
   edge" shown as plainly as a winning call.
6. **Calm and professional.** Built to support decisions involving real money.
