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
- **Completed in M2 below:** repair the contradicted `W → BTC` binding (D6); coin
  search by name, ticker and market alias (M4 search).
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

### M3 execution checkpoint — 2026-10-23

Trigger: Hamza requested continuation after the October 22 gap investigation.
Purpose: connect the existing measurements to immutable data and a usable Lab.
Impact: implements the accepted M3 direction. Economic rules remain unchanged.
Evidence: accepted MVP design §3–4, product decisions Q1–Q20 and current sources.

- Baseline: `2ce9820` on `feat/research-study-workspace`. Existing staged measurement
  modules, their tests, dependency changes and untracked Lab files are preserved.
- Analysis reads exact fingerprinted generations through the existing market-data
  owner. GET performs no download, identity binding, admission or financial write.
  The existing background data-open operation remains the sole acquisition path.
- Preparation retains at least 365 days. Analysis windows are 30/90/180/365 days,
  ending at the latest shared completed bar. No incomplete bars or forward fill.
- `GET /api/pair-rotation/analysis` returns the Lab contract. Undefined measurements
  use null. Coin identity, cutoff and immutable dataset fingerprints remain visible.
  Missing anchor history never substitutes pair prices or generated sample data.
- The dashboard supports coin search, automatic preparation, progress and retry,
  interval/window/band controls, ratio/anchor charts, evidence and a dataset audit.
  M3 says "Strategy not tested". Strategy wealth, trading calls and proof require M4.
  Existing expert routes remain reachable. No saved result changes silently.
- Code is necessary because neither a data-open result nor sample data supplies
  real analysis. Minimum boundary: analysis composition, typed API response and Lab.
  New modules stay below 500 lines and separate data, rendering and request state.
- TDD route: off / skipped. Add regression and API interaction tests after changes,
  covering read-only behavior, identity, exact data, alignment and typed failures.
- Sequence: analysis API and contract tests; connected dashboard and interaction
  tests; Phase 00 and web checks; desktop/mobile/theme browser checks.
- Human browser acceptance remains pending until Hamza reviews M3. Continue with
  M4 only after that existing milestone gate. The later 2026-10-23 finish request
  authorizes continued implementation before that review; human acceptance remains
  pending. No commit or push is authorized.

- Economic objective, benchmark ladder, cost and fill semantics and the spot-only,
  no-leverage boundary are unchanged from the system design.
- No live order placement.
- Third-party engines and libraries stay behind adapters; QAP owns accounting.
- Source files under 500 lines where possible; import-linter layers hold.

## 4. Tracker

| Milestone | Status | Evidence |
| --- | --- | --- |
| M0 | Done | Docs `8a42983`; dependencies/tokens `9434143`; spike in §5 |
| M1 | Done 2026-10-02 | [Independent parity report](../research/2026-10-02-engine-parity.md); 12/12 comparisons, 5/5 exact hand cases; verification below |
| M2 | Backend implemented; rendered-answer acceptance pending | API and cleanup record in §7; dashboard/analysis remains M3 onward |
| M3 | Initial data-backed slice implemented 2026-10-23; human acceptance pending | Analysis API, `/lab`, evidence and audit; record below. Remaining measurement depth and M4 strategy wealth are explicit. |
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

## 6. M1 record (2026-10-02)

Update context — 2026-10-02
Trigger: Hamza asked to continue the backend work, stopping before UI generation.
Purpose: record the engine gate and move to M2 under the accepted Phase 19 scope.
Impact: no economic, cost/fill, benchmark or holdout semantics changed. Dashboard
work (M3 here) remains outside this continuation.
Evidence: [parity report](../research/2026-10-02-engine-parity.md),
[machine-readable results](../research/2026-10-02-engine-parity.json).

Three recorded pairs over six calendar months of 15m bars pass all four strategies:
terminal error below 2.9e-15 relative, identical executed leg counts, inventory
coordinates within 0.0001 USDT of value. Five QAP hand-computed inventory cases
match exactly; bt's hand arithmetic agrees within 1e-10 floating precision. The
report names its limits: USDT settlement on real runs, direct and rounding hand
cases, historically unconstrained metadata, fixed per-leg costs, shared declared
policy rules. This is accounting verification, not strategy-edge evidence.

Phase 00 checks passed for the M1 checkpoint: 769 Python tests passed, one opt-in
network test skipped; Ruff, Pyright, source-size (39 existing review warnings) and
all eight import-linter contracts passed. All 116 web tests and production build
passed. An independent read-only Muse review found no verified blockers; its
inventory-coordinate suggestion was incorporated. The verification-runner timeout
test now allows interpreter startup under suite load while preserving its timeout
assertions. M2 receives its own integrated verification after owner changes.

## 7. M2 backend record (2026-10-02)

Update context — 2026-10-02
Trigger: Hamza asked to continue and finish the backend before UI generation.
Purpose: record the admission-free data path and bounded D6 cleanup accurately.
Impact: implements Q9/D1–D7 through existing universe, data and operation owners.
Criterion 3's rendered answer remains unaccepted until M3/M4; no dashboard work
starts in this continuation. Broader Phase 18 retirement remains outside the MVP.
Evidence: API contract tests `tests/contract/api/test_pair_rotation.py`, data and
universe unit tests, and retirement tests `tests/contract/api/test_identity_retirement.py`.

- `GET /api/pair-rotation/coins` searches names, tickers and market aliases from
  cached evidence; leveraged and synthetic listings are excluded. Responses expose
  identity/call availability, observation times and registry attribution. GET does
  neither fetches the network nor changes state or waits on refresh writer locks.
- `POST /api/pair-rotation/bootstrap` refreshes public directory/registry evidence;
  `POST /api/pair-rotation/open` opens two Binance spot USDT listings without
  admission. Existing operation records carry queued/download/derived progress,
  exact dataset fingerprints/cutoffs and typed errors. Identical running requests
  reuse the same operation across API instances; interruption permits retry.
- Data preparation starts with a year of 15m history and tops up to the latest
  completed bar, independently of a stale directory timestamp. Complete UTC 1h,
  4h and 1d buckets derive from exact immutable 15m parents. Reopening current
  data makes no upstream history request; partial download/client failure releases
  maintenance for retry. Longer explicit lookbacks extend existing generations.
- The universe owner accepts evidence-derived bindings, seeds USDT, keeps conflicts
  for review and separates venue-local unresolved research from economic identity.
  Unresolved coins remain viewable inputs with the economic call blocked. Portfolio
  admission and existing finance scopes retain their checks.
- D6 was applied to the local `runs`/repository-root data workspace. The preview
  found two mislabeled datasets (`binance-spot:WUSDT:1:1:1h` and `:4h`) and no saved
  dependencies. Their catalog entries and four parquet/provenance files were removed;
  four valid generations remain. Exact old provenance is retained in the ignored
  audit `runs/product/identity-retirements/3e81c85282e19672ebf0dc08474defe74c0a163c2c9076dd91a8a53fd94deb94.json`.
  The bad mapping is retired in v2 state; BTC admission awaits reconfirmation.
  No old series was relabeled and no saved result was deleted.
- Legacy v1 reads remain bounded migration support for other existing workspaces.
  The MVP drops blanket stored-data/compatibility retirement beyond this corruption;
  existing review/admission expert routes remain available until the UI work.

The backend API part of criterion 2 is covered by all required W aliases and
eligibility cases. The empty-workspace contract test verifies year-long acquisition,
eight immutable outputs, progress, reload, and current-data reuse without approval
or identity screens. This establishes data readiness, not a rendered analysis answer,
strategy edge, the UI experience, or live network performance.

The live registry refresh returned `unavailable / budget_exhausted` after its
bounded traversal. Cached directory search and venue-local research remain
available; W, BTC and PIXEL are currently unresolved and cannot make an economic
call. Registry evidence must recover before those calls become available. This
is an external-data limitation, not an inferred identity or automatic admission.

The integrated Phase 00 suite passed: 810 Python tests, one opt-in network test
skipped; Ruff, formatting, Pyright, all eight import contracts and source-size
checks passed (40 review warnings, no file above 700 lines). Operations remains
one lifecycle owner at 519 lines; universe contracts/policy/search and retirement
inventory are separate pure modules, while mutable writes stay with their existing
owners. Final targeted rechecks and web verification are recorded below before
commit. The independent read-only Muse review found no verified blockers; the
concurrent/busy API tests caught and verified a correction for immutable boundary
exceptions passing through Python's generator context managers.

Final rechecks passed after making cached search read-only (61 affected tests) and
blocking contradicted identities in untouched legacy finance scopes (31 tests).
All 116 web tests and the TypeScript/production build passed with regenerated
OpenAPI and API types. The stop point is M3 dashboard/analysis; rendered-answer,
performance and representative-user acceptance remain future gates.

## 8. Initial M3 implementation record (2026-10-23)

Trigger: Hamza requested continuation after context recovery and the October 22 gap report.
Purpose: record the connected Lab slice and its remaining acceptance boundary.
Impact: local workspaces open `/lab`. Descriptive analysis gains no economic authority.
Evidence: analysis contract tests, Lab interaction tests and live BTC/ETH browser checks.

- `GET /api/pair-rotation/analysis` reads exact sealed generations, verifies their
  identity and fingerprint, uses shared completed bars and returns finite typed
  measurements, ratio bands, anchor data, cutoffs and provenance. GET performs no
  acquisition, identity binding or admission write. OpenAPI and web types regenerate.
- The existing universe owner exposes a read-only scope option. Pair preparation
  uses cached registry evidence. Registry acquisition remains with the explicit
  refresh operation. A live first-open check exposed the former 300-second registry
  wait; the worker regression refuses registry refresh during ordinary pair opening.
- The Lab connects eligible Binance search, automatic preparation, progress, typed
  failures and retry, saved settings, interval/window/band controls, ratio/anchor
  charts, measurement visibility and the dataset audit. Saved pairs and standard
  anchors resolve independently of the first 100 search results. Control changes
  reuse prepared data. Late aborted responses cannot replace current analysis.
- Measurements handle flat hedge subwindows, tied lags, constant volatility and
  non-finite cointegration results. Small ratios retain meaningful chart precision.
  Hurst appears as an estimate, not a categorical promise. The specified at-or-below
  ratio percentile remains unchanged. No strategy call or profitable-edge claim is made.
- Full Python suite: **832 passed, 1 skipped**. After the live registry-delay fix,
  **18 affected API tests passed**. Full web suite: **124 passed**. Final control reuse
  tests: **5 passed**, chart precision/accessibility tests: **4 passed**. Production
  build, Ruff, formatting, full Pyright, source-size and all eight import contracts
  passed. Source-size retains 40 existing review warnings and no failure.
- DeepSeek V4.1 through Pi reviewed measurement edge cases. GPT-6.1 Sol reviewed
  integration, then checked the fixes in a second round and reported no blockers.
- The real Binance BTC/ETH view rendered 4,320 hourly bars through
  `2026-10-23T13:00:00Z`. Both identities remained unresolved and economic calls stayed
  blocked. Desktop (1440 px), mobile (390 px), dark/light themes and real chart
  rendering were checked. Both viewport widths had no document overflow. Labelled
  sample responses were used briefly for design checks, then removed by navigation.
- **Remaining:** Hamza's M3 browser acceptance, remaining measurement depth (Kalman,
  Granger, copula and rolling dependence), immutable saved-result/pinning behavior,
  and M4 strategy wealth/proof. Current browser persistence stores settings only.
  Startup has no frozen-result acceptance claim. M3 is not marked fully accepted.
- Final browser correction: the global evidence-table minimum width clipped the
  chart's internal table on mobile despite no document overflow. Chart containers
  now exempt their internal tables from that rule. At 390 px, both chart table and
  container measure 324 px. Final chart/Lab tests: **8 passed**; build passed.
  One live 1h-to-4h change issued only analysis GET and completed in 2,096 ms. This
  observation is not a comprehensive performance acceptance result.
- Existing staged and untracked work remains. No commit, push or live order occurs.
  [Retrospective proposals](../future-improvements.md) record follow-up work without
  changing project rules or adding new checks automatically.

## 9. MVP completion checkpoint — 2026-10-23

Trigger: Hamza explicitly requested finishing the app and a dedicated UI/UX agent.
Purpose: execute remaining accepted MVP requirements without intermediate approval pauses.
Impact: implementation continues through M4–M7. Human M8 acceptance is still separate.
Evidence: accepted MVP design, decisions Q1–Q20 and the current working tree.

Baseline: `2ce9820`, current branch and all uncommitted M3 work are preserved.
Task scope is the local single-user research Lab. No portfolio horizon or live orders.
Architecture review is required for the study/snapshot boundary. Existing accounting,
fills, inventory, immutable datasets and eligibility owners retain their authority.
TDD route: off / skipped. Add meaningful regression, economic and API checks.

### Contracts and decisions

- New study POST computes from sealed datasets. GET analysis remains read-only.
  A Lab study store owns trial counting, immutable completed studies and pin metadata.
  Reopening a study reads its original result, never current data. New settings or
  new market data create a new result. No retirement or deletion is authorized.
- Strategies are pure causal targets: ratio z-score, anchor lead-lag, copula and trend.
  One selected signal drives the call. Measurements never create an action themselves.
- Starting holdings default to a 50/50 mix worth 10,000 USDT. Controls start with the
  identical inventory. Daily, weekly and 5% drift controls compete only on tuning data.
  The selected control is frozen before validation. Eight chronological walk-forward
  folds choose thresholds using older data only. The newest 30% is validation.
- Proof uses after-cost wealth against both HODL and the selected control, a seeded
  SPA test and conservative family-count correction, at least 5/8 passing folds and
  at least 10 validation rotations by default. Reused validation is explicitly labelled.
  No result claims untouched final-OOS evidence after inspection.
- Execution composes existing QAP planning, fill and ledger functions. Decisions use
  completed bars and fills use observed next opens. Direct pair data is required when
  a direct market is selected. Otherwise both USDT legs pay fees and slippage.
  Slippage uses an explicit volume-impact estimate plus a configured floor. Missing
  required execution data blocks proof; it never becomes synthetic market evidence.
- Minute data supports lead-lag and refreshes once per minute while selected. Display
  intervals retain their existing meaning. Insufficient history stays an honest state.
- UI preserves accepted tokens, fonts and chart hierarchy. Simple/Full modes change
  detail only. Call, proof, ratio, signal, wealth, evidence and audit share one dashboard.
  Saved views expose their original cutoff. Costs remain enabled in every result.

### Execution and evidence

1. Implement settings, pure signals, authoritative replay and proof tests.
2. Integrate one-minute/direct market acquisition, remaining measurements and studies.
3. Implement immutable saves/pins and complete the dashboard using the UI agent brief.
4. Review scientific and economic boundaries. Run required suites sequentially.
5. Check real desktop/mobile/light/dark journeys and measured latency. Record every
   unmet criterion. Stop for human acceptance only after implementation/checks finish.

Current step: backend study API checkpoint reached. Dashboard continuation remains
pending. The UI design brief is available. See the bounded checkpoint below.

### Backend wrap-up checkpoint — 2026-10-24

Update context: Hamza requested the nearest checkpoint before ending the session.
Purpose: connect and test the study API, then record a usable handoff.
Impact: pause dashboard implementation after this backend checkpoint. The accepted
MVP scope remains unchanged. No whole-app completion or M3 acceptance is claimed.
Evidence: current study, replay, proof and immutable-store implementation in the
working tree. Fresh focused API and economic checks define the evidence below.

Fresh backend evidence:

- **40 focused tests passed** across study API, proof, replay, immutable store,
  pair preparation and descriptive analysis. The study contract exercises real
  sealed datasets, validation folds, trades, changed-setting counts and reopening.
- Unit checks cover causal signals, next-open fills, both routed legs, direct fills,
  matched HODL, no-edge behavior, chronological tuning, bootstrap reproducibility,
  correction floors, blocked calls and neutral exits. Snapshots reject tampering.
- Ruff lint and formatting pass. Full `pyright src tests scripts` reports zero
  errors. All eight import contracts pass. Source size passes with 40 existing
  review warnings. `git diff --check` passes.
- OpenAPI export and web type generation pass. `pnpm typecheck` passes with the
  regenerated contract. No new dashboard implementation is claimed.
- Two statsmodels rank-deficiency warnings arise from the deterministic study
  fixture. These passing checks do not establish statistical calibration.
- Full Python/web suites, live study-server checks, performance targets and the
  final scientific/economic review are not part of this checkpoint's evidence.

Implemented boundary:

- `api/routes/lab_studies.py` is registered in `api/app.py`. Study POST composes
  sealed data, causal signals, existing fill/ledger owners and validation proof.
- `product_lab_study.py` owns composition. `experiment/lab_replay.py` owns the
  replay adapter. `experiment/lab_proof.py` owns chronological tuning and proof.
  `policy/lab_settings.py` and `policy/lab_signals.py` own pure signal settings.
- `product_lab_store.py` owns content-addressed result files, integrity checks,
  trial counts and separate pin metadata. Reopening never reads current datasets.
- The current call follows the replay's last executed preference. A neutral exit
  can rotate back to the starting mix. An unchanged preference does not create a
  fresh rotation merely because prices drift. Minimum notional uses the setting.
- Proof discloses that observed venue constraints remain fixed during historical
  simulation. Missing identity or execution evidence blocks economic calls.
- OpenAPI and generated web types must stay synchronized with these routes.
  The existing server launcher does not reload Python changes automatically.

Resume here:

1. Connect `web/src/features/lab/useLab.ts` to the study API without stale results.
   Add controls, call/proof, signal/wealth charts, trade audit and saved-result views.
2. Use the design agent's Simple/Full dashboard brief. Keep accepted Geist fonts,
   semantic colors and synchronized charts. Simple/Full changes presentation only.
   Split pair controls, settings, answer, audit and saved views into focused files.
3. Complete remaining measurement contracts: Kalman, Granger, copula tails and
   rolling dependence. Feature helpers alone do not establish API/UI completion.
4. Check one-minute/native-pair acquisition and venue metadata through the real
   worker. Add minute refresh and browser recovery. Current identity gaps remain
   explicit. Do not infer admission or identity from a ticker.
5. Obtain independent scientific/economic review. Measure six-month performance.
   Run the full repository and web suites, then real browser journeys in both
   themes and mobile/desktop sizes. Human M3/M8 acceptance remains separate.

Stop boundary: backend study API checkpoint only. M4–M7 are not accepted or complete.
All edits remain uncommitted on `feat/research-study-workspace` at `2ce9820`.
Preserve the pre-existing staged files and all untracked work during continuation.

### Delegated continuation — 2026-10-24

Update context: Hamza requested delegation of the remaining work to DeepSeek Pi
at Max through T3 orchestration V2. This request resumes the remaining MVP work.
Purpose: execute one bounded assignment at a time and review every result.
Impact: the backend checkpoint remains valid. Whole-app completion remains pending.

Confirmed selection: provider `pi`, model
`opencode2api/deepseek-v4.1-flash-free`, option `thinking=max`.
T3 returned the requested provider/model/option and a running first task.

First assignment, completed: read-only proof and execution review, including chronology,
current calls, benchmark matching, correction and immutable result identity.
Review task ID:
`node:delegated-task:command%3Amcp%3Ad6ed20a7-ac1c-4f29-a2b3-0fd99d88b6a1%3Adelegate-task%3Aqap-finish-pi-max-proof-review-20261024-r1`

Subsequent assignments remain planned, not launched: resolve review findings,
dashboard integration, missing measurements, acquisition/refresh checks,
performance and final browser/tests. Parent owns interfaces, integration and
final acceptance. Avoid concurrent heavy jobs on this 7 GB machine.

Workspace constraint: this T3 thread is bound to a non-repository scratch folder.
The first reviewer reads `/home/hamza/repo/qap` explicitly without writes.
Before implementation delegation, resolve repository-bound T3 worktree isolation.
Do not silently assign writers to the shared dirty checkout or omit uncommitted
dependencies from a worktree based on HEAD.

Review response and next assignment:

- F1 is accepted for the routed partial-metadata path. The service computes a
  blocked-readiness flag, but proof replay reaches strict execution first and can
  raise before returning the blocked call. The earlier 40-test checkpoint did not
  cover this case. Its passing receipt is not acceptance of missing-data recovery.
- Fix design: return a blocked study before any strategy or rebalancing replay
  when execution readiness is false. Retain only HODL/hold-A/hold-B context paths.
  Preserve canonical executor checks. Add unit and real study-API regressions.
- F2's missing reuse label on shifted overlapping validation needs a separate fix.
  Trial identity and code-version counting need a distinct, explicit decision.
- F3 proof/call eligibility, F4 hold/cooldown wording and F5 proposed rotation size
  remain follow-up contract questions. F4's use of the stricter elapsed-bar limit
  is not accepted as an implementation bug merely because the smaller limit is
  redundant. Do not change economic timing from this review alone.
- T3 reports this thread attached to scratch with no branch, not a QAP checkout.
  The next Pi task therefore prepares a read-only exact patch artifact in `/tmp`.
  The parent applies, reviews and tests it. No shared-checkout writer is launched.

Completed F1 patch-proposal task (provider/model/Max option confirmed):
`node:delegated-task:command%3Amcp%3Ad6ed20a7-ac1c-4f29-a2b3-0fd99d88b6a1%3Adelegate-task%3Aqap-pi-max-f1-patch-proposal-20261024-r1`

F1 integration evidence: the parent inspected and applied the three-file patch.
The repository run passes **25 focused tests**, Ruff lint/format and changed-file
Pyright with zero errors. Four statsmodels warnings come from deterministic price
fixtures. Missing metadata now returns a saved blocked study with only non-trading
context paths. Full-metadata proof and immutable reopening remain covered. No
commit occurs. The canonical executor's strict metadata preflight remains intact.

Next slice, F2 reuse labelling:

- Keep distinct-configuration counts and configuration fingerprints unchanged in
  this slice. Code-version overcount is conservative and remains a separate issue.
- Extend the existing trial rows with deduplicated validation-window history.
  Preserve each row's first window, configuration and first-seen timestamp. Older
  rows without history still contribute their recorded first window.
- Compute overlap from all previous windows before recording the new observation.
  A shifted overlapping window is reused even for unchanged settings. A newly
  tried setting on overlapping history is reused too. Exact repeated requests on
  otherwise unchanged history remain idempotent. Disjoint windows are not reused.
- Keep the existing store as the single owner. No second journal, deletion or
  snapshot rewrite. Invalid stored history fails closed with files preserved.
- Check unit history cases and an API run after a sealed-data cutoff advances.

Failed F2 patch-proposal task, confirmed Pi / DeepSeek V4.1 Flash / Max:
`node:delegated-task:command%3Amcp%3Ad6ed20a7-ac1c-4f29-a2b3-0fd99d88b6a1%3Adelegate-task%3Aqap-pi-max-f2-reuse-patch-20261024-r1`

Update context: Pi returned HTTP 429 `FreeUsageLimitError`. No completed patch was
returned. The parent continues the bounded F2 fix inline without changing provider.
Design refinement: each window also retains a monotone `reused` flag. Without
that flag, an expanded configuration batch can return reused on its first request
and incorrectly return fresh on its identical retry. Preserve an observed reuse
fact on later retries. Counts still represent distinct settings, not observations.

F2 integration evidence:

- The parent implemented the approved reuse fix in the existing store owner.
  Window history is additive. Original configuration, first cutoff and first-seen
  fields remain intact. Legacy rows contribute their recorded first window.
- Ten new store checks fail against the old implementation and pass after the fix.
  An API check advances sealed data by one hour, keeps the settings count at one,
  labels reuse, preserves exact retry identity and reopens the original result.
- The fresh combined run passes **36 focused tests**. Full Ruff lint/format and
  `pyright src tests scripts` pass. All eight import contracts pass, as does
  `git diff --check`. Eight deterministic-fixture rank warnings remain disclosed.
- Changed files are `product_lab_store.py`, `test_lab_store.py` and
  `test_lab_studies.py`. They contain 267, 208 and 312 lines respectively.
  No snapshot file, existing trial record or Git index is deleted or reset.
- Code-fingerprint counting, F3/F5 interface decisions, remaining measurement/UI
  work, final economic review, full-suite and browser/performance acceptance remain
  open. This slice does not complete the app.

Earlier delegation state: DeepSeek Pi's free quota prevented further use of the
requested worker. Hamza selected waiting for DeepSeek, then explicitly requested
a retry. No alternate worker model is selected automatically.

Retry context — 2026-10-24: Hamza said the quota should work and asked to continue.
The live T3 catalog still advertises Pi DeepSeek V4.1 Flash with `thinking=max`.
T3 accepted a fresh read-only review of the completed F1/F2 fixes and returned
`running` with the requested provider, model and option. This launch receipt alone
does not prove the upstream quota is restored. Await the worker's actual result.

Failed retry review task:
`node:delegated-task:command%3Amcp%3Ad6ed20a7-ac1c-4f29-a2b3-0fd99d88b6a1%3Adelegate-task%3Aqap-pi-max-proof-fixes-review-20261024-r2`

The retry returned HTTP 429 `FreeUsageLimitError`, identical to the first quota
failure. No review result was produced. F1/F2 retain their parent test evidence,
but independent review remains pending. Hamza's selected route is waiting for
DeepSeek quota. Do not select another provider or retry repeatedly without new
quota evidence or user direction. No background quota monitor is scheduled.

Second user-requested retry — 2026-10-24: Hamza again said DeepSeek should work
and requested continuation. A fresh review round uses the live-catalog Pi model
`opencode2api/deepseek-v4.1-flash-free` with confirmed `thinking=max`.
T3 returned `running`. Upstream quota recovery remains unconfirmed until the
reviewer produces actual work or a terminal result. F1/F2 are already implemented.

Failed second retry review task:
`node:delegated-task:command%3Amcp%3A967616a9-1e4e-42c2-8c56-1e157959dc0a%3Adelegate-task%3Aqap-pi-max-proof-fixes-review-20261024-r3`

The second requested retry also returned HTTP 429 `FreeUsageLimitError`. No
independent review completed. Keep Hamza's selected wait-for-DeepSeek route.
No alternate provider, repeated automatic retry or quota monitor is started.

OpenCode retry — 2026-10-24: Hamza explicitly requested OpenCode DeepSeek.
This supersedes the earlier wait-for-Pi route. The live catalog advertises
`opencode` / `zengate/deepseek-v4.1-flash-free` with `variant=max`.
T3 accepted a fresh F1/F2 review with that exact selection and returned `running`.
Provider acceptance remains distinct from successful upstream work.

Completed OpenCode review task:
`node:delegated-task:command%3Amcp%3A271e70b0-dd17-44f9-945f-255d163ebb1d%3Adelegate-task%3Aqap-opencode-deepseek-proof-fixes-review-20261024-r4`

OpenCode review result: **36 tests pass**. F1's readiness gate and F2's canonical
window history comply with the brief. The worker found a new direct-route crash
with full metadata when a MARKET notional filter needs an explicit reference.
The direct replay caller omits that argument, while the routed caller supplies it.

Update context: fix the confirmed direct-replay caller defect before UI integration.
Purpose: preserve canonical notional filters and next-open fill semantics.
Decision: supply the observed direct-market next open as both execution reference
and notional reference, matching the existing routed replay convention. No USDT
ratio or invented cross price substitutes for the native observation. Filter
rejections remain no-fill results. Add minimum/maximum filter and proof regressions.
This small, tightly coupled fix stays inline under the updated AGENTS instructions.

Review limit: F2 validates stored history shape, ordering and reuse flags, but not
calendar-valid ISO timestamp strings. The writer emits canonical UTC values.
Non-canonical stored strings remain an explicit follow-up, not a reviewed guarantee.

Direct-filter fix evidence: five new regressions reproduce the missing-reference
exception before the fix. The parent added the native observed open argument and
an explicit proof limitation about average-price approximation. The combined run
passes **56 tests**, including direct execution and precision neighbors. Changed-file
Ruff and Pyright pass. Minimum and maximum filters still reject invalid fills.
An initial test-fixture relative import failed because the unit folder is not a
package. The corrected tests use local fixtures. No import failure remains.

Next frontend slice: a typed study transport adapter, with no component/hook change.
Expose compute, list, immutable reopen and pin operations through the current Lab
HTTP helper. Generated OpenAPI types own response shapes. Input settings may be
partial because Python supplies defaults. No strategy interpretation, local saved
results, automatic sample fallback or new economic defaults belong in this adapter.

Completed adapter patch-proposal task, OpenCode DeepSeek Max:
`node:delegated-task:command%3Amcp%3A271e70b0-dd17-44f9-945f-255d163ebb1d%3Adelegate-task%3Aqap-opencode-deepseek-lab-study-adapter-20261024-r1`

Adapter integration: parent inspected and applied the three-file patch. The nine
focused transport tests and TypeScript check pass. The initial `pnpm test -- ...`
invocation unexpectedly ran the whole suite and exposed a stale chart-label test.
The chart displays eight significant digits while retaining the persisted value.
The corrected assertion checks both the formatted label and unchanged raw value.
Fresh full web evidence: **132 tests pass**, followed by `pnpm typecheck`.
For future focused Vitest runs use `pnpm exec vitest run <files>`.

Next UI slice: standalone call/proof component and scoped CSS, using the accepted
Anthropic/Impeccable direction. It renders backend headlines/reasons and target
allocation, never computes an action from measurements or proof statistics.
Loading/error takes precedence over any previous result. Proof remains labelled
validation. A passing statistical result with blocked call eligibility gets a
neutral unavailable-call explanation. Do not render the unresolved
`rotation_fraction` field as a traded amount. Hook/dashboard wiring follows.

Interrupted call/proof patch-proposal task, OpenCode DeepSeek Max:
`node:delegated-task:command%3Amcp%3A271e70b0-dd17-44f9-945f-255d163ebb1d%3Adelegate-task%3Aqap-opencode-deepseek-lab-answer-20261024-r1`

Restart context — 2026-10-24: Hamza requested stopping and rerunning the panel
agent. The latest provider event reports: "No upstream route produced a response
within the admission deadline." A handoff was requested first. No completed panel
patch was returned. T3 cancellation was checked: the old task is `interrupted`,
with no pending child runs. Existing artifacts and repository files remain intact.

The parent recovered the complete original brief and started one fresh task with
the same three-file scope, provider/model and `variant=max`. The new task is
accepted as `running`. No second concurrent panel writer is started.

Active restarted panel task:
`node:delegated-task:command%3Amcp%3A271e70b0-dd17-44f9-945f-255d163ebb1d%3Adelegate-task%3Aqap-opencode-deepseek-lab-answer-20261024-r2`

Call/proof integration — 2026-10-24: the restarted panel task completed with
`/tmp/qap-lab-answer-20261024-130030.diff`. The parent inspected the artifact,
applied it after `git apply --check --whitespace=error-all` passed, and kept all
three files. The panel renders backend headlines, reasons and target allocation.
It never derives an action from measurements or proof statistics.

Hook/dashboard wiring: `useLab` owns one abortable study request, resets it on every
settings change and refuses a second concurrent run. The strategy test stays
explicit because `POST /api/pair-rotation/studies` persists one saved study. The
empty state keeps "Strategy not tested"; running shows indeterminate progress; a
failure keeps its message and offers one retry. A result replaces the empty state
and the header status changes to "Call and validation".

Wealth: the saved study's `wealth` curves now drive a second chart. Strategy,
starting-mix HODL and the selected control share one USDT axis. Extra hold curves
stay out of the chart. Terminal values appear as a small table, and `window_kind`
labels validation versus context-only. With no study, the honest "Strategy not
tested" placeholder remains.

Evidence: 25 focused Lab component tests (5 dashboard interaction, 20 panel) and
`pnpm typecheck` pass. Fresh full web evidence: **153 tests pass** across 39 files,
and `pnpm build` passes. No Python source changed in this slice.

Browser acceptance — 2026-10-24: live API on 127.0.0.1:8000 and Vite on
127.0.0.1:5173, page `/lab`. BTC/ETH with 15m/4h/1d execution data was prepared
first. The Lab open request now carries `include_execution: true`; the live open
completed 12 of 12 units.

A study at 15m, 180 days, band 672 returned call `identity_unresolved`. The panel
shows "Coin identity is unresolved" and keeps charts available. The proof reads
"Validation does not pass": 1 of 8 folds, 95 validation rotations, corrected
p-value 1, versus starting-mix HODL -2.69%, versus daily rebalancing -2.70%.
"Validation data reused" appears because the earlier 1h study on the same pair
registered the same validation window.

The wealth chart shows strategy 9,746.30 USDT, starting-mix HODL 10,015.23 USDT
and daily rebalancing 10,016.30 USDT. Legend, USDT axis and terminal table agree.
No `hold_a` or `hold_b` curve appears.

Changing Bar size from 15m to 1h removed the call and proof and restored
"Strategy not tested"; the header returned to "Measurements only". At 390x844 the
page has no horizontal overflow (`scrollWidth = 390`), the panels stack and both
charts render. A page reload cleared the in-memory study result and returned the
panel to "Strategy not tested"; saved-study restore after reload was added on
2026-10-25.

The method-audit copy no longer says that no simulation runs in this view. It now
says the measurements are not a simulation and the explicit strategy test runs
validation and replay.

The shell banner "Background collection failed" came from a stale collector
lease, not a Lab failure. The stored row held `running` with a dead PID and a
heartbeat older than the current WSL boot. The API only reads that row, so an
API restart cannot clear it. The documented launcher
(`./scripts/start_workbench.sh`) started a new collector and overwrote the stale
row on acquire. Status is now `running`, the heartbeat advances and the banner is
absent. Remaining risk: an unclean stop leaves the lease failed until a collector
starts again.

Presentation note: at 15m the relationship chart opens on the latest ~16 days
because Lightweight Charts clamps its bar spacing. The remaining 180-day history
is scrollable, so not all statistics are visible at once.

### Visible range disclosure — 2026-10-24

The relationship chart now captions its visible window, for example "Showing
7 Oct 2026–24 Oct 2026 (UTC). Scroll or drag for earlier data." Scrolling updates
the caption, and no data is removed. The reuse explanation reads "An earlier
study on this pair used overlapping validation data." and shows only when
`validation_reused` is true.

The first live check showed no caption on load: `fitContent()` ran before the
visible-range subscription, so the initial callback never fired. The subscription
now runs before `fitContent()` in `TimeSeriesChart.tsx`; the caption appears on
initial load and the chart still reports later scrolls.

Evidence: 31 Lab chart/answer tests and 38 chart plus Lab tests pass, desktop and
390 px layouts have no horizontal overflow, and `pnpm typecheck` passes.

### Identity evidence — 2026-10-24

The Lab blocks the economic call because `runs/product/asset-registry.json` is
absent, so BTC and ETH have no accepted policy binding. Identity comes from
CoinGecko evidence accepted by the ProductUniverse policy, never from familiar
symbols. A delegated task added
`tests/contract/api/test_pair_rotation_identity.py` (six tests): missing,
rate-limited, coins-only and stale evidence each keep
`identity_confirmed = false` and call `identity_unresolved`. Recorded evidence
confirms both coins, and rebinding never relabels stored prices.

No production code changed in this slice. Without a key, the live bootstrap
operation completed with `registry_status = unavailable`,
`registry_failure = budget_exhausted`, and BTC left in
`pending_admission_asset_ids`. A direct `GET
https://api.coingecko.com/api/v3/coins/list` returned HTTP 429 from this address,
so the refresh spent its 300-second budget on retries.

Evidence: 106 targeted Python tests pass across the pair rotation identity,
analysis, studies, universe and asset registry suites. Ruff and Pyright pass.
Twenty statsmodels singular-matrix warnings remain and are unchanged.

### Identity resolved — 2026-10-25

The operator supplied a CoinGecko Demo API key. The key lives in
`~/.config/qap/env` (mode 600, outside the repository).
`scripts/start_workbench.sh` sources that file when it exists, so the API and
collector inherit `COINGECKO_DEMO_API_KEY` on every launch. `QAP_ENV_FILE`
selects a different file.

Live result:

- Bootstrap returned `registry_status = refreshed` and wrote
  `runs/product/asset-registry.json` (9.3 MB).
- Coin search reports `binance:BTC` and `binance:ETH` as `resolved` with
  canonical assets BTC and ETH.
- The pair was prepared again under the confirmed identities, 12 of 12 units.
  `identity_confirmed` is true.
- A fresh Lab study at 15m, 180 days, band 672 returned call `no_edge`:
  "No reliable edge right now". The proof passes 1 of 8 folds against a
  minimum of 5, with 94 validation trades and corrected p-value 1 over six
  recorded settings. It is -2.80% against starting-mix HODL and -2.78% against
  daily rebalancing.
- Wealth: strategy 9,576.87 USDT, starting-mix HODL 9,852.72 USDT, daily
  rebalancing 9,850.76 USDT. All three appear in the chart and the table.
- The proof shows "Validation data reused" and "An earlier study on this pair
  used overlapping validation data", because the earlier 1h study registered the
  same window.

The economic call now runs on tested data. The earlier `identity_unresolved`
blocks are gone, and the unauthenticated rate limit is the only reason they
existed.

### Saved study after reload — 2026-10-25

The Lab keeps the last settings and the last study reference in local storage. A
completed test stores the study id with the request that produced it. On load the
Lab restores that study only when the current settings produce the same request,
so a result never appears next to different controls. A restored result carries a
"Saved result" label and a "Study from <date>" line, which keeps it distinct from
a fresh run.

A "Clear result" button returns the panel to "Strategy not tested" and removes the
local reference. It does not delete the server copy; every study stays saved. An
explicit clear stays clear across reloads.

Browser evidence: a fresh study showed "Study from 10/25/2026, 2:51:10 AM" and no
"Saved result" label. A reload restored the same call with "Saved result". "Clear
result" returned the panel to "Strategy not tested" and left no stored reference.

Component evidence: the dashboard suite covers restore, clear, and a stored result
whose settings do not match the current controls.

### Final local verification — 2026-10-24

- Web: 166 tests pass across 40 files, `pnpm typecheck` passes, `pnpm build` passes.
- Python: 106 targeted pair rotation and asset registry tests pass.
- Live workbench: API, Vite and the current-evidence collector run under one
  launcher, and the collector status is `running`.
- Identity: BTC and ETH resolve from a CoinGecko Demo key, the pair prepares
  under the confirmed identities, and a live study returns the tested `no_edge`
  call with its proof and wealth curves.
- Saved study: a reload restores the last result with a "Saved result" label, and
  "Clear result" returns the panel to the untested state.
- All changes remain uncommitted on `feat/research-study-workspace`.

### Measurement depth and plain-language UI — 2026-10-27

```text
Update context — 2026-10-27
Trigger: resume item 3 of the 2026-10-24 wrap-up; user asks for a UI a teenager can use.
Purpose: record completed measurement contracts, UI copy changes and a speed defect.
Impact: item 3 complete. No change to objective, benchmarks, costs or data roles.
Evidence: tests below; TASKS.md rows L1–L3.
```

**Measurements (item 3).** `relationship/dependence_measurements.py` adds four
pure readings to the analysis API, OpenAPI and web types: Kalman hedge slope
(at least 60 bars), Granger lead in each direction (lags 1–4, Bonferroni-corrected,
at least 100 bars), copula tail dependence (at least 120 bars) and rolling return
correlation over the band lookback (window at least 20 bars). Thin or flat data
returns null and the UI shows "Unavailable". `rolling_correlation` now returns NaN
for a flat window instead of a clipped ±1. Live BTC/ETH 15m/180d: Kalman β 0.984 ±
0.094; Granger BTC→ETH corrected p 0.0093 at lag 3, ETH→BTC p 0.135; Student copula
tails 0.62; rolling correlation 0.92 (range 0.74–0.94). Granger and copula fit the
whole window, so the UI labels them as context, not validation.

**Plain-language UI.** Every Lab surface leads with plain words and keeps the
technical term second:

- Evidence groups ask questions ("Do they move together?"). Each reading opens
  to a one-line meaning and the method name.
- The toolbar reads Compare with, Candle size, History and Usual level over.
- Charts read Usual level, Normal range, How unusual (z), Rotating, Just holding
  and Money over time, after fees. A crosshair readout shows the hovered bar.
- A test result opens with the money outcome, then the verdict. Proof terms sit
  under "How we checked this".

Control borders meet WCAG 1.4.11 (at least 3:1) in both themes.

**Speed defect, open.** The analysis GET takes 16–50 s for BTC/ETH 15m/180d.
Parquet reads and fingerprint checks take about 10 s. The market-data catalog
takes about 9 s. Registry JSON parsing (9 MB) takes about 8 s. Cointegration
takes 3 s, and the copula fit 2.5 s. A first open of a new pair also prepares
12 data units. TASKS.md row L6 owns the fix.
