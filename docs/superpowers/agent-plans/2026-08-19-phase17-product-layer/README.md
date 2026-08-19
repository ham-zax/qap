# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** hybrid — one writable M1 implementation plus one concurrent read-only M2 reconnaissance mission
**Current wave:** 1

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M1 workspace identity + clean zero-state | mixed executable | ready | now | `/home/hamza/repo/qap/.worktrees/phase17-m1-workspace` on branch `phase17-m1-workspace` | sole writer for M1 while main remains the integration/read-only base | none |
| Agent 2 — M2 market directory/admission reconnaissance | read-only | ready | now | `/home/hamza/repo/qap` read-only | no worktree needed; repository must remain unmodified by this mission | none for reconnaissance; executable M2 remains blocked by integrated M1 |

## Dependency map

```text
Phase 17 M0 design freeze (1bb6e78)
            |
            +------------------------------+
            |                              |
            v                              v
Agent 1: implement M1             Agent 2: read-only M2 reconnaissance
workspace identity / zero-state   owners, contracts, risks, minimal seam
            |                              |
            +---------------+--------------+
                            v
                 planner integrates M1 and replans
                            |
                            v
                 M2 executable implementation
                            |
                            v
                 M3 data acquisition/generations
                            |
                            v
                 M4 current-approved readiness
                            |
                            v
                 M5+ Product UI/lifecycle work
```

M2 executable work must not start until Agent 1's M1 result is integrated and the planner has reconciled Agent 2's reconnaissance report with the actual M1 interface/state ownership.

## Shared contracts

- Phase 17 changes Product operation, not QAP scientific/economic authority.
- Phase-12 live-capital authority remains `NO-GO`.
- The strict historical point-in-time scanner policy remains intact. The separately-versioned current-approved retrospective claim belongs to M4, not M1/M2.
- Asset-level admission remains explicit operator authority; exchange listing must never imply approval to own.
- Negative, invalid, incomplete, unavailable, and rejected research evidence remains first-class.
- The existing seven-command research mutation vocabulary remains protected; Product maintenance is a separate bounded owner.
- CCXT is not required for Product V1. Existing Binance/Gate public adapters are preferred until a concrete insufficiency is demonstrated.
- Tests are opt-in. This coordination wave does not authorize creating, modifying, or running tests. Use direct evidence and the smallest relevant non-test/static/build checks instead.

## Workspace policy

Agent 1 receives a dedicated writable worktree because it is an autonomous writer while the main checkout must remain a stable coordination/integration base and a safe read-only source for Agent 2.

Agent 2 is read-only and therefore does not receive a branch/worktree. It must not edit, stage, commit, switch branches, create worktrees, or run commands that mutate repository state.

No second writer may use Agent 1's worktree. The planner integrates Agent 1 centrally after its finish report and fresh Git inspection.

## Integration policy

The planner integrates Agent 1's branch into `main` after:

1. verifying its reported commit(s) and clean worktree;
2. inspecting the complete M1 diff against the frozen design and mission;
3. confirming the M1 exit criteria with focused direct/non-test evidence;
4. reconciling Agent 2's M2 report with the landed workspace/state interfaces.

Agent 1 must not merge/rebase/reset `main`. Agent 2 performs no Git mutations.

After M1 integration, the planner updates this coordination map and materializes the executable M2 mission only from the newly verified frontier.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user explicitly requested persistent execution and intends to steer long-running work.

- Agent 1: persistent loop required. Use bounded commands normally; if a server/watch/smoke process must stay alive, own it in Terminal and observe it with event waits. Checkpoint only meaningful milestones such as an M1 candidate implementation/commit, a real blocker, or steering that changes scope.
- Agent 2: persistent loop required for continuity/steering, but no wait or process should be manufactured. It should inspect the stable repository, produce the bounded M2 report, and stop when its read-only success conditions are met.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1

M1 changes executable backend/frontend/launcher behavior. Verification should prove the user-visible M1 contracts without adding/running tests:

- workspace mode/identity comes from the backend, not port inference;
- clean `local_market` state is presented honestly;
- `sample` state is persistently identifiable on primary product surfaces;
- launcher distinguishes intended QAP workspace, other QAP workspace, unrelated/partial port occupancy, and clean not-running state;
- relevant static/type/build/shell/OpenAPI checks are run only where needed to validate changed contracts.

### Agent 2

Read-only mission. Verification is repository evidence: exact owner/caller references, existing reusable primitives, concrete dependency/collision findings, and a bounded recommendation for M2. No tests or mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — current** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrates before executable M2 |
| **2** | **Write M2:** current market directory + explicit asset admission | **Read-only M3 reconnaissance** | sequential dependency; reconcile actual M1/M2 state owners before M3 |
| **3** | **Write M3 foundation:** immutable dataset-generation/provenance contract + shared acquisition seam + scan-refresh-freeze ownership repair | **Read-only venue/acquisition reconnaissance** focused on independently implementable Binance/Gate paths | shared M3 seam must land before two writers fan out |
| **4** | **Write M3 Binance path** in isolated worktree | **Write M3 Gate path** in isolated worktree | real parallel fan-out only if Wave-3 seam proves venue write ownership disjoint; integrate centrally |
| **5** | **Write M4:** current-approved research policy + backend readiness/safe cutoff | **Read-only M5 Research/IA reconnaissance** | M5 stays blocked until M1-M4 truth is integrated |
| **6** | **Write M5:** self-explanatory Research experience + primary IA | **Read-only M6 longitudinal-idea reconnaissance** | frontend product composition may begin only after M4 |
| **7** | **Write M6:** longitudinal Research Idea + all-survivor follow-up | **Read-only M7 collector reconnaissance** | keeps prospective semantics owned by existing QAP/scanner contracts |
| **8** | **Write M7:** persistent current-evidence collector/qualification bridge | **Read-only M8 convergence reconnaissance** | SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity composition | **Write M8-B:** Portfolio presentation convergence | parallel only after a tiny shared shell/navigation seam is verified stable; otherwise serialize |
| **10** | **M9 process-lifecycle/packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | M9 may conclude no desktop shell is needed; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M2 executable market directory + explicit asset admission — blocked by integrated M1 and Wave-1 replan.
- M3 historical market-data acquisition/provenance/generations — blocked by M2.
- M4 current-approved policy/readiness/safe cutoff — blocked by M2/M3.
- M5 primary React IA restructuring — blocked by M1-M4; do not start early.
- M6-M10 detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
