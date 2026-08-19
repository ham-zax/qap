# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** M0-M9 are integrated; the remaining M10 gate is human-led representative-user comprehension/authority acceptance, not another autonomous implementation writer
**Current wave:** 11 — final acceptance

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| M10 representative-user comprehension / authority closure | human-led acceptance | ready for representative participants | when representative users are available | stable integrated Product V1 on `main` | acceptance evidence must come from actual/likely users; an autonomous coding agent cannot fabricate it | none — M0-M9 integrated |

## Dependency map

```text
M0 design freeze
        |
        v
M1 workspace identity / zero-state
        |
        v
M2 directory / identity / admission
        |
        v
M3 immutable/adaptive market-data preparation
        |
        v
M4 current-approved claim/readiness/safe cutoff
        |
        v
M5 self-explanatory Research / truthful funnel / primary IA
        |
        v
M6 longitudinal Research Idea / all-survivor follow-up
        |
        v
M7 persistent current public-evidence collection / qualification bridge
        |
        v
M8 Product basket provenance + History/Activity + Portfolio convergence
        |
        v
M9 process/state lifecycle hardening / no-desktop-shell decision
        |
        v
M10 representative-user comprehension / authority closure   CURRENT
```

Full M8 is integrated through `3b7c32d`: M8-A adds backend-composed longitudinal History and utility Activity attention, while M8-B makes current-approved Product research the normal manual Portfolio source without changing basket science. M9 is integrated at `d9cb44e`: stale market-data maintenance now has exact process-owner recovery, the launcher proves API/workspace/web/collector readiness before declaring success, the UI refreshes collector health, and current evidence still does not justify Tauri. M10 is the only remaining Phase-17 gate and requires real representative-user evidence.

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
| M8-A History + utility Activity | complete / integrated at `2aa60ea` | — |
| M8-B Product Portfolio presentation | complete / integrated through `0efd728` plus claim-wording closure `3b7c32d` | — |
| M9 process/state ownership + packaging decision | complete / integrated at `d9cb44e`; no desktop shell selected | — |
| M10 representative-user comprehension/authority closure | current / requires representative participants | human-led acceptance |

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

No autonomous writer is currently required. M0-M9 are integrated on `main`; former Phase-17 worktrees are historical milestone state. M10 acceptance should exercise the stable integrated Product V1 rather than a feature branch. Any remediation triggered by an observed protected-concept misunderstanding must return through normal single-writer planning rather than editing scientific meaning during the study.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, final adaptive M3 orchestration at `c1d97eb`, M4 at `d49e597` plus planner closure `c3c81ca`, M5 at `6b40028`, M6 at `c1db648`, M7 at `d5fbddc`, M8-0 at `01e8d3e`, M8-A at `2aa60ea`, M8-B centrally at `0efd728` plus claim-wording closure `3b7c32d`, and M9 at `d9cb44e`.

Full M8 and M9 are closed. No generated-contract conflict remained after M8 integration, and the combined OpenAPI/type/build contract was revalidated centrally. M10 does not unlock another implementation branch by default; it unlocks Phase-17 closure only when representative-user evidence satisfies the protected comprehension criteria.

## Execution lifetime policy

M10 is human-led acceptance rather than a persistent coding mission. If the study spans sessions, preserve participant-independent notes, scenario coverage, observed misunderstandings, and exact evidence paths; never record secrets or fabricate participant reactions. Status/progress questions remain steering events unless the user explicitly stops/replaces the acceptance effort.

## Verification policy

### M10 — representative-user comprehension / authority closure

Use actual/likely users, including limited technical/trading expertise and low digital skill/accessibility where possible. Ask them to complete realistic Product tasks without developer coaching and then explain the protected concepts in their own words. Record qualitative evidence only; do not fabricate quantitative usability metrics. A misunderstanding of a protected scientific/authority concept triggers design review and, if needed, a separately scoped remediation cycle rather than redefining the concept in the acceptance notes.

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
| **10 — complete** | **Write M8-A:** History + utility Activity with research-learning semantics | **Write M8-B:** objective-aware Product Portfolio presentation convergence | full M8 integrated through `3b7c32d` |
| **11 — current/final** | **M9 lifecycle hardening complete at `d9cb44e`** | **M10 human-led comprehension/authority acceptance** | no desktop dependency on current evidence; Phase 17 closes only after real representative-user evidence satisfies M10 |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important remaining work now:

- M10 representative-user comprehension/authority closure is the sole remaining Phase-17 gate.
- No additional autonomous implementation writer is justified before actual M10 evidence identifies a concrete remediation need.
- Tauri/desktop packaging remains deferred; current Product-V1 evidence supports the hardened launcher/browser model.

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
- `2026-08-20` — M8-A `2aa60ea` and M8-B `291f2f3` returned complete on clean disjoint branches. Central review found one M8-B unknown-versioned-claim wording seam and closed it before integration; full M8 is integrated through `3b7c32d`. A fresh combined OpenAPI export, generated TypeScript contract, Ruff/format/Pyright/import-contract, typecheck, build, and diff-hygiene pass were green; no tests were run.
- `2026-08-20` — M9 lifecycle hardening completed centrally at `d9cb44e`. Market-data maintenance now persists PID/start-marker ownership and recovers orphaned `running` state as explicit failure; the launcher waits for exact API/workspace/web/collector readiness before declaring success; the shell refreshes collector status while open. A real Local Market launcher smoke reached `QAP workbench ready.` with the collector running and cleaned its ports on shutdown. Tauri remains deferred. M10 representative-user comprehension/authority closure is now the sole remaining Phase-17 gate.
