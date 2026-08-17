# Pre-Rearchitecture Audit Final Remediation Plan

**Goal:** Close every still-valid finding from the 2026-08-18 audit before Scanner V1 implementation begins.

**Architecture:** Preserve current QAP authority boundaries. Fix the three reproduced runtime bugs at their read/scope guards, narrow Slice-1 authoritative replay to real direct venue markets rather than synthesizing bridge execution, define conservative Slice-2 capacity/friction semantics, and make final-OOS safe-stop/legacy-run status explicit. No backward-compatibility shims and no fabricated historical venue evidence.

**Tech Stack:** Python 3.14, pytest, Pydantic, PyArrow, React/TypeScript docs/contracts, Git harness.

**Execution status — 2026-08-18:** Implemented. Runtime regressions are closed in `619fc5c`; scanner/recovery/archive contracts and review evidence are reconciled in the documentation commit containing this plan. Final verification: `460 passed, 1 skipped`, Ruff/format/Pyright clean, 5/5 import contracts, source-size hard cap green with 8 reviewed warnings, lock clean, frontend 47/47, production build, byte-identical OpenAPI, and Playwright 2/2.

## Global Constraints

- Preserve long-only, spot-only, owned-inventory, self-financing semantics.
- Do not consume reserved final-OOS evidence during tests.
- Do not add compatibility fallbacks for obsolete artifacts.
- Do not synthesize historical venue precision, MARKET notional-reference prices, spread/depth, or bridge execution from OHLCV/current exchange state.
- Scanner Slice 1 may deep-replay only candidates backed by a real direct venue market under the existing historical direct-execution engine; unsupported crosses remain searched research candidates but cannot become authoritative deep-replay survivors.
- Slice 2 capacity must be conservative under 40/60↔60/40 transitions and drift.

### Task 1: Seal the physical experiment artifact set

**Files:**
- Modify: `src/qap/experiment/integrity.py`
- Test: `tests/unit/experiment/test_artifact_integrity.py`

**Steps:**
- Add a regression proving an undeclared optional `evidence.parquet` or `commitment.json` is rejected.
- Require the physical authoritative sibling file set to exactly match `integrity.json`, excluding only `integrity.json` and non-authoritative failure metadata where applicable.
- Run focused artifact tests.

### Task 2: Isolate malformed paper-operation directories

**Files:**
- Modify: `src/qap/api/paper_operation_views.py`
- Test: `tests/contract/api/test_paper_operations.py`

**Steps:**
- Add a regression for an invalid directory name containing `paper_operation.json`.
- Pre-filter invalid IDs and surface them as invalid list summaries rather than aborting the collection.
- Preserve strict detail lookup behavior.

### Task 3: Guard Git HEAD and branch movement

**Files:**
- Modify: `tools/agent/git_guard.py`
- Modify: `tools/agent/README.md`
- Test: `tests/tools/agent/test_git_guard.py`

**Steps:**
- Add regressions for unexpected HEAD and branch changes.
- Make `assert_safe_scope()` fail closed unless explicit expected head/branch transitions are supplied.
- Document the transition parameters and preserve existing dirty-path checks.

### Task 4: Narrow Scanner Slice-1 authoritative replay to real direct markets

**Files:**
- Modify: `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`
- Modify: `docs/plans/15-research-scanner-and-candidate-workbench.md`
- Modify: `README.md`

**Steps:**
- State that a promoted candidate may enter authoritative deep replay only when the venue exposes a direct spot market matching the candidate pair/orientation and the historical data contract can supply that direct instrument.
- Keep relationship/scout research for unsupported crosses, but mark authoritative replay as `setup_failed` / unsupported direct market; never synthesize a bridge market.
- Remove the remaining stale “not implementation authorization” sentence.

### Task 5: Fix Slice-2 capacity mathematics and friction authority

**Files:**
- Modify: `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`

**Steps:**
- Replace `q_safe / 0.10` with a conservative required-rebalance fraction derived from the frozen policy: at minimum the 0.20 extreme target-to-target transition, increased when current drift implies a larger reachable corrective trade.
- Define `fee_h`, `slippage_budget_h`, and `B_h = fee_h + slippage_budget_h` from the frozen scanner horizon cost policy / QAP adverse CostModel; `C95(q)` includes the same fee once and book impact consumes the slippage allowance.
- Treat every required snapshot unable to fill `q` as a hard failure for that `q`; never drop it from the `C95` denominator.
- Update tests/acceptance prose accordingly.

### Task 6: Make final-OOS crash recovery semantics explicit

**Files:**
- Modify: `docs/reviews/2026-08-18-pre-rearchitecture-hardening.md`
- Modify: `docs/reviews/2026-08-17-live-readiness.md`
- Modify: `docs/reviews/2026-08-17-live-readiness-evidence.md`

**Steps:**
- Stop describing final-OOS reservation as fully recoverable.
- Record the actual policy: pre-registry publication failure is retryable/non-consumed; post-registry crash is a fail-closed safe-stop that requires operator investigation and does not auto-abandon/reuse the holdout.

### Task 7: Resolve obsolete Phase-10 artifact status without compatibility

**Files:**
- Modify: `docs/research/2026-08-17-phase10-momentum-family-results.md`
- Modify: `docs/reviews/2026-08-17-live-readiness-evidence.md`

**Steps:**
- Treat the nine old unsealed run directories as archived historical evidence only and explicitly non-readable under the current artifact contract.
- Do not retrofit integrity files onto old artifacts or regenerate the 2023 research family unless a later research task explicitly reruns it under a new current-schema family.

### Task 8: Update review docs and run the integrated gate

**Files:**
- Modify: `docs/reviews/2026-08-18-pre-rearchitecture-hardening.md`
- Modify: `docs/reviews/2026-08-18-source-decomposition-review.md` only if line counts change materially.

**Verification:**
- Focused regressions for Tasks 1–3.
- Full backend/static gate.
- Frontend type/test/build and Playwright because scanner/readme/API docs are coupled to current product contracts.
- `git diff --check` and clean status.

**Acceptance criteria:**
- All three reproduced runtime probes fail closed.
- Scanner Slice 1 cannot authorize synthetic bridge deep replay.
- Slice-2 capacity/friction rules are conservative and fully defined.
- Final-OOS recovery language matches actual implementation.
- The nine obsolete Phase-10 runs are explicitly archived, not silently considered current artifacts.
