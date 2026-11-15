# Phase 22 — Worker Task Cards: Dual-Interface Backend (AI CLI + Subscriber API) & Discovery

**Status:** Ready for AI worker execution (2026-11-15).
**Parent Plan:** [21-pair-mvp-fundamentals-and-l2-paper-plan.md](21-pair-mvp-fundamentals-and-l2-paper-plan.md).
**Tracker:** [TASKS.md](../../TASKS.md).

```text
Update context — 2026-11-15
Trigger: Hamza specified a dual-interface architecture (one fast CLI/JSON interface for AI agents alongside one clean Simple+Advanced Web API/UI for human users and subscribers) and requested literal, self-contained worker task cards for the next backend wave.
Purpose: Specify cards S2-A, S2-B, S2-C, and S4-A with exact files, signatures, edge cases, and qap_gate.py commands so any AI model can execute them autonomously without a frontier model.
Impact: Splits Stage S2 + S3 into two parallelizable Wave-1 cards (S2-A and S2-B), one Wave-2 integration card (S2-C adding qap.lab_cli + compare/advisor HTTP routes), and one Wave-3 discovery card (S4-A).
Evidence: src/qap/experiment/lab_replay.py, src/qap/product_lab_store.py, src/qap/product_lab_study.py, scripts/qap_gate.py.
```

---

## Global Rules for Every AI Worker

1. Read `AGENTS.md` first. Never change fees, slippage formulas (except the specified thin-bar penalty in `S2-A`), benchmark ladder rules, `final_oos`, or the spot-only no-leverage boundary.
2. **Never edit or weaken `tests/invariants/test_quant_compiler_laws.py`.**
3. Keep every hand-written file **below 500 lines** (`uv run python scripts/check_source_size.py`).
4. Edit **only** the files listed under **Owned Files** in your card. If another file seems required, stop and report.
5. After editing, run your card's **`qap_gate.py` command** in a repair loop until `failed=0`. `qap_gate.py` holds `/tmp/qap-gate-heavy.lock` automatically so parallel workers never exhaust RAM.
6. Do **not** `git commit` or `git push` inside a worker worktree unless explicitly instructed by the orchestrator.

### Parallel Execution Map

```text
Wave 1 (run in parallel worktrees — 100% disjoint files):
  ├── Card S2-A (Hydrogen @ high): Crash defense + trailing-volume cost fallback
  └── Card S2-B (DeepSeek @ max):  Actor-scoped store + Smart Strategy Advisor module

Wave 2 (after Wave 1 is merged & committed on main):
  └── Card S2-C (Hydrogen @ high): Dual-interface wiring (HTTP Compare/Advisor API + qap.lab_cli for AI agents)

Wave 3 (after S2-C is merged & committed on main):
  └── Card S4-A (DeepSeek @ max):  Preregistered 1h / 4h / 1d strategy discovery via qap.lab_cli
```

---

## Card `S2-A` — Crash Defense Policy & Trailing-Volume Cost Resilience

- **Model:** `pi` -> `aistudio2api/gemini-4-hydrogen` (`thinking="high"`), or Codex `high`.
- **Depends on:** `S0-2` and `S1` (already committed on `main`).
- **Owned Files:**
  - Edit: `src/qap/policy/lab_settings.py`, `src/qap/experiment/lab_replay.py`, `src/qap/experiment/lab_proof.py`, `src/qap/api/lab_study_schemas.py` (only if `LabTradeDto.direction` literal expands), `tests/unit/experiment/test_lab_replay.py`
  - Create: `tests/unit/experiment/test_lab_crash_defense.py`
  - Regenerate via scripts: `web/openapi.json`, `web/src/api/schema.d.ts`
- **Forbidden:** Do NOT touch `product_lab_store.py`, `product_lab_study.py`, `api/routes/lab_studies.py`, or `tests/invariants/test_quant_compiler_laws.py`.

### Exact Implementation Steps

1. **`LabSettings` (`src/qap/policy/lab_settings.py`):**
   - Add two fields after `trend_deadband`:
     ```python
     crash_defense_mode: Literal["coins_only", "park_anchor", "park_usdt"] = "coins_only"
     regime_break_drawdown: float = Field(default=0.15, ge=0.02, le=0.80)
     ```
2. **Trailing-20-Bar Median Volume Fallback (`src/qap/experiment/lab_replay.py:_costs`):**
   - Currently, if `bar.volume is None or bar.volume <= 0` at `index`, `_costs` marks `supported = False` immediately, causing false `cost_data_missing` failures on liquid pairs like `LINK/ETH` when a single quiet candle has zero volume.
   - Replace that single-bar check with a causal trailing-20-bar fallback:
     - Pass each leg's full `ValidatedBarSeries` (`inputs.direct` when direct, else `inputs.first` and `inputs.second`) into `_costs`.
     - If `bar.volume is not None and bar.volume > 0`, compute `quote_volume = bar.volume * bar.close * quote_mark` normally (`penalty = 1.0`).
     - Else inspect strictly prior bars `series.bars[max(0, index - 20) : index]`. Collect `b.volume * b.close * prior_quote_mark` for bars with `b.volume is not None and b.volume > 0`.
     - If **at least 5** positive prior bars exist in that 20-bar window, use `float(np.median(positive_quote_volumes))` as `quote_volume` and set `penalty = 2.0` (doubles volume impact for that leg on the thin bar) while keeping `supported = True`!
     - Only set `supported = False` when fewer than 5 positive bars exist in `[max(0, index - 20) : index]`.
     - Compute `impact = float(settings.volume_impact_bps) * max_leg_penalty_sqrt_participation`.
3. **Configurable Crash Defense (`src/qap/experiment/lab_replay.py` & `lab_proof.py`):**
   - Expand `LabTrade.direction` (and `LabTradeDto.direction` in `lab_study_schemas.py`) to `Literal["into_a", "into_b", "into_usdt", "into_anchor"]`.
   - Update `_execute` in `lab_replay.py` to accept a full weight mapping `target_weights: Mapping[AssetId, Decimal]` over the basket `(a, b, USDT)` (or `(a, b, anchor_asset, USDT)` when `inputs.anchor` is a distinct third coin):
     - Include `anchor_asset` in `_prices(...)` when `inputs.anchor is not None` and `inputs.anchor.instrument.base not in (a, b, USDT)`.
     - Compute one-way notional `plan.one_way_rebalance_notional`; if `< settings.minimum_notional`, return `None, True`.
     - When `target_weights` uses only `a` and `b` (`USDT == 0` and no third anchor weight) AND `inputs.direct is not None`, keep the single-leg `execute_direct_rebalance_leg` path. Otherwise use `execute_multi_asset_rebalance` with `bridge=USDT` over the relevant USDT instruments (`first`, `second`, and `anchor` if `anchor_asset` has non-zero current or target quantity).
     - Set `direction`: `"into_usdt"` if ending `USDT` weight > `0.5`; `"into_anchor"` if third `anchor_asset` weight > `0.5`; `"into_a"` if `ledger.current_state.quantity(a) > before_a`; else `"into_b"`.
   - In `run_lab_replay` (`kind == "strategy"`):
     - Track `peak_value = max(peak_value, value)` from `start` (include `anchor_asset` value in `value` when held!).
     - Let `drawdown = 0.0 if peak_value <= 0 else (1.0 - value / peak_value)`.
     - **`crash_defense_mode == "coins_only"` (default):** exact existing 2-coin behavior (`{a: target_w, b: 1 - target_w, USDT: 0}`).
     - **`crash_defense_mode in ("park_usdt", "park_anchor")`:**
       - Maintain `parked: bool = False`.
       - If not `parked` and `drawdown >= settings.regime_break_drawdown` and cooldown satisfied: set `parked = True` and schedule defensive target (`{a: 0, b: 0, USDT: 1}` for `"park_usdt"`; `{a: 0, b: 0, anchor_asset: 1, USDT: 0}` for `"park_anchor"`, or `100%` of `a`/`b` if `anchor_asset` equals `a` or `b`).
       - While `parked`: remain parked until `value` would recover OR cooldown (`max(minimum_hold, cooldown) * 2` bars) has elapsed AND `np.isfinite(path[index])` AND `float(path[index]) != 0.0`, at which point reset `peak_value = value`, `parked = False`, and re-enter `{a: target_w, b: 1 - target_w, USDT: 0}`!
   - In `prove_lab_strategy` (`src/qap/experiment/lab_proof.py`):
     - If `settings.crash_defense_mode == "park_anchor"` and `inputs.anchor is None`: return `LabProof` with `_call("execution_data_missing", "Anchor coin required", "Choose an anchor coin before testing park_anchor crash defense.")` so missing anchor never crashes.
     - Include `anchor` instrument in `required` metadata check in `prove_lab_strategy` / `product_lab_study` ONLY when `crash_defense_mode == "park_anchor"` and `inputs.anchor` is a third asset; if metadata for `anchor` is missing in `inputs.metadata`, pass `require_market_metadata=False` ONLY when `inputs.metadata` is empty (already how `lab_replay.py:173` works!). Check that `metadata` preflight passes cleanly when `inputs.metadata` has 2 legs vs 3 legs.
4. **Regenerate Contracts:**
   ```bash
   uv run python scripts/export_openapi.py web/openapi.json
   pnpm --pm-on-fail=ignore --dir web generate:api
   ```
5. **Tests to Add:**
   - `tests/unit/experiment/test_lab_replay.py`: test single zero-volume bar in a 30-bar liquid series keeps `costs_supported is True` and charges higher impact than a normal bar, while 20 consecutive zero-volume bars set `costs_supported is False`.
   - `tests/unit/experiment/test_lab_crash_defense.py`: (a) `coins_only` during a `-20%` crash keeps `USDT == 0` and stays in `A`/`B`; (b) `park_usdt` exits to `USDT` once drawdown crosses `regime_break_drawdown` and pays leg fees; (c) `park_anchor` without `anchor` returns `execution_data_missing` cleanly.
6. **Gate Command (loop until `failed=0`):**
   ```bash
   uv run python scripts/qap_gate.py --pytest tests/invariants tests/unit/experiment tests/contract/api/test_lab_studies.py
   ```

---

## Card `S2-B` — Per-Actor Store Isolation & Smart Strategy Advisor Module

- **Model:** `pi` -> `mistral/deepseek-v4-1-flash-1017` (`thinking="max"`).
- **Depends on:** `S0-2` and `S1` (already committed on `main`). Runs in parallel with `S2-A`.
- **Owned Files:**
  - Edit: `src/qap/product_lab_store.py`, `tests/unit/test_lab_store.py`
  - Create: `src/qap/product_lab_advisor.py`, `tests/unit/test_lab_advisor.py`
- **Forbidden:** Do NOT touch `lab_settings.py`, `lab_replay.py`, `lab_proof.py`, `product_lab_study.py`, `api/`, `web/`, or `tests/invariants/test_quant_compiler_laws.py`.

### Exact Implementation Steps

1. **Subscriber / Agent Actor Isolation (`src/qap/product_lab_store.py`):**
   - Add regex `_ACTOR_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")`.
   - Update `LabStudyStore.__init__(self, run_root: Path, *, actor_id: str = "local") -> None`:
     - If not `_ACTOR_RE.match(actor_id)`: raise `LabStoreError("Actor ID must be 1-64 alphanumeric, underscore, or hyphen characters.")`.
     - Store `self.actor_id = actor_id`.
     - If `actor_id == "local"`: `self.root = run_root / "product/pair-rotation-lab"` (100% backward compatible).
     - Else: `self.root = run_root / "product/pair-rotation-lab/actors" / actor_id`.
2. **Smart Strategy Advisor (`src/qap/product_lab_advisor.py`, < 220 lines):**
   - Write pure deterministic advisor `advise_pair_strategies(analysis: Mapping[str, Any]) -> dict[str, Any]`.
   - Read `m = analysis["measurements"]`, `bar = str(analysis["bar"])`, `suggested_anchor = analysis.get("suggested_anchor")`, `coin_a = analysis["coin_a"]["code"]`, `coin_b = analysis["coin_b"]["code"]`.
   - Inspect:
     - `coint_passes = bool(m.get("cointegration") and m["cointegration"]["passes"])`
     - `coint_p = m["cointegration"]["p_value"] if m.get("cointegration") else None`
     - `half_life_bars = m["half_life"]["bars"] if (m.get("half_life") and m["half_life"]["reverting"]) else None`
     - `hurst_state = m["hurst"]["state"] if m.get("hurst") else None`
     - `hurst_val = m["hurst"]["value"] if m.get("hurst") else None`
     - `copula_info = m.get("copula")`
     - `anchor_id = suggested_anchor["coin"]["id"] if suggested_anchor else analysis.get("anchor")`
     - `anchor_r2 = suggested_anchor["joint_r_squared"] if suggested_anchor else None`
   - Build dual-audience regime summaries:
     - `regime_label`: `"mean_reverting"` if (`coint_passes` or `hurst_state == "reverting"`), `"trending"` if `hurst_state == "trending"`, else `"mixed_or_noisy"`.
     - `simple_summary`: plain-English 1–2 sentence explanation for non-technical subscribers (no Greek letters or p-values).
     - `pro_summary`: concise quant summary citing exact `coint_p`, `half_life_bars`, `hurst_val`, `copula` family/tails, and `anchor_r2`.
     - `bar_warning`: if `bar == "15m"`, return `"15m candles generate high swap counts where 20 bps round-trip fees often exceed gross spread; compare 1h or 4h as well."`, else `None`.
   - Build `suggestions: list[dict[str, Any]]` (always 3 ranked presets, validated via `LabSettings(**settings_dict).model_dump(mode="json")`):
     - Compute `rec_lookback = int(min(500, max(60, round(2.0 * half_life_bars))))` when `half_life_bars` is finite, else `96`.
     - If `regime_label == "mean_reverting"`:
       1. `zscore_kalman`: `method="zscore", hedge_method="kalman", lookback=rec_lookback, entry=2.0, exit=0.4` (Rank 1)
       2. `spread_copula`: `method="copula", lookback=max(80, rec_lookback), copula_probability=0.05` with `recommended_anchor = anchor_id if (anchor_r2 and anchor_r2 >= 0.25) else None` (Rank 2)
       3. `ratio_trend_guard`: `method="trend", fast_window=12, slow_window=48` as trend falsifier (Rank 3)
     - If `regime_label == "trending"`:
       1. `ratio_trend`: `method="trend", fast_window=12, slow_window=48` (Rank 1)
       2. `spread_copula_anchor`: `method="copula", lookback=96, copula_probability=0.05` with `recommended_anchor = anchor_id` (Rank 2)
       3. `zscore_ols_wide`: `method="zscore", hedge_method="ols", lookback=120, entry=2.5, exit=0.5` (Rank 3)
     - Else (`"mixed_or_noisy"`):
       1. `spread_copula`: `method="copula", lookback=96, copula_probability=0.05` with `recommended_anchor = anchor_id` (Rank 1)
       2. `zscore_ols`: `method="zscore", hedge_method="ols", lookback=96, entry=2.2, exit=0.4` (Rank 2)
       3. `ratio_trend`: `method="trend", fast_window=16, slow_window=64` (Rank 3)
     - Each suggestion dict has keys: `rank: int`, `preset_id: str`, `title: str`, `simple_reason: str`, `pro_reason: str`, `recommended_bar: str` (`"1h"` if `bar == "15m"` else `bar`), `recommended_anchor: str | None`, `settings: dict[str, Any]`.
3. **Tests to Add:**
   - `tests/unit/test_lab_store.py`: test `actor_id="local"` uses legacy path, `actor_id="sub_alice"` and `actor_id="sub_bob"` isolate trial counts (`settings_tried`), studies, and pins completely, and invalid `actor_id="../bad"` raises `LabStoreError`.
   - `tests/unit/test_lab_advisor.py`: test mean-reverting, trending, and `15m` noisy analysis dicts produce expected `regime_label`, `bar_warning`, non-empty `simple_summary` & `pro_summary`, and 3 `LabSettings`-valid suggestions.
4. **Gate Command:**
   ```bash
   uv run python scripts/qap_gate.py --pytest tests/unit/test_lab_store.py tests/unit/test_lab_advisor.py
   ```

---

## Card `S2-C` — Dual-Interface Wiring: AI-Agent CLI (`qap.lab_cli`) + Subscriber HTTP API

- **Model:** `pi` -> `aistudio2api/gemini-4-hydrogen` (`thinking="high"`).
- **Depends on:** `S2-A` and `S2-B` merged on `main`.
- **Owned Files:**
  - Edit: `src/qap/product_lab_study.py`, `src/qap/api/lab_study_schemas.py`, `src/qap/api/routes/lab_studies.py`, `tests/contract/api/test_lab_studies.py`
  - Create: `src/qap/lab_cli.py`, `tests/unit/test_lab_cli.py`
  - Regenerate via scripts: `web/openapi.json`, `web/src/api/schema.d.ts`

### Exact Implementation Steps

1. **Multi-Strategy Compare & Actor Support in `LabStudyService` (`src/qap/product_lab_study.py`):**
   - Add `actor_id: str = "local"` to `LabStudyService.__init__`, passing `actor_id=actor_id` to `LabStudyStore(run_root, actor_id=actor_id)`.
   - Add `compare(self, coin_a: str, coin_b: str, *, bar: str, days: int, band_lookback: int, anchor: str | None, candidates: Sequence[LabSettings]) -> dict[str, Any]`:
     - Require `1 <= len(candidates) <= 8`.
     - Acquire `family_lock` once, compute `analysis` and `inputs` once, register all `settings_candidates(c)` across `candidates` in one `register_trials` batch (honest family multiplicity!), run `prove_lab_strategy` for each candidate, save each study in `self.store`, and return:
       - `advisor`: `advise_pair_strategies(analysis)`
       - `studies`: list of saved study envelopes sorted by `(result["proof"]["passes"], result["proof"]["vs_hodl_pct"] or -1e9)` descending
       - `best_study_id`: top study's `study_id` (only if `passes is True`, else `None`).
2. **Subscriber HTTP Routes & Dual Simple/Pro Schemas (`src/qap/api/lab_study_schemas.py`, `src/qap/api/routes/lab_studies.py`):**
   - Support optional `X-QAP-Actor-Id` header on `/api/pair-rotation/studies*` routes (default `"local"` when absent).
   - Add `GET /api/pair-rotation/advisor` (`operation_id="getLabAdvisor"`, query params matching `analyze_pair_rotation`: `coin_a`, `coin_b`, `bar`, `days`, `band_lookback`, `anchor`) returning `LabAdvisorDto`.
   - Add `POST /api/pair-rotation/studies/compare` (`operation_id="compareLabStudies"`, body `LabCompareRequestDto` with `coin_a`, `coin_b`, `anchor`, `bar`, `days`, `band_lookback`, and `candidates: list[LabSettings]` defaulting to the 3 `advise_pair_strategies` presets when `candidates` is omitted/empty!) returning `LabCompareResultDto`.
   - Regenerate `web/openapi.json` and `web/src/api/schema.d.ts`.
3. **Token-Efficient AI-Agent CLI (`src/qap/lab_cli.py`, < 260 lines):**
   - Invocable as `uv run python -m qap.lab_cli <subcommand> [flags]` (runs directly against `run_root=runs`, `market_data_root=.`, `repository_root=.` with `--run-root`, `--data-root`, `--actor-id` overrides and `--format json|md` defaulting to compact `json`):
     - `coins [--query TEXT] [--limit 25]` -> lists eligible coins (auto-bootstraps directory if needed with `--prepare`).
     - `prepare --coin-a ID --coin-b ID [--anchor ID]` -> prepares immutable Binance bars + execution metadata directly via `PairRotationData`.
     - `analyze --coin-a ID --coin-b ID [--anchor ID] [--bar 1h] [--days 180] [--band-lookback N]` -> returns compact measurements + `advisor` recommendations (omits raw 17,000-point chart arrays unless `--include-series` is passed, saving 95% of agent context tokens!).
     - `study --coin-a ID --coin-b ID [--anchor ID] [--bar 1h] [--days 180] [--settings JSON]` -> runs 1 study and prints compact summary (`study_id`, `call`, `proof`, terminal `statistics`, trade count).
     - `compare --coin-a ID --coin-b ID [--anchor ID] [--bar 1h] [--days 180] [--candidates JSON]` -> runs multi-strategy comparison (uses Smart Advisor presets when `--candidates` is omitted!) and prints ranked net-of-cost results.
     - `saved [--limit 20] [--study-id ID]` -> lists or inspects saved studies for `--actor-id`.
   - Exit codes: `0` success, `2` invalid CLI args/settings, `3` market/store error (printed as `{"error": ...}` on stderr).
4. **Tests to Add:**
   - `tests/contract/api/test_lab_studies.py`: test `X-QAP-Actor-Id` header isolation, `GET /api/pair-rotation/advisor`, and `POST /api/pair-rotation/studies/compare`.
   - `tests/unit/test_lab_cli.py`: test `analyze`, `study`, `compare`, and `saved` in both `--format json` and `--format md` on offline recorded fixtures, verifying compact output omits bulky series arrays by default.
5. **Gate Command:**
   ```bash
   uv run python scripts/qap_gate.py --pytest tests/unit/test_lab_cli.py tests/unit/test_lab_store.py tests/unit/test_lab_advisor.py tests/contract/api/test_lab_studies.py tests/contract/api/test_openapi.py
   ```

---

## Card `S4-A` — Preregistered `1h` / `4h` / `1d` Strategy Discovery via `qap.lab_cli`

- **Model:** `pi` -> `mistral/deepseek-v4-1-flash-1017` (`thinking="max"`).
- **Depends on:** `S2-C` merged on `main`.
- **Owned Files:**
  - Create: `docs/research/2026-11-15-stage-s4-trial-plan.json`, `docs/research/2026-11-15-stage-s4-trials.jsonl`, `docs/research/2026-11-15-stage-s4-discovery-results.md`
- **Steps:**
  1. Predeclare 24 trials across 6 liquid Binance pairs (`SOL/ETH`, `BNB/ETH`, `LINK/ETH`, `AVAX/SOL`, `DOGE/XRP`, `LTC/BTC`) on `1h` and `4h` (`days=180` and `days=365`) testing:
     - `zscore` (`kalman` and `ols`),
     - `copula` (direct and `binance:BTC` anchor-mediated),
     - `trend` (with `trend_deadband=0.002`),
     under isolated `--actor-id stage-s4-20261115` so discovery is cleanly audited.
  2. Prepare data once per pair via `uv run python -m qap.lab_cli prepare ...`, then run each trial sequentially (one heavy command at a time) via `uv run python -m qap.lab_cli study ... --format json >> docs/research/2026-11-15-stage-s4-trials.jsonl`.
  3. Compute Holm-corrected family survival at `alpha = 0.05` and write the complete honest table (`pair`, `bar`, `method`, `call`, `vs_hodl_pct`, `vs_control_pct`, `gross_vs_hodl_pct`, `cost_paid_pct`, `folds_passing`, `validation_trades`, `corrected_p_value`, `holm_survives`) in `docs/research/2026-11-15-stage-s4-discovery-results.md`.
  4. **Verify:** `uv run python scripts/qap_gate.py --fast`
