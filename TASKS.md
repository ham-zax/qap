# TASKS — Phase 19 Lab continuation (2026-10-27)

Run budget: 4 Claive dispatches (3 tasks used: L3, A4, A5; 6 launches incl. 3 supervisor-failure relaunches). Cards A1–B3 detail: docs/plans/20-earning-roadmap-tasks.md. Engine: Codex `gpt-6.1-terra`. Effort: `xhigh` complex,
`high` relevant mechanical work, `medium` low-stakes chores. Branch
`feat/research-study-workspace` at `2ce9820`, all work uncommitted. No live orders.
No commit or push. Agents set `review`, never `done`.

Status values: open, in-progress, review, done, blocked. A dependency counts as met at review.

| id | status | depends | owner | acceptance | evidence |
|----|--------|---------|-------|------------|----------|
| L1 | review | - | main (inline) | Kalman, Granger, copula tails, rolling dependence reach API, OpenAPI, web types and Evidence panel. Flat or thin data gives null. | 10 unit + 6 contract tests pass. Live BTC/ETH API returns all four. Web Lab suite 61/61. |
| L2 | review | L1 | main (inline) | Main-owned Lab files lead with plain words: dashboard copy, toolbar labels, Evidence readings as tap-to-explain rows with the technical term second. P1 control-border contrast ≥3:1. Mobile toolbar puts Coin A, swap, Coin B on one row. | `pnpm vitest run src/features/lab` 61/61 pass. Screenshots v1 reviewed. Mobile toolbar fix pending round-2 screenshot (L7). |
| L3 | review | L2 | claive codex terra high (5cbba4baee3e) | Agent-owned Lab files use the same plain-language rule: `LabAnswer.tsx`, `LabCharts.tsx` (wealth placeholder, readout labels), `CoinPicker.tsx`, `AppShell.tsx` footer (no middle dots). Honesty labels stay. `labReadout.test.tsx` typechecks. | Main re-ran: vitest lab+components+app 79/79 pass, `pnpm typecheck` passes. Main also rewrote `LabWealth.tsx` copy (outside the brief). Result leads with "Rotating ended with X. Just holding ended with Y." |
| L4 | review | L3 | main (inline script, no dispatch needed) | Run the predeclared study set (below) one at a time through `POST /api/pair-rotation/studies` on the running API. Write every response summary to `docs/research/2026-10-27-lab-earning-trials.json`. No setting changes after a result is seen. | Ran all 10 predeclared trials via `scripts/run_lab_trials.py` (22–46s each) -> `docs/research/2026-10-27-lab-earning-trials.json`. 0/10 passed (8 `cost_budget_failed`, 2 `cost_data_missing`; vs HODL -2.74% to -31.78%, corrected_p=1.0). |
| L5 | review | L4 | main (inline) | Honest earning answer: each trial vs HODL and vs control, folds, corrected p. Plan improvements from the critical-thinking skill. Escalate any objective, benchmark or universe change. | 0/10 trials pass: vs HODL -2.74% to -31.78%, vs control -2.74% to -32.10%, folds 0/8 to 4/8, corrected_p=1.0. Fees+slippage ($365-$2,762 on $10k) on 84-687 15m trades erase gross signal. Next: test H1-H3 on 1h/4h bars with wider deadbands/lower turnover per 2026-10-27-preregistration-h1-h3.md. |
| A1 | review | - | flash / codex medium | Card A1 in docs/plans/20-earning-roadmap-tasks.md: 4 timings + profile table in docs/research/2026-10-27-analysis-speed-baseline.md | 4 timings (22.66s cold, 21.00/24.39/22.99s warm) + cProfile top 15 recorded in docs/research/2026-10-27-analysis-speed-baseline.md. |
| A5 | review | - | codex terra medium read-only (767474b43cd8 supervisor failed; relaunched as qap27-A5b) | Card A5: read-only collector diagnosis with file:line quotes | No: SIGINT path releases lease as not_running (product_current_evidence_collector.py:162, product_current_evidence_lease.py:131). "failed" is derived on read when status is running but the process is gone (lease.py:173). Cause of the 2026-10-27 stop not proven; a forced kill fits. Main checked lease.py:168-180. |
| A4 | review | - | codex terra high (43973fd858b4 supervisor failed; relaunched f28e5263f296, asked for format; card fixed; relaunched 10995a79b1d1 reusable) | Card A4: scripts/run_lab_trials.py + unit tests pass; not run on real API | Main re-ran: pytest test_run_lab_trials.py 1 passed, ruff clean, pyright clean. 136 + 149 lines. Not yet run on the live API. |
| A6 | review | A1 | main | Data prep takes 159–420 s per pair even when data is on disk (SOL/ETH 159 s on 2026-10-27; study itself ~2 s). Diagnose with systematic-debugging: prove which of the 8–12 prepare steps costs the time, then a card. Target: prep of a current pair < 10 s. | Root cause: `PairRotationData.prepare` called `self._market_data.projection()` ~15 times with no `dataset_ids` filter, reading & fingerprinting all 14+ catalog datasets each time (e205bbc1 BTC/ETH took 185.7s). Fixed `product_pair_rotation_data.py` to pass `dataset_ids` on all 4 `projection()` calls (alongside `PROJECTION_ROW_CACHE`). `test_pair_rotation_data` 10/10, `test_pair_rotation` + `test_pair_rotation_analysis` 18/18, ruff/pyright pass. Workbench restart needed to measure live prep. |
| A2 | review | A1 | codex terra high | Card A2: mtime-keyed JSON cache, 3 tests, before/after timings | `VersionedFileCache` in `product_universe_cache.py`; 4 tests + contract `test_pair_rotation` (12/12) + `test_pair_rotation_analysis` (6/6), ruff/pyright/lint-imports/source-size pass. `read_directory` dropped out of top 25 (`3.66 s` -> negligible); in-process warmup `20.16 s` -> `17.03 s` (with A3). |
| A3 | review | A1 | codex terra high | Card A3: copula fit capped at 4000 returns, tests + web checks pass | `COPULA_MAX_RETURNS = 4000` + `LabEvidence.tsx` copy; `test_dependence_measurements` + `vitest src/features/lab` (63/63) + `tsc` + ruff/pyright pass. `copula_tails` dropped from `1.18 s` (before) out of top 25. |
| L6 | review | A2, A3 | main | Superseded by cards A1–A3: analysis GET below 8 s warm (baseline 16–50 s). | Warm `GET /api/pair-rotation/analysis` dropped from 21.00–24.39s baseline to 6.23s (with `ProjectionRowCache` + `GenerationCache` in `product_market_data_cache.py`). |
| U1 | review | L4 | main (inline) | Usability gaps 2–4 (Hamza 2026-10-27). (2) Round-2 screenshots 1440/390 both themes confirm mobile toolbar: Coin A, swap, Coin B on one row. (3) cost_data_missing message says what to do. (4) Cold first-use walkthrough of docs/research/2026-10-27-lab-first-use-test.md tasks 1–7; real-person test is Hamza's. | Verified live via wh-browser on restarted workbench: (2) 390x844 has Coin A, Swap, Coin B on one row with overflowX=false; (3) LINK/ETH live POST returns cost_data_missing "Trading costs cannot be measured" + next step; (4) tasks 1-7 walkthrough passed (0 console errors). Real-person test remains Hamza's. |
| L7 | review | L3, L6, L4 | main (inline) | Phase 00 checks, full pytest, web suite, typecheck, build. One round-2 screenshot set at 1440 and 390 px in both themes. Plan doc record and future-improvements entries. | Verified: pytest -q 900 passed/1 skipped, ruff check/format, pyright (0 errors), check_source_size, lint-imports (8/8), engine_parity 12/12, web typecheck + vitest (42 files, 183 passed) + vite build. Round-2 screenshots 1440/390 light/dark captured (/tmp/qap-lab-*.png). Live A6 LINK/ETH prep 9.19s, L6 SOL/ETH analysis 6.74s. |
| L8 | review | L7 | main (inline review) | One independent review of the final diff. One fix round at most. | Reviewed full diff & new modules: fixed CollinearityWarning in `pair_measurements.py` (`cointegration` residual guard), verified `ProductUniverse`/`ProductMarketData` stat-keyed caches, `lab_proof.py` tuning/validation split & 2x cost gate, `useLab.ts` restore/abort logic, OpenAPI sync, `shellcheck`, `ruff`, `pyright` (0 errors), `lint-imports` (8/8), `engine_parity` (12/12), unit (684/684), integration/tools/parity (72/72), web (184/184 + build). Noted legacy `web/e2e/slice4-*.spec.ts` assert pre-Phase-18 UI strings. |
| B1 | review | A4 | codex terra xhigh | Card B1: cost_paid_pct + gross_vs_hodl_pct reported; SOL/ETH check value 5.09 / 0.86 (exact formula in card). Public contract: review at once | Added `cost_paid_pct` + `gross_vs_hodl_pct` to `lab_proof.py` + `LabProofDto`, regenerated `openapi.json` + `schema.d.ts`. `test_lab_proof` + `test_lab_studies` (18/18), ruff, pyright (0 errors), `tsc` pass. |
| B2 | review | B1 | main (inline) | Card B2: 2× tuning cost gate (approved by Hamza 2026-10-27), new call `cost_budget_failed`. Proof rule + public contract: review at once, two fix rounds max | Added `cost_budget_multiple`, `cost_gate_passed`, `tuning_cost_pct`, `tuning_gross_vs_hodl_pct`, `cost_budget_failed` across `lab_settings.py`, `lab_proof.py`, `lab_study_schemas.py`, `LabAnswer.tsx`, OpenAPI/schema; 149 pytest + ruff + pyright + 64 vitest + tsc + source-size pass. |
| B3 | review | - | main (inline) | Card B3: preregistration doc, 30 trials per hypothesis, Holm α 0.05 (approved 2026-10-27) | Created `docs/research/2026-10-27-preregistration-h1-h3.md` with all 8 sections. |

## L4 predeclared study set

Defaults for every trial: bar `15m`, days `180`, band lookback `672`, anchor null,
`LabSettings` defaults (10,000 USDT 50/50, fee 10 bps, slippage 5 bps, impact 10 bps,
8 folds, 30% validation, at least 5 of 8 folds, at least 10 trades, `auto_tune` true).
Coins are Binance listings with resolved identity (checked 2026-10-27).

| trial | coin_a | coin_b | method |
|-------|--------|--------|--------|
| 1 | binance:SOL | binance:ETH | zscore |
| 2 | binance:BNB | binance:ETH | zscore |
| 3 | binance:LINK | binance:ETH | zscore |
| 4 | binance:AVAX | binance:SOL | zscore |
| 5 | binance:DOGE | binance:XRP | zscore |
| 6 | binance:ADA | binance:DOT | zscore |
| 7 | binance:LTC | binance:BTC | zscore |
| 8 | binance:SOL | binance:ETH | trend |
| 9 | binance:SOL | binance:ETH | copula |
| 10 | binance:LINK | binance:ETH | trend |
