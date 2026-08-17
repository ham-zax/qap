# Post-Phase-14 Review Remediation Implementation Plan

**Goal:** Close the verified integration/semantic gaps found in the `213a667..313179f` review without reopening QAP's financial/research architecture.

**Architecture:** Repair contracts at their authority boundary: Phase-11 E2E navigation in the frontend, target semantics in policy-owned `RebalancePlan`, family-attempt semantics in the API, and success-threshold semantics in presentation. Reconcile the mission map so Phase 14 and a separate Research Scanner/Candidate Workbench phase are completion scope, while preserving Phase-12 `NO-GO` and the no-live-capital boundary.

**Tech Stack:** Python 3.14, pytest, Pydantic/FastAPI/OpenAPI, React/Vite/TanStack Router, Vitest, Playwright, Tailwind CSS.

## Global Constraints

- Current HEAD is authoritative; preserve concurrent/user changes and never reset unrelated work.
- No backward-compatibility shims or migration paths for renamed/current-schema contracts.
- Do not manufacture positive research evidence or weaken success/holdout controls.
- Browser remains presentation-only; policy owns target semantics and backend owns research truth.
- Keep automated UI tests focused on serious semantic/integration regressions; use Playwright/Agent Browser for rendered UX.
- No Codex/subagents/external coding models.

### Task 1: Restore the Phase-11 critical browser contract

**Files:**
- Modify: `web/src/features/portfolio/PortfolioOverview.tsx`
- Modify: `web/e2e/portfolio-workbench.spec.ts`
- Modify: `web/e2e/pair-anchor-lens.spec.ts`
- Test: existing Playwright specs; focused frontend tests only if a serious semantic contract needs coverage.

**Interfaces:**
- Consumes: experiment manifest basket/anchor and existing pair-route URL contract.
- Produces: Experiment -> Portfolio -> Pair Workbench browser path and selectors matching the current Phase-14 UI.

**Steps:**
- [ ] Reproduce both current Playwright failures.
- [ ] Add a direct Portfolio -> Pair evidence/workbench link using the same canonical URL parameters as Experiment Detail.
- [ ] Update stale E2E selectors to current accessible names without weakening assertions.
- [ ] Remove the `page.goto(Experiment)` cheat from the portfolio E2E flow.
- [ ] Run both critical Playwright specs and frontend typecheck.

**Acceptance criteria:** both Phase-11.9 flows pass from deterministic fixture API; the portfolio flow reaches Pair Workbench through UI navigation only.

### Task 2: Make execution consume policy-authoritative rebalance semantics

**Files:**
- Modify: `src/qap/execution/multi_asset.py`
- Modify: call sites such as `src/qap/experiment/paper_operation.py` if the public execution interface changes.
- Test: `tests/scenarios/test_multi_asset_rebalance.py`
- Test: affected paper-operation/operator tests.

**Interfaces:**
- Consumes: `RebalancePlan` produced by `qap.policy.build_rebalance_plan`.
- Produces: deterministic multi-asset execution that cannot silently ignore a held asset omitted from an economic target.

**Steps:**
- [ ] Add a regression proving a held non-bridge asset omitted from target is rejected before execution.
- [ ] Verify RED against current `execute_multi_asset_rebalance`.
- [ ] Remove the duplicated target-delta authority from execution by consuming/constructing the policy `RebalancePlan` at the execution boundary.
- [ ] Preserve the execution-only bridge exception and existing deterministic route/precision semantics.
- [ ] Run focused multi-asset and paper-operation tests.

**Acceptance criteria:** omitted held non-bridge assets cannot survive silently; explicit zero remains the only liquidation declaration; existing bridge-only behavior remains valid.

### Task 3: Correct Phase-11/12 sequential status

**Files:**
- Modify: `docs/reviews/2026-08-17-live-readiness.md`
- Modify: `docs/reviews/2026-08-17-live-readiness-evidence.md`
- Modify: any durable phase/checkpoint document that claims Phase 11 was green before browser acceptance, if present.

**Interfaces:**
- Consumes: newly green Phase-11.9 browser evidence.
- Produces: an honest sequencing record: Phase 12 was an early/provisional readiness review until Phase 11 browser acceptance became green; `NO-GO` remains unchanged.

**Acceptance criteria:** docs no longer imply Phase 12 began after a fully green Phase 11; after remediation, Phase 11.9 is recorded green and the Phase-12 NO-GO remains economically unchanged.

### Task 4: Reconcile authoritative mission scope and add the scanner phase

**Files:**
- Modify: `implementation_prompt.md`
- Modify: `docs/plans/README.md`
- Modify: `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md`
- Create: `docs/plans/15-research-scanner-and-candidate-workbench.md`
- Refactor: `docs/plans/14-analytical-workbench-ux-redesign.md` and route/design companion plans under `docs/plans/14/`.

**Interfaces:**
- Produces: authoritative completion scope through Phase 15, with Phase 14 UX and Phase 15 active research scanner/candidate workflow explicitly mapped.

**Acceptance criteria:** no authoritative mission text still says completion ends at Phase 13; Phase 15 owns universe/pair/model/parameter scan -> ranking -> combination -> candidate freeze, without live-capital authority.

### Task 5: Finish success-threshold presentation semantics

**Files:**
- Modify: `web/src/components/visuals/ComparisonBars.tsx`
- Modify: `web/src/features/experiments/ExperimentDetail.tsx`
- Modify: `web/src/features/portfolio/BenchmarkLadder.tsx` if needed to pass threshold metadata to the primary bar.
- Test: existing experiment/portfolio semantic tests; add one focused regression for a positive arithmetic increment below a positive success threshold.

**Interfaces:**
- Consumes: persisted `success_threshold`, result status, and primary metric identity.
- Produces: visual treatment that distinguishes arithmetic direction from research success.

**Acceptance criteria:** a +1% primary increment with a +2% threshold is not rendered as a success-colored bar; Experiment Detail visibly states the predeclared success threshold.

### Task 6: Rename the family search denominator to what it actually counts

**Files:**
- Modify: `src/qap/api/schemas.py`
- Modify: `src/qap/api/readers.py`
- Modify: API contract tests.
- Regenerate: `web/openapi.json`, `web/src/api/schema.d.ts`
- Modify: frontend fixtures/components using the field.

**Interfaces:**
- Rename current-schema DTO field `sibling_trial_count` -> `family_attempt_count` with no compatibility alias.

**Acceptance criteria:** a single-run family reports `family_attempt_count = 1` and the UI renders `1 family attempt`, never `1 sibling trial`.

### Task 7: Perform decomposition review and split the oversized Phase-14 plan

**Files:**
- Create/modify: bounded design/route plan files under `docs/plans/14/`.
- Modify: `docs/plans/14-analytical-workbench-ux-redesign.md` to a concise phase overview/index.
- Create: `docs/reviews/2026-08-18-source-decomposition-review.md`.

**Interfaces:**
- Consumes: source-size warning output and current file ownership.
- Produces: explicit keep/split rationale for every 500+ line source/test warning and a non-God-object Phase-14 planning structure.

**Acceptance criteria:** the 1,261-line Phase-14 plan is materially decomposed; every current 500+ line warning has an ownership decision and no arbitrary source split is performed solely to silence the warning.

## Final verification

- `uv run pytest -q`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pyright src tests scripts`
- `uv run lint-imports`
- `uv run python scripts/check_source_size.py`
- `cd web && pnpm typecheck && pnpm test && pnpm build`
- E2E typecheck and `scripts/run_playwright_e2e.py`
- rendered browser smoke for Portfolio -> Pair, threshold semantics, and research-run family-attempt copy
- `git diff --check`
- inline self-review against this remediation plan
