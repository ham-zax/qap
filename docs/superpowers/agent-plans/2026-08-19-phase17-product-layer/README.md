# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** hybrid — one writable current milestone plus one concurrent read-only next-milestone reconnaissance mission; parallel writers only when a verified shared seam makes ownership disjoint
**Current wave:** 3

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M3 shared generation/provenance foundation | executable | ready | now | `/home/hamza/repo/qap/.worktrees/phase17-m3-foundation` on branch `phase17-m3-foundation` | sole shared-foundation writer while main stays stable for Agent 2 reconnaissance | integrated M2 `8e45c36` |
| Agent 2 — M4 policy/readiness reconnaissance | read-only | ready | now | `/home/hamza/repo/qap` read-only | no writable worktree needed; must not race Agent 1's M3 foundation | none for reconnaissance; executable M4 remains blocked by complete M3 |

## Dependency map

```text
M0 design freeze (1bb6e78)
        |
        v
M1 workspace identity / zero-state (461a33c, integrated)
        |
        v
M2 directory / identity / admission (8e45c36, integrated)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: implement M3 foundation      Agent 2: read-only M4 reconnaissance
generation/provenance/publisher       policy / readiness / safe-cutoff seam
freeze-lineage repair                           |
        |                                       |
        +-------------------+-------------------+
                            v
               planner integrates foundation + replans
                            |
                            v
           M3 Binance + Gate venue acquisition fan-out
                            |
                            v
               planner integrates complete M3
                            |
                            v
                M4 current-approved readiness
                           |
                           v
                M5+ Product UI/lifecycle work
```

M1 and M2 are integrated. Agent 1's M3 reconnaissance is complete and established a safe foundation-then-venue-fan-out topology. The shared M3 foundation is now the sole writable frontier. Venue-specific M3 writers must not start until that shared seam is integrated. M4 implementation remains blocked until complete M3 lands, but read-only M4 reconnaissance may proceed now against integrated M2 and the frozen expected M3 handoff.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 historical acquisition + provenance/generations | shared foundation is current writable frontier; venue fan-out follows foundation integration | Agent 1 foundation now |
| M4 current-approved policy + readiness/safe cutoff | reconnaissance ready; implementation blocked by complete M3 | Agent 2 recon now |
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

Agent 1 receives a dedicated writable M3-foundation worktree because it is the sole autonomous writer while the main checkout remains a stable coordination/integration base and a safe read-only source for Agent 2.

Agent 2 is read-only for M4 reconnaissance and therefore does not receive a new worktree. It must not edit, stage, commit, switch branches, create worktrees, or run commands that mutate repository state.

The former `phase17-m1-workspace` and `phase17-m2-universe` worktrees/branches are historical integrated milestone state and must not be reused as concurrent writers for Wave 3.

## Integration policy

M1 was fast-forward integrated into `main` at `461a33c`. M2 was fast-forward integrated into `main` at `8e45c36` after verifying the clean branch, complete scoped diff, fail-closed identity/admission contract, and M3 `ProductResearchScope` handoff.

The planner integrates Agent 1's M3-foundation branch into `main` only after:

1. verifying the reported commit(s) and clean worktree;
2. inspecting the complete shared-foundation diff against the frozen M3 mission;
3. confirming immutable generation/provenance/current-pointer semantics and the narrow historical-freeze lineage repair with focused non-test evidence;
4. checking that the shared acquisition-output seam is stable enough for disjoint Binance/Gate venue writers;
5. reconciling Agent 2's M4 reconnaissance with the actual landed generation/read interface.

Agent 1 must not merge/rebase/reset `main`. Agent 2 performs no Git mutations during M4 reconnaissance.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user explicitly requested persistent execution and intends to steer long-running work.

- Agent 1 M3-foundation writer: persistent loop required. Use bounded commands normally; if a real persistent process is needed, own it in Terminal and observe it with event waits. Checkpoint only meaningful implementation/commit/blocker/steering transitions.
- Agent 2 M4 reconnaissance: persistent loop required for continuity/steering, but no wait or process should be manufactured. Produce the bounded read-only report and stop when its success conditions are met.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1

M3 foundation changes executable Product/data/scanner lineage behavior. Verification should prove create-only immutable generations, exact provenance, atomic logical-pointer publication, bounded generation coverage/read state, and historical-freeze lookup of the originally sealed physical source. Testing remains opt-in; use focused runtime/static evidence rather than inventing tests.

### Agent 2

Read-only M4 mission. Verification is repository evidence: exact protocol/universe/preparation/scan-initiation owners, the new policy identity boundary, readiness/safe-cutoff inputs, M4 -> M5 DTO needs, and a bounded writer-topology recommendation. No tests or mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — complete** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrated at `461a33c`; M2 reconnaissance complete |
| **2 — complete** | **Read-only M3 reconnaissance** | **Write M2:** current market directory + explicit asset admission | M2 integrated at `8e45c36`; M3 reconnaissance complete and found a foundation-then-fan-out seam |
| **3 — current** | **Write M3 foundation:** immutable dataset-generation/provenance contract + shared publication/read seam + scan-refresh-freeze ownership repair | **Read-only M4 reconnaissance:** current-approved policy/readiness/safe cutoff | shared M3 seam must land before two writers fan out; M4 implementation remains blocked by complete M3 |
| **4** | **Write M3 Binance path** in isolated worktree | **Write M3 Gate path** in isolated worktree | real parallel fan-out only after Wave-3 foundation is verified stable; integrate centrally |
| **5** | **Write M4:** current-approved research policy + backend readiness/safe cutoff | **Read-only M5 Research/IA reconnaissance** | M5 stays blocked until M1-M4 truth is integrated |
| **6** | **Write M5:** self-explanatory Research experience + primary IA | **Read-only M6 longitudinal-idea reconnaissance** | frontend product composition may begin only after M4 |
| **7** | **Write M6:** longitudinal Research Idea + all-survivor follow-up | **Read-only M7 collector reconnaissance** | keeps prospective semantics owned by existing QAP/scanner contracts |
| **8** | **Write M7:** persistent current-evidence collector/qualification bridge | **Read-only M8 convergence reconnaissance** | SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity composition | **Write M8-B:** Portfolio presentation convergence | parallel only after a tiny shared shell/navigation seam is verified stable; otherwise serialize |
| **10** | **M9 process-lifecycle/packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | M9 may conclude no desktop shell is needed; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M3 venue-specific historical acquisition — blocked by integrated shared M3 foundation.
- M4 current-approved policy/readiness/safe cutoff implementation — blocked by complete M3; reconnaissance proceeds in Wave 3.
- M5 primary React IA restructuring — blocked by M1-M4; do not start early.
- M6-M10 detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
- `2026-08-19` — M2 `8e45c36` verified and fast-forward integrated into `main`. M3 reconnaissance traced the freeze defect to loss of the historical physical `relative_path`, confirmed existing native required intervals, and recommended a shared generation/provenance foundation followed by disjoint Binance/Gate writers. Wave 3 materialized with Agent 1 on the M3 foundation and Agent 2 on read-only M4 reconnaissance.
