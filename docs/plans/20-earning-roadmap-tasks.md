# Phase 20 (proposal) — Task cards for worker agents

```text
Update context — 2026-10-27
Trigger: Hamza: refine the plan so a small "flash" model can do the tasks without help.
Purpose: turn stages A–D of the roadmap into literal task cards.
Impact: proposal only. Cards marked BLOCKED wait for a decision by Hamza.
Evidence: 20-earning-roadmap-proposal.md, TASKS.md, live checks on 2026-10-27.
```

Parent plan: [20-earning-roadmap-proposal.md](20-earning-roadmap-proposal.md).
Status of each card lives in [TASKS.md](../../TASKS.md), not here.

## Rules for every card (read before you start)

1. Read `AGENTS.md` at the repo root. It overrides this file.
2. Work in `/home/hamza/repo/qap`. Do not commit. Do not push. Do not create branches.
3. Edit only the files that the card lists under **Edit**. If you need another
   file, stop and report. Do not guess.
4. Do not change these, ever: fees, slippage, impact, fill rules, benchmark
   definitions (HODL, control), fold counts, significance, `final_oos` use,
   universe eligibility, the action space. If a step seems to need one of them,
   stop and report.
5. Never place an order. Never call a private exchange endpoint. Never print or
   copy `~/.config/qap/env`.
6. Memory is small (about 7 GB shared). Run one heavy command at a time: pytest,
   pnpm build, a browser, or a study run. Never two together.
7. Hand-written files stay below 500 lines. Check with
   `uv run python scripts/check_source_size.py`.
8. When you finish, set the card's TASKS.md row to `review`, never `done`, and
   append your evidence: commands run, exit codes, numbers measured.
9. **Stop and report** (do not improvise) when: a check fails twice, a listed
   file or symbol does not exist, the card contradicts the code, or you are not
   sure. A short honest report is a success. A guessed change is a failure.

Report format, always:

```text
Outcome: done | blocked | failed
Files changed: <list>
Commands run: <command> -> exit <code>, <key number>
Measured: <before> -> <after> (if the card asks for a number)
Doubts: <list or "none">
```

## Running API facts

- The workbench runs with `./scripts/start_workbench.sh` (API on
  `http://127.0.0.1:8000`, web on `:5173`). It does **not** reload Python code.
  If you change Python, the parent restarts the workbench, not you.
- Workbench stop rule: the launcher stops every service when the API exits.
  Do not kill the API or the launcher yourself.
- Analysis URL for BTC/ETH:
  `http://127.0.0.1:8000/api/pair-rotation/analysis?coin_a=binance:BTC&coin_b=binance:ETH&bar=15m&days=180&band_lookback=672`
- Study URL: `POST http://127.0.0.1:8000/api/pair-rotation/studies` with JSON
  `{"coin_a":..., "coin_b":..., "bar":"15m", "days":180, "band_lookback":672, "anchor":null, "settings":{"method":"zscore"}}`.
- A new pair needs data first: `POST /api/pair-rotation/open` with
  `{"coin_a":..., "coin_b":..., "include_execution":true}`, then poll
  `GET /api/operations/<operation_id>` until `status` is `completed`
  (`failed`, `interrupted` or `cancelled` = stop).
- Reference script that does both: the parent's `trials.sh` logic is copied into
  card A4.

---

## Stage A — Fast, trusted research loop

### A1 — Measure the analysis time (read-only)

- **Engine:** flash or Codex `medium`. **Depends:** nothing.
- **Edit:** nothing in `src/`, `tests/`, `web/`. Create only
  `docs/research/2026-10-27-analysis-speed-baseline.md`. If that file exists, stop and report.
- **Steps (run each command exactly; copy its output into your notes):**
  0. Check the load. Run:
     `curl -s http://127.0.0.1:8000/api/operations | jq '[.items[] | select(.status=="running")] | length'`
     - If the command fails (no output, or "connection refused"): stop. Report "API not running".
     - If it prints a number above `0`: stop. Report "operations running, retry later".
     - If it prints `0`: end your turn with the single line
       `QUESTION: Is a study request running?` and outcome `blocked`. The parent answers in a
       follow-up message. Continue only after the answer is "no". Then run `uptime` and copy
       the output.
  1. Run this command 4 times, one after the other. Copy each number. The first number
     is the "cold" time, the next three are "warm":
     `curl -s -o /dev/null -w '%{http_code} %{time_total}\n' 'http://127.0.0.1:8000/api/pair-rotation/analysis?coin_a=binance:BTC&coin_b=binance:ETH&bar=15m&days=180&band_lookback=672'`
     - If the first word of any of the 4 runs is not `200`: stop. Report the run number and code.
  2. Profile one call in-process. Run from `/home/hamza/repo/qap`:
     ```bash
     QAP_API_RUN_ROOT=$PWD/runs QAP_API_WORKSPACE_MODE=local_market \
     QAP_API_MARKET_DATA_ROOT=$PWD QAP_API_REPOSITORY_ROOT=$PWD \
     QAP_API_CAPTURE_ROOT=$PWD/runs/public-capture \
     uv run python -c "
     import cProfile, pstats
     from fastapi.testclient import TestClient
     from qap.api.app import create_default_app
     c = TestClient(create_default_app())
     u = '/api/pair-rotation/analysis?coin_a=binance:BTC&coin_b=binance:ETH&bar=15m&days=180&band_lookback=672'
     print('warmup status', c.get(u).status_code)
     cProfile.run('c.get(u)', '/tmp/qap-analysis.prof')
     pstats.Stats('/tmp/qap-analysis.prof').sort_stats('cumulative').print_stats(25)
     " 2>&1 | tail -45
     ```
     - If the output has `Traceback`: copy the last 10 lines into the report and stop.
     - If `warmup status` is not `200`: copy it into the report and stop.
     - Ignore warning lines. Copy only rows that start with a number (pstats rows).
  3. Write the baseline file with exactly these sections:
     ```markdown
     # Analysis speed baseline — 2026-10-27
     ## Load
     <uptime output> | running operations: 0
     ## HTTP timings (seconds)
     | run | kind | seconds |
     |-----|------|---------|
     | 1 | cold | <n> |
     | 2 | warm | <n> |
     | 3 | warm | <n> |
     | 4 | warm | <n> |
     ## Profile (one warm in-process call, top 15 by cumulative time)
     | cumulative s | calls | function (file:line) |
     |--------------|-------|----------------------|
     <15 rows copied from the pstats output, top to bottom; skip rows for cProfile, TestClient, anyio, starlette internals only if more than 15 rows exist>
     ## Notes
     <one line per fact you saw; no guesses about causes>
     ```
- **Acceptance:** the file exists, has 4 timings and 15 profile rows. Set A1 to `review`.
- **Do not:** restart the workbench, change any setting, or run a study.

### A2 — Cache JSON state reads by file version

- **Engine:** Codex `high`. **Depends:** A1 at `review`.
- **Read first:** `src/qap/product_universe.py` lines 85–145 (constructor, `_state_guard`,
  `_write_model`, `read_state`, `read_directory`), `src/qap/product_universe_models.py`
  lines 49–50 (`_FrozenModel`, `frozen=True`), the A1 baseline file.
- **Edit:** create `src/qap/product_universe_cache.py`; edit `src/qap/product_universe.py`;
  create `tests/unit/test_product_universe_cache.py`. Before you start, run
  `ls src/qap/product_universe_cache.py tests/unit/test_product_universe_cache.py`.
  If either exists, stop and report.
- **Facts that constrain the design (already checked by the parent):**
  - `product_universe.py` has 618 lines. It must not grow by more than 15 lines. Put the
    cache logic in the new module.
  - `read_state` and `read_directory` parse with
    `ProductUniverseState.model_validate_json(path.read_text(...))` and
    `ProductMarketDirectory.model_validate_json(...)`. They do not use `json.loads`.
  - Both models are frozen Pydantic models. A cached instance can be returned to every
    caller. No deep copy is needed.
  - The API process and a worker process write these files with `_write_model`, which writes
    a temporary file and calls `os.replace`. So the inode changes on every write.
- **Steps:**
  1. In `product_universe_cache.py`, write a class `VersionedFileCache` with one method
     `get(self, path: Path, parse: Callable[[str], T]) -> T`. It calls `path.stat()` and
     builds the key `(st_ino, st_mtime_ns, st_size)`. If the stored key for `path` matches,
     it returns the stored value. Else it calls `parse(path.read_text(encoding="utf-8"))`,
     stores `(key, value)` and returns the value. If `stat()` or `parse` raises, store
     nothing and let the exception propagate (the callers already catch `OSError` and
     `ValidationError`). Add `drop(self, path: Path) -> None`.
     Protect the dict with a `threading.Lock`.
  2. In `ProductUniverse.__init__`, create one `VersionedFileCache` instance.
  3. In `read_state` and `read_directory`, replace only the `model_validate_json(path.read_text(...))`
     expression with `self._cache.get(path, Model.model_validate_json)`. Keep the
     `is_file()` check and the `except (OSError, ValidationError)` handling exactly as they are.
  4. In `_write_model`, you cannot reach the instance (it is a staticmethod). So after each
     of the four `self._write_model(...)` calls (lines 168, 291, 362, 411), add
     `self._cache.drop(<same path>)`. Do not change `_write_model`.
- **Tests to add (in the new test file, use `tmp_path`):**
  (a) `universe = ProductUniverse(tmp_path)`. The files live in a subdirectory:
      `universe.state_path` is `tmp_path / "product" / "research-universe.json"`
      (`product_universe.py:93–94`). Always use `universe.state_path`, never a path you build.
      Create the parent with `universe.state_path.parent.mkdir(parents=True, exist_ok=True)`,
      then write `ProductUniverseState().model_dump_json()` to `universe.state_path`.
      Call `read_state()` twice. Assert both results are the same object (`is`).
  (b) After a write through a public method (`set_asset_admission` or `apply_policy_bindings`;
      read its signature first), `read_state()` returns the new data.
  (c) Another writer: write a different valid state to the file with
      `os.replace` from a temporary file (as `_write_model` does). Assert `read_state()`
      returns the new data.
  (d) Unit test of `VersionedFileCache` alone: a counting `parse` function is called once
      for two `get` calls, and twice after the file is rewritten.
- **Checks (run in this order, one at a time):**
  `uv run pytest -q tests/unit/test_product_universe_cache.py`,
  `uv run pytest -q tests/contract/api/test_pair_rotation.py tests/contract/api/test_pair_rotation_analysis.py`,
  `uv run ruff check src tests`, `uv run ruff format --check src tests`,
  `uv run pyright src tests`, `uv run lint-imports`, `uv run python scripts/check_source_size.py`.
- **Acceptance:** all checks pass. Report "ask parent to restart the workbench". The parent
  restarts it and repeats A1 step 1, then records before and after timings in the A1 file.
- **Stop and report if:** a caller of `read_state`/`read_directory` mutates the result
  (frozen models raise on mutation, so a test failure with `ValidationError: frozen` means this),
  or a contract test fails after your change and passed before it.

### A3 — Bound the copula fit to recent returns

- **Engine:** Codex `high`. **Depends:** A1 at `review`.
- **Read first:** `src/qap/relationship/dependence_measurements.py` lines 15–25 and 125–150,
  `tests/unit/relationship/test_dependence_measurements.py`,
  `web/src/features/lab/LabEvidence.tsx` line 40, `web/src/features/lab/LabEvidence.test.tsx`.
- **Edit:** `src/qap/relationship/dependence_measurements.py`,
  `tests/unit/relationship/test_dependence_measurements.py`,
  `web/src/features/lab/LabEvidence.tsx` (line 40, the `term` value only),
  `web/src/features/lab/LabEvidence.test.tsx` (the expected term text only).
  Do not edit `src/qap/relationship/lab_copula.py`.
- **Facts (checked by the parent):** `copula_tails(close_a, close_b)` returns `None` when
  `close_a.size < MIN_BARS_COPULA` (120). It then calls
  `copula_features(close_a, close_b, training=close_a.size - 2)` and sets
  `observations=fitted.training_observations`. N closes give N−2 fitted returns.
  A 15m, 180-day Lab window has about 17,280 closes.
- **Steps:**
  1. Under `MIN_BARS_COPULA = 120`, add `COPULA_MAX_RETURNS = 4000`.
  2. In `copula_tails`, keep the `MIN_BARS_COPULA` check first, unchanged. After it, add:
     ```python
     keep = COPULA_MAX_RETURNS + 2
     close_a, close_b = close_a[-keep:], close_b[-keep:]
     ```
     Do not change anything else in the function.
  3. In `LabEvidence.tsx` line 40, change the `term` value to:
     `` m.copula ? `Copula tail dependence (${m.copula.family} family), fitted on the latest ${m.copula.observations} returns.` : 'Copula tail dependence.' ``
  4. In `LabEvidence.test.tsx`, the fixture has `observations: 2158`. Change the expected
     text `'Copula tail dependence (student family).'` to
     `'Copula tail dependence (student family), fitted on the latest 2158 returns.'`.
- **Tests to add (Python):**
  Build each series with this helper in the test file:
  ```python
  def walk(n: int) -> tuple[np.ndarray, np.ndarray]:
      rng = np.random.default_rng(7)
      x, y = rng.normal(0, 0.01, n), rng.normal(0, 0.01, n)
      a = 100 * np.exp(np.cumsum(x))
      b = 50 * np.exp(np.cumsum(0.6 * x + 0.8 * y))
      return a, b
  ```
  Import `copula_features` with `from qap.relationship.lab_copula import copula_features`.
  If `copula_features` returns `None` for either test series, stop and report.
  (a) `walk(10_000)`:
      result is not `None` and `result.observations == 4000`.
  (b) `walk(3_000)`: the result equals the result of calling
      `copula_features(close_a, close_b, training=close_a.size - 2)` directly
      (compare family, lower tail, upper tail, observations).
- **Checks (one at a time):** `uv run pytest -q tests/unit/relationship`,
  `uv run ruff check src tests`, `uv run pyright src tests`, then in `web/`:
  `pnpm vitest run src/features/lab` and `pnpm typecheck`. If `web/node_modules` does not
  exist, run `pnpm install --frozen-lockfile` in `web/` once first.
- **Acceptance:** all checks pass. Measure copula time before and after with the A1 step 2
  profile command: copy the cumulative seconds of the `copula_tails` row from both runs.
- **Stop and report if:** test (b) does not match. That means the cap changed short series.

### A4 — Batch study runner with predeclaration

- **Engine:** Codex `high`. **Depends:** none.
- **Edit:** new `scripts/run_lab_trials.py`, new `tests/unit/test_run_lab_trials.py`.
- **Behavior:**
  - Input: `--plan PATH` (JSON list of trials: `coin_a`, `coin_b`, `method`, optional
    `bar`, `days`, `band_lookback`) and `--out PATH` (JSONL).
  - Refuse (exit 2, message) when `--out` already exists. A rerun needs a new file.
    This keeps the trial family fixed before results.
  - Before the first study, write a first line
    `{"family": <plan file sha256>, "trials": <count>, "started_at": <UTC ISO>}`.
  - For each trial in order: prepare data (open + poll, see "Running API facts"),
    then POST the study. Write one line per trial with: `trial`, pair, `method`,
    `seconds`, `study_id`, `call.status`, and from `proof`: `passes`,
    `vs_hodl_pct`, `vs_control_pct`, `folds_passing`, `folds_total`,
    `validation_trades`, `raw_p_value`, `corrected_p_value`, `settings_tried`; plus
    `wealth.terminal_values`; plus total `fees_usdt` and `slippage_usdt` summed
    over `trades`. On an HTTP error write `{"trial":..., "error": <body>}` and continue.
  - Exact line shapes (one JSON object per line, keys in this order). `trial` is
    the 1-based position in the plan. Costs are decimal strings summed with
    `decimal.Decimal`, never floats. Copy API numbers as the API returns them.
    ```json
    {"family":"<sha256 hex of the plan file bytes>","trials":10,"started_at":"2026-10-27T00:00:00Z"}
    {"trial":1,"coin_a":"binance:SOL","coin_b":"binance:ETH","method":"zscore","seconds":161,"study_id":"<id>","call":"no_edge","passes":false,"vs_hodl_pct":-4.29,"vs_control_pct":-4.34,"folds_passing":1,"folds_total":8,"validation_trades":102,"raw_p_value":1.0,"corrected_p_value":1.0,"settings_tried":3,"terminal_values":{"hodl":"9876.01","strategy":"9452.23"},"fees_usdt":"268.12","slippage_usdt":"240.79"}
    {"trial":2,"coin_a":"binance:BNB","coin_b":"binance:ETH","method":"zscore","seconds":12,"error":{"status":409,"body":"<response text>"}}
    ```
    `seconds` is an integer of wall time for prepare plus study. When the API
    returns `wealth: null`, write `"terminal_values": null`. When a proof field is
    null, write null. Any other missing field: write null and continue.
  - Use only the standard library (`urllib.request`, `json`, `hashlib`, `decimal`).
  - No retries of a failed study. No setting changes. No parallel requests.
- **Tests:** use a fake HTTP server from `http.server` on a free port: refusal on an
  existing out file, the family line, one success line, one error line.
- **Checks:** `uv run pytest -q tests/unit/test_run_lab_trials.py`,
  `uv run ruff check scripts tests`, `uv run pyright scripts tests`.
- **Acceptance:** checks pass. Do not run it against the real API; the parent does.

### A5 — Diagnose the stopped collector (read-only)

- **Engine:** flash or Codex `medium`. **Edit:** nothing. Report only.
- **Fact:** on 2026-10-27, `GET /api/workspace` returned
  `current_evidence_collector_status: failed`, reason "Collector process stopped
  unexpectedly". The parent restarted the launcher with SIGINT earlier that day.
- **Steps:** read `scripts/start_workbench.sh` and `src/qap/api/routes/workspace.py`;
  find where the lease is written and when `failed` is set. Answer: does a launcher
  SIGINT mark the lease `failed` instead of `stopped`? Quote the lines.
- **Acceptance:** a report with file:line quotes and a yes/no answer.

---

## Stage B — Preregistered research program

### B1 — Report gross edge and cost paid (public contract: review at once)

- **Engine:** Codex `xhigh`. **Depends:** A4 at `review`.
- **Read first:** `src/qap/experiment/lab_proof.py` lines 120–148 (the initial `proof` dict)
  and 255–296 (`proof.update` and `passed`), `src/qap/api/lab_study_schemas.py` lines 58–81
  (`LabProofDto`), `src/qap/experiment/lab_replay.py` lines 60–70 (trade fields
  `fees_usdt: str`, `slippage_usdt: str`), `tests/contract/api/test_lab_studies.py`,
  `tests/unit/experiment/test_lab_proof.py`.
- **Edit:** `src/qap/experiment/lab_proof.py`, `src/qap/api/lab_study_schemas.py`,
  `tests/unit/experiment/test_lab_proof.py`, `tests/contract/api/test_lab_studies.py`,
  and by regeneration only: `web/openapi.json`, `web/src/api/schema.d.ts`.
- **Behavior (reporting only; do not change `passes`, `call`, folds, p-values or any rule):**
  1. In the initial `proof` dict (around line 133, next to `"validation_trades": 0`), add
     `"cost_paid_pct": None` and `"gross_vs_hodl_pct": None`.
  2. In the `proof.update({...})` block (around line 271), add:
     ```python
     cost_paid = sum(
         (Decimal(t.fees_usdt) + Decimal(t.slippage_usdt) for t in strategy.trades),
         Decimal(0),
     )
     start = Decimal(str(strategy.values[0]))
     hodl_end = benchmarks["hodl"].terminal_value
     ```
     on the lines directly above `proof.update(` (after `comparator = benchmarks[control]`),
     and these two keys inside it:
     `"cost_paid_pct": float(cost_paid / start) * 100,`
     `"gross_vs_hodl_pct": float((strategy.terminal_value + cost_paid) / hodl_end - 1) * 100,`
     `strategy.terminal_value` and `hodl_end` are already `Decimal` (`lab_replay.py:75`).
     If `start` or `hodl_end` is zero, set both keys to `None` instead of dividing.
     `Decimal` is already imported in this file. Check with `rg -n '^from decimal' src/qap/experiment/lab_proof.py`.
  3. In `LabProofDto`, after `vs_control_pct`, add `cost_paid_pct: float | None` and
     `gross_vs_hodl_pct: float | None`.
- **Regenerate (in this order):** `uv run python scripts/export_openapi.py web/openapi.json`,
  then `cd web && pnpm generate:api`. Do not edit those two files by hand.
- **Tests to add:** in `test_lab_proof.py`, copy the setup of
  `test_full_direct_metadata_with_market_filter_reaches_the_proof` (line 260) into a new test.
  Assert `proof["cost_paid_pct"] >= 0` and `proof["gross_vs_hodl_pct"] >= proof["vs_hodl_pct"]`
  when `proof["vs_hodl_pct"]` is not `None`. In the contract test, assert
  both keys exist in `result.proof`.
- **Check value (from trial 1 on 2026-10-27, SOL/ETH z-score):** strategy end 9452.24, HODL end
  9876.01, fees 268.13 + slippage 240.80 = 508.93 USDT, start 10,000. Expected
  `cost_paid_pct` ≈ 5.09 and `gross_vs_hodl_pct` ≈ (9452.24 + 508.93) / 9876.01 − 1 ≈ 0.86%.
  The parent checks this on the live API after a restart. You do not run a study.
- **Checks (one at a time):** `uv run pytest -q tests/unit/experiment tests/contract/api/test_lab_studies.py`,
  `uv run ruff check src tests`, `uv run pyright src tests`, in `web/`: `pnpm typecheck`.
- **Acceptance:** checks pass, the two regenerated files changed only by the two new fields
  (`git diff web/openapi.json web/src/api/schema.d.ts`: if any other line changed, stop
  and report). Then one independent review
  (risk override: public contract).

### B2 — Cost budget gate (approved by Hamza 2026-10-27; proof rule: review at once)

- **Engine:** Codex `xhigh`. **Depends:** B1 at `review` (B2 edits the same files).
- **Approved rule:** a candidate fails the proof when its gross gain over HODL on the
  **tuning period** is below 2× the cost it paid on the tuning period. The gate is an extra
  condition of `passes`. It does not remove any other condition. A gated trial still counts
  in the trial family (every run counts, decision 3).
- **Read first:** `src/qap/experiment/lab_proof.py` lines 97–310 (the whole
  `prove_lab_strategy`), `src/qap/experiment/lab_replay.py` lines 210–225 (`run_lab_replay`
  takes `start` and `end`), `src/qap/api/lab_study_schemas.py` lines 40–81,
  `web/src/features/lab/LabAnswer.tsx` lines 18–30, `web/src/features/lab/LabAnswer.test.tsx`
  lines 76–86.
- **Edit:** `src/qap/experiment/lab_proof.py`, `src/qap/policy/lab_settings.py`,
  `src/qap/api/lab_study_schemas.py`, `web/src/features/lab/LabAnswer.tsx`,
  `web/src/features/lab/LabAnswer.test.tsx`, `tests/unit/experiment/test_lab_proof.py`,
  `tests/contract/api/test_lab_studies.py`, and by regeneration only `web/openapi.json`,
  `web/src/api/schema.d.ts`.
- **Steps:**
  1. In `LabSettings` (`src/qap/policy/lab_settings.py`), add
     `cost_budget_multiple: Decimal = Field(default=Decimal("2"), ge=0, le=100)` after
     `minimum_notional`. Do not change any other field. Expected side effect: study IDs
     change for the same request, because the store hashes the settings JSON
     (`product_lab_store.py:34`). Old saved studies stay readable. Report this; do not fix it.
  2. In `prove_lab_strategy`, after the `paths = tuple(...)` line and before the
     `controls = {...}` line, add the tuning gate:
     ```python
     tuning_index = max(
         range(len(candidates)),
         key=lambda i: float(paths[i].values[split - 1] / paths[i].values[0]),
     )
     tuning = run_lab_replay(
         inputs, candidates[tuning_index], signals[tuning_index], end=split
     )
     tuning_hodl = run_lab_replay(inputs, settings, base_signal, kind="hodl", end=split)
     tuning_cost = sum(
         (Decimal(t.fees_usdt) + Decimal(t.slippage_usdt) for t in tuning.trades),
         Decimal(0),
     )
     tuning_gross = tuning.terminal_value + tuning_cost - tuning_hodl.terminal_value
     cost_gate = tuning_gross >= settings.cost_budget_multiple * tuning_cost
     tuning_start_value = Decimal(str(tuning.values[0]))
     proof["cost_gate_passed"] = cost_gate
     proof["tuning_cost_pct"] = float(tuning_cost / tuning_start_value) * 100
     proof["tuning_gross_vs_hodl_pct"] = float(tuning_gross / tuning_start_value) * 100
     ```
     A candidate with zero trades has cost 0. Then the gate passes when gross ≥ 0.
  3. In the initial `proof` dict, add `"cost_gate_passed": None`, `"tuning_cost_pct": None`,
     `"tuning_gross_vs_hodl_pct": None`.
  4. In the `passed = (...)` expression, add `and cost_gate` as the last condition.
  5. In the call chain after `elif not strategy.costs_supported:` and before
     `elif not passed:`, add:
     ```python
     elif not cost_gate:
         call = _call(
             "cost_budget_failed",
             "Costs eat the edge",
             "On the tuning period, the gain before costs was less than twice the costs paid.",
         )
     ```
  6. In `LabCallDto.status`, add `"cost_budget_failed"` after `"cost_data_missing"`.
     In `LabProofDto`, add `cost_gate_passed: bool | None`, `tuning_cost_pct: float | None`,
     `tuning_gross_vs_hodl_pct: float | None` after the B1 fields.
  7. In the `"correction"` text and `"limitations"` list: change nothing.
  8. Regenerate: `uv run python scripts/export_openapi.py web/openapi.json`, then
     `cd web && pnpm generate:api`.
  9. In `LabAnswer.tsx` `STATUS_LABELS`, add `cost_budget_failed: 'Costs eat the edge',`.
     In `LabAnswer.test.tsx` `statusLabels`, add `['cost_budget_failed', 'Costs eat the edge'],`.
- **Tests to add (`test_lab_proof.py`):** (a) a fixture with high fees (set
  `fee_bps` to a high value inside the field's allowed range; read the field limits first)
  gives `cost_gate_passed is False`, `passes is False` and call status `cost_budget_failed`;
  (b) the existing passing-proof test, if one exists, still passes (if it now fails only
  because of the gate, stop and report: do not change its fixture).
- **Checks (one at a time):** `uv run pytest -q tests/unit/experiment tests/unit/policy tests/contract/api/test_lab_studies.py`,
  `uv run ruff check src tests`, `uv run pyright src tests`, in `web/`:
  `pnpm vitest run src/features/lab` and `pnpm typecheck`.
- **Acceptance:** checks pass. Then one independent review (risk override: proof rule and
  public contract), at most two fix rounds.
- **Stop and report if:** a settings field name differs from this card, an existing test
  needs a fixture change, or saved studies fail to load after the change.

### B3 — Preregistration document (approved by Hamza 2026-10-27)

- **Engine:** flash or Codex `medium`. **Depends:** none. Documentation only.
- **Approved decisions:** 30 trials per hypothesis (H1, H2, H3: 90 in total). Holm correction
  over each hypothesis family at α = 0.05. Every run counts, also failed, gated and
  abandoned runs. Shadow run 180 days (decision 4). Coins only, no USDT cash (decision 1).
- **Edit:** create only `docs/research/2026-10-27-preregistration-h1-h3.md`. If it exists, stop.
- **Read first:** `docs/plans/20-earning-roadmap-proposal.md` sections 4 (stage B), 5 and 7;
  `docs/research/document-update-method.md`.
- **Write exactly these sections:**
  1. `# Preregistration H1–H3 — 2026-10-27` and an update-context block like the one at the
     top of the proposal.
  2. `## Hypotheses`: copy the section 5 table of the proposal unchanged.
  3. `## Trial budget`: one line per hypothesis: "30 trials. A trial is one study request."
  4. `## Correction`: "Each study already corrects across its own settings (Bonferroni,
     see `lab_proof.py` correction text). Across the trials of one hypothesis, apply Holm at
     α = 0.05 to the studies' corrected p-values. A hypothesis is supported only if at least
     one trial survives Holm and passes every other proof condition."
  5. `## Fixed settings`: bar list `1h`, `4h` for H2; costs as `LabSettings` defaults
     (fee 10 bps, slippage 5 bps, impact 10 bps); 8 folds; at least 5 passing; at least 10
     trades; cost gate 2× (B2). Write "no setting changes after the first result".
  6. `## Robustness set for a surviving trial`: copy the stage B robustness bullet of the
     proposal.
  7. `## Out of scope`: USDT cash, point-in-time discovery (stage C, decision 2 open), maker
     or BNB-discount cost models (decision 5 open), live orders.
  8. `## Trial log`: an empty table with columns
     `| # | hypothesis | pair | bar | method | study_id | call | corrected p | Holm survives |`.
- **Acceptance:** the file exists with the 8 sections. No other file changed
  (`git status --short docs/research` shows only this file as new).

---

## Stage C — Point-in-time universe — BLOCKED (decision 2)

## Stage D — Forward shadow run — BLOCKED (stage B exit, decision 4)

## Stage E/F — Live — BLOCKED (Phase 12 gate). No card exists by design.
