# QAP Design Direction

**Date:** 2026-09-30
**Status:** Accepted 2026-09-30.
**Serves:** [product vision](vision.md) §8 experience principles.
**Reference (vibe only):** [reference dashboard](assets/reference-dashboard-vibe-2026-09-30.png)

Update context — 2026-09-30
Trigger: Hamza supplied a generated dashboard image as the desired vibe and asked
for a better palette and fixes rather than a copy.
Purpose: define the visual language and the dashboard's information architecture
before implementation.
Impact: replaces the ad hoc styling direction of Phase 18 M6. Existing token
plumbing in `web/src/styles/tokens.css` (commit `6ae7f00`) is kept and re-valued.
Evidence: reference image; WCAG contrast check of the palette below.

## 1. Design read

A professional analysis tool for one expert operator making real-money decisions. The feel is TradingView-grade charts inside calm, restrained
chrome, in the spirit of Linear or Stripe's dashboard. Moderate density: every
number the expert needs is visible, but hierarchy does the work, not boxes.

## 2. Principles

1. **One answer, then proof, then detail.** Visual weight follows that order.
2. **Colour carries meaning, never decoration.** Green and red mean better and worse
   than a benchmark, nothing else. Series colours identify things, not outcomes.
3. **Charts over tables.** A number appears in a table only if it cannot be seen in
   a chart or it is part of the audit.
4. **Each number appears once.** No panel repeats another panel's statistics.
5. **Quiet structure.** Separation by spacing and hairlines; cards only where
   elevation means something (the call, the proof).
6. **Plain words.** "Holding is as good" beats "net edge not significant". The
   precise statistic sits next to it for the expert.

## 3. Palette

The reference used green and red for "hold coin A" and "hold coin B", which
collides with better and worse. The palette separates **semantic colours** (good,
bad, caution, interactive) from **series colours** (what a line is), and every series
colour is distinguishable by people with red-green colour blindness.

### Dark (default)

| Role | Token | Hex | Contrast on surface |
| --- | --- | --- | --- |
| Canvas | `canvas` | `#0b0f14` | |
| Surface (panels) | `panel` | `#11161d` | |
| Raised surface | `raised` | `#18202a` | |
| Hairline | `border` | `#232c38` | |
| Primary text | `foreground` | `#e6ebf2` | 15.2 |
| Secondary text | `secondary` | `#a9b3c1` | 8.6 |
| Muted text | `muted` | `#8390a2` | 5.6 |
| Accent (interactive only) | `accent` | `#5aa0ff` | 6.8 |
| Better than benchmark | `positive` | `#3ecf8e` | 9.1 |
| Worse than benchmark | `negative` | `#f2757a` | 6.6 |
| Caution | `warning` | `#e8b94a` | 9.9 |

### Light

| Role | Token | Hex | Contrast on surface |
| --- | --- | --- | --- |
| Canvas | `canvas` | `#f6f7f9` | |
| Surface | `panel` | `#ffffff` | |
| Raised surface | `raised` | `#eef1f5` | |
| Hairline | `border` | `#dde2e9` | |
| Primary text | `foreground` | `#101722` | 18.0 |
| Secondary text | `secondary` | `#3a4556` | 9.7 |
| Muted text | `muted` | `#5f6b7d` | 5.4 |
| Accent | `accent` | `#1f5fd6` | 5.7 |
| Better | `positive` | `#12804a` | 5.0 |
| Worse | `negative` | `#c2323a` | 5.5 |
| Caution | `warning` | `#9a6400` | 5.0 |

All text colours meet WCAG AA (4.5:1) in both themes.

### Series colours

The same identity in every chart, legend and table.

| Series | Dark | Light | Notes |
| --- | --- | --- | --- |
| Strategy (and the A/B ratio) | `#5aa0ff` | `#1f5fd6` | The accent: it is the subject of the screen |
| HODL of the starting mix | `#d8dde5` | `#394150` | Neutral, the baseline everything is judged against |
| Simple rebalancing | `#f0a94b` | `#b86a00` | Amber, the control to beat |
| Coin A (hold-only line, markers "into A") | `#34c4b4` | `#0e8a7e` | Teal |
| Coin B (hold-only line, markers "into B") | `#b394f7` | `#7a4fd6` | Violet |
| Anchor overlay | `#6b7686` area at ~30% | `#9aa4b2` area at ~30% | Background context; axis labels use `muted` |
| Signal bands (±1σ, ±2σ) | `border-strong` dashed | same | Never coloured |

Trade markers take the colour of the coin being rotated **into**, not green or red,
because a rotation is not good or bad at the moment it happens.

## 4. Typography

- **Geist Sans** for UI and **Geist Mono** for every number (tabular figures),
  self-hosted with `font-display: swap`. Fallback to the system UI stack.
- Scale: 12 (labels), 13 (table and secondary), 14 (body), 16 (section titles),
  22 (the call headline), 28 (key figure in the proof).
- Weight carries hierarchy (400, 500, 600). No oversized headings.
- No uppercase eyebrow labels above every section; section titles are enough.

## 5. Shape, spacing, motion

- Radius: 8 px on panels and inputs, 6 px on buttons, full pill only for toggles and
  the status chip. Applied everywhere.
- 4 px spacing grid; panel padding 16–20 px; 24 px between major regions.
- Motion only for feedback and state change: chart crosshair, value tween on
  recompute (≤150 ms), panel collapse. Respects `prefers-reduced-motion`.

## 6. Dashboard information architecture

Derived from the reference image, with its problems fixed.

**Regions**

| Region | Content |
| --- | --- |
| Top bar (one row) | Product mark; coin A, swap, coin B; anchor; venue; bar size; date range; data-through time. The only place pair, anchor and venue are chosen. |
| Left panel | Methods on/off (measurements and signals) and the active signal's settings, costs, and a quiet "spot only, no leverage, research only" note. Advanced settings collapsed. |
| Centre, top | **The call** (headline, one-line reason, status chip) and **the proof** side by side. |
| Centre, main | Ratio chart: A/B ratio, anchor behind it on its own axis, mean and ±σ bands, rotation markers, crosshair tooltip. The active signal sub-chart shares the time axis. |
| Centre, below | Wealth over time: strategy, HODL mix, best simple rebalancing, hold-A and hold-B. **Value / Coins** switch. |
| Right panel | Evidence: the measurements the user switched on, with live values. Then backtest summary and data and test integrity. |
| Bottom drawer | Every simulated trade and the full statistics table (the audit). |

**Fixes over the reference**

1. Proof shows only proof: walk-forward result vs simple rebalancing and vs HODL,
   folds passing, "tuned on X, proven on Y", settings tried. Relationship statistics
   live only in Evidence.
2. Pair, anchor and venue are chosen once, in the top bar.
3. HODL of the starting mix is added; hold-A and hold-B become context lines.
4. The wealth chart gains a Value / Coins switch.
5. No em dashes or jargon in the call; e.g. "No reliable edge right now. Holding is
   as good as rotating."
6. Win rate is demoted to the audit drawer; it is not a measure of wealth.

**Responsive**

- ≥1280 px: three columns as above.
- 768–1279 px: left panel collapses into a drawer; right panel moves below the charts.
- <768 px: single column: call, proof, ratio chart, wealth chart, then evidence and
  settings as collapsible sections.

## 7. States

Every region has designed loading (skeleton in the final shape), empty, error and
"no edge" states. Data download on first open shows real progress in the call
region, not a separate setup screen.
