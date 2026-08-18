# QAP Scanner Slice 2 Prospective Evidence + Liquidity Implementation Plan

**Goal:** Implement the corrected Slice-2 prospective-evidence and liquidity-qualification contracts on top of the remediated Slice-1 scanner without reopening Slice-1 economics or introducing a second execution/accounting engine.

**Architecture:** Slice 2 has two implementation tracks that share immutable candidate lineage but have different clocks and evidence sources: prospective candidate/cohort evidence (`PR-*`, `EV-*`) and current public liquidity evidence (`LQ-*`). `qap.scanner` owns research identity, qualification, orchestration, and evidence references; `qap.market` owns public venue observations/capture; `qap.experiment` remains mandatory economic authority. Slice 3 remains the only combined-inventory/basket boundary.

**Tech Stack:** Existing Python 3.14/QAP stack, Pydantic, PyArrow/Parquet, Decimal arithmetic, argparse, existing public HTTP adapter facilities. No new runtime dependency, database, scheduler, queue, service, or UI.

## Global Constraints

- Authoritative semantics are `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`; this plan references its contract IDs instead of restating alternative formulas.
- Slice-1 code baseline is the remediated `8ce0c31` implementation plus its committed result/remediation records. Do not reopen Slice-1 code unless a new concrete regression is demonstrated.
- Existing dirty Slice-2 work is non-authoritative WIP. Reuse only code that conforms to the corrected design; delete or replace stale interpretations rather than preserving sunk effort.
- Use the existing worktree and one writer. No secondary coding agents or per-task worktrees.
- `qap.scanner` must not own fills, balances, HODL/control wealth, private exchange actions, or combined multi-candidate inventory allocation.
- Prospective candidate economics always route through ordinary `qap.experiment`; neither `DataRole.FORWARD_PAPER` nor reserved `FINAL_OOS` may satisfy scanner prospective evidence.
- Public capture is bounded/one-shot and owned by `qap.market`; invocation cadence remains external.
- Keep permanent runtime names domain-based (`prospective`, `forward`, `liquidity`), not delivery labels such as `slice2_*`.
- The typed prospective protocol is runtime semantic authority. Do not hash the whole Markdown design as protocol identity.
- Testing/verification below is limited to checks explicitly required by the approved design/repository gates or checks that directly disprove one protected contract.

## Current Repository Reuse

Keep and reconcile:

- `src/qap/scanner/prospective.py` — prospective domain records and semantic identity.
- `src/qap/scanner/liquidity.py` — deterministic book walking / mid-relative friction mechanics.
- `src/qap/scanner/liquidity_policy.py` — coverage, directional capacity, qualification policy.
- `src/qap/market/microstructure.py` and `microstructure_storage.py` — immutable public book evidence and storage.
- `src/qap/market/adapters/binance_public.py` — existing bounded public Binance HTTP owner.
- existing `qap.experiment` run/artifact/evaluation authority.
- existing exact-file/digest integrity primitives; extract only the smallest neutral helper needed by multiple authoritative artifact families.

Rename/reconcile before more behavior is added:

- `src/qap/scanner/slice2_contract.py` -> `src/qap/scanner/prospective_protocol.py`.
- `src/qap/scanner/slice2_artifact_schemas.py` -> `src/qap/scanner/prospective_artifact_schemas.py`.
- `src/qap/scanner/slice2_artifacts.py` -> `src/qap/scanner/prospective_artifacts.py`.
- Remove `slice2_artifact_contract.py` if its only remaining responsibility is filename constants; keep those constants beside the artifact owner.
- `tests/unit/scanner/test_slice2_artifacts.py` -> `tests/unit/scanner/test_prospective_artifacts.py`.

New files are justified only where no current owner exists:

- `src/qap/experiment/prospective_scanner_adapter.py` — mandatory ordinary-QAP prospective replay adapter.
- `src/qap/market/adapters/gate_public.py` — bounded Gate public capture equivalent required by `LQ-01`.
- `src/qap/scanner/prospective_run.py` — thin vertical orchestration over freeze/advance/qualify/outcome publication.
- `src/qap/scanner/forward_cli.py` — bounded operator commands.
- focused adapter/capture/scenario tests required by the design contracts.

## Milestone 0 — Reconcile the existing Slice-2 WIP

**Contracts:** all; no new behavior.

**Files:** current dirty prospective/artifact files plus committed Slice-2 protocol/artifact modules.

**Steps:**

- Compare the current WIP to the corrected design contract IDs.
- Keep already-correct `CandidateFreeze`, zero-member cohort, reselection, strict timing, book-walk, coverage, and capacity work.
- Remove the Markdown-design SHA from runtime semantic identity.
- Rename `slice2_*` runtime modules to domain names and update imports.
- Do not preserve compatibility aliases unless a committed external caller requires them.

**Acceptance:** repository imports resolve under the domain names; no `slice2_*` runtime module remains solely as planning terminology; the WIP diff contains only behavior required by the corrected contracts.

## Milestone 1 — Prospective protocol, freeze, cohort, and checkpoint domain

**Contracts:** `PR-01`, `PR-02`, `PR-03`.

**Files:** `prospective_protocol.py`, `prospective.py`, `test_prospective.py`.

**Interfaces:**

- `ProspectiveProtocol`: one typed/versioned canonical semantic payload for forward windows, control/cost references, coverage/capacity policy references, and qualification policy version.
- `CandidateFreeze`: immutable hypothesis including `primary_control_reference`, `cost_policy_reference`, candidate/model lineage, `forward_start`, `forward_end`, and semantic rule identity.
- `ForwardCohort`: exactly one record per completed automatic Slice-1 scan/horizon, including valid zero-new-member cohorts and separate manual membership.
- `Reselection`: links a repeated automatic/manual selection to an active identical semantic freeze instead of opening a duplicate.
- `ForwardCheckpoint`: belongs to `freeze_id`; seals `through`, first outcome completion boundary, and exact forward information-state identity.

**Steps:**

- Enforce `eligible_information_end <= frozen_at < forward_start < first_outcome_observation_complete_at` when outcome evidence is admitted.
- Freeze `short=48h`, `medium=10d`, `swing=28d` in `ProspectiveProtocol`.
- Deduplicate active freezes by semantic rule identity, never source scan ID.
- Allow a new generation only after the prior identical freeze matures.
- Preserve automatic/manual/reselection counts and lineage in cohort evidence.

**Required evidence:** focused prospective contract tests for strict timing, zero-member cohorts, active reselection, matured re-entry, and semantic-ID stability.

## Milestone 2 — Prospective publication and integrity

**Contracts:** `EV-01`.

**Files:** `prospective_artifact_schemas.py`, `prospective_artifacts.py`, the neutral shared integrity primitive if extraction is necessary, `test_prospective_artifacts.py`.

**Steps:**

- Persist the full immutable `CandidateFreeze` contract; do not reduce it to a candidate attachment tuple.
- Keep `cohort.json` / freezes immutable and checkpoints/outcomes logically append-only.
- Completed checkpoint generations validate exact required/allowed file names, digests, counts, directory identity, cohort/freeze/checkpoint lineage before publication and whenever read/reindexed.
- Enforce monotonic checkpoint sequence per freeze; reject retroactive insertion/backfill after a later checkpoint is completed.
- Recover derived top-level indexes only from already-validated completed checkpoint generations.
- `.partial` remains recovery state and never counts as evidence.

**Required evidence:** adversarial tamper/read/reindex check, retroactive-backfill rejection, interruption-before-index-refresh recovery, immutable prior-checkpoint check.

## Milestone 3 — Mandatory prospective QAP economics

**Contracts:** `PR-04`, part of `EV-02`.

**Files:** `src/qap/experiment/prospective_scanner_adapter.py`, `src/qap/scanner_entry.py`, focused experiment tests.

**Steps:**

- Convert one frozen candidate/checkpoint into an ordinary QAP `DataRole.DEVELOPMENT` experiment without rerunning discovery/ranking on forward outcomes.
- Use the exact model/template/orientation, `primary_control_reference`, and `cost_policy_reference` frozen in `CandidateFreeze`.
- Reject `FORWARD_PAPER`, `FINAL_OOS`, pre-forward outcome rows, and any changed freeze/protocol identity before replay.
- Preserve existing next-observation execution semantics and matched starting quantities.
- Scanner artifacts retain run/result references and status only; QAP artifacts remain financial authority.
- Persist one `ForwardOutcome` reference/status (`pending | partial | matured | invalid`) per freeze generation; candidate-specific setup/replay failure remains visible and never deletes cohort membership.

**Required evidence:** one real adapter scenario proving strict post-freeze replay, frozen control/cost use, both economic gates, and role rejection.

## Milestone 4 — Bounded public capture and coverage

**Contracts:** `LQ-01`, `LQ-02`.

**Files:** extend `binance_public.py`; create `gate_public.py`; reuse `microstructure.py` / storage; add focused public-adapter/capture tests.

**Steps:**

- Add bounded one-shot Binance/Gate reads for L1/book ticker, shallow depth, and current instrument state/order constraints needed by QAP execution rules.
- Normalize all responses into the existing immutable `qap.market` microstructure/instrument metadata contracts before scanner use.
- No credentials, account endpoints, private order endpoints, persistent polling, or internal scheduler.
- Coverage is computed from actual captured timestamps against the design cadence: L1 60s, depth 5m, >=14 calendar days, >=95% overall and >=90% each UTC day. Missing scheduled observations remain missing; no interpolation.

**Required evidence:** payload normalization checks for both venues and coverage fail-closed examples. Do not require live-network tests; the operator capture command itself is the bounded integration surface.

## Milestone 5 — Directional liquidity capacity and qualification

**Contracts:** `LQ-03`, `LQ-04`, `LQ-05`, `LQ-06`.

**Files:** `liquidity.py`, `liquidity_policy.py`, their existing tests.

**Steps:**

- Preserve exact mid-relative book cost with adverse fee counted once.
- Keep buy/sell evidence separate through nearest-rank `C95_buy` / `C95_sell`, Decimal bisection `q_star_buy` / `q_star_sell`, and the frozen `0.5` haircuts `q_safe_buy` / `q_safe_sell`.
- Required unfillable observations remain denominator failures; never compute a favorable percentile from only fillable rows.
- Compute direction-specific required rebalance fractions from authoritative current prospective weight with the structural `0.20` floor and observed drift; candidate ceiling is the conservative minimum of buy/sell ceilings.
- Replace any design-document SHA dependency with typed protocol identity.
- Classification consumes an explicit immutable `requested_capital` request plus capture, instrument constraints, directional capacity, and ordinary-QAP empirical/adverse economic result references.
- Implement the design state machine literally: insufficient execution evidence -> `research_only`; `small_capacity` only when the evidence contract is satisfied, ceiling is usable, requested capital exceeds it, and economics survive at an allowed lower capital; `tradable_now` requires every §15.1 gate.

**Required evidence:** asymmetric buy/sell capacity example, 80/20 drift example, unfillable denominator example, explicit requested-capital state table, empirical/adverse-QAP gate references.

## Milestone 6 — Vertical orchestration, operator surface, and scoreboards

**Contracts:** `PR-02`, `PR-03`, `PR-04`, `EV-02`, `LQ-01`, `LQ-06`.

**Files:** `prospective_run.py`, `forward_cli.py`, `scanner_entry.py`, scenario tests, Slice-2 results record.

**Operator commands:**

```text
freeze automatic survivors from one completed Slice-1 scan/horizon
advance one cohort --through <UTC>
show candidate/cohort prospective evidence
capture one Binance/Gate L1 snapshot
capture one Binance/Gate shallow-depth snapshot
qualify one freeze/candidate --as-of <UTC> --requested-capital <decimal>
```

**Steps:**

- `freeze` automatically enrolls every automatic Slice-1 survivor or records a reselection link; it never asks the operator to cherry-pick an automatic winner.
- `advance` admits exact forward data, persists checkpoint intent, invokes mandatory QAP replay, records partial/matured/invalid outcome status, then atomically publishes.
- Capture commands perform one bounded public request and persist admitted evidence; external scheduling remains outside QAP.
- Qualification consumes only admitted current evidence and explicit capital; it has no order authority.
- Scoreboards report candidate count, matured/partial/invalid counts, pass fraction/distributions versus HODL/control, horizon/model/family, and automatic/manual/reselection attribution. Never sum overlapping pair wealth into scanner portfolio return.

**Required evidence:** one no-network vertical scenario from completed Slice-1 survivor -> freeze -> future checkpoint -> QAP outcome -> liquidity qualification -> scoreboard, plus negative paths for zero cohort, prospective failure, insufficient coverage, and unfillable capacity.

## Milestone 7 — Completion gate and handoff

Run only the repository/design-required completion checks after the vertical path is complete:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
uv run lint-imports
git diff --check
```

Additional completion requirements:

- exact-file integrity/readback and monotonic checkpoint order are green;
- no scanner-core dependency on experiment/execution/policy/evaluation;
- no `FORWARD_PAPER`, `FINAL_OOS`, private exchange action, scheduler/database/UI, or combined candidate inventory allocation path exists;
- current Slice-2 runtime files use domain names, not `slice2_*` delivery names;
- `docs/research/2026-08-18-qap-scanner-slice2-results.md` records the exact source commit, evidence produced, negative outcomes, limitations, and explicit Slice-3 deferral;
- update the Phase-15 umbrella status only after this exact source state is green.

Do not begin Slice 3 without its separately approved design/plan.
