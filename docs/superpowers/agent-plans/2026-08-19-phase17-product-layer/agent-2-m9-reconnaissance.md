# Agent 2 — M9 Process / State Ownership and Packaging Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only reconnaissance
**Workspace:** `/home/hamza/repo/qap` read-only
**Can start:** after the Wave-9 coordination base is committed
**Depends on:** M7 integrated at `d5fbddc`; M8 is contractually forbidden from adding another long-lived service or mutable Product store
**Execution lifetime:** persistent-agent-loop for mission continuity only

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M9 section is authoritative
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `scripts/start_workbench.sh`
- existing workspace/launcher/process ownership code
- integrated M7 collector/lease/Product SQLite state
- current scientific operation subprocess ownership

Do not inspect or mutate Agent 1's active M8-0 worktree.

## Objective

Prepare the exact repository-grounded M9 process/state ownership and packaging decision brief now that M7 has introduced the last planned long-lived Product process.

This mission is reconnaissance only. Do not choose or install Tauri or another desktop framework.

M8 may change read/presentation and immutable basket lineage but is not allowed to add a new service, queue, scheduler, or mutable Product database. Therefore the mature process topology can be investigated safely while M8-0 runs.

## Investigate

### 1. Exact mature local process map

Map the current owners, startup/shutdown relationships, workspace bindings, and failure behavior for:

```text
web process
FastAPI/uvicorn API process
persistent current-evidence collector
short-lived OperationStore scientific workers
launcher shell process
```

For each process/state identify:

```text
owner
allowed mutator/controller
consumer(s)
lifetime
workspace binding
restart/recovery rule
failure detection
failure effect
shutdown owner
```

### 2. Persistent state map

Map the exact mutable and immutable state families:

- Product SQLite operational state;
- scientific OperationStore state;
- immutable scanner/prospective/basket/QAP artifacts;
- Product market-data generations/provenance;
- current Product workspace/universe state;
- public manual capture artifacts where still relevant.

Identify which process may mutate each state and whether restart/recovery is currently deterministic.

Do not propose merging these authorities merely for packaging convenience.

### 3. Launcher correctness and burden

Inspect `scripts/start_workbench.sh` and determine what the current launcher already guarantees for:

- workspace identity mismatch;
- unrelated port occupancy;
- API/web/collector startup;
- Sample vs Local Market behavior;
- collector-health reporting;
- process-group shutdown;
- stale/dead collector lease recovery;
- partial-start failures;
- relaunch behavior;
- visible operator diagnostics.

Distinguish actual correctness gaps from mere UX inconvenience.

### 4. Packaging decision criteria

Determine whether the current local launcher plus browser UI is technically sufficient for Product V1, or whether a desktop shell would solve a demonstrated process-lifecycle/operator burden.

If a desktop shell may be justified, identify the smallest responsibility it should own and what it must not own.

The current candidate is Tauri only because the design names it as a possible shell. Do not assume Tauri is required or best without evidence.

Do not allow packaging to become scientific/economic authority, background research state, private exchange auth, or live-trading authority.

### 5. Native/platform options before new dependencies

Apply the current architecture/YAGNI standard:

1. existing launcher/browser experience;
2. small launcher/status improvements;
3. operating-system/native process features already available;
4. only then a desktop shell if it materially reduces a demonstrated burden.

Do not recommend Redis, system-wide service managers, auto-updaters, installers, tray applications, or cloud process managers unless actual repository/runtime evidence requires them.

### 6. M9 implementation topology

Recommend whether executable M9 should be:

- no code change / document decision only;
- a small launcher/process-lifecycle hardening mission;
- a desktop-shell proof/implementation mission;
- another narrowly justified shape.

Identify exact dependencies on M8 completion and the smallest safe writer topology.

### 7. M10 handoff

Identify which process/packaging choices materially affect representative-user comprehension/accessibility testing in M10:

- starting/stopping QAP;
- knowing which workspace is active;
- knowing whether background collection is healthy;
- recovering from partial process failure;
- distinguishing operational failure from research evidence.

Do not fabricate user-study results.

## Hard boundaries

Do not mutate the repository.

Do not run tests, builds, generators, migrations, captures, market downloads, browser mutations, or process-start experiments that alter Product state.

Do not inspect Agent 1's active worktree.

Do not install dependencies.

Do not implement M9/M10.

Do not reopen M7 collector scientific boundaries or M8 basket economics.

Do not propose private exchange credentials, live orders, capital authority, cloud infrastructure, or generic workflow/job infrastructure.

## Success criteria

Reconnaissance is complete when you can provide:

1. exact read-only Git state before/after;
2. mature process ownership map;
3. mutable/immutable state ownership map;
4. launcher capability/gap analysis;
5. evidence-based packaging decision criteria;
6. smallest recommended executable M9 shape;
7. M10-relevant operator/comprehension implications;
8. hard stops and risks;
9. explicit no-mutation confirmation.

## Finish report

Return those nine sections in order and clearly separate current repository facts from recommendations/inference.
