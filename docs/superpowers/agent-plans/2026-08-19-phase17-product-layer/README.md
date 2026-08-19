# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** two genuinely parallel M8 presentation writers on the now-stable basket/read contracts
**Current wave:** 10

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| Agent 1 — M8-A History + utility Activity convergence | mixed executable | ready after Wave-10 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m8-history` on branch `phase17-m8-history` | owns History composition/UI and Home activity attention only; no basket science/presentation files | M8-0 integrated at `01e8d3e` |
| Agent 2 — M8-B Product Portfolio presentation convergence | mixed executable | ready after Wave-10 coordination commit | immediately | `/home/hamza/repo/qap/.worktrees/phase17-m8-portfolio` on branch `phase17-m8-portfolio` | consumes stable M8-0 basket read contract; owns basket/Portfolio presentation only | M8-0 integrated at `01e8d3e` |

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
        v
M7 persistent current-evidence collector (complete at d5fbddc)
        |
        v
M8-0 Product basket provenance / immutable source binding (complete at 01e8d3e)
        |
        +--------------------------------------+
        |                                      |
        v                                      v
Agent 1: M8-A writer                  Agent 2: M8-B writer
History + utility Activity            Product Portfolio presentation
longitudinal read composition         claim-aware source/result UX
        |                                      |
        +------------------+-------------------+
                           |
                           v
                  planner integrates full M8
                           |
                           v
                  M9 lifecycle hardening
```

M8-0 is complete and integrated at `01e8d3e`. Product current-approved baskets now have a separately truthful source/basket protocol identity, exact immutable M3 execution-generation bindings, and catalog-independent replay/recovery while strict PIT basket behavior remains unchanged. This stabilizes the shared basket/read seam, so M8 now genuinely fans out: Agent 1 owns longitudinal History + utility Activity convergence, while Agent 2 owns claim-aware Product Portfolio presentation. M9 reconnaissance is complete and recommends no desktop shell for Product V1; executable M9 remains blocked until full M8 completion.

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
| M7 ownership-safe persistent current-evidence collector | complete / integrated at `d5fbddc` | — |
| M8-0 Product basket claim/provenance + immutable source binding | complete / integrated at `01e8d3e` | — |
| M8-A History + utility Activity | ready | Agent 1 writer |
| M8-B Product Portfolio presentation | ready | Agent 2 writer |
| M9 process/state ownership + packaging decision | reconnaissance complete; executable lifecycle hardening blocked by full M8 | — |
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

Agent 1 is the sole writer in `/home/hamza/repo/qap/.worktrees/phase17-m8-history`. Agent 2 is the sole writer in `/home/hamza/repo/qap/.worktrees/phase17-m8-portfolio`. They may run concurrently because M8-0 has frozen the shared basket provenance/read contract and the missions have disjoint primary ownership.

Former M1-M8-0 worktrees are historical integrated milestone state and must not be reused as concurrent writers for Wave 10.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, the final adaptive Product orchestration/exit at `c1d97eb`, M4 at `d49e597` plus planner review closure `c3c81ca`, M5 at `6b40028`, M6 at `c1db648`, M7 at `d5fbddc`, and M8-0 at `01e8d3e`.

The planner verifies/integrates M8-A and M8-B independently, then reconciles any shared generated/client artifacts centrally if needed. M8-A must not alter basket science/provenance. M8-B must not alter the M8-0 basket source/replay contract. Full M8 closes only when both branches are integrated and the primary `Home | Research | Portfolios | History` experience is coherent.

## Execution lifetime policy

Both sessions should load and use `persistent-agent-loop` because the user intends to steer long-running work.

- Agent 1 M8-A writer: persistent loop required; use Terminal + event wait only if a genuinely persistent browser/build process is needed.
- Agent 2 M8-B writer: persistent loop required; use Terminal + event wait only if a genuinely persistent browser/build process is needed.
- Status/progress questions are steering events, not stop commands, unless the user explicitly stops/replaces a mission.

## Verification policy

### Agent 1 — M8-A History + utility Activity

Prove History composes longitudinal Research Idea evidence from backend authority, preserves time-specific current assessments and specialist evidence links, keeps paper/operational evidence separate, and surfaces failed/interrupted background work as operational attention rather than research outcome. Do not create/run tests unless separately authorized.

### Agent 2 — M8-B Product Portfolio presentation

Prove Product current-approved research is the normal portfolio source experience, strict PIT remains Advanced, manual 3–6/exact-edge authority is unchanged, and Portfolio results explain only persisted HODL/control/cost/concentration evidence while consuming M8-0 claim/provenance truth. Do not create/run tests unless separately authorized.

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
| **8 — complete** | **Write M7:** ownership-safe persistent current-evidence collector/qualification bridge | **Read-only M8 objective-aware convergence reconnaissance** | M7 integrated at `d5fbddc`; M8 reconnaissance found a serial basket-provenance foundation is required |
| **9 — complete** | **Write M8-0:** Product basket source/provenance + immutable M3 generation binding | **Read-only M9 process/state ownership reconnaissance** | M8-0 integrated at `01e8d3e`; M9 recon recommends no desktop shell for Product V1 |
| **10 — current** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Product Portfolio presentation convergence | genuine two-writer fan-out on stable M8-0 basket/read contract |
| **11** | **M9 executable lifecycle hardening:** maintenance recovery + startup readiness + status freshness + operator wording | **M10 comprehension-study preparation/read-only acceptance support** | no desktop dependency on current evidence; M10 cannot fabricate representative-user evidence |
| **12 — closure** | integration/final Product Layer verification as assigned by planner | independent read-only cross-check only if useful and authorized | Phase 17 closes only when canonical exit criteria are actually met |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important blocked work now:

- M8-A History/Activity and M8-B Product Portfolio presentation — current parallel writable frontier.
- M9 executable lifecycle hardening remains blocked by full M8; reconnaissance is complete and does not justify Tauri for Product V1.
- M10 remains final acceptance / blocked.

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
- `2026-08-20` — M7 `d5fbddc` returned complete and was verified/fast-forward integrated. It adds bounded Product SQLite current-evidence state, exact slot/restart semantics, a Local Market collector process, M6 frozen-lineage instrument resolution, existing readiness/qualification reuse, Product amount assessment, and launcher lifecycle integration without changing scientific policy. M8 reconnaissance found Product-v1 basket economics compatible but provenance/current-catalog source binding incompatible; Wave 9 therefore materialized a serial M8-0 basket foundation before later M8-A/M8-B fan-out, with Agent 2 moving to read-only M9 process/state reconnaissance.
- `2026-08-20` — M8-0 `01e8d3e` returned complete and was verified/fast-forward integrated. Product baskets now seal separately truthful Product source provenance and exact immutable M3 execution generations, while strict PIT basket behavior remains unchanged. M9 reconnaissance found no current evidence for a desktop shell and identified one later lifecycle correctness repair: ownerless stale `market_data_maintenance=running`. Wave 10 materialized the intended genuine fan-out: Agent 1 on History/Activity and Agent 2 on Product Portfolio presentation.
