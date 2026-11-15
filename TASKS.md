# TASKS — Phase 21 Self-Verifying Pair Rotation MVP & L2 Paper Plan (2026-11-15)

Canonical spec & math playbook: [docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md](docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md).
Literal worker cards (next wave): [docs/plans/22-backend-and-agent-cli-tasks.md](docs/plans/22-backend-and-agent-cli-tasks.md).
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
| S2-A | done | S0-2, S1 | `hydrogen` (`high`) | **Wave 1 (parallel):** Add `crash_defense_mode` (`coins_only`, `park_anchor`, `park_usdt`) + trailing-20-bar median volume fallback (`2x` impact penalty) in `lab_settings.py`, `lab_replay.py`, `lab_proof.py` + OpenAPI sync (`docs/plans/22-backend-and-agent-cli-tasks.md`). | Committed `f3590cf`; `qap_gate.py` + 142 experiment/contract tests GREEN. |
| S2-B | done | S0-2, S1 | `deepseek` (`max`) | **Wave 1 (parallel):** Add `actor_id` subscriber/agent store isolation (`LabStudyStore`) + `product_lab_advisor.py` (Simple + Pro regime summary & 3 validated presets) (`docs/plans/22-backend-and-agent-cli-tasks.md`). | Committed `1af5a94` (merged `abc80c1`); `qap_gate.py` + 17 store/advisor tests GREEN. |
| S2-C | done | S2-A, S2-B | `hydrogen` (`high`) | **Wave 2:** Wire dual interfaces: `GET /api/pair-rotation/advisor` + `POST /api/pair-rotation/studies/compare` + `X-QAP-Actor-Id` for Web UI, AND `uv run python -m qap.lab_cli` (`coins`, `prepare`, `analyze`, `study`, `compare`, `saved`) for AI agents (`docs/plans/22-backend-and-agent-cli-tasks.md`). | Committed `2287af9`; `qap_gate.py` + 30 CLI/store/advisor/API contract tests GREEN. |
| S4-A | done | S2-C | `deepseek` (`max`) | **Wave 3:** Run 24 preregistered `1h`/`4h` trials across 6 liquid pairs via `qap.lab_cli` (`--actor-id stage-s4-20261115`), apply Holm `alpha=0.05`, and write `docs/research/2026-11-15-stage-s4-discovery-results.md`. | Committed `3043c42`; 24/24 trials ran with 0 `cost_data_missing`; 7/24 net positive vs HODL & Control (`DOGE/XRP` 4h BTC-copula `+15.55%`, `LINK/ETH` 4h BTC-copula `+7.14%`), 0/24 Holm survivors under 2x tuning cost gate. |
| S4-B | done | S4-A | T3 `acpRegistry_mistral_vibe` `deepseek-v4-1-flash-1017` (`max`) + architect fix | **Wave 4A:** Run 12 low-turnover `4h`/`1d` single-shot (`auto_tune=false`) trials testing `2%` tail BTC-copula (`minimum_hold=12`) + `crash_defense_mode="park_anchor"` under `--actor-id stage-s4b-20261115` and record Holm results. | Turnover fell 21–35% (`DOGE/XRP` 4h `+16.50%` vs HODL, `p=0.022`; `LINK/ETH` 1d `+10.92%` on `0.91%` cost); fixed 3rd-asset `park_anchor` metadata in `product_lab_inputs.py` & `product_lab_study.py` (`AVAX/SOL` `park_anchor` cut loss to `-4.67%`). |
| S5 | done | S2-C | inline + `wip/stage-s5-partial` | **Wave 4B (Backend L2 Paper):** Build `binance_ws_stream.py`, `l2_book_fill.py`, `live_paper_runner.py`, `lab_cli_paper.py`, and `/api/pair-rotation/paper-sessions` API (`docs/plans/23-stage-s5-and-s6-outsourcing-plan.md`). | Completed `binance_ws_stream.py`, `l2_book_fill.py`, `live_paper_execution.py`, `live_paper_state.py`, `live_paper_runner.py` (470 lines), `lab_cli_paper.py`, `/api/pair-rotation/paper-sessions` routes/schemas, OpenAPI/TS schema sync, and unit+contract suites (`qap_gate.py` 9/9 GREEN). |
| S6 | in-progress | S2-C, S5 | inline | **Wave 5 (Web Cockpit UI):** Build the 3-column Finance Cockpit on `/lab` (`docs/plans/23-stage-s5-and-s6-outsourcing-plan.md`). | |

---

## Historical Archive — Phase 19 Lab Continuation (2026-10-27)

All 18 cards (`L1`–`L8`, `A1`–`A6`, `U1`, `B1`–`B3`) reached `review` and were committed in `9e5ef1a` (`feat: complete Pair Rotation Lab MVP, caching, proof gates, and review fixes`). See Git commit `9e5ef1a:TASKS.md` and `docs/plans/19-pair-rotation-lab-mvp.md` for per-card historical evidence.
