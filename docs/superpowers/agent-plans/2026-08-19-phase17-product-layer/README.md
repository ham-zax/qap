# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** one writable M5 Research/funnel/primary-IA mission plus one concurrent read-only M6 longitudinal/evidence-layer reconnaissance mission
**Current wave:** 6

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M5 self-explanatory Research + truthful funnel + primary IA | mixed executable | ready after Wave-6 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m5-research-experience` on branch `phase17-m5-research-experience` | sole M5 writer; backend scan-read and frontend IA changes are causally coupled | M4 integrated through `c3c81ca` |
| Agent 2 — M6 longitudinal Research Idea / evidence-layer reconnaissance | read-only | ready | immediately | `/home/hamza/repo/qap` read-only | no writable worktree; executable M6 remains blocked by integrated M5 presentation/read contract | M4 integrated + M5 mission contract |

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
        v
M4 current-approved claim/readiness/safe cutoff (complete through c3c81ca)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: M5 writer                    Agent 2: M6 read-only reconnaissance
Research IA / truthful funnel         longitudinal evidence layers / follow-up seam
claim-aware reads / next actions
        |                                      |
        +------------------+-------------------+
                           |
                           v
                 planner verifies/integrates M5
                           |
                           v
                  M6 executable Research Idea
```

M4 is complete and integrated through `c3c81ca`. Product research now has a separately-versioned current-approved/current-survivor retrospective claim, backend-owned readiness and safe cutoff, direct-market readiness, exact M2/M3 binding, stale-launch rejection, and Product-default initiation without user-entered `as_of`, while strict historical PIT remains unchanged. M5 reconnaissance is complete and identifies the current writer frontier: compose the Product Research experience, add backend-composed completed-stage counts/claim-aware scan reads where needed, and move the visible primary IA to `Home | Research | Portfolios | History`. In parallel, M6 may be investigated read-only, especially the Product-scan all-survivor follow-up compatibility seam.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 adaptive historical prepare/refresh + provenance/generations | complete / integrated at `c1d97eb` | — |
| M4 current-approved policy + explainable readiness/safe cutoff | complete / integrated through `c3c81ca` | — |
| M5 self-explanatory Research + truthful discovery funnel/primary IA | reconnaissance complete; executable work ready | Agent 1 writer |
| M6 longitudinal Research Idea + evidence-layer semantics | executable work blocked by M5; reconnaissance ready | Agent 2 read-only |
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

Agent 1 is the sole writable autonomous process for M5 in `/home/hamza/repo/qap/.worktrees/phase17-m5-research-experience`. Agent 2 remains read-only on stable `main` for M6 reconnaissance and must not edit, stage, commit, switch branches, create worktrees, or run mutating Product/API commands.

Former M1-M4 worktrees are historical integrated milestone state and must not be reused as concurrent writers for Wave 6.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, the final adaptive Product orchestration/exit at `c1d97eb`, and M4 at `d49e597` plus planner review closure `c3c81ca`.

The planner integrates Agent 1's M5 branch only after verifying M4 remains the sole readiness/safe-cutoff authority, completed stage counts are backend-composed from immutable scanner artifacts, Product scans are claim-aware, strict PIT remains available under Advanced Research, primary navigation matches the frozen IA, and no fake progress/ETA or frontend scientific inference is introduced. Agent 2's M6 reconnaissance is advisory planning evidence and does not unlock executable M6 until M5 is integrated.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M5 writer: persistent loop required; use Terminal + event wait only for a genuinely persistent build/browser process.
- Agent 2 M6 read-only reconnaissance: persistent loop for continuity only; do not manufacture waits/processes.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M5 Research/funnel/primary IA

Prove the normal Product flow consumes M4 readiness/launch truth, uses one timeframe without user-entered `as_of`, exposes backend-composed completed research-stage counts, renders current-approved versus PIT claims truthfully, and presents `Home | Research | Portfolios | History` without deleting specialist routes. Running state must use only authoritative operation lifecycle. Do not create/run tests unless separately authorized.

### Agent 2 — M6 read-only reconnaissance

Map the exact historical replay -> all-survivor freeze -> forward checkpoint -> current-evidence readiness -> qualification chain, determine Product current-approved scan compatibility, preserve evidence-layer semantics, and define the smallest longitudinal Research Idea read/composition seam. No tests/builds/mutations.

## Future / blocked work

The whole Phase-17 implementation is decomposed at low resolution below. Detailed mission files are intentionally materialized only when each wave reaches the verified frontier.

| Planned wave | Agent 1 | Agent 2 | Execution shape / unlock |
|---|---|---|---|
| **1 — complete** | **Write M1:** workspace identity, zero-state, launcher/UI contract | **Read-only M2 reconnaissance** | M1 integrated at `461a33c`; M2 reconnaissance complete |
| **2 — complete** | **Read-only M3 reconnaissance** | **Write M2:** current market directory + explicit asset admission | M2 integrated at `8e45c36`; M3 reconnaissance complete and found a foundation-then-fan-out seam |
| **3 — complete** | **Write M3 foundation:** immutable dataset-generation/provenance contract + shared publication/read seam + scan-refresh-freeze ownership repair | **Read-only M4 reconnaissance:** current-approved policy/readiness/safe cutoff | foundation integrated at `1a476db`; M4 reconnaissance complete |
| **4 — complete** | **Write M3 Binance path** in isolated worktree | **Write M3 Gate path** in isolated worktree | both venue paths integrated without shared-contract conflict |
| **4b — complete** | **Write M3 combined Product orchestration/exit:** gap-aware coverage reuse + measured request pressure + both venues | **Read-only combined M3 integration/exit cross-check** | M3 integrated at `c1d97eb` |
| **5 — complete** | **Write M4:** current-approved policy + explainable backend readiness/safe cutoff | **Read-only M5 Research/funnel/IA reconnaissance** | M4 integrated through `c3c81ca`; M5 reconnaissance complete |
| **6 — current** | **Write M5:** self-explanatory Research + truthful discovery funnel + backend-owned next actions + primary IA | **Read-only M6 evidence-layer/longitudinal reconnaissance** | frontend product composition begins from integrated M4 truth |
| **7** | **Write M6:** longitudinal Research Idea + evidence-layer semantics + all-survivor follow-up | **Read-only M7 collector ownership reconnaissance** | later/negative evidence must identify its layer without rewriting earlier claims |
| **8** | **Write M7:** ownership-safe persistent current-evidence collector/qualification bridge | **Read-only M8 objective-aware convergence reconnaissance** | focused hidden-state audit; SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Portfolio presentation convergence | preserve current HODL/control/economic authority; parallel only after stable shared shell seam |
| **10** | **M9 process/state ownership + packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | packaging follows explicit ownership/recovery analysis; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M5 primary Research/funnel/IA implementation — current writable frontier.
- M6 longitudinal Research Idea implementation — blocked by integrated M5; read-only reconnaissance is current.
- M7-M10 remain blocked by the sequential Product lifecycle chain; detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
- `2026-08-19` — M2 `8e45c36` verified and fast-forward integrated into `main`. M3 reconnaissance traced the freeze defect to loss of the historical physical `relative_path`, confirmed existing native required intervals, and recommended a shared generation/provenance foundation followed by disjoint Binance/Gate writers. Wave 3 materialized with Agent 1 on the M3 foundation and Agent 2 on read-only M4 reconnaissance.

- `2026-08-19` — M3 shared foundation `1a476db` verified and fast-forward integrated. M4 reconnaissance completed the separate current-approved policy/readiness design. Wave 4 materialized as parallel Binance/Gate historical-acquisition writers on the frozen shared generation/provenance seam; full M3 still requires central combined orchestration/exit verification after both return.
- `2026-08-19` — Binance `f1fab24` and Gate `30297cd` returned clean with disjoint venue-only diffs and no shared-contract change; both were integrated on main. Wave 4b materialized with Agent 1 owning the bounded combined Product orchestration/exit pass and Agent 2 performing a read-only M3 exit/M4-handoff cross-check.
- `2026-08-19` — `tradingview_ratio` legacy-salvage report reviewed and selectively adopted as a Phase-17 planning amendment. M3 gains gap-aware coverage reuse/request-pressure evaluation; M4-M10 gain explainable readiness, truthful funnel/next-action UX, evidence-layer semantics, focused state-ownership audits, objective-aware History/Portfolio presentation, and stronger comprehension gates. Legacy runtime architecture remains rejected.
- `2026-08-19` — M3 adaptive Product orchestration completed and integrated at `c1d97eb`. Direct deterministic evidence proved zero network calls on repeat prepare, one-hour tail-only refresh with immutable parent lineage, failure-state retention, truthful workspace maintenance state, and a bounded real Binance+Gate Short-horizon smoke. Wave 5 materialized with Agent 1 writing M4 and Agent 2 performing read-only M5 reconnaissance.
- `2026-08-19` — M4 `d49e597` returned complete. Planner review found one reachable Product replay-recovery binding seam and closed it at `c3c81ca` without changing strict PIT behavior; M4 was then fast-forward integrated. M5 reconnaissance confirmed that `candidate_count` is rule/trial rows rather than relationships and recommended backend-composed completed stage counts, claim-aware reads, a normal one-timeframe Product flow, and `Home | Research | Portfolios | History`. Wave 6 materialized with Agent 1 writing M5 and Agent 2 on read-only M6 longitudinal/follow-up reconnaissance.
