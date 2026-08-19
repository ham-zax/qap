# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** one writable M4 current-approved/readiness mission plus one concurrent read-only M5 Research/funnel reconnaissance mission
**Current wave:** 5

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M4 current-approved policy + explainable readiness/safe cutoff | mixed executable | ready after Wave-5 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m4-current-approved` on branch `phase17-m4-current-approved` | sole M4 writer; isolates scanner/Product/API contract work from the read-only M5 investigation | M3 complete at `c1d97eb` |
| Agent 2 — M5 Research experience / truthful funnel reconnaissance | read-only | ready | immediately | `/home/hamza/repo/qap` read-only | no writable worktree; M5 executable work remains blocked by integrated M4 truth | M3 complete + M4 mission contract |

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
M3 Binance + Gate + Product adaptive orchestration (complete at c1d97eb)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: M4 writer                    Agent 2: M5 read-only reconnaissance
current-approved policy               Research IA / truthful funnel / next actions
+ readiness + safe cutoff
        |
        +------------------+-------------------+
                           |
                           v
                 planner verifies/integrates M4
                           |
                           v
                  M5 executable Product UI
```

M3 is complete and integrated at `c1d97eb`: combined Product preparation/refresh now composes M2 scope, Scanner-V1 timeframe requirements, Binance/Gate acquisition, immutable generation publication, current-coverage reuse, bounded request pressure, and truthful Product maintenance state. M4 reconnaissance is already complete, so executable M4 is the current writer frontier. In parallel, M5 may be investigated read-only so the Research/funnel/IA implementation can start immediately after M4 integration.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 adaptive historical prepare/refresh + provenance/generations | complete / integrated at `c1d97eb` | — |
| M4 current-approved policy + explainable readiness/safe cutoff | reconnaissance complete; executable work ready | Agent 1 writer |
| M5 self-explanatory Research + truthful discovery funnel/primary IA | executable work blocked by M4; reconnaissance ready | Agent 2 read-only |
| M6 longitudinal Research Idea + evidence-layer semantics | blocked by M5 | unassigned |
| M7 ownership-safe persistent current-evidence collector | blocked by M6 | unassigned |
| M8 objective-aware Portfolios + History + utility Activity | blocked | unassigned |
| M9 process/state ownership + packaging decision | blocked | unassigned |
| M10 representative-user comprehension/authority closure | final acceptance / blocked | unassigned |

## Shared contracts

- Phase 17 changes Product operation, not QAP scientific/economic authority.
- Phase-12 live-capital authority remains `NO-GO`.
- The strict historical point-in-time scanner policy remains intact. The separately-versioned current-approved retrospective claim belongs to M4, not M1/M2.
- Asset-level admission remains explicit operator authority; exchange listing must never imply approval to own.
- Negative, invalid, incomplete, unavailable, and rejected research evidence remains first-class.
- The existing seven-command research mutation vocabulary remains protected; Product maintenance is a separate bounded owner.
- CCXT is not required for Product V1. Existing Binance/Gate public adapters are preferred until a concrete insufficiency is demonstrated.
- Legacy `tradingview_ratio` is conceptual evidence only: no monolithic fetcher/cache owner, global mutable API guardian, synthetic execution, presenter-derived verdict authority, or legacy eligibility thresholds may be ported into Phase 17.
- Acquisition availability/earliest history is not strict historical PIT eligibility evidence.
- Tests are opt-in. This coordination wave does not authorize creating, modifying, or running tests. Use direct evidence and the smallest relevant non-test/static/build checks instead.

## Workspace policy

Agent 1 is the sole writable autonomous process for M4 in `/home/hamza/repo/qap/.worktrees/phase17-m4-current-approved`. Agent 2 remains read-only on stable `main` for M5 reconnaissance and must not edit, stage, commit, switch branches, create worktrees, or run mutating Product/API commands.

Former M1/M2/M3 worktrees are historical integrated milestone state and must not be reused as concurrent writers for Wave 5.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, and the final adaptive Product orchestration/exit is integrated at `c1d97eb`.

The planner integrates Agent 1's M4 branch only after verifying strict-PIT preservation, separate current-approved claim identity, backend readiness/safe cutoff, stale-binding protection, and synchronized public contracts. Agent 2's M5 reconnaissance is advisory planning evidence and does not unlock M5 executable work until M4 is integrated.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M4 writer: persistent loop required; use Terminal + event wait only for a genuinely persistent verification/process.
- Agent 2 M5 read-only reconnaissance: persistent loop for continuity only; do not manufacture waits/processes.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M4 current-approved/readiness

Prove the existing strict historical PIT scanner remains unchanged while a separately-versioned Product current-approved claim can compose exact M2 scope + M3 generations into explainable readiness, backend-owned safe cutoff, stale-binding protection, and a normal Product research initiation path without user-entered `as_of`. Do not create/run tests unless separately authorized.

### Agent 2 — M5 read-only reconnaissance

Map the current Phase-16 shell, scanner/Product read models, truthful stage counts, progressive-disclosure opportunities, and backend-authorized next actions into a concrete `Home | Research | Portfolios | History` M5 implementation brief. No tests/builds/mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — complete** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrated at `461a33c`; M2 reconnaissance complete |
| **2 — complete** | **Read-only M3 reconnaissance** | **Write M2:** current market directory + explicit asset admission | M2 integrated at `8e45c36`; M3 reconnaissance complete and found a foundation-then-fan-out seam |
| **3 — complete** | **Write M3 foundation:** immutable dataset-generation/provenance contract + shared publication/read seam + scan-refresh-freeze ownership repair | **Read-only M4 reconnaissance:** current-approved policy/readiness/safe cutoff | foundation integrated at `1a476db`; M4 reconnaissance complete |
| **4 — complete** | **Write M3 Binance path** in isolated worktree | **Write M3 Gate path** in isolated worktree | both venue paths integrated without shared-contract conflict |
| **4b — complete** | **Write M3 combined Product orchestration/exit:** gap-aware coverage reuse + measured request pressure + both venues | **Read-only combined M3 integration/exit cross-check** | M3 integrated at `c1d97eb` |
| **5 — current** | **Write M4:** current-approved policy + explainable backend readiness/safe cutoff | **Read-only M5 Research/funnel/IA reconnaissance** | readiness preserves structured reasons and does not import legacy eligibility thresholds |
| **6** | **Write M5:** self-explanatory Research + truthful discovery funnel + backend-owned next actions + primary IA | **Read-only M6 evidence-layer/longitudinal reconnaissance** | frontend product composition begins only after M4 truth is integrated |
| **7** | **Write M6:** longitudinal Research Idea + evidence-layer semantics + all-survivor follow-up | **Read-only M7 collector ownership reconnaissance** | later/negative evidence must identify its layer without rewriting earlier claims |
| **8** | **Write M7:** ownership-safe persistent current-evidence collector/qualification bridge | **Read-only M8 objective-aware convergence reconnaissance** | focused hidden-state audit; SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Portfolio presentation convergence | preserve current HODL/control/economic authority; parallel only after stable shared shell seam |
| **10** | **M9 process/state ownership + packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | packaging follows explicit ownership/recovery analysis; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M4 current-approved policy/readiness/safe cutoff implementation — current writable frontier.
- M5 primary React IA implementation — blocked by integrated M4; read-only reconnaissance is current.
- M6-M10 remain blocked by the sequential Product truth/lifecycle chain; detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
- `2026-08-19` — M2 `8e45c36` verified and fast-forward integrated into `main`. M3 reconnaissance traced the freeze defect to loss of the historical physical `relative_path`, confirmed existing native required intervals, and recommended a shared generation/provenance foundation followed by disjoint Binance/Gate writers. Wave 3 materialized with Agent 1 on the M3 foundation and Agent 2 on read-only M4 reconnaissance.

- `2026-08-19` — M3 shared foundation `1a476db` verified and fast-forward integrated. M4 reconnaissance completed the separate current-approved policy/readiness design. Wave 4 materialized as parallel Binance/Gate historical-acquisition writers on the frozen shared generation/provenance seam; full M3 still requires central combined orchestration/exit verification after both return.
- `2026-08-19` — Binance `f1fab24` and Gate `30297cd` returned clean with disjoint venue-only diffs and no shared-contract change; both were integrated on main. Wave 4b materialized with Agent 1 owning the bounded combined Product orchestration/exit pass and Agent 2 performing a read-only M3 exit/M4-handoff cross-check.
- `2026-08-19` — `tradingview_ratio` legacy-salvage report reviewed and selectively adopted as a Phase-17 planning amendment. M3 gains gap-aware coverage reuse/request-pressure evaluation; M4-M10 gain explainable readiness, truthful funnel/next-action UX, evidence-layer semantics, focused state-ownership audits, objective-aware History/Portfolio presentation, and stronger comprehension gates. Legacy runtime architecture remains rejected.
- `2026-08-19` — M3 adaptive Product orchestration completed and integrated at `c1d97eb`. Direct deterministic evidence proved zero network calls on repeat prepare, one-hour tail-only refresh with immutable parent lineage, failure-state retention, truthful workspace maintenance state, and a bounded real Binance+Gate Short-horizon smoke. Wave 5 materialized with Agent 1 writing M4 and Agent 2 performing read-only M5 reconnaissance.
