# Product Direction Decisions — 2026-09-30

**Status:** Record of the design interview with Hamza on 2026-09-30.
**Outcome:** all decisions settled (see Resolution).
**Legend:** **Settled** = Hamza chose it. **Recommended** = proposed in the interview,
awaiting Hamza's explicit confirmation. **Needs OK** = changes a project rule in
`AGENTS.md`, so it must not be implemented without explicit approval.

Update context — 2026-09-30
Trigger: Hamza asked to be interviewed before further building, then asked for
well-defined direction documents.
Purpose: make every product decision from the interview traceable.
Impact: supersedes the Phase 18 M4–M7 experience direction (see
[Phase 19](../plans/19-pair-rotation-lab-mvp.md)). Does not change the economic
objective, benchmark definitions, cost semantics or the action-space boundary.
Evidence: interview transcript; [vision](vision.md).

| # | Question | Decision | Status |
| --- | --- | --- | --- |
| Q1 | What is QAP for? | An advisor that shows its proof: it studies how coins move relative to each other and to their anchors (correlation, cointegration, copula, ratio, lead-lag, trend) and says when rotating between owned coins beats holding. Hamza acts; QAP does not trade. | Settled |
| Q2 | Starting position and winning | The user holds coins and wants more wealth than holding them, shown in value and coin units. Must demonstrate **real edge**. A **professional variant** is required. | Settled |
| Q3 | Scope of the MVP and "pro" | MVP is **pick two coins, get an answer** on one dashboard: ratio chart, prices, selectable anchor overlay, tuning in a side panel. No approve/verify/prepare ceremony. Portfolio with holdings, multi-coin rotation and automation come later. Pro depth = methods, parameters and full statistics visible in the same app. | Settled |
| Q4 | What "the answer" is | Headline = the call (what to do now, or "no reliable edge, holding is as good"). Under it = the proof (backtest vs HODL and simple rebalancing, after fees). Around it = the relationship explained in charts and statistics. | Settled |
| Q5 | Engine | QAP's existing engine is the judge; statsmodels, pyvinecopulib and arch provide the statistics; vectorbt only if tuning is slow. Because Hamza does not yet trust the engine, an **independent engine (bt) verifies it** with a parity report and hand-computed cases. QAP stays only if they agree. LEAN or Nautilus are reconsidered only for automation. | Settled |
| Q6 | Methods | Full toolbox (measurements and signals, see the [MVP spec](../superpowers/specs/2026-09-30-pair-rotation-lab-mvp-design.md) §4). The user chooses which are on; results appear in a side or bottom panel and recompute on change. Signal delivery order: z-score, lead-lag, copula, trend. | Settled |
| Q7 | "Real-time" | MVP: instant recompute on any change, using data up to the latest closed bar. Live streaming arrives with automation. Lead-lag needs a one-minute refresh when it ships. | Settled |
| Q8 | Data | Binance spot first, Gate second. Bars: 15m (default), 1h, 4h, 1d; 1m for lead-lag. Automatic download on first open and top-up on every open; no visible "prepare" step. | Settled (recommendation accepted) |
| Q9 | Which coins can be researched | Any eligible spot coin, searchable by name or ticker, **without an approval step**. Automatic eligibility still hides leveraged tokens, tokenized stocks and fiat. "Willing to own" returns only for portfolio and automation. | **Settled** (explicit OK: "no select and verify first", 2026-09-30) |
| Q10 | Anchor overlay | QAP suggests the anchor that best explains the pair; the user can switch or add others. | Settled (recommendation accepted) |
| Q11 | Tuning controls | Bar size, lookback, method and its thresholds, hedge-ratio method, rotation size, minimum hold, cooldown, fee tier, slippage. Advanced knobs collapsed. | Settled (recommendation accepted) |
| Q12 | Guarding against overfitting | Tune on older data, prove on unseen data, walk-forward, count settings tried, apply a multiple-testing correction. The call uses proof results only. | Settled (recommendation accepted) |
| Q13 | Simulated rotation trades | Direct pair market if it exists, otherwise two legs through USDT with both fees and slippages. Never trade what is not held. | Settled (recommendation accepted) |
| Q14 | Benchmarks | HODL of the starting mix; simple rebalancing (schedule and drift threshold, strongest shown); hold-A-only and hold-B-only as context lines. Reported in value and coins. | Settled (recommendation accepted) |
| Q15 | Layout | Follows the [reference image](assets/reference-dashboard-vibe-2026-09-30.png) as vibe, with the fixes in the [design direction](design-direction.md) §6. | Settled (vibe) |
| Q16 | Look and feel | Calm, professional, TradingView-grade charts, restrained chrome. Palette to be improved beyond the reference. | Settled (vibe) |
| Q17 | Saving | Autosave each pair view with settings and data cutoff; pinning; saved results never change silently. | Settled (recommendation accepted) |
| Q18 | Where it runs | Locally, single user, no login, for the MVP. | Settled (recommendation accepted) |
| Q19 | Existing plan and code | Phase 18 M4–M7 experience direction is superseded by Phase 19. Keep M1, M2, the corrupt-binding repair from M3, and coin search from M4. Stash the uncommitted scan-screen rework. | Settled (recommendation accepted) |
| Q20 | Build order | Engine parity, then coin search and data, dashboard, z-score with the call, lead-lag, copula, trend. Browser review after dashboard, z-score and lead-lag. | Settled (recommendation accepted) |

## Resolution

On 2026-09-30 Hamza accepted all recommendations ("go with them") and stated the
goal: personal use, make money, with evidence. Q9 is approved on the strength of his
explicit instruction that the MVP must not require selecting or verifying coins first.
"Pair Rotation Lab" is the working name of the MVP surface.
