# Phase 21 — Self-Contained Pair Rotation MVP Playbook, Math Specification, and L2 Paper Plan

**Status:** Approved for execution 2026-11-15. Active plan for all human and AI agents (including non-frontier models).

```text
Update context — 2026-11-15
Trigger: Hamza approved Stage S0 + S1 kickoff, legacy code retirement, the compiler-style qap_gate.py verification loop, and T3 Code Pi model routing so smaller models can execute reliably without needing a frontier model.
Purpose: Provide one complete, self-contained engineering specification with exact equations, file paths, locked compiler gates, and literal step-by-step task cards for Stages S0 through S5.
Impact: Governs repository cleanup, signal-math repair, crash-defense settings, historical discovery (S4), and millisecond WebSocket L2 paper trading (S5). Preserves Decimal PortfolioState, benchmark ladder, Shariah spot-only rules, and Phase-12 live NO-GO. Pre-cleanup code is preserved at git tag archive/pre-phase21-workbench (9e5ef1a).
Evidence: Tadi & Witzany (2024, arXiv:2305.06961), Hanicová & Vojtko (SSRN 3982120), Binance Spot WebSocket Docs, scripts/qap_gate.py, tests/invariants/test_quant_compiler_laws.py.
```

---

## 1. How Any Agent or Developer Works in This Repository (Self-Verifying Loop)

### 1.1 The Compiler Loop (`scripts/qap_gate.py`)
Never trust an edit until `scripts/qap_gate.py` exits `0`. `qap_gate.py` acquires `/tmp/qap-gate-heavy.lock` automatically so parallel worktrees never exhaust WSL's ~7 GB RAM.

- **Fast inner loop (run after every edit):**
  ```bash
  uv run python scripts/qap_gate.py --pytest <your_test_paths>
  ```
  Checks `ruff check`, `ruff format --check`, `check_source_size.py` (< 500 lines), `lint-imports` (8 package layers), strict `pyright`, `web/openapi.json` sync against FastAPI, `pnpm typecheck`, `tests/invariants/test_quant_compiler_laws.py`, and your targeted tests.
- **When API DTOs or `LabSettings` change (regenerate contracts in this exact order):**
  ```bash
  uv run python scripts/export_openapi.py web/openapi.json
  pnpm --pm-on-fail=ignore --dir web generate:api
  ```
- **Full outer release gate (run on `main` before pinning a stage commit):**
  ```bash
  uv run python scripts/qap_gate.py --full
  ```
- **Locked Invariant Rule:** Workers are **forbidden** from weakening or deleting assertions in `tests/invariants/test_quant_compiler_laws.py`. Before accepting any worker diff, check `git diff HEAD -- tests/invariants/test_quant_compiler_laws.py`.

### 1.2 T3 Code Subagent Routing (`providerInstanceId: "pi"`)
When delegating via T3 Code `delegate_task` (`isolation: "worktree"`):
- **Complex math, algorithms, stateful execution (`S1`, `S2` backend, `S5` L2 engine):**
  - `target: { providerInstanceId: "pi", model: "aistudio2api/gemini-4-hydrogen", options: { thinking: "high" } }`
- **Mechanical refactors, legacy cleanup, schema/UI wiring, batch scripts (`S0-2`, `S2` UI, `S3`, `S4` runner):**
  - `target: { providerInstanceId: "pi", model: "mistral/deepseek-v4-1-flash-1017", options: { thinking: "max" } }`
- **Worktree rule:** `isolation: "worktree"` clones from committed `HEAD` (uncommitted `main` files are excluded). Commit foundation/test prerequisites on `main` before launching worktree children, keep file ownership disjoint across concurrent workers, inspect `git diff` on completion, apply cleanly to `main`, regenerate `openapi.json` + `schema.d.ts` if both touched schemas, and run `qap_gate.py --full`.

---

## 2. Product Constitution & Six Invariant Laws

### 2.1 Scope & Strategy Vehicle
- **MVP Scope:** Two spot coins (`Coin A` and `Coin B`) plus one optional non-traded reference `Anchor` (`BTC`, `ETH`, `BNB`, `SOL`). Underlying kernel types (`AllocationTarget`, `execute_multi_asset_rebalance`) remain N-asset capable for Horizon 2 (5–20 coin hopping).
- **Default Trading Style (`coins_only`):** Stay 100% invested across `Coin A` and `Coin B`. When Coin A drops `-10%` and Coin B drops `-15%` inside an intact stationary relationship, rotate into Coin B to accumulate extra units for the recovery.
- **Configurable Crash Defense (`crash_defense_mode`):** Do not hardcode one dogma. Expose `crash_defense_mode: Literal["coins_only", "park_anchor", "park_usdt"] = "coins_only"` in `LabSettings` and `/lab` UI so the operator can optionally park into `Anchor` or `USDT` during regime breakdowns.
- **MVP Starter Sizing:** Default to `0%`–`100%` full rotation (`initial_weight = Decimal("0.5")`, `rotation_size = Decimal("0.5")`, giving targets `1.0`, `0.5`, or `0.0`). Granular partial steps (`60/40`, continuous scaling) are deferred to Horizon 2.
- **MVP Paper Order Type:** Taker (market) orders sweeping live Binance WebSocket L2 depth (`depth20@100ms`) with 4-clock millisecond delay across Leg 1 and Leg 2. Maker queue depletion is deferred to Horizon 2.

### 2.2 Six Non-Negotiable Laws (Enforced by `tests/invariants/test_quant_compiler_laws.py`)
1. **I1 — Single Inventory Owner:** `PortfolioState` and `PortfolioLedger` own exact `Decimal` quantities, fees, and lot rounding.
2. **I2 — Strict Causality:** Mutating prices at `index >= t` must never alter `signal.values[:t]` or `signal.preference[:t]`.
3. **I3 — Price-Scale Invariance:** Multiplying Coin A by `1000x`, Coin B by `0.0001x`, and Anchor by `500x` must leave `signal.values` and `signal.preference` identical within `1e-7`.
4. **I4 — Rolling Stationary Spreads & Hysteresis:** Copula, regression, and lead-lag estimators refit on rolling windows and hold positions until explicit exit bands are reached (never 1-bar return resets or zero-crossing whipsaw).
5. **I5 — Synthetic Recovery:** Clean synthetic mean-reverting pairs must pass proof and beat `HODL` at low friction.
6. **I6 — Benchmark Ladder & Multiplicity:** Every study counts in `LabStudyStore` and must beat `50/50 HODL` and the best simple rebalancing control (`daily`, `weekly`, `drift`) after realistic costs plus `2x` tuning cost budget.

### 2.3 Backend-First, Dual-Interface (AI CLI + Human Web) & Subscriber-Ready Rules
1. **Backend before UI:** Complete and prove Backend Stages `S2`–`S5` before building the full Three-Column Finance Cockpit UI (`Stage S6`).
2. **Dual First-Class Interfaces over One Shared Core:** Every backend capability lives in pure Python domain services (`src/qap/product_lab_*.py` and `src/qap/experiment/`) exposed equally through **two thin interfaces**:
   - **AI-Agent Interface (`uv run python -m qap.lab_cli`):** Runs directly in-process with compact JSON/Markdown output (omitting 17,000-point chart arrays unless requested) so AI agents inspect pairs, get advisor presets, compare strategies, and run paper sessions with minimal tokens and zero browser overhead.
   - **Human Subscriber Interface (`FastAPI` + OpenAPI -> `/lab` Web Cockpit):** Exposes the exact same services over typed HTTP/SSE routes for interactive visual exploration.
3. **Shared Market Data vs Per-User (`actor_id`) State:** Market candles, CoinGecko identity, pair analysis, and live Binance WebSocket streams are shared read-only across all users. User-owned records (`LabStudyStore` trial-family counts, saved studies, pins, and paper sessions) take an explicit `actor_id` (defaulting to `"local"`, mapping to `"actors/<actor_id>"` for subscribers or AI-agent runs so one actor's trials never pollute another actor's Bonferroni multiplicity count).
4. **Simple + Advanced Dual DTOs:** Every response carries plain-English summaries and recommended presets for everyday subscribers alongside exact `Decimal` costs, walk-forward folds, and statistical diagnostics for advanced users.
5. **Literal Worker Task Cards:** Step-by-step autonomous worker cards for Stages `S2`, `S3`, and `S4` live in **[22-backend-and-agent-cli-tasks.md](22-backend-and-agent-cli-tasks.md)**.

---

## 3. Exact Stage Cards (Executable Without a Frontier Model)

### Stage S0 — Compiler Gate & Legacy Surface Retirement
- **S0-1 (Done by Architect):** Archive tag `archive/pre-phase21-workbench` on `9e5ef1a`; `scripts/qap_gate.py`, `tests/unit/scripts/test_qap_gate.py`, and `tests/invariants/test_quant_compiler_laws.py` committed.
- **S0-2 (Mechanical — `mistral/deepseek-v4-1-flash-1017` at `thinking="max"`):**
  - **Delete frontend legacy features & routes:**
    - Directories: `web/src/features/{baskets,discovery,experiments,home,lineage,pairs,paper,portfolio,prospective}`, `web/src/components/{analytics,visuals}`, `web/e2e`
    - Route files in `web/src/routes/`: `baskets.index.tsx`, `baskets.$basketId.tsx`, `candidate.$scanId.$candidateId.tsx`, `experiments.index.tsx`, `experiments.$runId.tsx`, `pair.$runId.$assetX.$assetY.tsx`, `paper-operations.index.tsx`, `paper-operations.$operationId.tsx`, `portfolio.$runId.tsx`, `prospective.index.tsx`, `prospective.$cohortId.tsx`, `research.index.tsx`, `scanner.index.tsx`, `scanner.$scanId.tsx`, `universe.tsx`
    - Playwright configs/scripts: `web/playwright.config.ts`, `web/tsconfig.e2e.json`, `scripts/run_playwright_e2e.py`, `scripts/serve_playwright_fixture_api.py`, `tests/unit/scripts/test_run_playwright_e2e.py`
  - **Delete backend Phase 17/18 Pair-Study & Research-Recipe bloat:**
    - `src/qap/product_pair_study.py`, `src/qap/product_pair_study_data.py`, `src/qap/product_pair_study_models.py`, `src/qap/product_research_authority.py`
    - `src/qap/research_recipe_basket_authority.py`, `src/qap/research_recipe_capabilities.py`, `src/qap/research_recipe_compiler.py`, `src/qap/research_recipe_entry.py`, `src/qap/research_recipe_pair_study.py`, `src/qap/research_recipe_product.py`
    - `src/qap/experiment/research_recipe.py`, `src/qap/experiment/research_recipe_artifacts.py`
    - `src/qap/api/routes/{baskets,history,product_pair_study,product_research,research_recipes,scanner}.py`
    - `src/qap/api/{basket_schemas,basket_views,history_schemas,history_views,product_pair_study_schemas,product_research_schemas,research_recipe_schemas,research_idea_views,scanner_completed,scanner_views}.py`
    - `tests/contract/api/test_scanner_workbench.py`
  - **Update surviving wiring:**
    - Clean `src/qap/experiment/__init__.py`, `src/qap/api/routes/__init__.py`, `src/qap/api/app.py`, `src/qap/api/operations.py`, and `src/qap/api/operation_worker.py` (remove `RUN_RESEARCH_RECIPE` and deleted routers/readers; keep `experiments`, `portfolios`, `pairs`, `paper_operations`, `operations`, `workspace`, `research_universe`, `product_market_data`, `product_current_evidence`, `pair_rotation`, `lab_studies`, `health` intact so core kernel contract tests still pass).
    - Simplify `web/src/routes/index.tsx` to redirect `/` directly to `/lab`.
    - Simplify `web/src/components/AppShell.tsx` navbar to `Lab` (`/lab`) and `Activity` (`/operations`), and update `web/src/app.test.tsx`, `web/src/components/ScreenGuide.tsx`, `web/src/features/operations/presentation.ts`, `web/src/features/operations/OperationList.test.tsx`, `web/src/api/{client.ts,queries.ts,types.ts,client.test.ts,queries.test.ts}`, `web/package.json` (remove `e2e` scripts), and `tests/contract/api/test_openapi.py`.
    - Regenerate `web/openapi.json`, `web/src/api/schema.d.ts`, and `web/src/routeTree.gen.ts` (`pnpm --pm-on-fail=ignore --dir web build`).
  - **Verify:** `uv run python scripts/qap_gate.py --skip-invariants --pytest tests/contract/api --vitest`

---

### Stage S1 — Signal Math Repair & 0%–100% Walk-Forward Proof
- **Model:** `aistudio2api/gemini-4-hydrogen` at `thinking="high"`.
- **Owned files:** `src/qap/relationship/lab_features.py`, `src/qap/relationship/lab_copula.py`, `src/qap/policy/lab_settings.py`, `src/qap/policy/lab_signals.py`, `src/qap/experiment/lab_proof.py`, `tests/unit/relationship/*`, `tests/unit/experiment/test_lab_proof.py`, `tests/contract/api/test_lab_studies.py`, plus regenerated `web/openapi.json` & `web/src/api/schema.d.ts`.
- **Forbidden:** Do NOT edit `tests/invariants/test_quant_compiler_laws.py`.
- **Exact Math Equations Required:**
  1. **Centered Scale-Invariant Spreads (`src/qap/relationship/lab_features.py`):**
     - Define causal origin-shifted logs `da = log(close_a) - log(close_a[0])` and `db = log(close_b) - log(close_b[0])`. Notice `da` and `db` are exact machine-precision invariants under `close_a * c_a` and `close_b * c_b`!
     - In `kalman_hedge(log_a, log_b)`: run the sequential filter on `da = log_a - log_a[0]` and `db = log_b - log_b[0]` with `state = [0.0, 1.0]`. Store `intercept_d[t] = state[0]` and `beta[t] = state[1]` (add `intercept: Floats` with default or field on `KalmanHedge` while keeping `beta` and `standard_error` compatible with `dependence_measurements.py`!).
     - In `hedge_residual(close_a, close_b, *, window, method)`:
       - `"ratio"`: return `(close_a / close_a[0]) / (close_b / close_b[0])` (scale-invariant normalized ratio; `trailing_zscore` is identical to `close_a / close_b` without float underflow/overflow).
       - `"kalman"`: `da, db = log(close_a) - log(close_a[0]), log(close_b) - log(close_b[0])`; `kh = kalman_hedge(log_a, log_b)`; return `da - kh.intercept - kh.beta * db` (where `kh.intercept` is the `da`-space intercept `state[0]`).
       - `"ols"` and `"tls"`: compute `mean_a, std_a = rolling_mean_std(da, window)`, `mean_b, std_b = rolling_mean_std(db, window)`, `cov = rolling_covariance(da, db, window)`. Compute `beta` as before on `(da, db)`, and return `(da - mean_a) - beta * (db - mean_b)` (exact rolling regression residual including rolling intercept `alpha_t = mean_a - beta * mean_b`!).
  2. **Rolling Stationary-Spread Copula (`src/qap/relationship/lab_copula.py`):**
     - Keep `copula_features(close_a, close_b, training)` intact so `dependence_measurements.copula_tails` does not break.
     - Add `rolling_spread_copula(close_a: Floats, close_b: Floats, *, window: int, anchor: Floats | None = None, refit_step: int | None = None) -> Floats | None`:
       - Require `close_a.size == close_b.size`, `window >= 60`, `close_a.size > window`. Let `step = max(16, window // 4)` if `refit_step is None` else `max(1, refit_step)`.
       - Let `da = np.log(close_a) - np.log(close_a[0])`, `db = np.log(close_b) - np.log(close_b[0])`.
       - Allocate `prob_a = np.full(close_a.size, np.nan)`.
       - For `tau` in `range(window, close_a.size, step)`:
         - Formation slice `F = slice(tau - window, tau)` (strictly `< tau`); evaluation slice `E = slice(tau, min(close_a.size, tau + step))`.
         - **If `anchor is not None` (Tadi & Witzany 2024 anchor-mediated spreads):**
           Let `dc = np.log(anchor) - np.log(anchor[0])`. On `F`, fit OLS `da[F] = alpha_a + beta_a * dc[F]` and `db[F] = alpha_b + beta_b * dc[F]` (if `np.ptp(dc[F]) <= 1e-12`, skip block). Compute stationary spreads `sa_train = da[F] - (alpha_a + beta_a * dc[F])`, `sb_train = db[F] - (alpha_b + beta_b * dc[F])`, and out-of-sample `sa_eval = da[E] - (alpha_a + beta_a * dc[E])`, `sb_eval = db[E] - (alpha_b + beta_b * dc[E])`.
         - **If `anchor is None` (causal rolling-mean-centered spreads):**
           Compute causal trailing means `ma_a, _ = rolling_mean_std(da, min(window // 2, max(10, window // 3)))` and `ma_b, _ = rolling_mean_std(db, min(window // 2, max(10, window // 3)))`! Check: `da - ma_a` and `db - ma_b` are strictly causal, scale-invariant, and $I(0)$ stationary! Slice valid finite rows inside `F` for `(sa_train, sb_train)` (require `>= 40` finite points with `ptp > 0`), and evaluate `(sa_eval, sb_eval) = ((da - ma_a)[E], (db - ma_b)[E])`.
         - Fit `pyvinecopulib.Bicop.from_data` on empirical ranks `(rankdata(sa_train) / (n + 1), rankdata(sb_train) / (n + 1))` using `[indep, gaussian, student, clayton, gumbel]`, `num_threads=1`.
         - Map `(sa_eval, sb_eval)` through training empirical CDF `(searchsorted(sort(s_train), s_eval, side="right") + 0.5) / (n + 1)` clipped to `[1e-6, 1 - 1e-6]`, and set `prob_a[E] = model.hfunc2(margins_eval)` (`P(U_A <= u_A | U_B = u_B)`).
       - Return `prob_a` (or `None` if no finite predictions).
  3. **Settings & Hysteresis State Machine (`src/qap/policy/lab_settings.py`, `src/qap/policy/lab_signals.py`):**
     - In `LabSettings`:
       - Change `rotation_size` default from `Decimal("0.25")` to `Decimal("0.5")` (`0%`–`100%` MVP starter).
       - Add `copula_exit_band: float = Field(default=0.10, gt=0.0, lt=0.45)` (neutral zone `[0.5 - band, 0.5 + band]`, validated so `copula_probability < 0.5 - copula_exit_band`).
       - Add `trend_deadband: float = Field(default=0.002, ge=0.0, le=0.5)` (`0.2%` log-ratio MA spread deadband).
     - In `signal_path`:
       - `"trend"`: compute centered log ratio `lr = (np.log(a) - np.log(a[0])) - (np.log(b) - np.log(b[0]))`; `fast, _ = rolling_mean_std(lr, settings.fast_window)`; `slow, _ = rolling_mean_std(lr, settings.slow_window)`; `values = fast - slow`; `upper, lower = settings.trend_deadband, -settings.trend_deadband`. State machine: if `value >= upper: state = 1.0`, `elif value <= lower: state = -1.0`, `elif (state > 0 and value <= 0.0) or (state < 0 and value >= 0.0): state = 0.0`.
       - `"copula"`: call `rolling_spread_copula(a, b, window=settings.lookback, anchor=anchor)`. State machine: `lower = settings.copula_probability`, `upper = 1.0 - settings.copula_probability`; if `value <= lower: state = 1.0`, `elif value >= upper: state = -1.0`, `elif abs(value - 0.5) <= settings.copula_exit_band: state = 0.0` (holds `+1` or `-1` while dislocation persists!).
       - `"lead_lag"`: compute `returns_a = np.diff(np.log(a))`, `returns_b = np.diff(np.log(b))`, `driver = np.diff(np.log(anchor))` (all 100% scale-invariant!). For each return index `r_idx` from `settings.lookback` to `driver.size - 1`, fit `beta_a` and `beta_b` over the strictly preceding window `w = slice(r_idx - settings.lookback, r_idx)`: `var_d = np.var(driver[w])`; if `var_d > 1e-20`, `beta_a = cov(returns_a[w], driver[w]) / var_d`, `beta_b = cov(returns_b[w], driver[w]) / var_d`, and `values[r_idx + 1] = (beta_a - beta_b) * driver[r_idx] - (returns_a[r_idx] - returns_b[r_idx])`. State machine: if `value >= upper: state = 1.0`, `elif value <= lower: state = -1.0`, `elif abs(value) <= 0.25 * settings.anchor_threshold: state = 0.0`.
  4. **Verify:** `uv run python scripts/qap_gate.py --pytest tests/unit/relationship tests/unit/policy tests/unit/experiment tests/contract/api/test_lab_studies.py` MUST exit `0` with `quant_invariants` 100% GREEN!

---

### Stage S2 — Backend Policy Completeness, Actor Scoping & Smart Advisor API
- **Model:** `aistudio2api/gemini-4-hydrogen` at `thinking="high"`.
- **Goal:** Make the backend policy, store, and API subscriber-ready and strategy-complete before UI work.
- **Steps:**
  1. **Configurable Crash Defense (`lab_settings.py`, `lab_replay.py`, `lab_proof.py`):** Add `crash_defense_mode: Literal["coins_only", "park_anchor", "park_usdt"] = "coins_only"` and `regime_break_drawdown: float = Field(default=0.15, ge=0.02, le=0.80)`. Default `"coins_only"` keeps `100%` in `Coin A` + `Coin B` (accumulating the deeper-dropped coin when relationship holds). Optional `"park_anchor"` / `"park_usdt"` steps out via `execute_multi_asset_rebalance` with full two-leg fees on regime breakdown.
  2. **Per-Actor Store Isolation (`product_lab_store.py`, `api/routes/lab_studies.py`):** Add `actor_id: str = "local"` support (`LabStudyStore.for_actor(run_root, actor_id)` -> backward-compatible root for `"local"`, isolated `actors/<actor_id>/` directory for future authenticated subscribers).
  3. **Smart Strategy Advisor & Multi-Strategy Compare API (`product_lab_advisor.py`, `api/routes/lab_studies.py`):**
     - Deterministic Quant Advisor inspecting `cointegration`, `half_life`, `hurst`, `copula`, and `anchor` measurements to return ranked `LabStrategySuggestionDto` presets (plain-English rationale for beginners + exact statistical trigger for pros + ready-to-run `LabSettings`).
     - `POST /api/pair-rotation/studies/compare`: runs a declared list of strategies on one pair under one shared family registration and returns ranked net-of-cost proofs.
  4. Regenerate `web/openapi.json` and `web/src/api/schema.d.ts`.
- **Verify:** `uv run python scripts/qap_gate.py --pytest tests/unit/experiment tests/unit/test_lab_store.py tests/contract/api/test_lab_studies.py`

---

### Stage S3 — Historical Data Completeness & Cost-Coverage Hardening (Backend)
- **Model:** `mistral/deepseek-v4-1-flash-1017` at `thinking="max"`.
- **Goal:** Eliminate false `cost_data_missing` blocks on liquid Binance pairs (such as `LINK/ETH`) when an isolated candle has `volume == 0` on a quiet bar, and ensure `1m`/`15m`/`1h`/`4h`/`1d` archive + REST top-ups are gap-free.
- **Steps:**
  1. Inspect `product_market_data_binance.py` and `lab_replay.py:_costs`.
  2. Ensure `product_market_data_binance.py` fetches complete archive + REST top-up windows for `1m`, `15m`, `1h`, `4h`, and `1d`.
  3. In `lab_replay.py:_costs`, if a single bar has `volume == 0`, estimate participation from the trailing 20-bar median quote volume (with conservative `2x` impact penalty) and mark `costs_supported = False` ONLY when trailing 20-bar median volume itself is zero/missing.
  4. Add unit tests in `tests/unit/experiment/test_lab_replay.py`.
- **Verify:** `uv run python scripts/qap_gate.py --pytest tests/unit/experiment/test_lab_replay.py tests/unit/test_pair_rotation_data.py`

---

### Stage S4 — Preregistered Historical Strategy Discovery via Backend API (`1h`, `4h`, `1d`)
- **Model:** `mistral/deepseek-v4-1-flash-1017` at `thinking="max"` + architect review.
- **Goal:** Prove which repaired strategies (`H1` volatility harvesting, `H2a` direct & anchor-mediated `copula`, `H2b` centered `OLS`/`Kalman` `zscore`, `H3` deadband `trend`) beat `HODL` and rebalancing on `1h`, `4h`, and `1d` bars through the real backend comparison API.
- **Steps:**
  1. Drive `POST /api/pair-rotation/studies/compare` (and `scripts/run_lab_trials.py` as a thin API client) across liquid Binance pairs on `1h`, `4h`, and `1d`.
  2. Apply Holm `alpha = 0.05` across each hypothesis family and record honest results (`vs HODL`, `vs Control`, `cost_paid_pct`, `gross_vs_hodl_pct`, `folds_passing`).
- **Exit Gate:** At least one candidate passes walk-forward proof, `2x` cost gate, and `2x` fee robustness before live streaming.

---

### Stage S5 — Millisecond-Aware Binance WebSocket L2 Paper Engine & API (Backend)
- **Model:** `aistudio2api/gemini-4-hydrogen` at `thinking="high"`.
- **Goal:** Forward-test strategies on live Binance Spot order books (`wss://data-stream.binance.vision/stream?timeUnit=MICROSECOND`) as a shared market-stream + per-`actor_id` paper-session backend service with typed FastAPI endpoints.
- **Modules (< 500 lines each):**
  1. `src/qap/market/binance_ws_stream.py`: Shared public WebSocket hub subscribing once per symbol to `<symbol>@bookTicker`, `<symbol>@depth20@100ms`, and `<symbol>@aggTrade`, recording `(t_exch_us, t_recv_ns)` and handling 24h rollovers, 20s ping/pong, and `serverShutdown`.
  2. `src/qap/execution/l2_book_fill.py`: Pure deterministic L2 book sweep for taker orders at `t_recv_ns >= t_fill_ns` (`max_staleness_ms = 500`), enforcing Binance `LOT_SIZE`/`PRICE_FILTER`/`NOTIONAL` and computing exact VWAP fill price, fee, and book-walk slippage.
  3. `src/qap/experiment/live_paper_runner.py` + `src/qap/api/routes/live_paper.py`: Per-`actor_id` paper sessions logging all 4 timestamps (`t_exch_us`, `t_recv_ns`, `t_decide_ns`, `t_fill_leg1_ns`, `t_fill_leg2_ns`), reconciling through `PortfolioLedger` against live `HODL` and rebalancing controls, and exposing `POST/GET /api/pair-rotation/paper-sessions` for the Web UI.
- **Verify:** Hand-calculated 20-level partial-sweep tests, stale-book refusal tests, live `BTCUSDT`/`ETHUSDT` stream smoke test, and `uv run python scripts/qap_gate.py --full`.

---

### Stage S6 — Three-Column Finance Cockpit UI (Simple + Advanced Users)
- **Follows after Backend Stages S2–S5 are 100% verified.**
- Build the complete web experience on `/lab` (`docs/product/design-direction.md`):
  - **Left Column:** Smart/AI Advisor one-click presets, Strategy switcher (`Z-Score`, `Copula`, `Trend`, `Lead-Lag`), progressive simple vs advanced tuning knobs, `Compare All Strategies` button, and Saved/Pinned runs list.
  - **Center Column:** Plain-language Call + Proof, Ratio chart with Buy A / Buy B markers + synced active-signal sub-chart, Wealth chart with `USDT | Coin A | Coin B` switch, and expandable Trade & Fold drawer.
  - **Right Column:** Plain-English + Pro relationship readings, Backtest Scorecard, and Live L2 Paper session monitor.

---

## 4. Deferred Horizon 2 Roadmap (Do Not Build Until S0–S5 Exit Green)
1. **Granular partial rotation sizing** (`60/40`, `75/25`, signal-conviction continuous weights).
2. **Maker (post-only limit) paper execution** with `@aggTrade` queue-position depletion and legged-fill recovery.
3. **Multi-coin whitelist hopping (5–20 coins)** built on `AllocationTarget` + `execute_multi_asset_rebalance`.
4. **Rust `PyO3` Core & Verifier Crate (`qap-rs`):** Once Stage S4 proves strategy edge, migrate money-critical implementation modules (`PortfolioState`, `L2BookFill`, replay state machines, and/or the `qap_gate` verifier binary) into Rust (`PyO3`/`maturin`) while keeping Python for `pyvinecopulib`/`statsmodels`/`arch` statistics and strict TypeScript for `web/`. Rust adds compile-time guarantees Python lacks: `NewType` unit safety (`Price` vs `Quantity` vs `Weight`), forced `Option`/`Result` handling (eliminating silent runtime `StopIteration`/exception bugs), exhaustive `enum` matching, borrow-checked immutability, and `50x`–`100x` tick/grid speed.
5. **Stricter Python & TypeScript Static Guards (Bridge Before Rust):** Expand `qap_gate` static rules with branded TypeScript types in `web/`, Python `typing.NewType` + `typing.assert_never` exhaustiveness checks, and expanded `ruff` bugbear/safety rules (`B`, `SIM`, `RUF`) to catch implementation bugs earlier.
6. **Phase 12 Live-Readiness Gate** (only after 90–180 days of positive forward L2 paper shadow evidence).
