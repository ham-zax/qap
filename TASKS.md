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
| S4-B | done | S4-A | T3 `acpRegistry_mistral_vibe` `deepseek-v4-1-flash-1017` (`max`) + architect fix | **Wave 4A:** Run 12 low-turnover `4h`/`1d` single-shot (`auto_tune=false`) trials testing `2%` tail BTC-copula (`minimum_hold=12`) + `crash_defense_mode="park_anchor"` under `--actor-id stage-s4b-20261115` and record Holm results. | Turnover fell 21–35% (`DOGE/XRP` 4h `+16.50%` vs HODL, `p=0.022`; `LINK/ETH` 1d `+10.92%` on `0.91%` cost; 0/12 Holm survivors); `7f0f7e3` fixed 3rd-asset `park_anchor` metadata in `product_lab_inputs.py` & `product_lab_study.py` (an unarchived post-fix `AVAX/SOL` check saw `-4.67%`, while `S4B-07`..`S4B-10` remain `blocked` in `2026-11-15-stage-s4b-trials.jsonl`). |
| S5 | done | S2-C | inline + `wip/stage-s5-partial` | **Wave 4B (Backend L2 Paper):** Build `binance_ws_stream.py`, `l2_book_fill.py`, `live_paper_runner.py`, `lab_cli_paper.py`, and `/api/pair-rotation/paper-sessions` API (`docs/plans/23-stage-s5-and-s6-outsourcing-plan.md`). | Completed `binance_ws_stream.py`, `l2_book_fill.py`, `live_paper_execution.py`, `live_paper_state.py`, `live_paper_runner.py`, `lab_cli_paper.py`, and `/api/pair-rotation/paper-sessions`; fixed post-RTT book freshness, historical close warmup, and `@aggTrade` `exchange_time_us` propagation; verified live against `wss://data-stream.binance.vision`. |
| S6 | done | S2-C, S5 | inline + architect live audit | **Wave 5 (Web Cockpit UI):** Build the 3-column Finance Cockpit on `/lab` (`docs/plans/23-stage-s5-and-s6-outsourcing-plan.md`). | Built 3-column Simple+Advanced Cockpit (`LabSidebar`, `LabAdvisorCard`, `LabSavedRuns`, `LabCompareTable`, `LabSignalChart`, `LabWealth` unit toggle, `LabTradeDrawer`, `LabScorecard`, `LabLivePaperPanel`); fixed `/api/workspace` state, `/advisor` dict-anchor serialization, real fold-key mapping, and CORS header; verified live in `wh-browser` + `qap_gate.py --full` 12/12 GREEN. |

---

## Phase 24 terminal integration

Update context — 2026-11-16: record integration checks after the provider handoff.
The approved [Phase 24 design](docs/plans/24-binance-terminal-ui-redesign.md) retains its requirements.

| id | status | acceptance | evidence |
|----|--------|------------|----------|
| P24 | review | Terminal layout, full coin discovery, Simple/Pro controls, saved snapshots, and bottom tabs. | All 12 compiler gates pass. Browser checks cover desktop, mobile, themes, search, saved runs, and a real strategy test. Rapid pair edits, explicit no-anchor support, header mode switch, 4 strategy presets, Anchor Lead-Lag 1m preparation/guard, and slider/InfoTip UI upgrades pass targeted and full checks. Fresh-process HTTP on check port 8001 measures 1,911 ms cold no-anchor analysis, 543 ms warm auto-anchor, and 50–59 ms advisor. See the [checkpoint](docs/aegis/work/2026-11-16-phase24-terminal/20-checkpoint.md). |

---

## Audit repair continuation — Plan 25

Update context — 2026-11-16
Trigger: Hamza asks the current editing AI to execute the audit repairs after its existing task.
Purpose: make the handoff visible without interrupting the current editor.
Impact: queues repairs and preserves the wider audit scope. No live-capital or research-contract relaxation is authorized.
Evidence: [Plan 25](docs/plans/25-audit-repairs-and-evidence-integrity.md) and [audit findings](docs/research/2026-11-16-audit/README.md).

Execution owner: the current editing AI after it completes or hands off its current task.
Read Plan 25 before claiming a row. Existing milestone statuses above remain historical evidence.

| id | status | depends | acceptance | evidence |
|----|--------|---------|------------|----------|
| AR-0 | done | current editor completion/handoff | Record the completed baseline and reproduce or reconcile every audit finding. | Baseline `2667425`; all 6 probes reproduced identically; registry locations & raw-artifact SHA-256 checksums recorded in [completion note](docs/reviews/2026-11-16-audit-repair-completion.md). |
| AR-1 | done | AR-0 | Timestamped completed-candle paper signals, restart/idempotency checks, replay parity, and legacy-session recovery. | `live_paper_candles.py`, `product_paper_inputs.py`, v2 schema + legacy v1 read/stop/block-step; 44 targeted pytest + 9/9 `qap_gate.py` + 90/90 Vitest GREEN. |
| AR-2 | done | AR-1 | Reconcile and retry partial target execution without duplicate fills or false completion. | `live_paper_reconcile.py` + `pending_target`/`pending_drift_target`/`superseded_targets`/`applied_fill_ids`; partial-sell retry & flip-supersede tests GREEN. |
| AR-3 | done | AR-2 | Require observed venue metadata through API and CLI, including third-anchor markets. | `resolve_paper_inputs` + `market_metadata_provenance` enforced on create/step (HTTP 409 / CLI exit 3 when missing or mismatched, incl. 3rd anchor). |
| AR-4 | done | AR-3 | Record actual supporting fill times, nonnegative book ages, and correct cross-leg ordering. | `L2SweepResult` + `latency_audit` track `requested_fill_leg*_ns` & nullable `actual_fill_leg*_ns`, `effective_fill_ns = max(target, book_recv)`, nonnegative `book_age_ms`. |
| AR-5 | done | AR-4 | Repair bootstrap resolution and add family preflight while preserving statistical rejection rules. | `lab_statistics.py` (`9,999` SPA reps default, floor `1/(reps+1)`, `qap.lab.proof.v2` provenance, `require_family_resolution` preflight in `run_lab_trials.py` & `LabStudyService`); 9/9 `qap_gate.py` GREEN. |
| AR-6 | done | AR-5 | Align measurement labels, advisor inputs, and stitched executed signals across every method. | Fixed-fallback Kalman lookback (`96`), `conditional rank` unit, ratio-vs-residual/copula labels, stitched walk-forward `values`/`preferences`/`upper_series`/`lower_series` & legacy compatibility; 9/9 `qap_gate.py` (148 pytest) + 90/90 Vitest GREEN. |
| AR-7 | done | AR-6 | Correct cost explanations and document drift while preserving historical artifacts. | Cost add-back & denominator notes in `lab_proof.py` & `LabVerdictSection.tsx`; dated corrections in S4-A & S4-B preserving raw JSONL SHA-256s; updated `README.md` & `TASKS.md`; links + `git diff --check` + 9/9 `qap_gate.py` GREEN. |
| AR-8 | done | AR-7 | Pass targeted and full gates, check repaired interfaces, and publish finding-to-test evidence. | OpenAPI synced, browser-fast check on `5174/lab` (`0` console errors, `overflowX: false`), finding-to-test matrix in `docs/reviews/2026-11-16-audit-repair-completion.md`, retired scanner extracted/removed, and `qap_gate.py --full` GREEN. |
| RD-1 | done | AR-8 | Deliver the research-policy proposal before changing admission or correction contracts. No new strategy trials. | Proposal delivered in `docs/research/2026-11-16-rd1-research-policy-proposal.md`; no new trials run and research contracts remain unchanged pending approval. |
| AUDIT-WIDE | done | AR-8 | Continue the overall audit of all strategies, portfolio economics, relationship maps, repository boundaries, usefulness, and market potential. | Equal-coverage 7-area assessment delivered in `docs/reviews/2026-11-16-broader-audit.md`. |

---

## Historical Archive — Phase 19 Lab Continuation (2026-10-27)

All 18 cards (`L1`–`L8`, `A1`–`A6`, `U1`, `B1`–`B3`) reached `review` and were committed in `9e5ef1a` (`feat: complete Pair Rotation Lab MVP, caching, proof gates, and review fixes`). See Git commit `9e5ef1a:TASKS.md` and `docs/plans/19-pair-rotation-lab-mvp.md` for per-card historical evidence.
