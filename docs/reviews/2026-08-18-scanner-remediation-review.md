# Scanner Slice-1 / Slice-2 Remediation Review

Update context — 2026-08-18

Trigger: two external review reports supplied after Slice-2 Tasks 4-7 were committed.
Purpose: verify every supplied finding against the current worktree, de-duplicate overlapping findings, preserve reproducible evidence, and maintain a fix/verification checklist that can be marked as remediation progresses.
Impact: Slice-1 remediation is verified and committed. Slice 2 must not proceed to Task 8 until the remaining prospective-integrity gaps are remediated and re-verified.
Evidence: current branch `qap-implementation-20260818` at `8ce0c31` (Slice-1 remediation), base/merge-base `30adfb75e78792c5656003b4c6564ca97fcdcf27`, approved Slice-1/Slice-2 specs and implementation plans, and the verification commands recorded below.

## Verdict

**NO-GO — Request changes.**

Current verified disposition: **0 blockers, 5 major open Slice-2 findings, 0 minor open issues, 15 findings resolved and re-verified.**

The Slice-1 design did not need reopening; its implementation-fidelity and verification findings are closed. The remaining NO-GO scope is Slice-2 prospective causality, cohort-denominator semantics, and append-only artifact integrity.

## Review baseline

- Repository: `/home/hamza/repo/qap/.worktrees/qap-implementation-20260818`
- Branch: `qap-implementation-20260818`
- Current committed Slice-1 remediation point: `8ce0c31`
- Review base / merge base: `30adfb75e78792c5656003b4c6564ca97fcdcf27`
- Branch commits ahead of base at that checkpoint: 21
- The earlier untracked Slice-1 forensic helper and architecture guard are now committed.
- The supplied reviews were mostly performed at `c2d4f2a`; this document preserves their original evidence while recording current remediation status.

## Status rules

- `[ ]` = open; do not mark complete until the code correction **and** the stated regression/verification route pass on the current branch.
- `[x]` = resolved/refuted with fresh evidence. Keep the finding in this document for provenance.
- When fixing an item, append `Resolved at <commit>` and the exact verification command/output summary.
- A green unit test that encodes the wrong contract does not close a finding.
- A successful `lint-imports` run does not close an architecture finding unless the scanner boundary is actually represented in `.importlinter`.

## Master remediation checklist

### Blockers

- [x] **S1-01** Clean checkout is self-contained: the corrected forensic helper is committed and uses the actual SSD graph interface. Resolved at `f565898`.
- [x] **S1-02** Canonical Slice-1 execution no longer passes the stale `evaluate_series()` argument. Resolved at `f565898`.

### Slice-1 research integrity and fidelity

- [x] **S1-03** Reserved final-OOS fingerprints are rejected at the outer catalog-admission boundary before scanner source reads. Resolved at `8ce0c31`.
- [x] **S1-04** Completed Slice-1 artifacts seal and revalidate the exact physical authoritative file set and SHA-256 digests. Resolved at `8ce0c31`.
- [x] **S1-05** `graph_metadata.parquet` persists the complete SSD denominator/config/slice fingerprints/distance digest. Resolved at `8ce0c31`.
- [x] **S1-06** Historical candidate/universe semantic identity is independent of mutable whole-source extent and generation scan ID. Resolved at `8ce0c31`.
- [x] **S1-07** Persisted component-version labels are supplied from the exact `ScannerProtocol` instance. Resolved at `8ce0c31`.
- [x] **S1-08** Explicit manual candidate replay is wired CLI -> composition root -> promotion/replay, outside the automatic budget. Resolved at `8ce0c31`.
- [x] **S1-09** Scanner CLI test naming no longer collides with experiment CLI tests; whole-repository collection succeeds. Resolved at `8ce0c31`.
- [x] **S1-10** Scanner orchestration was decomposed by responsibility; the hard source-size gate is green (`run.py` = 700 lines). Resolved at `8ce0c31`.
- [x] **S1-11** Benchmark script is bound to current protocol fields and records 500/1,000 timing, memory, trial counts, and replay cap. Resolved at `8ce0c31`.
- [x] **S1-12** `.importlinter` now contains scanner boundary contracts; three deliberate forbidden-edge probes fail and clean state is 8/8 kept. Resolved at `8ce0c31`.
- [x] **S1-13** Semantic definition tamper is reported as mismatch while malformed input remains fail-closed; regression passes. Resolved at `8ce0c31`.

### Slice-2 prospective integrity

- [ ] **S2-01** Prospective checkpoint timing is not structurally strict: equality at `freeze_at` is accepted and the model has no candidate-specific `forward_start` / first-outcome-completion boundary.
- [ ] **S2-02** Zero-new-member prospective cohorts are rejected despite the approved denominator contract.
- [ ] **S2-05** The current cohort model cannot represent required active-freeze deduplication/reselection lineage and the approved automatic/manual cohort denominator fields.
- [ ] **S2-06** Completed Slice-2 checkpoint table hashes are written to the manifest but not validated when completed evidence is later read/reindexed; tampered qualification data can become authoritative index state.
- [ ] **S2-07** Slice-2 checkpoint persistence allows retroactive/out-of-order publication; an earlier checkpoint can be added after a later checkpoint has already been observed.

### Supplied findings now resolved

- [x] **S2-03** Mid-relative taker book friction now includes spread cost; the old best-side-reference bug is fixed and verified.
- [x] **S2-04** Direction-specific buy/sell capacity plus the frozen `q_safe = 0.5 * q_star` haircut are implemented and verified.

## Slice-1 remediation closure evidence

Commit `8ce0c31` (`fix: close scanner slice1 remediation gaps`) closes S1-03 through S1-13. Fresh evidence before commit:

- canonical Slice-1 / artifact / graph / candidate tests: `31 passed`;
- universe / slices / CLI / architecture / experiment-adapter / benchmark-smoke tests: `35 passed`;
- focused Pyright: `0 errors, 0 warnings, 0 informations`;
- focused Ruff: all checks passed;
- source-size: green, with `src/qap/scanner/run.py` reduced to 700 lines and scanner artifact responsibility split into focused modules;
- import-linter: `8 kept, 0 broken`, plus three deliberate prohibited-edge probes that each failed as required;
- benchmark: 500 assets -> 124,750 valid SSD pairs, 2,795 retained edges, 50,310 fixed trials, 39.7707s SSD, 110,712 KiB peak RSS; 1,000 assets -> 499,500 valid pairs, 5,667 retained edges, 102,006 fixed trials, 158.7503s SSD, 194,908 KiB peak RSS; authoritative replay ceiling remains 30 across all horizons.

The reproducible benchmark/result record is `docs/research/2026-08-18-qap-scanner-slice1-results.md`. The remaining open findings are Slice-2 only.

---

## Detailed findings

### S1-01 [Blocker] Clean checkout is not self-contained and the untracked forensic helper is API-incompatible

**Current code:** `src/qap/scanner/run.py:49`; untracked `src/qap/scanner/forensic_graph.py:70-77,116-121`; `src/qap/scanner/graph.py:144-150`.

**Supplied-review mapping:** first review Critical #1 points 2-3; second review F1.

**Verified current evidence:**

- `git cat-file -e HEAD:src/qap/scanner/forensic_graph.py` reports the file absent from HEAD.
- A temporary `git archive HEAD` clean-tree import fails with:

  `ModuleNotFoundError: No module named 'qap.scanner.forensic_graph'`

- The untracked helper calls `build_ssd_graph(..., evaluated_by_asset=...)`; the real API requires `series_by_asset=`.
- Focused Pyright reproduces both `Argument missing for parameter "series_by_asset"` and `No parameter named "evaluated_by_asset"`.

**Failure:** a clean checkout of the committed branch cannot import the canonical scanner path. Keeping the untracked file locally only changes the failure to an incompatible graph call.

**Fix direction:** either commit a corrected narrow forensic helper or remove the dependency and keep the logic in an already tracked scanner module. Align all graph calls to the actual `build_ssd_graph` contract.

**Resolved at `f565898` (`fix: restore canonical scanner execution`).**

Verification:

- [x] `forensic_graph.py` is committed.
- [x] All `build_ssd_graph` calls use `series_by_asset=`.
- [x] Clean `git archive HEAD` imports `qap.scanner.run` and `qap.scanner_entry` (`CLEAN_ARCHIVE_IMPORT_OK`).
- [x] `uv run pytest -q tests/scenarios/test_scanner_slice1.py` -> `4 passed` without compatibility shims.
- [x] `uv run pyright src/qap/scanner/run.py src/qap/scanner/forensic_graph.py src/qap/scanner_entry.py` -> `0 errors` before commit.

### S1-02 [Blocker] Normal Slice-1 scan crashes at `evaluate_series()`

**Current code:** `src/qap/scanner/run.py:356-362`; `src/qap/scanner/slices.py:125-171`.

**Supplied-review mapping:** first review Critical #1 point 1; second review F2.

**Verified current evidence:**

`uv run pytest -q tests/scenarios/test_scanner_slice1.py -x` fails on the first scenario with:

`TypeError: evaluate_series() got an unexpected keyword argument 'source_artifact_fingerprint'`

`evaluate_series()` computes `source_artifact_fingerprint` internally from the validated series and exposes no caller-supplied parameter.

**Failure:** every supported `run_scan_with_qap()` path reaches `_prepare_inputs()` and crashes before discovery.

**Fix direction:** make the call/function ownership consistent. With the current `evaluate_series()` design, removing the stale caller argument is the minimal correction unless a separate prevalidated-source contract is deliberately introduced.

**Resolved at `f565898` (`fix: restore canonical scanner execution`).**

Verification:

- [x] Real `run_scan_with_qap()` scenarios run without monkeypatch/shim.
- [x] Existing end-to-end scenarios reach the real discovery/promotion/replay-attempt path; full file reports `4 passed`.
- [x] Focused Pyright reports `0 errors` for scanner execution sources.

### S1-03 [Major] Final-OOS seal is checked after scanner admission can read source bytes

**Current code:** `src/qap/scanner/catalog.py:222-258`; trusted seal logic in `src/qap/experiment/dataset_seals.py:20-53`; scanner admission call in `src/qap/scanner/run.py:335-364`.

**Supplied-review mapping:** first review Critical #2.

**Verified current evidence:**

- `resolve_catalog_source()` resolves the path and immediately calls `read_parquet_bar_series(path)` at `catalog.py:237` before any role/seal check.
- No scanner module imports or calls `validate_dataset_seals` or an equivalent lower-level trusted reservation guard.
- Safe probe: a catalog source with the known reserved final-OOS semantic fingerprint was pointed at a dummy file while the Parquet reader was replaced with a sentinel. `resolve_catalog_source()` reached the sentinel and printed `READ_CALLED_BEFORE_ROLE_GUARD`. No reserved holdout bytes were opened during this probe.

**Failure:** scanner universe/graph/model/scout admission may consume information that is reserved final OOS before the experiment adapter eventually labels deep replay as development and rejects it. At that point the leakage has already happened.

**Fix direction:** enforce the trusted fingerprint-role reservation before scanner source bytes are opened, at a lower/outer admission boundary that does not make `qap.scanner` depend on `qap.experiment`.

**Mark fixed only when:**

- [ ] A sealed fingerprint is rejected before the storage reader is invoked.
- [ ] Scanner core still has no dependency on experiment/evaluation/policy/execution.
- [ ] Regression test proves final-OOS cannot enter scanner warm-up/search/replay.

### S1-04 [Major] Slice-1 completed artifacts do not enforce the exact physical authoritative file set

**Current code:** `src/qap/scanner/artifacts.py:587-665`, especially `publish_scan_generation()` and `discover_completed_scans()`.

**Supplied-review mapping:** first review High #3.

**Verified current evidence:**

A fresh temp-directory probe against current code:

- inserted `undeclared-authoritative.parquet` into staging;
- publication succeeded and retained the file (`extra_survived_publish True`);
- deleted declared `scout_trials.parquet` from the final directory;
- `discover_completed_scans()` still returned that directory (`missing_declared_still_discovered True`).

The experiment subsystem already has an exact-file-set integrity pattern in `src/qap/experiment/integrity.py`.

**Failure:** a directory can be treated as completed scanner evidence even when the authoritative physical set differs from what the manifest implies.

**Fix direction:** use a scanner integrity record or equivalent exact required/allowed-file contract, hash physical authoritative files, validate before rename, and revalidate on every completed-reader/discovery path.

**Mark fixed only when:**

- [ ] Undeclared authoritative file causes publication/read failure.
- [ ] Missing declared file causes discovery/read failure.
- [ ] Digest tamper causes failure.
- [ ] Completed discovery validates evidence instead of checking only `manifest.json` + `definition.json` + directory name.

### S1-05 [Major] Full SSD comparison denominator is not persisted

**Current code:** `src/qap/scanner/graph.py:81-88,273-280`; `src/qap/scanner/run.py:714-836`; `src/qap/scanner/artifact_schemas.py:27-42`.

**Supplied-review mapping:** first review High #4.

**Verified current evidence:**

`SsdGraph` computes and carries:

- `eligible_asset_count`
- `total_valid_pair_comparisons`
- `distance_digest`

but `_search_scope()` returns `graph.records`, not graph metadata, and the authoritative scanner schemas contain only retained `neighbors.parquet` rows. No scanner artifact schema or manifest field persists the full denominator count/digest.

**Failure:** final evidence cannot prove the retained k=8 neighborhood came from exactly the claimed full set of valid comparisons without recomputing against a sealed expected digest that was never published.

**Fix direction:** add one deterministic graph-metadata record per `(scan, venue, horizon)` with generator/protocol identity, eligible asset count, valid comparison count, exact graph-slice identities and `distance_digest`; include it in artifact integrity.

**Mark fixed only when:**

- [ ] Published artifact contains denominator count and digest for every searched scope.
- [ ] Manifest/integrity seals the graph metadata.
- [ ] A regression changes one non-retained valid comparison and proves the digest changes.

### S1-06 [Major] Future source extension re-identifies historical candidates

**Current code:** `src/qap/scanner/catalog.py:146-169`; `src/qap/scanner/models.py:223-255`; `src/qap/scanner/trials.py:151-171`.

**Supplied-review mapping:** first review High #5; second review F3.

**Verified current evidence:**

Current candidate hash directly includes whole-source fingerprints. A targeted probe kept the exact `selection_slice_fingerprint` unchanged and replaced only BTC 15m's `source_artifact_fingerprint`:

- `selection_same True`
- `source_changed True`
- `changed_15m_ids 9 of 9`
- `same_1h_ids 9 of 9`

The approved design explicitly requires future-row append stability for older causal candidate identity.

**Failure:** physically appending rows after the historical cutoff can change candidate identity even though the information available at that candidate's decision boundary is byte-identical.

**Fix direction:** keep whole-source fingerprint in generation/admission/resume provenance, but derive historical candidate semantics from frozen protocol/PIT context and exact evaluated-slice identities. Do not let post-cutoff extent mutate the causal candidate ID.

**Mark fixed only when:**

- [ ] Future rows change whole-source identity.
- [ ] Old `selection_slice_fingerprint` remains identical.
- [ ] Old candidate/trial IDs remain identical.
- [ ] Partial-generation resume still fails if its frozen whole-source identity changed.

### S1-07 [Major] Persisted component-version labels disagree with the actual scanner protocol

**Current code:** constants in `src/qap/scanner/protocol.py:14-17`; actual `SCANNER_V1_SLICE1` values at `protocol.py:217-226`; `ScanDefinition` defaults at `src/qap/scanner/models.py:134-143`; construction at `src/qap/scanner/run.py:468-479`.

**Supplied-review mapping:** second review F4.

**Verified current evidence:** a direct current-schema `ScanDefinition` constructed the same way as `run.py` prints:

- definition: `scanner-v1-pit-usdt-v1`, `scanner-v1-normalized-log-ssd-k8-v1`, `scanner-v1-mr-template-set-v1`
- protocol: `scanner-v1-pit-universe-v1`, `normalized-log-price-ssd-v1`, `scanner-v1-pair-mr-templates-v1`

Only promotion version currently matches.

**Failure:** artifacts can claim component versions different from the code/configuration actually used, weakening provenance and protocol auditability.

**Fix direction:** make the supplied `ScannerProtocol` instance the single source of truth for all persisted component-version fields; remove independent stale defaults from scan construction semantics.

**Mark fixed only when:**

- [ ] Definition fields equal the exact protocol instance passed to the scan.
- [ ] Manifest fields repeat the corrected definition values.
- [ ] Regression uses a modified protocol instance and proves the persisted component labels follow it.

### S1-08 [Major] Explicit manual deep replay is not wired through production

**Current code:** `src/qap/scanner/promotion.py:59-177`; `src/qap/scanner/run.py:908-916`; `src/qap/scanner/cli.py:50-79`.

**Supplied-review mapping:** first review Important #6.

**Verified current evidence:**

- `apply_promotion_policy()` supports `manual_candidate_ids` and has unit coverage.
- `run_scan()` calls it without `manual_candidate_ids`.
- Scanner CLI exposes pins but no explicit manual candidate replay request.
- Call-site search found no production path supplying manual candidate IDs.

**Failure:** a manually investigated/pinned trial can be discovered and lineage-attributed but cannot enter the explicit manual deep-replay mechanism promised by the Slice-1 plan unless it also wins automatic promotion.

**Fix direction:** add one narrow explicit manual-replay request input and thread deterministic candidate IDs into promotion/replay-attempt enumeration. Pair pinning should not automatically mean mandatory deep replay.

**Mark fixed only when:**

- [ ] Production entry accepts explicit manual candidate replay IDs.
- [ ] Manual replay remains outside automatic `10/horizon` count.
- [ ] Automatic/manual overlap produces one replay attempt with both lineage facts.
- [ ] CLI/operator path has deterministic validation for unknown candidate IDs.

### S1-09 [Major] Whole-repository pytest collection fails due scanner `test_cli.py` basename collision

**Current files:** `tests/unit/scanner/test_cli.py`; existing `tests/unit/experiment/test_cli.py`.

**Supplied-review mapping:** first review Medium #7.

**Verified current evidence:** `uv run pytest -q --collect-only` collects 597 tests, then aborts with an import-file mismatch because both unit modules import as top-level `test_cli`.

**Failure:** the required full regression gate cannot collect.

**Fix direction:** rename the scanner module (for example `test_scanner_cli.py`) or make test module imports package-safe under the repository's standard pytest configuration.

**Mark fixed only when:**

- [ ] Default `uv run pytest -q --collect-only` completes without import mismatch.
- [ ] Full pytest gate can run without requiring a nonstandard import mode.

### S1-10 [Major] `scanner/run.py` violates the hard source-size gate

**Current file:** `src/qap/scanner/run.py` = 997 lines.

**Supplied-review mapping:** first review Medium #8; second review F9.

**Verified current evidence:** `uv run python scripts/check_source_size.py` reports:

`source-size error: src/qap/scanner/run.py has 997 lines (over the 700-line hand-written limit)`

**Failure:** explicit repository completion gate is red; the file currently combines input preparation, lifecycle/source resolution, graph/scout execution, promotion/replay and publication.

**Fix direction:** decompose along those existing responsibilities without introducing generic framework abstractions.

**Mark fixed only when:**

- [ ] No hand-written scanner source file exceeds 700 lines.
- [ ] The decomposition does not create circular/new forbidden dependency edges.
- [ ] Slice-1 end-to-end behavior and replay ordering remain unchanged.

### S1-11 [Major] Required 500/1,000 benchmark cannot run

**Current code:** `scripts/benchmark_scanner_slice1.py:174-195`.

**Supplied-review mapping:** first review Medium #9; second review F10.

**Verified current evidence:** script references nonexistent `ScannerProtocol.nearest_neighbors` and `max_automatic_replays_per_horizon`. A tiny smoke command fails immediately with `AttributeError` before any measurement.

Current protocol names are `neighbors_per_asset` and `automatic_replay_cap_per_horizon`.

**Failure:** the required acceptance evidence for 500/1,000-asset SSD and bounded post-graph scout workload cannot be produced.

**Fix direction:** bind benchmark code to the current frozen protocol contract, add a small smoke regression, then run 500 and 1,000 assets and record time/memory/trial/replay-ceiling evidence. Optimize only after the repaired production-equivalent measurement identifies a bottleneck.

**Mark fixed only when:**

- [ ] Small benchmark smoke runs.
- [ ] 500-asset result recorded.
- [ ] 1,000-asset result recorded.
- [ ] Trial counts and `10/horizon` replay ceiling are included.
- [ ] Any optimization is justified by the measured bottleneck.

### S1-12 [Major] Import-linter does not enforce the scanner architecture boundary

**Current config:** `.importlinter` contains only the pre-scanner package layer and four independence contracts.

**Supplied-review mapping:** second review F11.

**Verified current evidence:** `uv run lint-imports` reports `5 kept, 0 broken`, but `.importlinter` contains no `qap.scanner` contract at all. The useful `tests/unit/scanner/test_architecture.py` currently passes 6/6 but remains untracked.

**Failure:** prohibited edges such as `qap.scanner -> qap.execution` or financial-kernel packages importing scanner would not be detected by the required import-linter gate.

**Fix direction:** add the explicit scanner contracts from the approved Slice-1 plan, preserving `qap.experiment.scanner_adapter` and `qap.scanner_entry` as the narrow outer integration boundaries. Commit the architecture regression test if it remains useful.

**Mark fixed only when:**

- [ ] `.importlinter` names scanner restrictions explicitly.
- [ ] Intentional outer adapter/composition exceptions are narrow and documented.
- [ ] Temporary prohibited-edge probes make `lint-imports` fail.
- [ ] Clean configuration returns green after probes are removed.

### S1-13 [Minor / gate hygiene] Scanner artifact resume test expects the wrong error wording

**Current test:** `tests/unit/scanner/test_scanner_artifacts.py:377`.

**Supplied-review mapping:** noted in both verification summaries but not elevated as an implementation-integrity defect.

**Verified current evidence:** the single test still fails because it expects `partial scan definition mismatch`; current code raises `partial scan definition is malformed`. The path remains fail-closed.

**Failure:** once collection/runtime blockers are corrected, this still keeps the required test suite red.

**Fix direction:** decide the intended stable error contract and align test/implementation. Do not weaken the fail-closed validation.

**Mark fixed only when:**

- [ ] The targeted test passes.
- [ ] Tampered frozen definition still fails closed.

### S2-01 [Major] Prospective timing is not strictly enforceable

**Current code:** `src/qap/scanner/prospective.py:162-257`, especially `207-214`; current test encodes equality at `tests/unit/scanner/test_prospective.py:87-103`.

**Supplied-review mapping:** second review F5.

**Verified current evidence:**

- approved design requires `frozen_at < forward_start` and first outcome completion strictly after the candidate-specific `forward_start`;
- current validator only rejects `evidence_window_start < freeze_at`;
- a direct object-construction probe confirmed `equality_at_freeze_accepted True`;
- `ProspectiveCheckpoint` has no `forward_start` or first-outcome-completion field, and `forward_slices` carries only dataset/fingerprint identities with no timing boundary.

**Failure:** evidence available exactly at freeze can be labeled prospective, and the persisted checkpoint cannot prove the candidate-specific first forward decision/outcome boundary required by the design.

**Fix direction:** make candidate-specific `forward_start` and first admitted outcome-completion boundary explicit semantic fields; require strict ordering and keep pre-forward warm-up distinguishable from prospective outcome data.

**Mark fixed only when:**

- [ ] Outcome completing exactly at freeze is rejected.
- [ ] `forward_start` is strictly after `freeze_at`.
- [ ] First counted outcome completes strictly after `forward_start`.
- [ ] Checkpoint identity seals those boundaries.

### S2-02 [Major] Zero-new-member cohorts are rejected

**Current code:** `src/qap/scanner/prospective.py:116-134`.

**Supplied-review mapping:** second review F6.

**Verified current evidence:** direct construction with `candidates=()` raises a Pydantic `ValidationError` because `validate_candidates()` requires at least one member. Approved Slice-2 design explicitly states zero-new-member cohorts are valid results for completed automatic scans/horizons.

**Failure:** prospective policy evidence becomes conditioned on having at least one historical survivor, omitting negative/empty discovery generations from the denominator.

**Fix direction:** permit deterministic zero-new-member automatic cohort records and preserve source scan/horizon/protocol context even when member count is zero.

**Mark fixed only when:**

- [ ] Empty automatic cohort is valid and has deterministic identity.
- [ ] It publishes immutable cohort/freeze evidence without fabricating members.
- [ ] Zero-member generations remain discoverable in prospective policy summaries.

### S2-03 [Resolved] Mid-relative book friction includes spread cost

**Old supplied finding:** second review F7.

**Current code:** `src/qap/scanner/liquidity.py` stores `mid_reference_price` and computes `book_price_impact_bps` against mid; tests assert mid-relative impact for both buy and sell.

**Resolution:** fixed in the post-`c2d4f2a` Task-4–6 work (`9fb2462`).

**Fresh verification:** `uv run pytest -q tests/unit/scanner/test_liquidity.py tests/unit/scanner/test_liquidity_policy.py` -> `14 passed`.

### S2-04 [Resolved] Direction-specific capacity and 0.5 safety haircut are implemented

**Old supplied finding:** second review F8 against the dirty `c2d4f2a` worktree.

**Current code:** `src/qap/scanner/liquidity_policy.py` keeps independent buy/sell `q_star`/`q_safe`, applies `SAFE_CAPACITY_HAIRCUT == Decimal("0.5")`, computes direction-specific required fractions from current base weight, and takes the minimum buy/sell capital ceiling. Tests include asymmetric capacity and the anti-`0.10` shortcut regression.

**Resolution:** fixed in `9fb2462`.

**Fresh verification:** same 14-test liquidity suite passes.

### S2-05 [Major, related finding] Cohort model cannot represent active-freeze dedup/reselection denominator semantics

**Current code:** `src/qap/scanner/prospective.py:88-158`.

**Related approved design:** Slice-2 design Section 6 requires, per completed automatic scan/horizon, all automatic survivors, active semantic freeze deduplication, explicit reselection events, separate manual lineage, zero-new-member result, horizon and automatic/manual counts.

**Verified current evidence:** repository search finds no `reselect`, `active_freeze`, `freeze_id`, `automatic_member_count`, `manual_member_count`, `candidate_freeze` or `forward_start` implementation under scanner. Current `ProspectiveCohort` has only one cohort-level `freeze_at`, source scan ID and candidate attachments.

**Failure:** repeated scans cannot distinguish a reselection of the same active semantic rule from a new independent prospective freeze, so overlapping selections can be double-counted or lose the required denominator lineage. The current schema also cannot encode the approved automatic/manual membership counts/horizon record.

**Fix direction:** represent candidate freeze identity separately from source scan selection, implement the approved semantic active-freeze dedup key, record reselections rather than opening duplicate overlapping freezes, and persist automatic/manual counts/horizon.

**Mark fixed only when:**

- [ ] Same semantic unmatured candidate is linked as reselection, not duplicated.
- [ ] Manual membership stays separate from automatic cohort summary.
- [ ] Cohort persists horizon and member counts.
- [ ] Matured freeze may legitimately permit a later new generation.

### S2-06 [Major, related finding] Completed Slice-2 checkpoint digests are not revalidated on read/reindex

**Current code:** `src/qap/scanner/slice2_artifacts.py:487-620`.

**Verified current evidence:** publication writes `table_hashes` into the checkpoint manifest, but `_required_tables()`, `_completed_generation_dirs()`, `read_completed_checkpoints()` and `_rebuild_indices()` do not validate those hashes against completed physical files.

A temp probe published a `research_only` checkpoint, rewrote `qualification.parquet` with the same schema but `qualification_state='tradable_now'`, then reopened the cohort. The derived outcome index reported:

`tampered_state_reindexed tradable_now`

with a stale manifest hash still present.

**Failure:** completed prospective evidence can be modified after publication and later become top-level index truth despite the manifest claiming different bytes.

**Fix direction:** implement a completed-checkpoint integrity validator that verifies manifest identity, exact required/allowed file set, table hashes/counts and lineage before any discovery/reindex/read operation.

**Mark fixed only when:**

- [ ] Post-publication Parquet value tamper is rejected.
- [ ] Missing/extra authoritative files are rejected.
- [ ] Reindexing consumes only validated completed generations.
- [ ] Integrity regression covers qualification and checkpoint tables.

### S2-07 [Major, related finding] Retroactive checkpoint backfill is accepted after later outcomes exist

**Current code:** `src/qap/scanner/slice2_artifacts.py:303-354,520-620`; `ProspectiveCheckpoint` only requires a positive index.

**Verified current evidence:** a temp probe published checkpoint index `2` first, then index `1`; both publications succeeded. Rebuilt `checkpoints.parquet` reported `[1, 2]`, masking the actual publication order.

**Failure:** after observing a later checkpoint/outcome, an operator or orchestration defect can backfill an earlier checkpoint as though it belonged to the original append-only prospective sequence. That violates the approved append-only schedule semantics and enables retrospective evidence insertion.

**Fix direction:** enforce checkpoint schedule monotonicity/collision rules at the cohort artifact boundary. Existing completed indexes/information cutoffs must constrain the next admissible checkpoint index/window; a late earlier index or duplicate semantic schedule slot must fail closed.

**Mark fixed only when:**

- [ ] Index 2 cannot be followed by new index 1.
- [ ] Same index with different checkpoint identity is rejected.
- [ ] `information_end`/window schedule is monotone according to the frozen checkpoint policy.
- [ ] Append-only ordering has an explicit regression test, including interrupted recovery.

---

## Supplied-review coverage map

This mapping preserves where each original report landed after de-duplication and current-state verification.

### First supplied review

- Critical #1 -> **S1-01**, **S1-02**
- Critical #2 final-OOS -> **S1-03**
- High #3 artifact integrity -> **S1-04**
- High #4 SSD denominator -> **S1-05**
- High #5 future-row identity -> **S1-06**
- Important #6 manual replay -> **S1-08**
- Medium #7 pytest collision -> **S1-09**
- Medium #8 source-size -> **S1-10**
- Medium #9 benchmark -> **S1-11**
- error-message verification note -> **S1-13**

### Second supplied review

- F1 -> **S1-01**
- F2 -> **S1-02**
- F3 -> **S1-06**
- F4 -> **S1-07**
- F5 -> **S2-01**
- F6 -> **S2-02**
- F7 -> **S2-03** (resolved after reviewer baseline)
- F8 -> **S2-04** (resolved after reviewer baseline)
- F9 -> **S1-10**
- F10 -> **S1-11**
- F11 -> **S1-12**

### Related findings added by this verification pass

- **S2-05** active-freeze/reselection/cohort-denominator model is absent.
- **S2-06** completed Slice-2 manifest hashes are not enforced on later reads/reindex.
- **S2-07** checkpoint append order can be retroactively backfilled.

## Contract status snapshot

| Contract | Current status | Governing findings |
| --- | --- | --- |
| Clean-checkout executable Slice-1 path | FAIL | S1-01, S1-02 |
| Reserved final-OOS unavailable to scanner search/warm-up | FAIL | S1-03 |
| Exact completed Slice-1 physical artifact set | FAIL | S1-04 |
| Complete SSD search denominator sealed | FAIL | S1-05 |
| Future-row-stable causal candidate identity | FAIL | S1-06 |
| Persisted component versions match actual protocol | FAIL | S1-07 |
| Explicit manual deep replay outside automatic budget | NOT WIRED | S1-08 |
| Full pytest collection | FAIL | S1-09 |
| Source-size gate | FAIL | S1-10 |
| 500/1,000 benchmark acceptance | FAIL | S1-11 |
| Scanner dependency boundary enforced by import-linter | FAIL / false-green gate | S1-12 |
| Strict freeze-before-forward outcome | FAIL | S2-01 |
| Zero-new-member cohort denominator | FAIL | S2-02 |
| Mid-relative taker book friction | PASS | S2-03 |
| Direction-specific conservative capacity + 0.5 haircut | PASS | S2-04 |
| Active-freeze dedup / reselection lineage | NOT IMPLEMENTED | S2-05 |
| Completed Slice-2 artifact integrity on read | FAIL | S2-06 |
| Append-only prospective checkpoint schedule | FAIL | S2-07 |

## Verification snapshot

Commands below were run fresh against `d951bf9` plus the two untracked files unless stated otherwise.

- `git diff --check 30adfb75...HEAD` — **PASS**
- current worktree `git diff --check` — **PASS**
- clean `git archive HEAD` import of `qap.scanner.run` — **FAIL**, missing `qap.scanner.forensic_graph` (**S1-01**)
- `uv run pytest -q tests/scenarios/test_scanner_slice1.py -x` — **FAIL** immediately on `evaluate_series` unsupported keyword (**S1-02**)
- `uv run pytest -q --collect-only` — **FAIL**, 597 tests collected then scanner/experiment `test_cli.py` import mismatch (**S1-09**)
- targeted scanner artifact resume test — **FAIL**, expected `mismatch`, got `malformed` (**S1-13**)
- `uv run python scripts/check_source_size.py` — **FAIL**, `scanner/run.py` 997 lines (**S1-10**)
- benchmark smoke `--assets 8 --bars 40 --scout-sample 4` — **FAIL**, stale `nearest_neighbors` attribute (**S1-11**)
- `uv run lint-imports` — **5/5 existing contracts pass**, but scanner is absent from `.importlinter` (**S1-12 remains open**)
- `uv run pytest -q tests/unit/scanner/test_architecture.py` — **6 passed**, but the file is untracked and not a substitute for the required import-linter contract
- focused scanner Pyright (`src/qap/scanner`, scanner entry, benchmark, scanner tests/scenario) — **FAIL**, 64 errors; direct material errors include S1-01, S1-02 and S1-11 plus additional test typing issues
- focused scanner Ruff — **FAIL**, 7 errors; these are gate status, not separate findings in this review
- focused graph/promotion/prospective/liquidity/Slice-2-artifact unit set — **44 passed**; note that current prospective tests encode the wrong equality-at-freeze behavior and therefore do not close S2-01
- focused liquidity tests — **14 passed**, closing S2-03 and S2-04
- final-OOS safe sentinel probe — scanner source reader was reached before any role guard (`READ_CALLED_BEFORE_ROLE_GUARD`); reserved holdout bytes were not accessed
- candidate source-fingerprint probe — selection fingerprint unchanged, 9/9 affected 15m candidate IDs changed (**S1-06**)
- Slice-1 artifact adversarial probe — undeclared Parquet survived publish; deletion of declared scout table still left scan discoverable (**S1-04**)
- Slice-2 tamper probe — modified `qualification.parquet` was reindexed as `tradable_now` despite stale manifest hash (**S2-06**)
- Slice-2 ordering probe — checkpoint 2 then checkpoint 1 both published successfully (**S2-07**)

## Recommended remediation order

1. **Make the branch runnable and self-contained:** S1-01, S1-02.
2. **Close research-integrity leaks before trusting any scanner result:** S1-03, S1-04, S1-05, S1-06, S1-07.
3. **Repair the prospective identity/denominator foundation before Task 8:** S2-01, S2-02, S2-05, S2-06, S2-07.
4. **Finish required Slice-1 operator/architecture behavior:** S1-08, S1-12.
5. **Restore mandatory verification gates:** S1-09, S1-10, S1-11, S1-13, then fresh full Ruff/format/Pyright/source-size/import-linter/pytest.
6. **Re-review Slice 1 from a clean checkout.** Do not use reviewer-only compatibility shims.
7. **Only after that review is green, resume Slice-2 Task 8.**

## Re-review completion checklist

Slice 1 may move from NO-GO only when all of the following are true:

- [ ] S1-01 through S1-12 are checked off with fresh evidence.
- [ ] S1-13 is closed or explicitly reclassified with an approved stable error contract.
- [ ] `uv run pytest -q` completes and passes from the ordinary repository configuration.
- [ ] `uv run ruff check .` passes.
- [ ] `uv run ruff format --check .` passes.
- [ ] `uv run pyright src tests scripts` passes.
- [ ] `uv run python scripts/check_source_size.py` passes.
- [ ] `uv run lint-imports` passes **with scanner contracts present**.
- [ ] repaired 500- and 1,000-asset benchmark evidence is recorded.
- [ ] clean-checkout Slice-1 scenario suite passes with no shims/untracked dependencies.
- [ ] adversarial final-OOS, artifact-file-set, source-append identity and SSD-denominator regressions pass.

Before Slice-2 Task 8 resumes:

- [ ] S2-01, S2-02, S2-05, S2-06 and S2-07 are checked off.
- [x] S2-03 mid-relative friction remains green.
- [x] S2-04 direction-specific capacity / 0.5 haircut remains green.
- [ ] Prospective checkpoint/cohort artifact tests are updated to enforce the corrected strict timing, denominator, integrity and append-order contracts.

## Current recommendation

**FIX FINDINGS THEN RE-REVIEW. Do not merge or declare Slice 1 complete, and do not start Slice-2 Task 8 yet.**
