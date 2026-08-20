# Agent B — M10-C Capability / Fidelity Proof

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** research/acceptance evidence; docs-only unless a blocker is found
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m10c-capability-proof`
**Branch:** `phase17-m10c-capability-proof`
**Isolation reason:** the proof may create temporary Product workspaces/artifacts and a durable evidence report while `main` remains the stable integrated M10-A/B review baseline.
**Can start:** immediately after the Wave-14 coordination base is committed and this worktree is created
**Depends on:** M10-A integrated at `12ed08a`; M10-B integrated at `f39b4b4`
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless; report checkpoints without treating steering as a stop

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M10-C is authoritative
- `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
- integrated M10-A recipe/preflight/lineage implementation at `12ed08a`
- integrated M10-B Product cockpit implementation at `f39b4b4`
- current Product Research, Experiment Lab, operations, History, experiment lineage, and scanner surfaces

Before any repository mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Testing remains opt-in. Do not create, modify, or run tests.

## Objective

Prove that the integrated M10-A/B research machinery reports capability, authority, readiness, fidelity, lineage, and final-OOS truth correctly across deliberately different research cases, without implementing missing methods or moving scientific authority into the Product UI.

This milestone is an acceptance proof, not another implementation wave.

## Ownership

You own:

- direct deterministic evidence for the eight frozen M10-C cases;
- verification that Product presentation consumes backend truth without changing it;
- one durable evidence report under `docs/research/` recording inputs, observed support axes/reasons, execution/lineage evidence where applicable, and pass/fail disposition;
- a clear APPROVE / REQUEST CHANGES verdict for M10-C.

You do **not** own production-code remediation. If a blocking defect is found, document it precisely and stop rather than fixing it inside the proof mission.

## Frozen cases to prove

### 1. Current rolling-residual pair recipe

Show a current `pair` recipe using the admitted rolling residual/OLS relationship path.

Expected truth:

- `structure=valid`;
- `capability=executable`;
- `authority=allowed`;
- readiness follows actual setup state;
- `runnable` follows the backend report rather than UI inference.

Where practical, use a deterministic ready Product fixture/workspace so one case reaches runnable execution and ordinary experiment artifacts.

### 2. Current slow-momentum semantics

Demonstrate that slow momentum is described truthfully through current capability/research-object semantics and is not silently presented as a pair-relationship model when that is not its current owner/meaning.

Record the exact support axes/reasons returned by the integrated backend/Product.

### 3. Student-t Copula

Use the known-but-unimplemented capability metadata.

Expected truth includes:

- `capability=unimplemented`;
- `runnable=false`;
- `known_method_not_implemented`;
- no false claim that the chosen pair itself is incompatible.

Do not implement Copula.

### 4. Palazzi 2025 exact replication

Represent the manually curated exact-replication recipe described by the M10 plan/research report.

Expected simultaneous truths include, as applicable to the declared recipe:

- related current OLS/z-score capability;
- constitution blocking for required short exposure;
- unimplemented selection/risk semantics;
- `fidelity=adaptation_required`;
- `runnable=false`;
- all applicable reasons preserved together rather than one precedence winner.

Do not reinterpret the paper automatically or implement its missing methods.

### 5. Palazzi-inspired QAP adaptation

If the current recipe contract can represent the already-planned adaptation example, prove that:

- it has a distinct exact `recipe_sha256`;
- `derived_from_recipe_sha256` points to the source methodology declaration;
- its fidelity claim is distinct from exact replication;
- adaptation lineage is not confused with final-OOS selection lineage.

This case is about identity/fidelity truth, not strategy implementation.

### 6. Invalid final-OOS multi-variant recipe

Expected preflight:

- `structure=invalid`;
- `runnable=false`;
- `final_oos_requires_single_precommitted_variant`;
- failure occurs before compilation/reservation.

Confirm no final-OOS commitment/consumption is created by this invalid attempt.

### 7. Development-to-final-OOS family continuity

Prove the frozen lineage contract:

```text
development [A,B]
  recipe_sha256 = X
  research_family_id = FAMILY
  compilation_sha256 = C

selected final-OOS [A]
  recipe_sha256 = Y
  selected_from_compilation_sha256 = C
  research_family_id = SAME FAMILY
```

Then demonstrate that sibling B cannot consume the same family holdout under existing runtime authority.

Use the integrated immutable recipe/compilation lineage read to show exact family + manifest membership rather than relying on labels.

### 8. Unknown method ID

Expected truth:

- `capability=unknown`;
- `runnable=false`;
- `unknown_method`;
- no dynamic import/dispatch or arbitrary execution.

## Product presentation proof

For representative cases above, verify the integrated M10-B surface preserves backend truth:

- Experiment Lab choices come from backend-described capability metadata;
- SupportReport axes render independently;
- every backend reason/suggestion remains visible or inspectable;
- Run is disabled unless backend `support.runnable=true` and a canonical recipe exists;
- recipe execution links exact backend `run_ids[]`;
- advanced experiment provenance can disclose recipe/compilation lineage;
- manual recipe runs remain experiments/history evidence, not scanner Research Ideas;
- Universal Scan remains scanner-owned and separate from recipe compilation.

Use browser/rendered evidence only where it directly proves a Product claim. Do not fabricate representative-user results; that belongs to M10-D.

## Evidence discipline

Prefer temporary deterministic workspaces/fixtures and existing application/domain entry points. Do not mutate the user's normal Product workspace merely to create evidence.

Capture enough exact evidence to make the report reconstructible, including where relevant:

- recipe identity/family;
- support axes;
- typed reason codes;
- compilation SHA;
- run IDs / manifest hashes;
- final-OOS selection lineage;
- whether reservation/commitment existed before/after invalid attempts.

Do not turn the evidence report into a new scientific artifact authority. Existing QAP artifacts remain authoritative.

## Deliverable

Create one report:

`docs/research/2026-08-20-qap-m10c-capability-fidelity-proof.md`

Recommended structure:

1. baseline / integrated commits;
2. proof environment and evidence method;
3. eight-case matrix with expected vs observed truth;
4. Product presentation checks;
5. protected-boundary checks;
6. deviations/blockers if any;
7. verdict: `APPROVE M10-C` or `REQUEST CHANGES`;
8. exact M10-D handoff: which user tasks are now technically ready for human acceptance.

## Required validation

No tests.

Use only validation needed by the docs/evidence deliverable:

- direct deterministic proof commands/fixtures for the eight cases;
- bounded browser/render evidence where Product behavior itself must be observed;
- `git diff --check` for the report/coordination changes;
- any focused parser/static command necessary to establish evidence, but do not rerun broad lint/type/build suites already completed by M10-A/B unless a concrete discrepancy requires it.

## Out of scope

- production source fixes;
- new research methods;
- Copula implementation;
- Palazzi implementation;
- automatic paper interpretation;
- new scanner/focus-scan mechanics;
- new backtester/plugin system;
- changing SupportReport semantics;
- changing final-OOS reservation/consumption;
- M10-D participant/user-study execution;
- live/private trading authority.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. M10-C verdict;
4. the eight-case observed support/lineage outcomes;
5. exact Product presentation evidence checked;
6. any defect found, with owner and severity, without silently fixing it;
7. evidence report path;
8. validation actually run; explicitly state no tests were run;
9. protected scientific/scanner/final-OOS/live-trading boundaries confirmed unchanged;
10. M10-D handoff: exact human tasks now ready and any task still blocked.
