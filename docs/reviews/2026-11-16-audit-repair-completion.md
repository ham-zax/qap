# Plan 25 — Audit Repair Completion & Evidence Note

Date: 2026-11-16.
Status: `AR-0` through `AR-8` implemented and verified; `RD-1` proposal and `AUDIT-WIDE` assessment delivered.
Authoritative plan: [Plan 25](../plans/25-audit-repairs-and-evidence-integrity.md).
Audit source: [2026-11-16 Audit](../research/2026-11-16-audit/README.md).
Related deliverables: [RD-1 Proposal](../research/2026-11-16-rd1-research-policy-proposal.md) and [Broader Audit](2026-11-16-broader-audit.md).

## AR-0 — Baseline & Finding Reconciliation

- **Implementation baseline HEAD:** `2667425c8b4b905fe5914109b56224f476f754f2` (`fix(lab): stabilize benchmarks, swap markers, compare labels, and strategy registries`).
- **Strategy registry locations:**
  - Backend: `src/qap/policy/lab_strategy_registry.py` (`STRATEGY_REGISTRY`, dispatched by `src/qap/policy/lab_signals.py`).
  - Frontend: `web/src/features/lab/strategyRegistry.ts` (`STRATEGY_REGISTRY`, consumed by `web/src/features/lab/LabProControls.tsx`).
- **Probe reproduction at `2667425`:** Ran `uv run python docs/research/2026-11-16-audit/probes.py` into `/tmp/qap-ar0-probes.json` (original `docs/research/2026-11-16-audit/probe-results.json` preserved untouched).

## Implemented Repairs (`AR-1` through `AR-8`)

- **`AR-1` (Completed-candle paper clock):** Added `src/qap/experiment/live_paper_candles.py` and `src/qap/product_paper_inputs.py`; upgraded `live_paper_state.py`, `live_paper_runner.py`, `api/routes/live_paper.py`, `lab_cli_paper.py`, and `LabLivePaperPanel.tsx` to `v2` timestamped candle state while preserving `v1` read/stop and refusing `v1` step.
- **`AR-2` (Partial target reconciliation):** Added `src/qap/experiment/live_paper_reconcile.py` and updated `live_paper_execution.py` / `live_paper_runner.py` with `pending_target`, `pending_drift_target`, `superseded_targets`, `applied_fill_ids`, and tradable-leg remainder completion. Superseded pending targets on neutral/changed candles restore committed 50/50 or new target weights instead of completing stale rotations.
- **`AR-3` (Observed venue metadata):** Enforced observed `MarketMetadata` (including 3rd-asset `park_anchor` markets) across API and CLI create/step boundaries via `resolve_paper_inputs` and `market_metadata_provenance`. Preserved `market_quantity_step`, `market_minimum_quantity`, and `market_maximum_quantity` across `metadata_to_record` / `metadata_from_record` round-trips.
- **`AR-4` (Actual supporting fill times):** Updated `L2SweepResult` (`l2_book_fill.py`) and `latency_audit` (`live_paper_execution.py`) to separate `requested_fill_leg*_ns` from nullable `actual_fill_leg*_ns`, enforce `effective_fill_ns = max(target, book_recv)`, and guarantee nonnegative `book_age_ms`.
- **`AR-5` (Bootstrap resolution & family preflight):** Added `src/qap/experiment/lab_statistics.py` (`DEFAULT_SPA_REPLICATES = 9_999`, `DEFAULT_SPA_SEED = 20260930`, `PROOF_PROTOCOL_VERSION = "qap.lab.proof.v2"`, derived floor `1/(reps+1)`, and `require_family_resolution` preflight). Updated `scripts/run_lab_trials.py` to normalize and forward full `settings`, `anchor`, `bar`, `days`, `band_lookback`, and `X-QAP-Actor-Id` headers.
- **`AR-6` (Measurements, advisor, and stitched signals):** Scoped `half_life` / `hurst` explicitly to `1:1 log-ratio`, fixed Kalman advisor fallback lookback (`96`), labeled spread copula as `conditional rank`, and persisted walk-forward stitched `values`, `preferences`, `upper_series`, and `lower_series` (`signal_provenance = "walk_forward_stitched"`) with honest legacy fallback.
- **`AR-7` (Economic explanations & document drift):** Clarified `cost add-back approximation` and percentage denominators in `lab_proof.py` and `LabVerdictSection.tsx`; added dated `Update context — 2026-11-16` notes to `docs/research/2026-11-15-stage-s4-discovery-results.md`, `docs/research/2026-11-15-stage-s4b-discovery-results.md`, `README.md`, and `TASKS.md` while keeping raw JSON/JSONL checksums identical.
- **`AR-8` (Integration, OpenAPI sync, browser check):** Verified `web/openapi.json` sync, ran `browser-fast` check on `http://127.0.0.1:5174/lab` against a clean preview API on `127.0.0.1:8001` (`0` console errors, `overflowX: false`, all updated labels rendered), and left existing `8000` / `5173` services untouched.

## Finding-to-Test Matrix

| Audit finding | Repaired owners | Regression tests |
| --- | --- | --- |
| 1. `corrected_spa` 499-replicate floor vs Holm | `lab_statistics.py`, `lab_proof.py`, `product_lab_study.py`, `scripts/run_lab_trials.py` | `tests/unit/experiment/test_lab_proof.py`, `tests/unit/test_run_lab_trials.py` |
| 2. Paper step untimed midpoint closes | `live_paper_candles.py`, `product_paper_inputs.py`, `live_paper_runner.py`, `live_paper_state.py` | `tests/unit/experiment/test_live_paper_candles.py`, `tests/unit/experiment/test_live_paper_runner.py`, `tests/contract/api/test_live_paper.py` |
| 3. Partial rotation stalls / stale pending target | `live_paper_reconcile.py`, `live_paper_execution.py`, `live_paper_runner.py` | `tests/unit/experiment/test_live_paper_runner.py`, `tests/contract/api/test_live_paper.py` |
| 4. Normal paper API omits venue metadata / limits | `product_paper_inputs.py`, `live_paper_state.py`, `api/routes/live_paper.py`, `lab_cli_paper.py` | `tests/unit/execution/test_l2_book_fill.py`, `tests/unit/experiment/test_live_paper_runner.py`, `tests/contract/api/test_live_paper.py` |
| 5. Nominal fill times precede late books | `l2_book_fill.py`, `live_paper_execution.py`, `api/live_paper_schemas.py` | `tests/unit/execution/test_l2_book_fill.py`, `tests/unit/experiment/test_live_paper_runner.py`, `tests/contract/api/test_live_paper.py` |
| 6. Residual stationarity assumption (`lab_copula`) | `lab_statistics.py` / `RD-1` proposal (`docs/research/2026-11-16-rd1-research-policy-proposal.md`) | Admission threshold changes deferred to `RD-1` approval |
| 7. Ratio vs residual measurements & stitched signals | `lab_strategy_registry.py`, `product_lab_advisor.py`, `lab_proof.py`, `product_lab_study.py`, `LabSignalChart.tsx` | `tests/unit/relationship/test_pair_measurements.py`, `tests/unit/relationship/test_dependence_measurements.py`, `tests/unit/test_lab_advisor.py`, `tests/contract/api/test_lab_studies.py`, `web/src/features/lab/LabAuditRepair.test.tsx` |
| 8. Cost add-back wording & S4-A/B / README drift | `lab_proof.py`, `LabVerdictSection.tsx`, `docs/research/2026-11-15-stage-s4*.md`, `README.md`, `TASKS.md` | `tests/unit/experiment/test_lab_proof.py`, `web/src/features/lab/LabAuditRepair.test.tsx` |

## Preserved Immutable Historical Artifact SHA-256 Checksums

- `b04d48b96bc48927c867836d6b957df5662569b780086710ead828bcd5fb7251` — `docs/research/2026-10-27-lab-earning-trials.json`
- `997eae34f87dd2ed7012e2e8892b209a641752036b5483497408ea9ad4712642` — `docs/research/2026-11-15-stage-s4-trial-plan.json`
- `02ff5ac52123591be864397871cea92c3c3a74551609310acdd7d8486ccbe4bb` — `docs/research/2026-11-15-stage-s4-trials.jsonl`
- `d57c5cdb9ab96a17005991c242f668086ae9b7c2017027a165c9d2b5d4a162d4` — `docs/research/2026-11-15-stage-s4b-trial-plan.json`
- `7b54ec70bf06eddcdd19f6a0012353c6cfccca30644fe29d71123d402cb918f9` — `docs/research/2026-11-15-stage-s4b-trials.jsonl`
- `8a3acdb34d544697d2bc7753eaa6f48b2c432208e918da05d13752a9793afb6f` — `docs/research/2026-11-16-audit/probe-results.json`

## Verification Gate & Test Cleanup Evidence

- **Full compiler gate (`uv run python scripts/qap_gate.py --full --fail-fast`):** `14/14` passed (`0` failed) in `178.81s` (`ruff_check`, `ruff_format`, `source_size`, `import_layers` 5/5, `pyright` 0 errors, `openapi_sync`, `web_typecheck`, `quant_invariants`, `regression_checks`, `research_protocol`, `pytest_full` `889 passed, 1 skipped` in `106.36s` with `--durations=15`, `engine_parity`, `web_vitest_full`, `web_build`).
- **Retired scanner extraction & test cleanup:** Extracted `src/qap/product_market_data_catalog.py` and `src/qap/product_market_data_protocol.py` for retained product data loading/preparation; removed retired `qap.scanner` implementation, dead scanner worker branches, and dedicated scanner tests (`test_scanner_slice1..3`, `test_scanner_adapter`, `tests/unit/scanner/*`, `test_benchmark_scanner_slice1`). Full pytest runtime dropped from `397.81s` to `112.80s` (`-71.6%`).

## Scope Disclaimer

Passing compiler gates establishes software checks only. It does not establish strategy profitability, market fit, or live-capital readiness. Research-policy decisions remain open in [RD-1 Proposal](../research/2026-11-16-rd1-research-policy-proposal.md).
