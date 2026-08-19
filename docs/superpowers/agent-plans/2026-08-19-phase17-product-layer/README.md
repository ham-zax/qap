# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** one final writable M3 Product orchestration/exit pass plus one concurrent read-only combined-state cross-check; M4 starts only after M3 exit is verified
**Current wave:** 4b

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M3 combined Product orchestration / exit | mixed executable | ready | now | `/home/hamza/repo/qap/.worktrees/phase17-m3-orchestration` on branch `phase17-m3-orchestration` | sole final M3 writer while main stays stable for Agent 2 cross-check | integrated Binance `f1fab24` + Gate integration on main + Wave-4b coordination base |
| Agent 2 — M3 combined integration / exit cross-check | read-only | ready | now | `/home/hamza/repo/qap` read-only | no writable worktree; must not race Agent 1 | integrated combined M3 venue state |

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
        v
M3 shared generation/provenance foundation (1a476db, integrated)
        |
        v
M3 Binance + Gate venue acquisition (integrated)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: Product orchestration/exit   Agent 2: read-only M3 cross-check
prepare/refresh across both venues    combined owners / exit / M4 handoff
        |                                      |
        +------------------+-------------------+
                           |
                           v
                 planner verifies M3 exit
                           |
                           v
               M4 current-approved readiness
                           |
                           v
                M5+ Product UI/lifecycle work
```

M3 shared foundation, Binance acquisition, and Gate acquisition are integrated. Agent 2's M4 reconnaissance is complete and provides the executable M4 policy/readiness contract, but M4 implementation remains blocked until complete M3. The sole remaining writable M3 work is the bounded Product orchestration/exit pass that connects captured approved scope + Scanner-V1 timeframe requirements to both venue acquirers and the shared immutable publisher through Product prepare/refresh operations.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 historical acquisition + provenance/generations | foundation + Binance + Gate integrated; combined Product orchestration/exit is the only remaining M3 work | Agent 1 writer + Agent 2 read-only cross-check |
| M4 current-approved policy + readiness/safe cutoff | reconnaissance complete; implementation blocked by complete M3 | unassigned until M3 exit |
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

Agent 1 is the sole writable autonomous process for the final M3 pass and receives `/home/hamza/repo/qap/.worktrees/phase17-m3-orchestration`. Agent 2 is read-only on stable `main` and must not edit, stage, commit, switch branches, create worktrees, or run mutating Product/API commands.

The former M1/M2/M3-foundation/Binance/Gate worktrees are historical integrated milestone state and must not be reused as additional writers for Wave 4b.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, and Gate is integrated on combined main after its venue commit `30297cd`. The venue fan-out required no shared-contract changes and produced no file overlap.

The planner integrates Agent 1's final M3 orchestration branch only after verifying the clean branch, the bounded Product operation surface, combined Binance/Gate dispatch, immutable refresh behavior, and M3 exit criteria. Agent 2's read-only cross-check is advisory evidence; it does not replace direct integration verification.

Only after full M3 exit is established may executable M4 start.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M3 orchestration writer: persistent loop required; use Terminal + event wait only for a genuinely persistent Product acquisition smoke/process.
- Agent 2 read-only cross-check: persistent loop for continuity only; do not manufacture waits/processes.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M3 orchestration / exit

Prove a clean explicitly approved Local Market scope can initiate bounded Product preparation/refresh across both integrated venue drivers, publish immutable generations with complete provenance, preserve old generations on refresh, and expose truthful Product maintenance state without implementing M4 readiness. Do not create/run tests unless separately authorized.

### Agent 2 — read-only M3 cross-check

Verify combined owner/caller composition, timeframe/window ownership, logical-ID compatibility, prepare/refresh invariants, exact M3 exit evidence, and M4 handoff completeness. No tests or mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — complete** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrated at `461a33c`; M2 reconnaissance complete |
| **2 — complete** | **Read-only M3 reconnaissance** | **Write M2:** current market directory + explicit asset admission | M2 integrated at `8e45c36`; M3 reconnaissance complete and found a foundation-then-fan-out seam |
| **3 — complete** | **Write M3 foundation:** immutable dataset-generation/provenance contract + shared publication/read seam + scan-refresh-freeze ownership repair | **Read-only M4 reconnaissance:** current-approved policy/readiness/safe cutoff | foundation integrated at `1a476db`; M4 reconnaissance complete |
| **4 — complete** | **Write M3 Binance path** in isolated worktree | **Write M3 Gate path** in isolated worktree | both venue paths integrated without shared-contract conflict |
| **4b — current** | **Write M3 combined Product orchestration/exit pass** | **Read-only combined M3 integration/exit cross-check** | full M3 exit must be proven before M4 |
| **5** | **Write M4:** current-approved research policy + backend readiness/safe cutoff | **Read-only M5 Research/IA reconnaissance** | M5 stays blocked until M1-M4 truth is integrated |
| **6** | **Write M5:** self-explanatory Research experience + primary IA | **Read-only M6 longitudinal-idea reconnaissance** | frontend product composition may begin only after M4 |
| **7** | **Write M6:** longitudinal Research Idea + all-survivor follow-up | **Read-only M7 collector reconnaissance** | keeps prospective semantics owned by existing QAP/scanner contracts |
| **8** | **Write M7:** persistent current-evidence collector/qualification bridge | **Read-only M8 convergence reconnaissance** | SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity composition | **Write M8-B:** Portfolio presentation convergence | parallel only after a tiny shared shell/navigation seam is verified stable; otherwise serialize |
| **10** | **M9 process-lifecycle/packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | M9 may conclude no desktop shell is needed; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M3 combined orchestration/exit pass — current writable frontier.
- M4 current-approved policy/readiness/safe cutoff implementation — reconnaissance complete but executable work remains blocked by full M3.
- M5 primary React IA restructuring — blocked by M1-M4; do not start early.
- M6-M10 detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
- `2026-08-19` — M2 `8e45c36` verified and fast-forward integrated into `main`. M3 reconnaissance traced the freeze defect to loss of the historical physical `relative_path`, confirmed existing native required intervals, and recommended a shared generation/provenance foundation followed by disjoint Binance/Gate writers. Wave 3 materialized with Agent 1 on the M3 foundation and Agent 2 on read-only M4 reconnaissance.

- `2026-08-19` — M3 shared foundation `1a476db` verified and fast-forward integrated. M4 reconnaissance completed the separate current-approved policy/readiness design. Wave 4 materialized as parallel Binance/Gate historical-acquisition writers on the frozen shared generation/provenance seam; full M3 still requires central combined orchestration/exit verification after both return.
- `2026-08-19` — Binance `f1fab24` and Gate `30297cd` returned clean with disjoint venue-only diffs and no shared-contract change; both were integrated on main. Wave 4b materialized with Agent 1 owning the bounded combined Product orchestration/exit pass and Agent 2 performing a read-only M3 exit/M4-handoff cross-check.
