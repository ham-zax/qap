# Future improvements

Proposals from the 2026-11-16 terminal continuation. These entries authorize no implementation.

- **Stop full verification after early failures.** The compiler continued through a
  397-second Python suite after formatting and TypeScript failures. A corrected
  full run repeated that suite. Consider stopping before expensive checks when
  an earlier check fails. Preserve the existing lock and every required gate.

- **Running API provenance.** The browser received HTTP 422 from an older process,
  although current source supported the request. Expose a source revision and
  startup time in health output. Compare that contract before browser checks.
  Preserve active paper sessions during any restart.
- **Frontend acceptance coverage.** Mock tests passed while terminal controls lacked
  styles and saved runs restored only coin identifiers. Consider a small browser
  smoke test against the actual API contract, with desktop and mobile checks.
- **Complete coin discovery.** A 600-row response contained only 396 trading rows.
  A 1,000-row response contained all 415 current trading rows. Consider explicit
  pagination or server-side eligibility filtering before the directory exceeds
  the current request limit.
- **Bounded evidence output.** Combined reads exceeded the tool output limit during
  recovery. Keep each result bounded and extract only checkpoint fields from history.
- **Repeated directory fingerprints.** A warm analysis profile spends 1.01 seconds
  in five research-scope calls. Directory fingerprints account for 0.97 seconds.
  Consider reusing the digest for an immutable snapshot. Check copied models,
  changed snapshots, and historical v1 hashes before introducing any cache.

Proposals from the 2026-10-23 M3 session. These entries authorize no implementation.

- **Route generation before type checks.** The first build rejected a new route
  because TypeScript ran before Vite generated the route tree. Consider an explicit
  generation step in the existing web build command. Keep the version check.
- **Recorded browser fixture.** Cached failed module imports and a live registry
  refresh delayed browser checks. Consider a development server that serves sealed
  recorded market data through the real API. Keep sample and market labels explicit.
  Reload the browser after correcting a failed module import.
- **Statistical calibration.** Hurst estimates can misclassify short random walks.
  Lead-lag peak selection also needs significance and overlap calibration. Add
  simulation-based calibration before interpreting either as a signal or proof.
- **M3 coverage.** Add non-flat anchor ranking, unequal history, missing shared bars
  and first-open bootstrap failure/retry cases. Current tests cover exact data,
  mutation refusal, finite degeneracies, eligibility, saved settings and stale results.
- **Chart layout regression.** A page overflow check missed a clipped third-party
  chart table. Add a browser check that compares the chart table width with its
  container. The session fixes the global style collision, but no new CI gate is added.

Proposals from the 2026-10-27 session. These entries authorize no implementation.

- **Launcher restarts.** `start_workbench.sh` stops every service when the API
  exits, and it does not reload Python. A stale API served old measurements, and
  a manual restart stopped another session's collector. Consider a reload flag
  for the API alone.
- **Screenshot tooling.** Windows Chrome cannot write screenshots to WSL paths.
  One four-view screenshot round took 13 min, because each fresh page prepares
  data again. Consider a warm fixture route for visual checks.

Proposals from the 2026-11-15 Phase 21 planning session. Deferred until Stages S0–S5 exit green; see `docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md` §4.

- **Rust `PyO3` implementation & verifier core (`qap-rs`).** Python misses
  compile-time implementation bugs such as raw `Decimal` unit mix-ups (`Price`
  vs `Quantity` vs `Weight`), undeclared runtime exceptions (for example bare
  `next(...)` raising `StopIteration`), and shared mutable buffer aliasing.
  After Stage S4 confirms strategy edge, move execution/ledger state machines,
  L2 order-book matching, and/or the `qap_gate` verifier loop into a compiled
  Rust crate (`PyO3`/`maturin`) while keeping Python's C++ econometrics
  (`pyvinecopulib`, `statsmodels`, `arch`) and strict TypeScript on `web/`.
- **Branded types and exhaustiveness guards.** Before any Rust migration, tighten
  `qap_gate` with `typing.NewType` / `assert_never` in Python, branded scalar
  types in TypeScript, and `ruff` bugbear (`B`, `RUF`) checks to catch
  implementation defects at gate time.
- **Align `web/package.json` `packageManager` and drop `@playwright/test`.**
  Corepack runs `pnpm v12.18.0` while `web/package.json` declares `pnpm@11.21.0`,
  requiring `--pm-on-fail=ignore` in non-interactive shells, and `@playwright/test`
  has no remaining E2E consumer. Update `packageManager` and refresh
  `pnpm-lock.yaml` in one dedicated dependency commit.
- **Extract `scanner/catalog.py` into `market/` to retire `scanner/` tests.**
  Full `pytest -q` still takes ~357 s largely due to `tests/scenarios/test_scanner_*`
  and `tests/unit/scanner/`, retained only because `product_market_data.py`
  imports `scanner/catalog.py`. Moving catalog lookup into `qap.market` allows
  retiring `qap.scanner` and cutting full `pytest` below 60 s.
