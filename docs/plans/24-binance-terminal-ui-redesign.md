# Phase 24 — Binance-Grade Progressive Terminal + Bottom Tabs UI Redesign

**Status:** Approved by Hamza 2026-11-15 after live walkthrough & cold-start Binance trader teardown.

Implementation status — 2026-11-16: in review. The terminal integration passes all
12 compiler gates. See the [continuation checkpoint](../aegis/work/2026-11-16-phase24-terminal/20-checkpoint.md)
for executed browser checks and remaining acceptance gaps.
The follow-up adds rapid pair-edit handling, sample no-anchor support, and the header mode switch.
Prepared browser requests meet two seconds. Cold requests under test load remain above that target.

Update context — 2026-11-16
Trigger: provider handoff and integration checks.
Purpose: record current evidence separately from approved requirements.
Impact: no change to economic, benchmark, or research decisions.
Evidence: the continuation checkpoint and `/tmp/qap-phase24-gate.log`.

```text
Update context — 2026-11-15
Trigger: Hamza rated the Stage S6 3-column text-heavy layout 1/10 (slow directory load, only 3 Binance coins shown, 5-line disclaimer inside top bar, weird patronizing copy like "Usual level over 672" / "Pick for me" / "Recent togetherness", fake Simple/Advanced toggle, silent saved-study jumps) and approved all 4 structured UX decisions.
Purpose: Replace the cluttered 3-column text wall on `/lab` with a crisp, fast, progressive Binance Spot Terminal + Bottom Tabs experience that serves both everyday Binance users (Simple default) and advanced quants (Pro mode).
Impact: Frontend (`web/src/features/lab/`, `AppShell.tsx`) + `/api/pair-rotation/coins?venue=binance&limit=600` (2.4 ms warm, all 396 eligible Binance USDT coins). Backend financial/math authority is unchanged.
Evidence: Cold-start Binance trader UX teardown, Impeccable craft-floor rules, Hamza's 4 questionnaire choices (2026-11-15).
```

---

## 1. Settled UX Architecture (Hamza's 4 Decisions)

1. **Layout — Binance Terminal + Bottom Tabs:**
   - **Slim 1-Row App Header (`44px`):** `QAP` brand + `Lab` / `Jobs` subtle nav + `[Simple | Pro]` segmented pill (defaults to **`Simple`**!) + single **Sun/Moon SVG icon button** (NEVER the word `"Auto"`!).
   - **Slim 1-Row Pair Ticker Bar (`52px`):**
     - `[Coin A ▾] [⇄] [Coin B ▾]`
     - **Live Ratio Readout right in the bar:** `0.0584` + stretch badge (`-6.8% vs 30d MA · -2.1σ`, tabular mono)
     - **Interval pills:** `15m | 1h | 4h | 1D` (default **`1h`** instead of fee-heavy `15m`!)
     - **Window pills:** `30D | 90D | 180D | 1Y`
     - **Benchmark selector:** `Benchmark: Auto (BTC)` (`BTC`, `ETH`, `BNB`, `SOL`, `None`) with `(i)` tooltip
     - **Refresh icon button** (`↻ Sync latest candles` — only runs `/open` on demand or when data is missing!)
     - **ZERO disclaimers or multi-line helper paragraphs in the ticker bar!**
   - **Above-the-Fold Split Hero (`minmax(0, 1fr) 340px`):**
     - **Left/Main Hero Canvas (Immediate Chart Above the Fold!):**
       - Chart header tabs: **`Ratio Chart`** | **`Wealth Curve ($10,000)`** (with `USDT | Coin A | Coin B` unit pills when on Wealth Curve, and `±2σ Band` / `Benchmark` toggles when on Ratio Chart).
       - In `Pro` mode after a test, synced **Signal Oscillator (`Z-Score / Copula Tail / MA Spread`)** renders cleanly directly below the Ratio pane.
     - **Right Action & Verdict Panel (`340px`, sticky):**
       - **Saved-Run Banner** (when viewing a loaded saved run): clearly states `"Viewing Saved Run (Pair · Bar · Time)"` with `"Edit Settings"` / `"Reset"` so clicking a saved run is never silent or confusing!
       - **Verdict Summary (`$10,000` Base Explicit!):**
         - Before test: clean pair stretch summary (*"SOL/ETH is 6.8% below its 96-bar MA (-2.1σ). Pick a strategy preset below to backtest on $10,000."*)
         - After test: **`$10,000 → $11,140`** (`+7.14% vs Hold $10,400` · `+6.66% vs Rebalance`), `24 swaps · $416 fees`, and a clear Pass/Fail badge (`Validated 5/8 Folds` or `No Net Edge After Fees` — Hold beats swapping).
       - **Strategy Picker:**
         - **`Simple` mode (Default):** **3 clickable Strategy Preset Cards** powered by Smart Advisor (`Mean Reversion · Buy Dip Coin`, `Tail Mispricing · Copula`, `Trend Follow · Ride Stronger Coin`) showing 1-line trader rationale + `Test Strategy` primary CTA + `Compare All 3` button. Zero raw math inputs!
         - **`Pro` mode:** Unlocks full trader controls with clear units (`Strategy: Z-Score | Copula | Trend | Lead-Lag`, `Regression: Ratio | OLS | TLS | Kalman`, `MA / Lookback Period` showing real duration e.g. `96 bars (4.0 days)`, `Entry / Exit (σ or tail %)`, `Swap Size: 25% | 50% | 75% | 100%`, `Crash Stop: Hold Pair | Park Benchmark | Park USDT`, `Auto-Tune`, `Min Hold / Cooldown / Fee bps`).
   - **Bottom Workspace Tabs (Full width below the Hero):**
     1. **`Overview`** — 4 crisp trader KPI cards (*Correlation*, *Mean-Reversion Half-Life*, *Regime / Trend*, *Benchmark Fit*) in plain trader terms with `(i)` hover tooltips.
     2. **`Compare Strategies`** — Side-by-side table comparing tested/preset strategies (`Strategy | Ending $10k | vs Hold | vs Rebalance | Swaps | Fees | Verdict | View`).
     3. **`Simulated Swaps (N)`** — Clean trade log (`Time | Action | Route | Fee | Slippage`).
     4. **`Saved Runs (N)`** — Pin, inspect, and load past studies (clicking one syncs pair/chart AND shows the Saved-Run banner!).
     5. **`Live Paper`** — Start, step, and stop live Binance L2 order-book paper sessions (`vs Hold`, `vs Rebalance`, 4-clock latency in ms).
     6. **`Pro Diagnostics`** *(shown in `Pro` mode or as last tab)* — Full Cointegration ADF `p`, Kalman `β ± SE`, Granger Lead-Lag, Copula `λL / λU`, Walk-Forward Folds table, SPA `p`-values, and Dataset SHA-256 provenance.

2. **All 396 Active Binance Spot Coins + Instant Open:**
   - Single startup call `GET /api/pair-rotation/coins?venue=binance&limit=600` (`2.4 ms` warm!) loads all `396` eligible Binance Spot USDT coins at once.
   - Coin selector popover shows **Top Quick-Pick Chips (`BTC`, `ETH`, `SOL`, `BNB`, `XRP`, `DOGE`, `LINK`, `ADA`, `AVAX`, `SUI`)** + instant local search across all `396` tickers and names!
   - **Cache-First Pair Open (`loadLab`):** Call `GET /api/pair-rotation/analysis` **first**! If cached data exists on disk, render charts immediately in `< 2 s` without spawning `/open`. Run `POST /api/pair-rotation/open` automatically **only** when `/analysis` reports missing history (409) or when the user clicks `↻ Sync`.

3. **Impeccable Craft Floor Enforcement:**
   - Zero `border-left: 3px solid` slop (`impeccable detect --json web/src/features/lab` must return `[]` 0 warnings!).
   - Tabular monospace (`font-variant-numeric: tabular-nums`) on every price, ratio, percentage, and fee.
   - Dark theme default on first visit (matching Binance Spot), clean light theme support, `overflowX === false` at `1440px` and `390px`, every file `< 500` lines.
