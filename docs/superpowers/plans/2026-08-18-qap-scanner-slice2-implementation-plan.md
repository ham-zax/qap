# QAP Scanner Slice 2 Prospective Evidence + Liquidity Implementation Plan

> **Execution contract:** implement sequentially in the existing `qap-implementation-20260818` worktree. Do not dispatch external coding/review agents. Slice 2 is already implementation-authorized; Slice 3 remains a separate design/user gate.

**Goal:** Add the approved Scanner-V1 Slice-2 prospective-evidence and liquidity-qualification layer so a frozen Slice-1 survivor can accumulate forward-only checkpoint evidence and candidate-local public microstructure/capacity evidence without changing Slice-1 identity, inventing historical venue feasibility, creating a second execution/accounting engine, or allocating combined portfolio capital.

**Architecture:** Slice 2 attaches immutable evidence to an existing Slice-1 candidate/run lineage. `qap.scanner` owns prospective freeze/checkpoint identity, public microstructure evidence normalization, deterministic liquidity calculations, qualification state, and evidence artifacts only. Any prospective economic replay that needs QAP financial truth crosses through an outer composition adapter and ordinary `qap.experiment`; scanner artifacts retain references/statuses rather than copying balances/fills/terminal wealth. Public order-book evidence lives in `qap.market`. Slice 2 never routes private orders, never mutates `PortfolioState`, and never resolves competing candidates into one combined inventory allocation.

## Frozen boundaries

- Slice-1 `scan_id`, `candidate_id`, direct-market lineage, model/template/orientation identity, and deep-replay run identity are immutable inputs. Slice 2 attaches new evidence; it does not rewrite Slice-1 artifacts or identity.
- Prospective evidence is forward-only: a cohort/freeze timestamp is established before observations used for prospective scoring. Rows observed before or at freeze may be context only; they cannot be relabeled as prospective after results are known.
- A prospective checkpoint is identified from frozen cohort/candidate identity, checkpoint schedule/index, information cutoff, exact admitted forward slice identities, and the Slice-2 protocol version. Creation timestamp and filesystem location are non-semantic.
- Prospective evidence is not `final_oos`. Scanner code must continue to treat protected `final_oos` experiment roles as unavailable for automatic search/qualification.
- Public market/microstructure inputs are evidence only. No authenticated/private exchange action, order placement, balance query, API key, or live-capital authority is added.
- Slice 2 may report candidate-local evidence/capacity. It must not allocate one owned inventory across several survivors; that one-inventory resolver remains a Slice-3 design concern.
- Historical/current capacity is not backfilled. Liquidity/capacity claims are valid only for the prospective/current microstructure cohort actually captured under the declared evidence protocol.
- Liquidity friction authority is the frozen **adverse** QAP cost model bound by Slice 1. Scanner does not create a second fee/slippage budget. Fees are counted exactly once.
- A required shallow-book snapshot that cannot fill tested quote notional `q` makes that observation/test size infeasible. It must not be dropped from the `C95(q)` denominator.
- Capacity must use the approved conservative policy transition/drift requirement. Do **not** infer portfolio capacity as `q_safe / 0.10`; maximum tilt is not the same thing as maximum required one-way transition after state changes and NO_ACTION drift.
- Qualification labels remain the approved bounded states: `research_only`, `small_capacity`, and `tradable_now`. No learned reliability score, optimizer, or discretionary ranking layer is introduced.
- Scanner/prospective artifacts may reference authoritative QAP run IDs/statuses and candidate-local liquidity numbers, but may not copy `PortfolioState`, fills, terminal strategy/HODL/control wealth, or user account balances.
- Same worktree/branch. No scanner UI, scheduler, database, queue, private exchange integration, or Slice-3 basket allocator.

## File map

### Public market evidence

- Create `src/qap/market/microstructure.py` — immutable public top-of-book and bounded shallow-depth snapshot contracts; exact venue/instrument/source/observed-at provenance; bid/ask level validation; deterministic fingerprint.
- Create `src/qap/market/microstructure_storage.py` — explicit current-schema Parquet read/write for prospective public microstructure snapshots; no network client and no live polling loop.
- Modify `src/qap/market/__init__.py` — export only stable snapshot/storage types.
- Create `tests/unit/market/test_microstructure.py` — validation, causality, level ordering, fillability, fingerprint and storage round-trip tests.

### Slice-2 protocol / freeze identity

- Create `src/qap/scanner/prospective.py` — Slice-2 protocol/version references, frozen cohort and candidate attachment identity, checkpoint schedule/index, forward-slice identity, current-schema qualification enums and immutable records.
- Create `tests/unit/scanner/test_prospective.py` — candidate identity preservation, freeze/checkpoint causality, append-only schedule semantics, semantic hash stability, final-OOS rejection.

### Liquidity / capacity evidence

- Create `src/qap/scanner/liquidity.py` — deterministic book-walk, one-way friction calculation, `C95(q)` aggregation, fail-closed unfillable observation handling, `q_safe`, conservative policy transition/drift capacity conversion, and bounded qualification state.
- Create `tests/unit/scanner/test_liquidity.py` — hand-computed book walks, fee counted once, unfillable snapshots remain infeasible, monotone tested-size feasibility, adverse-cost authority, no `q_safe/0.10` shortcut, qualification transitions.

### Prospective / liquidity evidence artifacts

- Create `src/qap/scanner/slice2_artifact_schemas.py` — explicit PyArrow schemas for frozen cohort, checkpoint observations, liquidity snapshots/aggregates, capacity qualifications, and authoritative prospective-run references.
- Create `src/qap/scanner/slice2_artifacts.py` — immutable cohort publication, append-only checkpoint staging, deterministic table hashes/counts, resume validation, checkpoint reconciliation, atomic publication.
- Create `tests/unit/scanner/test_slice2_artifacts.py` — freeze immutability, append-only checkpoints, interrupted write/resume, identity mismatch rejection, unfillable evidence persistence, run-reference reconciliation.

### Outer economic adapter

- Create `src/qap/experiment/prospective_scanner_adapter.py` only if the approved prospective checkpoint needs authoritative QAP economic replay. It must consume one frozen prospective checkpoint request and execute through ordinary experiment artifacts with a forward-only development/prospective evidence boundary; it must not make scanner the economic authority.
- Modify `src/qap/scanner_entry.py` — compose the Slice-2 scanner service with the experiment adapter if authoritative replay is required, preserving scanner-core dependency inversion.
- Create `tests/unit/experiment/test_prospective_scanner_adapter.py` — freeze cutoff, no pre-freeze outcome leakage, no final-OOS access, ordinary QAP artifact reference only.

### Sequential operator surface

- Create `src/qap/scanner/slice2_run.py` — deterministic attach/freeze/checkpoint/liquidity qualification orchestration over existing Slice-1 completed scan evidence.
- Create `src/qap/scanner/slice2_cli.py` — bounded argparse operator surface for explicit freeze/checkpoint processing from local admitted data/evidence; no scheduler/daemon.
- Create `tests/unit/scanner/test_slice2_cli.py`.
- Create `tests/scenarios/test_scanner_slice2.py` — end-to-end frozen survivor -> forward checkpoint -> public book evidence -> qualification, including negative/infeasible cases.

### Architecture/results

- Extend `.importlinter` and `tests/unit/scanner/test_architecture.py` only as needed so new Slice-2 scanner modules remain unable to import policy/execution/evaluation/experiment; any experiment composition remains in outer adapter/root.
- Create `scripts/benchmark_scanner_slice2.py` only if the approved design has a meaningful local workload requiring measured performance evidence; otherwise use bounded unit/scenario evidence and do not invent a performance framework.
- Update `docs/plans/15-research-scanner-and-candidate-workbench.md` with verified Slice-2 status after implementation.
- Create `docs/research/2026-08-18-qap-scanner-slice2-results.md` with exact prospective/liquidity evidence scope, commands/results, negative outcomes, limitations, and explicit Slice-3 deferral.

## Task 1 — Freeze the Slice-2 protocol and prospective attachment identity

**Behavior:**

- Define one current-schema Slice-2 protocol/version whose semantic payload binds the approved cohort/checkpoint policy, microstructure evidence requirements, tested-size policy, adverse-cost reference, capacity transition/drift rule, and qualification semantics.
- Define immutable `ProspectiveCohort` with cohort ID, freeze timestamp, originating Slice-1 scan ID, ordered attached candidate IDs, originating deep-replay run references/statuses, and protocol identity.
- A cohort may attach only to completed Slice-1 survivors/eligible candidate lineage admitted by the approved design. Attachment never changes the original candidate ID.
- Define deterministic checkpoint identity from cohort/candidate, checkpoint index/schedule, information cutoff, exact forward-data identities and protocol identity. `created_at` is excluded from semantic identity.
- Reject any checkpoint whose admitted outcome/economic observation precedes or is available at the freeze boundary in a way that would create hindsight labeling.
- Reject `final_oos` as an automatic Slice-2 scanner input/role.

**Verification:** `uv run pytest -q tests/unit/scanner/test_prospective.py` plus Ruff/Pyright on the new module.

## Task 2 — Add immutable public microstructure evidence contracts

**Behavior:**

- Model public top-of-book/shallow-depth evidence as one immutable timestamped venue/instrument snapshot with explicit source ID/fingerprint and observation-complete timestamp.
- Bids must be strictly descending positive prices; asks strictly ascending positive prices; quantities positive finite; best bid < best ask; no duplicate/zero/negative/non-finite levels.
- The evidence object exposes no authenticated client, order API, balances, or mutable venue state.
- Fingerprint all economically used fields with canonical exact numeric serialization; append/future observations cannot mutate an older snapshot fingerprint.
- Persist/read current-schema Parquet with safe paths and exact schema validation.

**Verification:** focused unit/storage round-trip tests; no network tests.

## Task 3 — Implement deterministic one-way book walk and friction evidence

**Behavior:**

For each tested quote notional `q` and required snapshot/side:

- walk only the recorded shallow depth in price priority;
- return exact acquired/sold base quantity, VWAP, best-reference price, quote notional consumed, and book-impact/slippage evidence;
- if recorded depth cannot fill the entire requested `q`, mark the observation `unfillable`/infeasible; never extrapolate hidden depth;
- calculate candidate liquidity friction against the approved direct execution instrument/economic direction only; do not synthesize USDT bridge execution;
- combine book-derived friction with the Slice-1 adverse QAP `CostModel` exactly as approved, counting the fee once and never adding a scanner-local fee budget.

**Verification:** hand-calculated bid/ask examples, partial final level, unfillable examples, fee-once regression.

## Task 4 — Compute `C95(q)` and safe tested size fail-closed

**Behavior:**

- A checkpoint/cohort liquidity test uses the frozen required snapshot set. The denominator is fixed before looking at which sizes fill.
- For tested notional `q`, every required snapshot contributes either finite friction evidence or explicit infeasible/unfillable evidence.
- Any required unfillable snapshot makes that `q` infeasible for the checkpoint rather than disappearing from the percentile calculation.
- For fully fillable `q`, compute deterministic `C95(q)` using the approved percentile/interpolation convention and compare it only with the frozen adverse-cost authority from Slice 1.
- Determine `q_safe` from the frozen tested-size grid/rule. Never interpolate/extrapolate beyond tested evidence unless the approved design explicitly defines such interpolation; otherwise choose the largest tested feasible size.
- Preserve complete per-size evidence so a later reader can reconstruct why a larger size failed.

**Verification:** percentile examples, denominator preservation, monotonic feasibility tests, all-unfillable and boundary cases.

## Task 5 — Convert `q_safe` to conservative candidate-local capacity

**Behavior:**

- Implement the approved policy transition/drift demand rule from the actual fixed EvidenceTilt state semantics and prospective drift evidence; do not use maximum tilt (`0.10`) as the trade-fraction divisor.
- Capacity conversion must be conservative under direct transitions among neutral/tilted states and NO_ACTION drift. If the required one-way transition fraction cannot be established from the approved evidence, capacity fails closed to `research_only` rather than substituting a favorable number.
- Keep candidate-local quote-capacity evidence separate from portfolio allocation. No cross-candidate allocator or combined balance resolver.
- Store the exact transition/drift evidence and formula inputs used so qualification is auditable.

**Verification:** regression explicitly showing a case where `q_safe/0.10` would overstate capacity; transition/drift boundary tests; missing-evidence fail-closed test.

## Task 6 — Implement bounded qualification states

**Behavior:**

- `research_only`: prospective or liquidity evidence is incomplete/insufficient, required size is infeasible, or conservative capacity cannot be established.
- `small_capacity`: approved evidence establishes positive bounded capacity but does not satisfy the stricter current/actionable evidence required for `tradable_now`.
- `tradable_now`: all approved prospective/current microstructure freshness/completeness and capacity conditions are satisfied at the declared candidate-local test size/current checkpoint.
- Qualification is evidence/status, not an instruction to trade. It cannot mutate balances or submit an order.
- Preserve failure/reason codes rather than collapsing negative evidence into missing rows.

**Verification:** table-driven state/reason tests and stale/missing/current boundary cases.

## Task 7 — Persist immutable cohort/checkpoint/liquidity evidence

**Behavior:**

- Publish a cohort definition immutably before any prospective outcome is admitted.
- Checkpoint staging persists definition/evidence rows before economic/liquidity evaluation can fail.
- Use explicit PyArrow schemas and deterministic hashes/counts for candidate checkpoint rows, microstructure evidence references, tested-size liquidity rows, capacity/qualification rows, and any authoritative QAP run references.
- Resume only when cohort/protocol/frozen source identities match exactly; otherwise fail closed.
- A completed checkpoint generation is immutable and atomically published; `.partial` is recovery state only.
- Forward checkpoints append by new checkpoint identity; they never rewrite prior completed checkpoint evidence.

**Verification:** interrupted staging, duplicate/collision, resume mismatch, append-only checkpoint ordering, table/manifest reconciliation tests.

## Task 8 — Add prospective economic checkpoint adapter only through ordinary QAP authority

If the approved design requires QAP economic replay at forward checkpoints:

- construct one forward-only manifest/data request from the frozen candidate/cohort without rerunning discovery/ranking on checkpoint outcome data;
- preserve the candidate model/template/orientation and frozen costs/control from Slice 1;
- make forward evaluation start strictly after the cohort freeze and use only data causally available by checkpoint cutoff;
- execute through `run_experiment_to_artifacts` and retain only run ID/status/economic-gate reference in scanner artifacts;
- never consume reserved `final_oos` automatically;
- candidate-specific replay/setup failure is recorded and does not delete the cohort/checkpoint denominator.

If the design records forward returns/score evidence without authoritative QAP replay, do not add the adapter merely because the file map permits it. The approved evidence contract decides; YAGNI applies.

## Task 9 — Sequential Slice-2 attach/freeze/checkpoint orchestrator

**Behavior:**

- Input is one completed Slice-1 scan generation plus explicit candidate/cohort selection allowed by the approved design; never rescan/reselect historical outcomes during a checkpoint.
- Freeze cohort identity first.
- At checkpoint processing: admit exact forward data/evidence through cutoff -> persist checkpoint attempt/definition -> evaluate prospective evidence -> evaluate liquidity sizes -> derive capacity/qualification -> write authoritative run references if applicable -> reconcile -> atomically publish.
- Candidate-specific missing book/source/replay evidence produces explicit negative/incomplete qualification and continues unrelated candidates.
- Generation-level frozen identity/hash/cutoff collisions abort the checkpoint.

## Task 10 — Bounded CLI/operator surface

- Use explicit local file roots and UTC timestamps only.
- Expose separate freeze/checkpoint actions or subcommands only if required by the approved design; no daemon/scheduler/poll loop.
- Print bounded counts/statuses/IDs/paths. Do not print `tradable_now` as an order recommendation or claim confirmed alpha.
- No API/web route in Slice 2 unless the approved design explicitly requires one; the current mission assumes CLI/local artifacts only.

## Task 11 — Architecture and research-integrity guards

Prove with import-linter/source tests/scenarios:

- scanner core does not import experiment/execution/policy/evaluation;
- financial kernel does not depend on scanner;
- prospective evidence cannot rewrite Slice-1 identity or completed checkpoint artifacts;
- post-freeze observations cannot be injected into pre-freeze identity/model selection;
- final-OOS cannot enter automatic Slice-2 evidence;
- unfillable snapshots remain denominator failures;
- fee counted exactly once;
- no `q_safe / 0.10` capacity shortcut exists;
- no private exchange/authenticated action path exists;
- qualification carries no order/live-capital authority;
- no combined multi-candidate inventory allocation is introduced.

## Task 12 — Integrated negative/positive scenarios

Create deterministic no-network scenarios covering at least:

1. frozen Slice-1 survivor + forward checkpoint + fully fillable shallow books -> finite `C95(q)`, bounded capacity, qualification according to evidence;
2. one required shallow-book snapshot unfillable at a larger tested size -> larger `q` infeasible and excluded from `q_safe`, with the observation retained;
3. insufficient/stale public evidence -> `research_only`, not silently dropped;
4. positive candidate-local capacity but insufficient stricter current evidence -> `small_capacity`;
5. all approved current evidence satisfied -> `tradable_now` evidence label without order authority;
6. a later checkpoint appends new evidence without changing prior checkpoint/cohort/Slice-1 identities.

## Task 13 — Final verification and result record

Run fresh affected checks followed by the repository-wide gate:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
uv run lint-imports
git diff --check
```

Run OpenAPI/frontend generation only if an API-visible manifest/schema changes. Slice-2 scanner-local artifact schemas alone do not require frontend regeneration.

Perform a separate inline self-review against the approved Slice-2 design, especially prospective causality, denominator preservation, friction/fee authority, capacity conversion, current-evidence freshness, and the Slice-3 one-inventory boundary. Record honest negative/research-only results; do not relax qualification to manufacture `tradable_now`.

Update the Phase-15 umbrella and write `docs/research/2026-08-18-qap-scanner-slice2-results.md`. Commit coherent verified changes. Do not begin Slice 3 without its separately user-approved detailed design/implementation plan.

## Slice-2 completion gate

Slice 2 is complete only when repository evidence proves all of the following:

- a prospective cohort is frozen before forward outcome evidence and never mutates Slice-1 identity;
- checkpoint IDs bind frozen candidate/cohort/protocol/cutoff/exact forward evidence identities;
- completed forward checkpoints are append-only immutable evidence;
- public microstructure snapshots are causal, source-attributed, bounded-depth evidence with no private/live authority;
- every tested liquidity size preserves the fixed evidence denominator; required unfillable snapshots make the size infeasible;
- `C95(q)` and `q_safe` use only the approved prospective/current evidence and frozen adverse cost authority, with fee counted once;
- conservative capacity uses the approved policy transition/drift requirement and never `q_safe/0.10`;
- qualification is one of `research_only`, `small_capacity`, `tradable_now` with auditable reasons and no order authority;
- candidate-local capacity never becomes combined portfolio allocation;
- scanner core dependency boundaries remain intact;
- final-OOS, private exchange actions, scheduler/database/queue/UI, and Slice-3 basket allocation remain absent;
- full repository verification is green and the result record states the actual evidence/limitations.

## Pre-execution review note

Plan review classifies Slice 2 as mixed executable/persistence research infrastructure. Existing QAP abstractions should be reused for asset/instrument identity, cost authority, experiment replay, artifact hashing and import boundaries. No new runtime dependency, service, scheduler or database is justified.

The only implementation-sensitive values are the approved tested-size/percentile/freshness/transition-demand conventions in the Slice-2 design. They are protected research semantics: implementation must lift them from the authoritative design verbatim and add regression tests before Tasks 3–6; no numeric fallback, operator-tunable substitute or `q_safe / 0.10` shortcut is permitted. Tasks 1–2 can proceed independently because they establish identity/evidence contracts without choosing those values.
