# Pre-Rearchitecture Baseline Hardening Review — 2026-08-18

**Verdict:** GREEN for the mechanically reproducible baseline-hardening findings. The scanner-specific architecture findings are reconciled with the subsequently user-approved Slice-1/Slice-2 evidence boundary rather than “fixed” by fabricating unavailable historical venue truth.

**Scope:** Verify the 2026-08-18 baseline-hardening plan against current repository behavior, close stale status/documentation, and state the exact remaining Phase-15 contracts before scanner implementation. This review does not authorize live trading and does not change the Phase-12 `NO-GO` decision.

## Verification summary

Fresh focused verification on current main covered the hardening areas directly:

```text
uv run pytest -q \
  tests/unit/experiment/test_runner.py \
  tests/scenarios/test_market_dataset_roundtrip.py \
  tests/unit/experiment/test_artifact_integrity.py \
  tests/unit/experiment/test_artifacts.py \
  tests/unit/experiment/test_paper_operation_integrity.py \
  tests/scenarios/test_paper_operator_workflow.py \
  tests/contract/api/test_paper_operations.py \
  tests/unit/relationship/test_observation_invariants.py \
  tests/unit/relationship/models/test_cross_sectional_relative.py \
  tests/unit/experiment/test_final_oos_reservation_recovery.py \
  tests/contract/api/test_experiments.py \
  tests/tools/agent

99 passed
```

Phase-14 acceptance and the frontend gate were also fresh in the same hardening sequence:

```text
pnpm typecheck                  PASS
pnpm typecheck:e2e              PASS
pnpm test                       PASS — 20 files / 47 tests
pnpm build                      PASS
python scripts/run_playwright_e2e.py
                                PASS — 2/2 critical flows
Agent Browser rendered matrix   PASS — desktop/mobile/reflow, axe 0/0,
                                no failed app requests/console/page errors
```

Rendered evidence is recorded in `docs/reviews/2026-08-18-phase14-browser-acceptance.md`.

The final integrated repository gate after the documentation/spec reconciliation was:

```text
uv run pytest -q                         PASS — 460 passed, 1 skipped
uv run ruff check .                      PASS
uv run ruff format --check .             PASS — 240 files formatted
uv run pyright src tests scripts tools   PASS — 0 errors / 0 warnings
uv run lint-imports                      PASS — 5 contracts kept / 0 broken
uv run python scripts/check_source_size.py
                                             PASS — hard cap green; 8 review warnings
uv lock --check                          PASS
pnpm install --frozen-lockfile --offline PASS
pnpm typecheck                           PASS
pnpm typecheck:e2e                       PASS
pnpm test                                PASS — 20 files / 47 tests
pnpm build                               PASS
OpenAPI export diff                      PASS — byte-identical
uv run python scripts/run_playwright_e2e.py
                                             PASS — 2/2
git diff --check                         PASS
```

## Finding-by-finding status

| Finding | Current status | Evidence / correction |
|---|---|---|
| Reserved final-OOS fixture could be relabeled development | **FIXED** | Trusted dataset seal is checked before data bytes are returned; ordinary storage-role test inspects Parquet metadata without deserializing reserved bars. |
| Completed experiment artifacts could be edited without a content seal | **FIXED** | Completed runs require `integrity.json`; digest set and semantic terminal reconciliation fail closed on tampering. |
| Paper-operation artifacts were not fully self-auditing/root-contained | **FIXED** | Integrity verification, semantic recomputation, strict operation ID/path containment, cost/code/notional-reference provenance, and corrupt-list isolation are covered. |
| Relationship observations admitted contradictory/invalid value objects | **FIXED** | Constructor invariants now reject invalid counts/status/coverage/timestamps/fingerprints/non-finite values while model-produced observations remain valid. |
| Final-OOS registry reservation could become an orphaned registry-only state | **FIXED, WITH SAFE-STOP BOUNDARY** | Durable run prelude/commitment exists before registry reservation; a reservation-publication failure is retryable and non-consumed. A crash after the registry is already `committed` is intentionally fail-closed: the reservation remains blocking and QAP has no automatic resume/abandon path. Operator investigation is required; this is identifiable safe-stop behavior, not full resumability. |
| Pair Workbench identity could be guessed from `basket[0:2]` | **FIXED** | Backend projects `available_pairs` from persisted evidence or the only unambiguous two-asset case; frontend links use that metadata. |
| Tiny negative absolute percentages could lose their sign | **FIXED** | `formatPercent()` renders tiny negative nonzero values as `−<0.01%`; regression is present. |
| Root README/old remediation plan contradicted implemented reality | **FIXED** | README documents engine/API/web/paper/harness, Phase-12 `NO-GO`, startup/verification, Phase-14 acceptance, and current Phase-15 authorization; Python version is 3.14. |
| Completed Phase-13 harness was absent from main | **FIXED** | Four harness commits are integrated; focused harness suite is included in the 99-test verification. |
| Phase-14 lacked durable rendered acceptance evidence | **FIXED** | Dedicated browser acceptance review exists; two serious browser regressions were fixed and re-verified. |
| Historical replay does not contain contemporaneous Phase-11 venue-capacity truth | **RECLASSIFIED / BOUNDED** | Full retroactive venue-capacity reconstruction is not an honest Slice-1 prerequisite. Missing historical spread/depth/MARKET notional-reference observations cannot be synthesized from OHLCV/current exchange state. Slice 1 may establish historical research economics under the frozen QAP replay/cost model; Slice 2 owns prospective/current execution and capacity qualification. |
| Setup failure before experiment manifest publication could disappear from the search denominator | **SPEC CONTRACT FIXED BEFORE SCANNER CODE** | Slice-1 spec now requires deterministic `replay_attempts.parquet` rows to be durably enumerated before experiment preparation/data admission; `setup_failed` remains counted even when no experiment manifest can be produced. |
| Gate support was treated as an implicit second-venue default in the older audit | **AUTHORITY UPDATED** | The later user-approved Scanner-V1 design explicitly includes Binance and Gate. This is no longer an unapproved architecture choice, but implementation must still fail closed until the required public evidence adapter exists. |

## Historical execution claim boundary

The earlier audit treated the difference between historical replay and the Phase-11 paper executor as if Slice 1 had to reconstruct full historical venue execution before any scanner work could begin. That is too strong and would encourage false precision.

Repository/spec evidence supports a stricter and more honest split:

1. **Slice 1 — historical discovery/research economics.** QAP's deterministic historical replay remains the sole owner of strategy/control/HODL economics, but authoritative deep replay is restricted to candidates with a real direct venue market and admitted historical bars for that direct instrument. Indirect crosses may remain scout evidence but cannot be silently bridged through the single-instrument replay engine. All roles share the same timing and declared cost model. A historical survivor is searched development evidence, not proof of executable capacity.
2. **Slice 2 — prospective/current execution evidence.** Current public instrument constraints, L1/depth, reference observations, and capacity evidence are captured forward. `research_only`, `small_capacity`, and `tradable_now` require that evidence and fail closed when it is missing.
3. **Slice 3 — future basket execution.** If separately approved, basket replay must reuse the existing Phase-11 multi-asset/bridge executor; scanner code does not invent a second router/fill/accounting engine.

Therefore QAP must **not** backfill historical Binance/Gate MARKET-filter reference prices from today's venue state or pretend OHLCV proves historical depth/capacity. The correct value for unavailable contemporaneous execution evidence is `unknown`, not an approximation presented as venue truth.

## Search-denominator contract before Phase-15 code

The scanner design now requires two complementary ledgers:

- `scout_trials.parquet` contains every deterministic fixed scout trial, including invalid/negative trials and both required residual orientations;
- `replay_attempts.parquet` contains every promoted authoritative-replay attempt **before** experiment preparation begins.

A replay attempt starts as `enumerated` and may become `setup_failed`, `replay_failed`, or `completed`. Publication must reconcile promotions and replay attempts. This closes the pre-manifest disappearance hole without forcing generic Phase-07 experiment artifacts to invent a run ID before their input data/provenance can be prepared.

## Final audit closure — 2026-08-18

A later adversarial review found three additional runtime bugs plus seven scanner/recovery/archive contract issues. Their current disposition is:

| Final audit finding | Disposition |
|---|---|
| Undeclared optional `evidence.parquet` / `commitment.json` could appear after sealing | **FIXED in `619fc5c`.** Integrity validation now compares the physical authoritative sibling set with the declared integrity set before parsing; both injected optional-file regressions fail closed. |
| Invalid paper-operation directory name could poison the whole list | **FIXED in `619fc5c`.** Invalid-ID directories containing `paper_operation.json` are surfaced as invalid collection entries; strict detail lookup remains 404. |
| Phase-13 scope guard ignored HEAD/branch movement | **FIXED in `619fc5c`.** HEAD/branch must match the baseline unless the caller supplies the exact reviewed `expected_head` / `expected_branch` transition. |
| General scanner pair could be deep-replayed through semantics the historical engine does not implement | **FIXED BY NARROWING THE CONTRACT.** Slice-1 authoritative deep replay requires a real direct venue instrument plus admitted historical direct-market data. Indirect crosses remain scout evidence only; no synthetic bridge execution is allowed. |
| Scanner authorization docs disagreed | **FIXED.** README/plan/spec authority now consistently states Slices 1–2 are authorized and Slice 3 remains a separate gate. |
| `q_safe / 0.10` could overstate safe capital | **FIXED IN SPEC.** Capacity uses `r_required = max(r_structural, r_current)`, with `r_structural=0.20` for 40/60↔60/40 and current drift allowed to increase the requirement. |
| `B_h` had no authority / fee-depth relationship | **FIXED IN SPEC.** `B_h` derives only from the frozen adverse QAP `CostModel`: fee is counted once and book impact consumes the adverse slippage allowance. Missing adverse cost policy => `research_only`. |
| Unfillable shallow-book snapshots could be omitted from `C95(q)` | **FIXED IN SPEC.** Any required snapshot that cannot fill `q` makes that size infeasible; it cannot disappear from the percentile denominator. |
| Final-OOS was described too broadly as recoverable | **CORRECTED TO SAFE-STOP.** Pre-registry publication failure is retryable/non-consumed. A crash after a `committed` registry reservation remains blocking and requires operator investigation; there is no automatic resume/abandon path. |
| Nine Phase-10 run directories predate mandatory integrity | **RESOLVED AS ARCHIVE, NO COMPATIBILITY.** They remain historical report evidence only and are intentionally unreadable by the current artifact reader. They will not receive retrofitted seals; a future rerun must create a new current-schema family. |

Final adversarial rechecks after `619fc5c`:

```text
undeclared optional experiment artifacts -> 2 regressions passed
malformed paper-operation directory       -> 1 regression passed
unexpected Git HEAD/branch movement       -> 2 regressions passed
```

The final integrated gate for this remediation is the `460 passed, 1 skipped` / `47 frontend tests` / `2/2 Playwright` gate recorded above.

## Phase-12 impact

None of these hardening fixes creates a live-readiness `GO`:

- the designated Phase-10 development family still had zero HODL-surviving candidates;
- the reserved final-OOS window remains intentionally unconsumed for that family;
- no genuinely prospective post-freeze candidate evidence exists;
- no private venue/order lifecycle or user capital-risk authority exists.

Scanner Slices 1 and 2 are research-product implementation authority only. They do not grant private API access, live order placement, authenticated venue state, or capital deployment.

## Conclusion

The reproducible baseline defects are closed after the final remediation recorded below. Phase 15 can proceed under the user-approved slice architecture once its detailed implementation plan is written, but it must preserve the clarified contracts above: historical research economics cannot be upgraded into a retroactive venue-capacity claim, every promoted replay attempt must exist durably before setup can fail, and Slice-1 authoritative deep replay is restricted to real direct venue markets with admitted historical direct-market data.
