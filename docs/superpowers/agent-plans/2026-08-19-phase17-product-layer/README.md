# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** one writable M7 persistent current-evidence collector/qualification-bridge mission plus one concurrent read-only M8 Portfolios/History/Activity reconnaissance mission
**Current wave:** 8

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M7 persistent current public-evidence collector + Product qualification bridge | mixed executable | ready after Wave-8 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m7-current-evidence` on branch `phase17-m7-current-evidence` | sole M7 writer; SQLite schema, scheduler, collector lease/process, evidence reader, launcher lifecycle, Product qualification wrapper, and Research Idea collection state share one contract | M6 integrated at `c1db648` |
| Agent 2 — M8 Portfolios / History / Activity convergence reconnaissance | read-only | ready | immediately | `/home/hamza/repo/qap` read-only | no writable worktree; M8 executable topology depends on Product-basket compatibility and old-scan/current-catalog coupling findings | M6 integrated + frozen M7 mission contract |

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
        v
M5 Research / truthful funnel / primary IA (complete at 6b40028)
        |
        v
M6 longitudinal Research Idea / all-survivor follow-up (complete at c1db648)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: M7 writer                    Agent 2: M8 read-only reconnaissance
SQLite + collector process            Product basket compatibility / History
slot/restart + qualification bridge   old-scan catalog coupling / Activity
        |                                      |
        +------------------+-------------------+
                           |
                           v
                 planner verifies/integrates M7
                           |
                           v
                  M8 executable convergence
```

M6 is complete and integrated at `c1db648`. Product Research Ideas now compose immutable historical, later prospective, reselection, and persisted current-capacity evidence, and current-approved Product generations can start backend-stamped all-survivor follow-up through the existing `FREEZE_FORWARD_COHORT`/`PROSPECTIVE_V1` path. M7 reconnaissance is complete and freezes the next boundary: one Local Market collector process, bounded Product SQLite operational state, exact scheduled-slot accounting, restart-safe missed-slot semantics, frozen-lineage instrument resolution, and reuse of existing capture-readiness/qualification authorities. In parallel, M8 may be investigated read-only, including Product-basket compatibility and the deferred old-scan/current-catalog basket coupling.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 adaptive historical prepare/refresh + provenance/generations | complete / integrated at `c1d97eb` | — |
| M4 current-approved policy + explainable readiness/safe cutoff | complete / integrated through `c3c81ca` | — |
| M5 self-explanatory Research + truthful discovery funnel/primary IA | complete / integrated at `6b40028` | — |
| M6 longitudinal Research Idea + evidence-layer semantics | complete / integrated at `c1db648` | — |
| M7 ownership-safe persistent current-evidence collector | reconnaissance complete; executable work ready | Agent 1 writer |
| M8 objective-aware Portfolios + History + utility Activity | executable work blocked by M7; reconnaissance ready | Agent 2 read-only |
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

Agent 1 is the sole writable autonomous process for M7 in `/home/hamza/repo/qap/.worktrees/phase17-m7-current-evidence`. Agent 2 remains read-only on stable `main` for M8 reconnaissance and must not edit, stage, commit, switch branches, create worktrees, or run mutating Product/API commands.

Former M1-M6 worktrees are historical integrated milestone state and must not be reused as concurrent writers for Wave 8.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, the final adaptive Product orchestration/exit at `c1d97eb`, M4 at `d49e597` plus planner review closure `c3c81ca`, M5 at `6b40028`, and M6 at `c1db648`.

The planner integrates Agent 1's M7 branch only after verifying SQLite remains operational rather than scientific authority, scheduled-slot uniqueness and restart misses are exact, frozen instruments resolve from immutable M6 lineage, collector process ownership is restart-safe, existing capture-readiness/qualification policies remain authoritative, and no Product basket compatibility or M9 packaging work is absorbed. Agent 2's M8 reconnaissance is advisory planning evidence and does not unlock executable M8 until M7 is integrated.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M7 writer: persistent loop required; use Terminal + event wait for the genuinely persistent collector/process verification where appropriate.
- Agent 2 M8 read-only reconnaissance: persistent loop for continuity only; do not manufacture waits/processes.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M7 persistent current-evidence collector

Prove a real Local Market workspace can accumulate the existing 14-day public-evidence contract through exact scheduled slots, survive restart without fabricating observations, preserve frozen-lineage instrument identity, feed the existing readiness/qualification authorities, and expose Product collection/amount-assessment state without changing scientific policy. Do not create/run tests unless separately authorized.

### Agent 2 — M8 read-only reconnaissance

Determine the exact Product current-approved basket compatibility boundary, the deferred old-scan/current-catalog basket coupling, the smallest objective-aware Portfolio/History read/presentation convergence, Activity utility role, and whether M8 can safely fan out after a shared compatibility seam. No tests/builds/mutations.

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
| **6 — complete** | **Write M5:** self-explanatory Research + truthful discovery funnel + backend-owned next actions + primary IA | **Read-only M6 evidence-layer/longitudinal reconnaissance** | M5 integrated at `6b40028`; M6 reconnaissance found Product-v1 prospective compatibility already exists |
| **7 — complete** | **Write M6:** longitudinal Research Idea + evidence-layer semantics + all-survivor follow-up | **Read-only M7 collector ownership reconnaissance** | M6 integrated at `c1db648`; M7 state/process contract frozen |
| **8 — current** | **Write M7:** ownership-safe persistent current-evidence collector/qualification bridge | **Read-only M8 objective-aware convergence reconnaissance** | focused hidden-state audit; SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Portfolio presentation convergence | preserve current HODL/control/economic authority; parallel only after stable shared shell seam |
| **10** | **M9 process/state ownership + packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | packaging follows explicit ownership/recovery analysis; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M7 persistent collector/qualification bridge — current writable frontier.
- M8 Portfolios/History/Activity implementation — blocked by integrated M7; read-only reconnaissance is current.
- M9-M10 remain blocked by the sequential Product lifecycle chain; detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

## Status log

- `2026-08-19 11:24 +05:30` — Wave 1 materialized from Phase-17 M0 design freeze. One M1 writer plus one concurrent read-only M2 reconnaissance mission chosen because M2 executable state ownership depends on M1.
- `2026-08-19` — M1 `461a33c` verified and fast-forward integrated into `main`. M2 reconnaissance reported that directory/identity/admission/API/UI are one causally coupled writer mission; CCXT and SQLite-for-admission are not justified. Wave 2 materialized with Agent 2 as the M2 writer and Agent 1 on read-only M3 reconnaissance.
- `2026-08-19` — M2 `8e45c36` verified and fast-forward integrated into `main`. M3 reconnaissance traced the freeze defect to loss of the historical physical `relative_path`, confirmed existing native required intervals, and recommended a shared generation/provenance foundation followed by disjoint Binance/Gate writers. Wave 3 materialized with Agent 1 on the M3 foundation and Agent 2 on read-only M4 reconnaissance.

- `2026-08-19` — M3 shared foundation `1a476db` verified and fast-forward integrated. M4 reconnaissance completed the separate current-approved policy/readiness design. Wave 4 materialized as parallel Binance/Gate historical-acquisition writers on the frozen shared generation/provenance seam; full M3 still requires central combined orchestration/exit verification after both return.
- `2026-08-19` — Binance `f1fab24` and Gate `30297cd` returned clean with disjoint venue-only diffs and no shared-contract change; both were integrated on main. Wave 4b materialized with Agent 1 owning the bounded combined Product orchestration/exit pass and Agent 2 performing a read-only M3 exit/M4-handoff cross-check.
- `2026-08-19` — `tradingview_ratio` legacy-salvage report reviewed and selectively adopted as a Phase-17 planning amendment. M3 gains gap-aware coverage reuse/request-pressure evaluation; M4-M10 gain explainable readiness, truthful funnel/next-action UX, evidence-layer semantics, focused state-ownership audits, objective-aware History/Portfolio presentation, and stronger comprehension gates. Legacy runtime architecture remains rejected.
- `2026-08-19` — M3 adaptive Product orchestration completed and integrated at `c1d97eb`. Direct deterministic evidence proved zero network calls on repeat prepare, one-hour tail-only refresh with immutable parent lineage, failure-state retention, truthful workspace maintenance state, and a bounded real Binance+Gate Short-horizon smoke. Wave 5 materialized with Agent 1 writing M4 and Agent 2 performing read-only M5 reconnaissance.
- `2026-08-19` — M4 `d49e597` returned complete. Planner review found one reachable Product replay-recovery binding seam and closed it at `c3c81ca` without changing strict PIT behavior; M4 was then fast-forward integrated. M5 reconnaissance confirmed that `candidate_count` is rule/trial rows rather than relationships and recommended backend-composed completed stage counts, claim-aware reads, a normal one-timeframe Product flow, and `Home | Research | Portfolios | History`. Wave 6 materialized with Agent 1 writing M5 and Agent 2 on read-only M6 longitudinal/follow-up reconnaissance.
- `2026-08-19` — M5 `6b40028` returned complete and was verified/fast-forward integrated. It delivers the frozen primary IA, M4-driven Product Research, backend-composed completed-stage counts, claim-aware Product/PIT reads, truthful negative/unavailable states, and Advanced strict PIT preservation. M6 reconnaissance established that Product-v1 survivors already work with the existing prospective/qualification scientific contracts; the missing seams are reselection-aware longitudinal reads and a Product generation-wide follow-up wrapper. Wave 7 materialized with Agent 1 writing M6 and Agent 2 on read-only M7 collector/state-ownership reconnaissance.
- `2026-08-19` — M6 `c1db648` returned complete and was verified/fast-forward integrated. It adds a pure longitudinal Research Idea composition, reselection-aware active-freeze lineage, backend-owned evidence-layer states, and a Product generation-wide follow-up wrapper reusing the existing freeze/prospective scientific path. M7 reconnaissance froze one-process/SQLite/slot/restart/frozen-instrument ownership and reuse of existing readiness/qualification authority. Wave 8 materialized with Agent 1 writing M7 and Agent 2 on read-only M8 Portfolios/History/Activity reconnaissance.
