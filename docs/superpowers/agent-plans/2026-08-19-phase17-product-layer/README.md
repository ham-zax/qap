# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** one writable M6 longitudinal Research Idea mission plus one concurrent read-only M7 collector/state-ownership reconnaissance mission
**Current wave:** 7

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M6 longitudinal Research Idea + evidence-layer semantics + all-survivor follow-up | mixed executable | ready after Wave-7 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m6-research-idea` on branch `phase17-m6-research-idea` | sole M6 writer; reselection-aware backend composition, Product follow-up action, and longitudinal UI are one coupled contract | M5 integrated at `6b40028` |
| Agent 2 — M7 persistent current-evidence collector/state-ownership reconnaissance | read-only | ready | immediately | `/home/hamza/repo/qap` read-only | no writable worktree; executable M7 remains blocked by integrated M6 Research Idea/frozen-lineage handoff | M5 integrated + M6 mission contract |

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
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: M6 writer                    Agent 2: M7 read-only reconnaissance
longitudinal Research Idea            collector ownership / SQLite / scheduler
reselection + all-survivor follow-up  frozen-instrument capture handoff
        |                                      |
        +------------------+-------------------+
                           |
                           v
                 planner verifies/integrates M6
                           |
                           v
                  M7 executable collector
```

M5 is complete and integrated at `6b40028`. The visible primary IA is now `Home | Research | Portfolios | History`; normal Product research consumes M4 readiness/launch truth, completed scanner stages are backend-composed, Product/PIT claims are explicit, and strict historical research remains available under Advanced Research. M6 reconnaissance is also complete and established that current-approved Product scans already satisfy the existing all-survivor prospective scientific contracts. The current writer frontier is therefore Product composition only: reselection-aware longitudinal Research Idea reads, evidence-layer wording, and a backend-stamped generation-wide follow-up action that reuses `FREEZE_FORWARD_COHORT`. In parallel, M7 may be investigated read-only for the persistent 14-day collector/state-ownership boundary.

## Milestone progress

| Milestone | Status | Active owner / next owner |
|---|---|---|
| M0 design freeze | complete | — |
| M1 workspace identity + clean zero-state | complete / integrated at `461a33c` | Agent 1 finished |
| M2 market directory + explicit asset admission | complete / integrated at `8e45c36` | Agent 2 finished |
| M3 adaptive historical prepare/refresh + provenance/generations | complete / integrated at `c1d97eb` | — |
| M4 current-approved policy + explainable readiness/safe cutoff | complete / integrated through `c3c81ca` | — |
| M5 self-explanatory Research + truthful discovery funnel/primary IA | complete / integrated at `6b40028` | — |
| M6 longitudinal Research Idea + evidence-layer semantics | reconnaissance complete; executable work ready | Agent 1 writer |
| M7 ownership-safe persistent current-evidence collector | executable work blocked by M6; reconnaissance ready | Agent 2 read-only |
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

Agent 1 is the sole writable autonomous process for M6 in `/home/hamza/repo/qap/.worktrees/phase17-m6-research-idea`. Agent 2 remains read-only on stable `main` for M7 reconnaissance and must not edit, stage, commit, switch branches, create worktrees, or run mutating Product/API commands.

Former M1-M5 worktrees are historical integrated milestone state and must not be reused as concurrent writers for Wave 7.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, the final adaptive Product orchestration/exit at `c1d97eb`, M4 at `d49e597` plus planner review closure `c3c81ca`, and M5 at `6b40028`.

The planner integrates Agent 1's M6 branch only after verifying historical evidence remains immutable, Product follow-up reuses the existing all-survivor operation/prospective protocol, reselection lineage is represented correctly, evidence-layer states are backend-composed rather than inferred independently in React, and no M7 collector or Product basket compatibility work is absorbed. Agent 2's M7 reconnaissance is advisory planning evidence and does not unlock executable M7 until M6 is integrated.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M6 writer: persistent loop required; use Terminal + event wait only for a genuinely persistent build/browser process.
- Agent 2 M7 read-only reconnaissance: persistent loop for continuity only; do not manufacture waits/processes.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M6 longitudinal Research Idea

Prove a Product historical Research Idea composes immutable historical, prospective, and persisted current-capacity evidence without rewriting earlier claims; resolves both new-freeze and reselection memberships; and starts follow-up through a backend-stamped generation-wide wrapper that reuses `FREEZE_FORWARD_COHORT`. Do not create/run tests unless separately authorized.

### Agent 2 — M7 read-only reconnaissance

Map exact current capture/readiness/qualification owners, the bounded SQLite/state-ownership boundary, scheduled-slot/idempotency/restart semantics, frozen-lineage instrument resolution, and the smallest persistent Product collector process/API handoff. No tests/builds/mutations.

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
| **7 — current** | **Write M6:** longitudinal Research Idea + evidence-layer semantics + all-survivor follow-up | **Read-only M7 collector ownership reconnaissance** | later/negative evidence identifies its layer without rewriting earlier claims; no scientific protocol rewrite |
| **8** | **Write M7:** ownership-safe persistent current-evidence collector/qualification bridge | **Read-only M8 objective-aware convergence reconnaissance** | focused hidden-state audit; SQLite stays bounded to Product operational/collector state |
| **9** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Portfolio presentation convergence | preserve current HODL/control/economic authority; parallel only after stable shared shell seam |
| **10** | **M9 process/state ownership + packaging decision** | **M10 comprehension-study preparation/read-only acceptance support** | packaging follows explicit ownership/recovery analysis; M10 cannot fabricate representative-user evidence |
| **11 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M6 longitudinal Research Idea implementation — current writable frontier.
- M7 persistent collector implementation — blocked by integrated M6; read-only reconnaissance is current.
- M8-M10 remain blocked by the sequential Product lifecycle chain; detailed briefs remain intentionally unmaterialized until their prerequisite contracts are real.

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
