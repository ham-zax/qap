# TASKS — Phase 21 Self-Verifying Pair Rotation MVP & L2 Paper Plan (2026-11-15)

Canonical spec & math playbook: [docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md](docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md).
Compiler verifier: `uv run python scripts/qap_gate.py` (locked Quant invariants in `tests/invariants/test_quant_compiler_laws.py`).
Archive tag for retired Phases 14–18 workbench: `archive/pre-phase21-workbench` (`9e5ef1a`).

T3 Code `pi` subagent routing:
- Complex math / stateful logic: `pi` -> `aistudio2api/gemini-4-hydrogen` (`thinking="high"`).
- Mechanical cleanup / UI / scripts: `pi` -> `mistral/deepseek-v4-1-flash-1017` (`thinking="max"`).

Status values: `open`, `in-progress`, `review`, `done`, `blocked`.

| id | status | depends | owner / model | acceptance | evidence |
|----|--------|---------|---------------|------------|----------|
| S0-1 | done | - | frontier architect (inline) | Archive tag `archive/pre-phase21-workbench`, `scripts/qap_gate.py` compiler loop, `test_qap_gate.py`, `tests/invariants/test_quant_compiler_laws.py`, and self-contained Phase 21 playbook written. | `qap_gate.py --skip-invariants --pytest tests/unit/scripts/test_qap_gate.py` 8/8 passed; `test_quant_compiler_laws.py` catches all 10 pre-fix math defects in 2.4s. |
| S0-2 | done | S0-1 | T3 `pi` `mistral/deepseek-v4-1-flash-1017` (`max`) | Delete superseded Phases 14–18 web routes/features/E2E and backend Pair-Study/Research-Recipe bloat; simplify `AppShell` to `Lab` + `Activity`; regenerate OpenAPI, `schema.d.ts`, `routeTree.gen.ts`; pass `qap_gate.py --skip-invariants`. | Deleted 179 legacy files (~39k lines incl. OpenAPI/schema); merged cleanly with S1 on `main`; `qap_gate.py --full` passed 12/12 gates (`ruff`, `pyright`, `lint-imports`, `openapi_sync`, `tsc`, `quant_invariants`, full `pytest`, `engine_parity`, `vitest`, `vite build`). |
| S1 | done | S0-1 | T3 `pi` `aistudio2api/gemini-4-hydrogen` (`high`) | Fix `OLS`/`TLS`/`Kalman` centered intercepts, rolling stationary-spread `Copula` (direct + anchor-mediated) with exit band, rolling `lead_lag` beta, `trend` deadband hysteresis, and `0%`–`100%` (`rotation_size=0.5`) default; turn `tests/invariants/test_quant_compiler_laws.py` 100% GREEN without modifying invariant tests. | Reviewed diff & verified on `main`: `qap_gate.py` 9/9 passed (`quant_invariants` 23/23 GREEN, `hypothesis` scale-invariance `1e-6..1e6` GREEN, unit+contract suites GREEN). |
| S2 | open | S0-2, S1 | `hydrogen` (`high`) + `deepseek` (`max`) | Add `crash_defense_mode` (`coins_only` default, `park_anchor`, `park_usdt`) in `LabSettings`, `lab_replay.py`, OpenAPI, and `/lab` UI settings with unit/contract/Vitest coverage. | |
| S3 | open | S1 | `deepseek` (`max`) | Fix missing single-bar volume (`cost_data_missing` on `LINK/ETH`) using trailing 20-bar median volume fallback with `2x` impact penalty; verify archive completeness. | |
| S4 | open | S2, S3 | `deepseek` (`max`) + architect review | Extend `scripts/run_lab_trials.py` for anchor/settings overrides; run preregistered `1h`/`4h`/`1d` batch (`H1`, `H2a`, `H2b`, `H3`) with Holm `alpha=0.05` and record honest results. | |
| S5 | open | S4 | `hydrogen` (`high`) | Build `binance_ws_stream.py` (`wss://data-stream.binance.vision?timeUnit=MICROSECOND`), `l2_book_fill.py` (20-level taker sweep), and `live_paper_runner.py` (4-clock millisecond latency across Leg 1 & Leg 2). | |

---

## Historical Archive — Phase 19 Lab Continuation (2026-10-27)

All 18 cards (`L1`–`L8`, `A1`–`A6`, `U1`, `B1`–`B3`) reached `review` and were committed in `9e5ef1a` (`feat: complete Pair Rotation Lab MVP, caching, proof gates, and review fixes`). See Git commit `9e5ef1a:TASKS.md` and `docs/plans/19-pair-rotation-lab-mvp.md` for per-card historical evidence.
