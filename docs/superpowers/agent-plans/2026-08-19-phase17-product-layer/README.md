# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** hybrid — one writable current milestone plus one concurrent read-only next-milestone reconnaissance mission; parallel writers only when a verified shared seam makes ownership disjoint
**Current wave:** 2

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 2 — M2 market directory + explicit asset admission | mixed executable | ready | now | `/home/hamza/repo/qap/.worktrees/phase17-m2-universe` on branch `phase17-m2-universe` | sole M2 writer while main stays a stable integration/read-only base | integrated M1 `461a33c` |
| Agent 1 — M3 acquisition/generation reconnaissance | read-only | ready | now | `/home/hamza/repo/qap` read-only | no worktree needed; must not race the M2 writer | none for reconnaissance; executable M3 remains blocked by integrated M2 |

## Dependency map

```text
M0 design freeze (1bb6e78)
        |
        v
M1 workspace identity / zero-state (461a33c, integrated)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 2: implement M2                 Agent 1: read-only M3 reconnaissance
directory / identity / admission      acquisition / generations / freeze seam
        |                                      |
        +------------------+-------------------+
                           v
                planner integrates M2 + replans
                           |
                           v
                M3 executable implementation
                           |
                           v
                M4 current-approved readiness
                           |
                           v
                M5+ Product UI/lifecycle work
```

M1 is integrated. M2 executable work is now the sole writable frontier. M3 implementation must not start until M2 is integrated and the planner reconciles Agent 1's reconnaissance with the actual landed M2 scope/provenance interface.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | ready / current writable frontier | Agent 2 |
| M3 historical acquisition + provenance/generations | reconnaissance active; implementation blocked by M2 | Agent 1 recon |
| M4 current-approved policy + readiness/safe cutoff | blocked by M2-M3 | unassigned |
| M5 self-explanatory Research + primary IA | blocked by M4 | unassigned |
| M6 longitudinal Research Idea | blocked by M5 | unassigned |
| M7 persistent current-evidence collector | blocked by M6 | unassigned |
| M8 Portfolios + History + utility Activity | blocked | unassigned |
| M9 packaging/process-lifecycle decision | blocked | unassigned |
| M10 representative-user comprehension closure | final acceptance / blocked | unassigned |

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

Agent 2 receives a dedicated writable M2 worktree because it is the sole autonomous writer while the main checkout remains a stable coordination/integration base and a safe read-only source for Agent 1.

Agent 1 is read-only for M3 reconnaissance and therefore does not receive a new worktree. It must not edit, stage, commit, switch branches, create worktrees, or run commands that mutate repository state.

The former `phase17-m1-workspace` worktree/branch is historical M1 state after integration and must not be used as a second writer for Wave 2.

## Integration policy

M1 was fast-forward integrated into `main` at `461a33c` after fresh branch/status/diff inspection and reconciliation with the M2 reconnaissance.

The planner integrates Agent 2's M2 branch into `main` only after:

1. verifying the reported commit(s) and clean M2 worktree;
2. inspecting the complete M2 diff against the frozen design and M2 mission;
3. confirming the M2 exit criteria with focused direct/non-test evidence;
4. reconciling Agent 1's M3 reconnaissance with the actual landed M2 scope/provenance interface.

Agent 2 must not merge/rebase/reset `main`. Agent 1 performs no Git mutations during M3 reconnaissance.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user explicitly requested persistent execution and intends to steer long-running work.

- Agent 2 M2 writer: persistent loop required. Use bounded commands normally; if a server/watch/smoke process must stay alive, own it in Terminal and observe it with event waits. Checkpoint only meaningful implementation/commit/blocker/steering transitions.
- Agent 1 M3 reconnaissance: persistent loop required for continuity/steering, but no wait or process should be manufactured. Produce the bounded read-only report and stop when its success conditions are met.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 2

M2 changes executable Product directory/admission/backend/frontend behavior. Verification should prove current-market normalization, fail-closed identity, persistent explicit admission, directory-refresh/admission independence, M1 compatibility, public contract synchronization, and the asset-oriented Research Universe without adding/running tests.

### Agent 1

Read-only M3 mission. Verification is repository evidence: exact owner/caller references for historical acquisition, immutable generation/provenance, direct-market preparation, scan-refresh-freeze lineage, and a bounded recommendation for M3 writer topology. No tests or mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — complete** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrated at `461a33c`; M2 reconnaissance complete |
| **2 — current** | **Read-only M3 reconnaissance** | **Write M2:** current market directory + explicit asset admission | M2 is the sole writable frontier; reconcile M3 report after M2 lands |
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

- M3 historical market-data acquisition/provenance/generations — blocked by integrated M2; reconnaissance may proceed now.
- M4 current-approved policy/readiness/safe cutoff — blocked by M2/M3.
- M5 primary React IA restructuring — blocked by M1-M4; do not start early.
- M6-M10 detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
