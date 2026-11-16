# Continuation checkpoint

State: partial, in review. Branch: `main`. Baseline: `f31cba4`.

The previous session integrated the terminal components. Its last recorded web run passed 74 tests.
Current review found missing control styles, incomplete saved-run restoration, and incorrect fallback preset execution.
Repairs also limit history preparation to HTTP 409 and reset cancelled comparison state.
Saved runs render their stored analysis and restore every chart control.
The coin request now uses 1,000 rows. The live directory contains 619 Binance rows and 415 trading rows.
The prior 600-row request returned only 396 trading rows.

Evidence: all 12 full compiler gates pass in 451.45 seconds.
The full web run includes the additional comparison cancellation test.
TypeScript and production build pass after the final source changes.
Browser checks cover 1,440px desktop, 390px mobile, themes, and local XRP search.
Both viewport checks report no page overflow. The mechanical design detector returns no findings.
Real saved-run loading restores LINK/ETH, 15m, 180 days, a 672-bar band, and BTC benchmark.
A real BTC/ETH strategy test completes without a page alert. Its wealth chart renders.
The result reports $7,027.54 for strategy and $7,079.65 for matched holding.
Those results show a failed strategy, not evidence of profitable performance.

The original API on port 8000 serves an older contract and owns an active paper session.
Do not stop that process as part of frontend checks.
Fresh check services use API port 8001 and web port 5174 during verification.
Initial check services ended with SIGTERM. The cause remains unknown.
The agent closed its browser tab and stopped both check services after verification.
The original services on ports 8000 and 5173 remain running.
All source changes remain uncommitted.

Remaining acceptance:

- Cached-history HTTP requests measured 3.56–4.90 seconds during the live strategy check.
  A browser request during the full tests took 3.12 seconds. The below-two-second target remains open.
  An isolated process took 5.70 seconds cold and 1.53–1.55 seconds warm.
  Its profile attributes 1.01 seconds to repeated research-scope construction, mainly directory fingerprints.
  These timings have different load and process conditions. They do not establish an end-to-end speedup.
- The API uses an omitted anchor for automatic selection. The explicit no-benchmark
  option needs a separate design decision under the repository's benchmark boundary.
- The mode switch remains in the ticker. The approved header placement remains open.
- Human usability acceptance and multi-day paper stability remain untested.

Evidence: [90-evidence.md](90-evidence.md). Full gate log: `/tmp/qap-phase24-gate.log`.
Next: measure the full chart-opening path and remove repeated directory hashing with freshness checks.
Resolve the explicit no-benchmark design before changing backend benchmark behavior.
Drift decision: retain Phase 24 in review. No economic or research boundary changed.


## Follow-up checks — 2026-11-16

Update context: user requests rapid pair edits and completion of remaining checks.
Purpose: record implemented behavior and current measurements.
Impact: no changes to economic objectives or research benchmarks.

Rapid edits now wait 250 ms before analysis starts. Both selectors remain usable.
Request cleanup cancels browser work and ignores obsolete results.
Preparation retries only HTTP 409 with `operation_busy`, once per second.
The wait stops on selection changes and ends after 1,200 attempts.
Server preparation already in progress continues under its existing operation owner.
The UI shows a waiting state instead of a resource-busy error.

Explicit `anchor="none"` now works in sample data as well as the backend and UI.
The header owns the Simple/Pro switch. Both views share the same mode store.
Web checks pass: 84 tests, plus one separate header synchronization test.
The pair-edit test delivers the obsolete response after the latest result.
The latest result stays visible.
Browser checks show Pro mode, None selected, seven chart canvases, and no alerts.

Timing evidence on check ports 8001 and 5174:
- Browser analysis requests: 1,006 ms and 91 ms.
- Prepared no-anchor HTTP request: 15 ms warm.
- Cold no-anchor HTTP request: 3,887 ms during the full test run.
These measurements establish fast prepared requests, not a universal cold-load limit.
The below-two-second cold-load target remains open.

Full compiler gate: all 12 checks pass in 430.57 seconds after formatting and TypeScript repairs.
The full Python suite passes in 372.42 seconds. The full web suite includes 85 tests.
Fresh-process HTTP after tests: 2,210 ms for no-anchor analysis.
The next automatic-anchor request takes 518 ms.
The cold result still exceeds two seconds. No universal cold-start claim is accepted.
Check services stop after measurements. Original services remain untouched.
Logs: `/tmp/qap-final-gate.log` and `/tmp/qap-final-gate-rerun.log`.

## Cold-start follow-up — 2026-11-16

Added fast-path bar/fingerprint/storage checks, `AssetResolver.resolve_markets`,
`coins_for_listings`, single-snapshot `research_scope_from_snapshot` in
`PairRotationAnalysis.analyze`, and bounded concurrent `ProductMarketData.projection()`.

Fresh-process HTTP after edits on check port 8001 (`create_default_app --factory`):
- Cold no-anchor analysis: 1,911 ms (under the 2,000 ms target; down from 2,210 ms / 2,171 ms).
- Warm automatic-anchor analysis: 543 ms.
- Cached no-anchor hit: 186 ms (first cached hit; 56 ms on repeat).
- Advisor auto / no-anchor: 59 ms / 50 ms.

## Strategy presets, Lead-Lag 1m, and UI control upgrades — 2026-11-16

Completed remaining review items:
- Fixed `product_lab_advisor.py` to emit all 4 strategy presets (`zscore_kalman`, `spread_copula`, `zscore_ols_wide`, `ratio_trend`) and avoid claiming benchmark parking when no benchmark is selected or covers the window.
- Fixed Anchor Lead-Lag `1m` validation mismatch: selecting `lead_lag` auto-switches the bar interval to `1m`, warns and disables testing if switched away, and `preparePair` in `labApi.ts` passes `base_interval: '1m'` when preparing 1m data.
- Added slider controls (`RangeField`), conditional Crash Drawdown Trigger slider, inline Auto-tune badge, `InfoTip` click popovers (benchmark, validation gate, Overview KPIs), and aligned tests in `LabCockpit.test.tsx`, `labApi.test.ts`, `test_lab_advisor.py`, `test_lab_cli.py`, and `test_lab_studies.py`.
- All 12 compiler gates pass in 454.50 seconds (`pytest_full` 400.68s, `web_vitest_full` 12.67s, `web_build` 5.65s; log `/tmp/qap-phase24-final-verify.log`).
- Check services on port 8001 stopped after measurement; original services on ports 8000 and 5173 remain untouched.
