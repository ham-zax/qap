# Phase 19 — Pair Rotation Lab MVP

**Status:** Approved 2026-09-30; current phase. Direction: [vision](../product/vision.md),
[decision record](../product/decisions-2026-09-30.md),
[MVP design](../superpowers/specs/2026-09-30-pair-rotation-lab-mvp-design.md).
The tracker (§4) is the single place to record progress.

Update context — 2026-09-30
Trigger: Hamza redirected the product after the design interview: pick two coins,
get an honest answer on one dashboard, with real edge and a verified engine.
Purpose: order the MVP work and define exits.
Impact: supersedes the experience direction of Phase 18 M4–M7 (search is kept;
backend research requests are reduced to "fetch and compute on open"; the M6 UI
rebuild is replaced by M3–M7 here). Phase 18 M1 and M2 remain the foundation.
Evidence: [decision record](../product/decisions-2026-09-30.md).

## 1. Carried over from Phase 18

- **Kept and done:** M1 exchange metadata (`438b3d9`); M2 registry, resolver and
  eligibility (`62dd8e0`); web foundation, themes and passing web suite (`6ae7f00`).
- **Kept, still to do:** repair the contradicted `W → BTC` binding (D6); coin search
  by name, ticker and market alias (M4 search).
- **Dropped from the MVP path:** durable multi-stage research requests, scan
  preparation, custom-experiment lineage UI, stored-data retirement beyond the
  corrupt binding. Revisit for portfolio and automation horizons.
- **Parked:** the uncommitted scan-screen rework from 2026-09-30 (stash, not commit).

## 2. Milestones

Each milestone lands as small reviewable commits with Phase 00 verification and the
web suite green.

### M0 — Confirm and de-risk

- Commit the accepted direction documents; stash the parked scan-screen rework.
- Dependency spike on Python 3.14: `statsmodels`, `arch`, `pyvinecopulib`, `bt`
  (and `vectorbt` only if needed later). Record versions and any blockers; choose the
  independent reference engine if `bt` cannot install.
- Apply the palette and typography from the design direction to the existing tokens.

**Exit:** documents committed; dependency spike recorded; tokens updated.

### M1 — Engine parity report

- Independent reference implementation of HODL, periodic rebalancing, threshold
  rebalancing and one simple signal strategy.
- Five hand-computed cases (single swap, two-leg route, fee rounding, partial
  rotation, insufficient inventory).
- Three recorded real pairs over 6 months of 15m bars.

**Exit:** MVP design §10 criterion 1 passes; the report is committed. If parity fails,
stop and escalate with the diffs before continuing.

### M2 — Coins and data without ceremony

- Search API over the M2 resolver: names, tickers and market aliases; eligibility
  applied.
- Research on any eligible coin without admission (Q9, approved).
- Automatic download and top-up of Binance 15m bars on open, with progress; 1h, 4h
  and 1d derived.
- `W → BTC` binding repair.

**Exit:** criteria 2 and 3 pass against the API.

### M3 — Dashboard with measurements

- Pair analysis API: aligned series, ratio, anchor, measurements (§4.1) and anchor
  suggestion.
- Dashboard shell per the design direction: top bar, left settings, ratio chart with
  anchor overlay, wealth chart with Value and Coins, Evidence panel with toggles,
  audit drawer, all states.

**Exit:** browser review by Hamza on real pairs (desktop, mobile, dark, light).

### M4 — Z-score signal, proof and the call

- Signal 1 as a pure function; benchmarks; tuning and proof split; walk-forward;
  research-family counting and multiple-testing correction; the call.
- Instant recompute within the §9 targets (add `vectorbt` exploration only if needed).

**Exit:** criteria 4, 5 and 6 pass; browser review by Hamza.

### M5 — Lead-lag with 1-minute data

- 1m bars for the pair and anchor; lead-lag measurement and signal 2; one-minute
  refresh while the view is open.

**Exit:** lead-lag verified on recorded data; browser review by Hamza.

### M6 — Copula

- `pyvinecopulib` adapter; tail dependence measurement; signal 3.

### M7 — Trend

- Signal 4.

### M8 — Acceptance

- Full MVP design §10; Hamza accepts the experience. Then decide on the portfolio
  horizon.

## 3. Constraints

- Economic objective, benchmark ladder, cost and fill semantics and the spot-only,
  no-leverage boundary are unchanged from the system design.
- No live order placement.
- Third-party engines and libraries stay behind adapters; QAP owns accounting.
- Source files under 500 lines where possible; import-linter layers hold.

## 4. Tracker

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | Done 2026-09-30 | Docs `8a42983`; spike and tokens in §5 |
| M1 | Not started | |
| M2 | Not started | |
| M3 | Not started | |
| M4 | Not started | |
| M5 | Not started | |
| M6 | Not started | |
| M7 | Not started | |
| M8 | Not started | |

## 5. M0 record (2026-09-30)

### Dependency spike (Python 3.14.4, uv)

| Package | Version | Smoke check | Result |
| --- | --- | --- | --- |
| `statsmodels` | 0.15.0 | `coint` on synthetic cointegrated pair | Works |
| `arch` | 8.0.0 | `SPA` test on synthetic losses | Works |
| `pyvinecopulib` | 1.0.0 | `Bicop.from_data` fit | Works |
| `bt` (with `ffn` 1.2.2) | 1.2.3 | Periodic rebalance backtest with commissions | Works |

Environment at spike time: numpy 2.5, pandas 3.0, scipy 1.18.1. No blockers, so the
fallback independent minimal engine is not needed; `bt` is the M1 reference engine.

- Caveat: under pandas 3, `bt` emits `ChainedAssignmentError` from
  `bt.core.get_transactions` (`positions[x.name] = x.positions` in Cython code). It
  is a false positive of pandas' reference-count check on compiled code; the
  transactions are populated correctly. The M1 harness also derives trades from
  position differences as a cross-check rather than trusting that table alone.
- Only `bt` is added now (dev dependency group; M1 test/reference use only).
  `statsmodels`, `arch` and `pyvinecopulib` are added to project dependencies by
  the milestones that first use them (M4, M4, M6).

### Tokens

- `web/src/styles/tokens.css` carries the design-direction palette (dark default,
  light by system preference or `data-theme`), the series colours as
  `--chart-series-1..5` plus named aliases (`--chart-strategy`, `--chart-hodl`,
  `--chart-rebalancing`, `--chart-coin-a`, `--chart-coin-b`, `--chart-anchor`,
  `--chart-band`), the 22/28 title/display sizes and 8 px panel radius. Token names
  and the theme mechanism are unchanged.
- `subtle`, `border-strong`, `info` and `context` are not specified by the direction;
  they are interpolated from the neighbouring specified tones.
- Geist Sans and Geist Mono are self-hosted through `@fontsource-variable/geist` and
  `@fontsource-variable/geist-mono` 5.3.0 (bundled by Vite, `font-display: swap`).
