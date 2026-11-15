# Phase 23 — Outsourced Completion Plan: Stage S5 (L2 Paper API/CLI/Tests) & Stage S6 (3-Column Web Cockpit UI)

**Status:** Ready for external AI agent execution (2026-11-15).
**Saved Partial S5 Branch:** `wip/stage-s5-partial` (4 core modules, 1,536 lines already written).
**Compiler Verifier:** `uv run python scripts/qap_gate.py` (must exit `0` before finishing each stage).

```text
Update context — 2026-11-15
Trigger: Stage S4-B completed (with park_anchor third-asset metadata fixed on main), and AI Studio hit its daily quota mid-Stage-S5 after writing all 4 core L2 paper engine modules (saved on branch wip/stage-s5-partial). Hamza requested exact outsourcing plans/prompts for the remaining heavy work.
Purpose: Provide self-contained specifications for finishing Stage S5 (~650 lines) and building Stage S6 (~1,200 lines) so any external AI agent can complete QAP to 100% and pass qap_gate.py --full.
Impact: Preserves all invariants, dual AI-CLI + Subscriber-Web interfaces, and <500 line module limits.
Evidence: Branch wip/stage-s5-partial, docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md, docs/product/design-direction.md.
```

---

## Outsourced Task 1 — Finish Stage S5: Binance WebSocket L2 Paper API, CLI & Tests

### Starting State
Branch `wip/stage-s5-partial` already contains 4 core modules:
1. `src/qap/market/binance_ws_stream.py` (317 lines — `wss://data-stream.binance.vision` microsecond parser & stream helper)
2. `src/qap/execution/l2_book_fill.py` (267 lines — 20-level `Decimal` L2 taker book sweep)
3. `src/qap/experiment/live_paper_execution.py` (424 lines — two-leg L2 rebalance & 4-clock latency helper)
4. `src/qap/experiment/live_paper_runner.py` (528 lines — actor-scoped session manager & 3 parallel ledgers)

### Exact Steps to Complete Stage S5
1. **Bring the 4 partial files onto `main` (or a worktree off `main`):**
   ```bash
   git checkout wip/stage-s5-partial -- src/qap/market/binance_ws_stream.py src/qap/execution/l2_book_fill.py src/qap/experiment/live_paper_execution.py src/qap/experiment/live_paper_runner.py
   ```
2. **Polish & Trim the 4 Core Files for `qap_gate.py`:**
   - Trim `src/qap/experiment/live_paper_runner.py` from `528` lines to **below `490` lines** (move small view/JSON helpers into `live_paper_execution.py` or a small `live_paper_models.py` if needed so EVERY file stays `< 500` lines).
   - Run `uv run ruff format src/` and `uv run ruff check --fix src/`.
   - Fix any strict `pyright` issues across all 4 files (`uv run pyright src`).
   - Verify `.importlinter` passes (`uv run lint-imports`).
3. **Add Dual Interfaces (AI-Agent CLI + Subscriber HTTP API):**
   - **AI-Agent CLI (`src/qap/lab_cli_paper.py`, < 200 lines, wired into `src/qap/lab_cli.py`):**
     - Subcommands under `uv run python -m qap.lab_cli`:
       - `paper-start --coin-a ID --coin-b ID [--anchor ID] [--bar 1h] [--settings JSON] [--order-rtt-ms 75]`
       - `paper-step --session-id ID [--duration-seconds 3.0]`
       - `paper-status --session-id ID`
       - `paper-list`
       - `paper-stop --session-id ID`
     - Support `--actor-id` and `--format json|md`.
   - **Subscriber HTTP API (`src/qap/api/live_paper_schemas.py` + `src/qap/api/routes/live_paper.py`, mounted in `src/qap/api/app.py`):**
     - `POST /api/pair-rotation/paper-sessions` (`operation_id="createLivePaperSession"`)
     - `GET /api/pair-rotation/paper-sessions` (`operation_id="listLivePaperSessions"`)
     - `GET /api/pair-rotation/paper-sessions/{session_id}` (`operation_id="getLivePaperSession"`)
     - `POST /api/pair-rotation/paper-sessions/{session_id}/step` (`operation_id="stepLivePaperSession"`)
     - `POST /api/pair-rotation/paper-sessions/{session_id}/stop` (`operation_id="stopLivePaperSession"`)
     - Honor `X-QAP-Actor-Id` header (default `"local"`) and `require_local`.
   - **Regenerate OpenAPI & TypeScript Schema:**
     ```bash
     uv run python scripts/export_openapi.py web/openapi.json
     pnpm --pm-on-fail=ignore --dir web generate:api
     ```
4. **Write Deterministic Unit & Contract Tests (No live network required in CI):**
   - `tests/unit/market/test_binance_ws_stream.py`: test `bookTicker`, `depth20@100ms`, `aggTrade` (ms and `MICROSECOND`), `serverShutdown`, and stale `lastUpdateId` rejection.
   - `tests/unit/execution/test_l2_book_fill.py`: hand-computed multi-level `BUY` and `SELL` sweeps, `PortfolioLedger.apply_fill` balance conservation, stale-book rejection (`book_age_ms > 500`), and insufficient 20-level depth rejection.
   - `tests/unit/experiment/test_live_paper_runner.py`: two-leg `USDT` swap with 75 ms RTT price drift between Leg 1 and Leg 2, monotonic 4-clock check (`t_recv_ns <= t_decide_ns < t_fill_leg1_ns < t_fill_leg2_ns`), `actor_id` isolation, and `integrity.json` verification.
   - `tests/contract/api/test_live_paper.py`: test all 5 HTTP endpoints + `qap.lab_cli paper-*` commands with an injected mock `book_provider`.
5. **Mandatory Self-Verification Gate:**
   ```bash
   uv run python scripts/qap_gate.py --pytest tests/invariants tests/unit/market/test_binance_ws_stream.py tests/unit/execution/test_l2_book_fill.py tests/unit/experiment/test_live_paper_runner.py tests/contract/api/test_live_paper.py tests/contract/api/test_openapi.py
   ```
   Loop until `failed=0`, update `TASKS.md` (`S5 -> done`), and commit on `main`.

---

## Outsourced Task 2 — Build Stage S6: Three-Column Finance Cockpit Web UI (`/lab`)

### Goal
Upgrade `web/src/features/lab/` from a static 2-column viewer into the complete **Three-Column Simple + Advanced Finance Cockpit** (`docs/product/design-direction.md` & `docs/product/assets/reference-dashboard-vibe-2026-09-30.png`) consuming the finished backend APIs (`/advisor`, `/studies`, `/studies/compare`, `/paper-sessions`).

### Exact UI Architecture (`web/src/features/lab/`, every file `< 450` lines)
1. **Top Bar (`LabDashboard.tsx`):**
   - Keep `Coin A` ↔ Swap ↔ `Coin B`, `Anchor` (`Auto-suggest` / `BTC` / `ETH` / `BNB` / `SOL`), `Candle size` (`1m`, `15m`, `1h`, `4h`, `1d`), `History` (`30d`, `90d`, `180d`, `365d`), plus a clean **`Simple | Advanced` view mode switch**.
2. **Left Column — Strategy Workbench, Advisor & Saved Runs (`LabSidebar.tsx`, `LabAdvisorCard.tsx`, `LabSavedRuns.tsx`):**
   - **Smart Strategy Advisor Card:** Calls `GET /api/pair-rotation/advisor`; shows `simple_summary` (or `pro_summary` in Advanced mode), `bar_warning` when on `15m`, and 3 clickable preset cards (**"Apply & Test"**).
   - **Strategy & Contextual Controls:**
     - Strategy pills: `Z-Score` | `Spread Copula` | `Ratio Trend` | `Anchor Lead-Lag`.
     - Contextual knobs for the active strategy (`hedge_method`, `lookback`, `entry`/`exit`, `copula_probability`/`copula_exit_band`, `fast_window`/`slow_window`/`trend_deadband`, `anchor_threshold`).
     - Sizing & Risk: `Rotation Size` quick pills (`25%`, `50%`, `75%`, `100%`), `Crash Defense` (`Stay in coins`, `Park in Anchor`, `Park in USDT`), `Auto-tune` toggle, and collapsible `Advanced Execution` (`minimum_hold`, `cooldown`, `fee_bps`, `slippage_bps`).
   - **Actions:** Primary **`Apply & Run Test`** button (with dirty-settings badge when sliders move after a test) + secondary **`Compare All Presets`** button calling `POST /api/pair-rotation/studies/compare`!
   - **Saved & Pinned Studies List:** Calls `GET /api/pair-rotation/studies` and `POST .../pin`; click any saved study to inspect it immediately.
3. **Center Column — Verdict, Pro Charts & Trade Audit (`LabCharts.tsx`, `LabSignalChart.tsx`, `LabWealth.tsx`, `LabTradeDrawer.tsx`):**
   - **Call & Proof Row:** Keep `LabAnswer.tsx`, plus render comparison table when `Compare All Presets` runs.
   - **Ratio Chart + Trade Markers + Signal Sub-Chart:** Render Buy A (`teal`) / Buy B (`violet`) / Defensive Park markers from `study.result.trades`, and render the synchronized active-signal sub-pane (`study.result.signal`: `values`, `upper`, `lower`, `unit`) in Advanced mode.
   - **Wealth Chart Toggle:** Add **`USDT Value` | `Coin A Units` | `Coin B Units`** segmented toggle reading `wealth.value`, `wealth.coins_a`, and `wealth.coins_b` (including `hold_a` and `hold_b` context toggles).
   - **Bottom Expandable Drawer (`LabTradeDrawer.tsx`):** Tabs for **Simulated Swaps** (`study.result.trades`), **Walk-Forward Folds** (`study.result.folds`), and **Dataset Provenance**.
4. **Right Column — Relationship Evidence, Scorecard & Live Paper (`LabEvidence.tsx`, `LabScorecard.tsx`, `LabLivePaperPanel.tsx`):**
   - Toggleable Evidence readings (plain words in Simple mode, exact parameters/p-values visible in Advanced mode).
   - **Backtest Scorecard (`LabScorecard.tsx`):** Renders `study.result.statistics` (`Max Drawdown`, `Total Swaps`, `Fees USDT`, `Slippage USDT`, `Ending Coin Holdings`).
   - **Live L2 Paper Panel (`LabLivePaperPanel.tsx`):** Start, step/refresh, and stop a live paper session via `/api/pair-rotation/paper-sessions`, displaying `vs HODL`, `vs Control`, and 4-clock millisecond fill latencies (`t_exch`, `t_recv`, `t_decide`, `t_fill`).
5. **Responsive & Theme Rules:**
   - `>= 1280px`: 3 columns (`280px` Left | `1fr` Center | `300px` Right).
   - `< 1280px` / Mobile `390px`: zero horizontal overflow (`scrollWidth <= clientWidth`), collapsible Left Strategy drawer, stacked panels, both dark and light themes meeting WCAG AA contrast.
6. **Tests & Full Gate:**
   - Add focused Vitest + Testing Library suites in `web/src/features/lab/` covering strategy switching, `settings` payload submission in `useLab`, Advisor preset click, `Compare All Presets`, `USDT | Coin A | Coin B` wealth toggle, Trade Drawer, and Live Paper panel.
   - Run full repository verification until `12/12` pass:
     ```bash
     uv run python scripts/qap_gate.py --full
     ```
   - Update `TASKS.md` (`S6 -> done`) and commit on `main`.
