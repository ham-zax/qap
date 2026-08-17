# Pre-Rearchitecture Baseline Hardening Implementation Plan

**Goal:** Close the mechanically reproducible integrity, safety, auditability, and status defects identified by the 2026-08-18 pre-rearchitecture audit, then reconcile the audit's scanner assumptions with the subsequently user-approved Scanner-V1 Slice-1/Slice-2 boundary without silently changing research semantics.

**Architecture:** Preserve QAP's existing ownership boundaries: market data remains role-neutral storage, experiment preparation owns research-role admission, policy/execution/accounting remain authoritative, and the browser only projects persisted evidence. Add trusted research-data seals and explicit content-integrity/read-time reconciliation at artifact boundaries; harden value objects and paper-operation reads; integrate the already-completed Phase-13 harness onto current main; remove UI/documentation assumptions that contradict current product reality. Do not add compatibility shims for obsolete artifacts: current-schema artifacts must be regenerated when integrity contracts change.

**Tech Stack:** Python 3.14, pytest, Pydantic/FastAPI/OpenAPI, PyArrow, React 19, TypeScript, Vite, Vitest, Playwright, Agent Browser.

## Global Constraints

- Current `main`/HEAD is authoritative; preserve unrelated work.
- Direct implementation only; no Codex or external coding/review agents.
- No backward compatibility, migration layer, fallback schema, or legacy artifact acceptance.
- No live/private exchange API, credentials, order placement, leverage, borrowing, derivatives, or live-capital authority.
- Do not consume the reserved 2024 final-OOS evidence while testing the seal; tests may inspect file metadata but must not deserialize its price/bar contents.
- Add regression tests only for serious repeatable defects/invariants.
- Phase-15 Scanner V1 Slices 1 and 2 are now user-approved for implementation. Historical research economics and prospective/current execution-capacity qualification remain separate evidence layers; no historical venue precision/notional-reference truth may be synthesized. The scanner-attempt ledger remains a mandatory Slice-1 contract.

**Execution status — 2026-08-18:** Tasks 1–9 are implemented and freshly re-verified in `docs/reviews/2026-08-18-pre-rearchitecture-hardening.md`. Their original procedural checkboxes are retained as plan-history rather than rewritten to imply a new RED/GREEN run. Task 10 records the later scanner-architecture reconciliation explicitly.

### Task 1: Mechanically seal reserved final-OOS datasets

**Files:**
- Create: `src/qap/experiment/dataset_seals.py`
- Modify: `src/qap/experiment/data.py`
- Modify: `tests/scenarios/test_market_dataset_roundtrip.py`
- Test: `tests/unit/experiment/test_data.py` or nearest existing experiment-data test module

**Interfaces:**
- Consumes: manifest `data_role`, declared data window, ordered expected semantic fingerprints.
- Produces: trusted in-code seal lookup keyed by semantic fingerprint + exact window; development/exploratory/forward-paper preparation rejects a reserved final-OOS seal.

**Steps:**
- [ ] Add a RED test proving a development manifest pointing at the reserved 2024 fingerprint/window fails before experiment data are returned.
- [ ] Implement a frozen trusted seal registry for the reserved BTCUSDT 2024 fingerprint/window and enforce it in experiment data admission.
- [ ] Permit the exact reserved dataset only when manifest role is `final_oos`.
- [ ] Change the ordinary storage-role test to inspect Parquet metadata only; do not call the bar-series reader/fingerprint over the reserved file.
- [ ] Run focused experiment-data/storage tests.

**Acceptance criteria:**
- The audit's `RESERVED_HOLDOUT_AS_DEVELOPMENT_ACCEPTED` probe fails closed.
- Storage remains `role_neutral_market_data`.
- No ordinary test deserializes the reserved 2024 bars.

### Task 2: Seal and semantically reconcile completed experiment artifacts

**Files:**
- Create: `src/qap/experiment/integrity.py`
- Modify: `src/qap/experiment/artifacts.py`
- Test: `tests/unit/experiment/test_artifacts.py`

**Interfaces:**
- Consumes: completed manifest/provenance/result/performance/inventory/events, optional evidence and commitment.
- Produces: mandatory `integrity.json` with exact SHA-256 digests plus read-time terminal semantic reconciliation.

**Steps:**
- [ ] Add RED regressions for tampered `result.json` and tampered terminal performance Parquet content.
- [ ] Write the integrity record only after every authoritative completed artifact (and final-OOS consumed commitment) is finalized.
- [ ] On read, require the current integrity record and verify exact declared file set/digests before parsing.
- [ ] Reconcile result role terminal values/unitized NAV, HODL/primary-control/matched-contribution terminal deltas, terminal timestamps, and terminal inventory quantities against persisted tables.
- [ ] Keep event initial-state validation and final-OOS commitment validation as independent checks.
- [ ] Run focused artifact tests and API corruption tests.

**Acceptance criteria:**
- Both experiment tamper probes fail with `ArtifactError` / API `corrupt_artifact`.
- Current-format generated runs remain readable.
- Obsolete runs without integrity records are intentionally invalid.

### Task 3: Make paper-operation artifacts self-auditing and root-contained

**Files:**
- Modify: `src/qap/experiment/paper_operation.py`
- Modify: `src/qap/api/paper_operation_views.py`
- Modify: `src/qap/api/paper_operation_schemas.py`
- Modify: `tests/scenarios/test_paper_operator_workflow.py`
- Modify: `tests/contract/api/test_paper_operations.py`
- Modify: `web/src/features/paper/PaperOperationDetail.tsx`
- Modify: `web/src/features/paper/PaperOperationList.tsx`
- Modify generated OpenAPI/TypeScript artifacts

**Interfaces:**
- Consumes: persisted paper JSON, sibling integrity record, fills/balance deltas, valuation prices, market metadata/reference inputs.
- Produces: read-time validated operation; strict operation ID containment; explicit fee/slippage/code/notional-reference provenance in API/UI; corrupt list entries do not poison the collection.

**Steps:**
- [ ] Add RED tests for `detail("..")`, reconciliation-total tampering, missing/changed integrity, and one corrupt list member.
- [ ] Persist `fee_bps`, `slippage_bps`, `code_fingerprint`, and integrity digest alongside the existing notional-filter reference map.
- [ ] Recompute fill gross/fee/slippage arithmetic, balance deltas, ending holdings, top-level totals, and terminal valuation from persisted raw fills/inputs on every read; reject disagreement with stored reconciliation.
- [ ] Use the writer's strict operation-ID regex plus resolved-path containment in the reader.
- [ ] Project `market_notional_reference_prices`, cost model, and code fingerprint through DTO/OpenAPI/UI technical details.
- [ ] Make list summaries explicit `valid`/`invalid` entries with stable corruption error context instead of failing the entire list.
- [ ] Regenerate OpenAPI/TypeScript and run focused backend/frontend tests.

**Acceptance criteria:**
- The paper tamper and path-escape probes fail closed.
- An auditor can see cost bps, code fingerprint, and notional-filter reference prices without opening raw JSON.
- One corrupt operation does not hide valid operations.

### Task 4: Enforce relationship evidence value-object invariants

**Files:**
- Modify: `src/qap/relationship/observation.py`
- Modify: `src/qap/relationship/models/cross_sectional_relative.py`
- Test: existing relationship model/unit tests (add focused invariant cases)

**Interfaces:**
- Consumes/produces: existing immutable observation classes; no public model semantics change.

**Steps:**
- [ ] Add RED tests for non-integer counts, valid-with-insufficient-coverage, invalid status/value contradictions, naive timestamps, empty model IDs, duplicate assets, invalid coverage/window, non-finite returns/scores, and invalid fingerprints.
- [ ] Make both constructors exhaustively validate type/range/status/value/fingerprint invariants and freeze normalized mappings/tuples.
- [ ] Preserve the actual model factories' currently valid outputs.
- [ ] Run relationship/model tests.

**Acceptance criteria:**
- The audit's forged observations are rejected at construction.
- Existing model-generated observations remain unchanged in meaning.

### Task 5: Make final-OOS reservation crash state recoverable

**Files:**
- Modify: `src/qap/experiment/artifacts.py`
- Test: `tests/unit/experiment/test_artifacts.py`
- Document operator recovery only if a concrete recovery command/API is added.

**Interfaces:**
- Consumes: deterministic run ID, run directory prelude, holdout registry commitment.
- Produces: no registry reservation can exist without a matching durable run prelude/commitment that identifies recovery state.

**Steps:**
- [ ] Add a RED fault-injection test at the registry/run-publication boundary.
- [ ] Reorder publication so the deterministic run directory/prelude/initial commitment exists before the atomic family/holdout registry reservation.
- [ ] If registry reservation fails, record the non-consumed attempt failure without marking the holdout consumed.
- [ ] Ensure a crash after registry reservation leaves enough deterministic state for an operator to identify the exact committed run rather than an orphan registry-only record.
- [ ] Preserve fail-closed holdout semantics and concurrency tests.

**Acceptance criteria:**
- No testable failure interval produces a registry-only orphan with no run-side identity.
- Concurrent reservation still permits at most one committed final-OOS execution.

### Task 6: Stop deriving Pair Workbench identity from basket ordering

**Files:**
- Modify: `src/qap/api/schemas.py`
- Modify: `src/qap/api/readers.py` and/or relationship/evidence projection helper
- Modify: `tests/contract/api/test_experiments.py`
- Modify: `web/src/features/experiments/ExperimentDetail.tsx`
- Modify: `web/src/features/portfolio/PortfolioOverview.tsx`
- Modify serious relevant frontend tests
- Regenerate OpenAPI/TypeScript

**Interfaces:**
- Produces: backend-owned `available_pairs` metadata for a run, derived from persisted model evidence when present; a fallback pair exists only when the run genuinely has one unambiguous two-asset pair.

**Steps:**
- [ ] Add a RED multi-asset/evidence contract test proving UI pair identity is not `basket[0:2]`.
- [ ] Derive canonical available pairs from persisted evidence; for model-free two-asset runs expose the single unambiguous pair; for ambiguous multi-asset runs do not invent a preferred pair.
- [ ] Render Pair Workbench links from backend pair metadata; omit the direct link when no unique/relevant pair exists rather than guessing.
- [ ] Regenerate API types and run focused route/E2E tests.

**Acceptance criteria:**
- Multi-asset/cross-sectional basket order cannot silently choose an unrelated pair.
- Existing two-asset critical E2E flow remains green.

### Task 7: Fix remaining presentation/repository truth defects

**Files:**
- Modify: `web/src/lib/format.ts`
- Test: `web/src/lib/format.test.ts`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-08-18-review-remediation.md`

**Steps:**
- [ ] Add RED formatter regression proving tiny negative absolute percentages retain a negative sign (`>−0.01%` or equivalent nonzero-negative notation).
- [ ] Fix `formatPercent()` without changing relative-percent conventions.
- [ ] Rewrite root README to describe the implemented Python engine/API/web/paper workflow, current Phase-12 `NO-GO`, startup/use/verification commands, and Phase-15 authorization boundary.
- [ ] Correct Python 3.13 -> 3.14 in the remediation plan.
- [ ] Run focused frontend test and documentation stale-text/path checks.

**Acceptance criteria:**
- Tiny positive and tiny negative percentages cannot render identically.
- README no longer claims the repository is documentation-only or awaiting Phase 00.

### Task 8: Integrate the completed Phase-13 harness onto current main

**Files:**
- Integrate the four unique `phase13-harness` commits/new `tools/agent/` and `tests/tools/agent/` files, resolving `.gitignore` against current main.
- Update phase/status docs only if current integrated behavior differs from the Phase-13 plan.

**Steps:**
- [ ] Verify the branch's unique paths and tests against current main.
- [ ] Integrate the four commits in original order without rewriting unrelated current-main history.
- [ ] Resolve only current-main conflicts; do not import stale product files from the old branch base.
- [ ] Run the harness's 29-test suite plus Ruff/format/Pyright.

**Acceptance criteria:**
- `tools/agent/` exists on `main` and its focused verification is green.
- Plan map no longer claims an implementation absent from the product branch.

### Task 9: Record Phase-14 rendered acceptance evidence

**Files:**
- Create: `docs/reviews/2026-08-18-phase14-browser-acceptance.md`

**Steps:**
- [ ] Run current-head Agent Browser desktop 1440x1000 and mobile 390x844 across Research Runs, Experiment Detail, Portfolio, Pair Workbench, Paper Operations/list/detail, and shell error state.
- [ ] Record axe violations/incomplete, document-width overflow, key keyboard/navigation checks, and material screenshots/observations without snapshot testing.
- [ ] Fix any serious regressions found; otherwise persist exact acceptance evidence.

**Acceptance criteria:**
- Phase 14 has durable repository evidence for its required rendered acceptance matrix.

### Task 10: Reconcile scanner architecture findings with the approved Slice-1/Slice-2 evidence boundary

**Files:**
- Modify: `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`
- Modify: `docs/plans/15-research-scanner-and-candidate-workbench.md` if needed
- Modify: `implementation_prompt.md` only if authorization wording still conflicts

**Scope:**
- Historical experiment replay still does not contain contemporaneous Phase-11 venue-capacity evidence (including historical MARKET notional-reference truth), and that evidence cannot be reconstructed honestly from OHLCV/current exchange state. This is a claim-boundary issue, not a reason to fabricate a unified historical venue simulator.
- Pre-execution setup failures are not a durable Phase-07 family-attempt ledger; Phase 15's pre-enumerated `ScanAttempt` ledger is the intended solution.

**Steps:**
- [x] State explicitly that Slice 1 may establish historical research economics but cannot retroactively certify venue precision/capacity or synthesize historical MARKET notional-reference truth; Slice 2 owns forward/current execution-capacity evidence, and any approved Slice 3 must reuse Phase-11 multi-asset routing.
- [x] Require promoted scanner replay attempts to be durably enumerated before experiment preparation/data admission so setup failures remain in the denominator.
- [x] Record that Binance/Gate support is no longer an implicit default: both venues are explicitly part of the subsequently user-approved Scanner-V1 design; implementation must still fail closed until each venue's required public evidence adapter exists.
- [x] Reconcile the newer explicit Slice-1/Slice-2 authorization with the older baseline-hardening stop wording while preserving all research/economic protected boundaries.

**Acceptance criteria:**
- Slice 1 cannot turn missing historical execution/capacity evidence into a venue-feasibility claim.
- A promoted candidate that fails before experiment manifest publication still has a durable scanner replay-attempt row and remains counted.
- The plan does not pretend historical capacity is mechanically solved by the baseline-hardening commits or by current OHLCV.

## Final Verification

Run fresh, from current main after all coherent commits:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts tools
uv run lint-imports
uv run python scripts/check_source_size.py
uv lock --check
cd web
pnpm install --frozen-lockfile --offline
pnpm typecheck
pnpm typecheck:e2e
pnpm test
pnpm build
cd ..
uv run python scripts/export_openapi.py /tmp/qap-openapi.json
diff -u web/openapi.json /tmp/qap-openapi.json
uv run python scripts/run_playwright_e2e.py
```

Then run the recorded adversarial probes (reserved-holdout relabel, experiment JSON/Parquet tamper, paper reconciliation tamper, `PaperOperationReader.detail("..")`, forged observations) and confirm they fail closed. Perform a final inline self-review of the integrated diff and verify `git status --short --branch`.