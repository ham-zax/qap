# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Research cockpit evidence:** `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** M0-M9 remain integrated; M10 is reopened in design review after real-user feedback exposed both a missing Pair Research / Universal Scan cockpit and a missing typed Research Recipe / capability-preflight layer. No executable writer is authorized until M10-0 is reviewed.
**Current wave:** 11 — M10-0 Research Cockpit + Experiment Contract design review

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| M10-0 Research Cockpit + Experiment Contract amendment | read-only/design planning | current / ready for review | now | stable integrated Product V1 on `main` | freezes Pair/Universe UX plus Research Recipe, support/fidelity states, capability catalog, and compile-down boundary | none — M0-M9 integrated |
| M10-A Typed Research Recipe + capability preflight | executable backend | blocked | after M10-0 approval | not materialized | read-only `Check support`, typed reasons, faithful compile to existing experiment authority | M10-0 |
| M10-B Research Cockpit + Experiment Lab | executable Product | blocked | after M10-A | not materialized | Pair Research, Universal Scan, Experiment Lab, exact-first search, JIT setup | M10-A |
| M10-C capability/fidelity proof | acceptance/research | blocked | after M10-A/B | stable integrated build | proves current, unsupported, constitution-blocked, paper-replication/adaptation cases | M10-A and M10-B |
| M10-D representative-user closure | human-led acceptance | blocked | after M10-C | stable integrated Product build | validates corrected research/experiment tasks with actual/likely users | M10-C |

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
M10-0 Research Cockpit + Experiment Contract design         CURRENT
        |
        v
M10-A typed Research Recipe + capability preflight
        |
        v
M10-B Research Cockpit + Experiment Lab
        |
        v
M10-C capability/fidelity proof with real methods
        |
        v
M10-D representative-user comprehension / authority closure
```

Full M8 is integrated through `3b7c32d` and M9 at `d9cb44e`. The first real-user mobile walkthrough then exposed a different problem: the trustworthy Product substrate exists, but normal Research does not yet expose the user's primary jobs (`W/BTC` Pair Research and an explicit Universal Scan) before identity/provenance administration. M10 is therefore reopened at M10-0 design review. The frozen Phase-17 design remains unchanged until the cockpit amendment is reviewed.

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
| M10-0 Research Cockpit + Experiment Contract design | current / review | planner + user review |
| M10-A typed Research Recipe + capability preflight | blocked on M10-0 | future backend writer after approval |
| M10-B Research Cockpit + Experiment Lab | blocked on M10-A | future Product writer |
| M10-C capability/fidelity proof with real methods | blocked on M10-A/B | acceptance/research pass; no method implementation implied |
| M10-D representative-user comprehension/authority closure | final / blocked | human-led acceptance |

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

No autonomous writer is currently authorized. M0-M9 are integrated on `main`; former Phase-17 worktrees are historical milestone state. M10-0 is a design-review checkpoint, not an implementation branch. After approval, M10-A should first materialize the bounded backend Research Recipe / `Check support` boundary. Only after that contract is stable should M10-B build the Product cockpit/Experiment Lab. Copula, Palazzi-style reproduction, Momentum variants, or any other method must be classified by the capability layer; M10 does not preapprove implementing them.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, final adaptive M3 orchestration at `c1d97eb`, M4 at `d49e597` plus planner closure `c3c81ca`, M5 at `6b40028`, M6 at `c1db648`, M7 at `d5fbddc`, M8-0 at `01e8d3e`, M8-A at `2aa60ea`, M8-B centrally at `0efd728` plus claim-wording closure `3b7c32d`, and M9 at `d9cb44e`.

Full M8 and M9 are closed. No generated-contract conflict remained after M8 integration, and the combined OpenAPI/type/build contract was revalidated centrally. Real-user evidence now explicitly blocks Phase-17 closure: M10-0 must review/freeze the Research Cockpit amendment before any executable M10-A branch is created. The existing scientific design is not implicitly amended by the planning report.

## Execution lifetime policy

M10-0 is a bounded design/review mission. No persistent coding process is needed while the user is reviewing the cockpit/experiment plan. If/when M10-A implementation is approved, return to normal one-writer Persistent Agent Loop execution. M10-D remains human-led acceptance; never fabricate participant reactions or usability metrics.

## Verification policy

### M10-0 — Research Cockpit + Experiment Contract design review

Review `docs/research/2026-08-20-qap-research-cockpit-investigation.md` against the current backend and legacy product-intent evidence. No implementation until Pair Research, Universal Scan, optional Focus Scan, Research Recipe decomposition, support/fidelity states, typed reasons, capability catalog, and faithful compile-down semantics are explicitly approved.

### M10-C — capability/fidelity proof

Use representative recipes rather than new method implementations: a current rolling-residual recipe, current momentum semantics, known-unimplemented Student-t Copula, a Palazzi exact-replication recipe that should be blocked truthfully, a separately declared adaptation, and an unknown method ID.

### M10-D — representative-user comprehension / authority closure

After M10-A/B/C exist, use actual/likely users, including limited technical/trading expertise and low digital skill/accessibility where possible. Ask them to complete realistic Pair Research / Universal Scan / Experiment Lab support-check tasks without developer coaching and then explain the protected concepts in their own words. Record qualitative evidence only; do not fabricate quantitative usability metrics.

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
| **11 — current/design review** | **M10-0 Research Cockpit + Experiment Contract amendment** | user/planner review; no executable agent | Pair/Universe UX + typed recipe/support contract must be frozen |
| **12 — blocked** | **M10-A typed Research Recipe + capability preflight** | read-only contract review | starts only after M10-0 approval; no new research method implementation |
| **13 — blocked** | **M10-B Research Cockpit + Experiment Lab** | **M10-C capability/fidelity proof** | Product surface follows stable preflight semantics; proof uses current/unsupported/paper cases |
| **14 — closure** | integration/remediation only if approved | **M10-D human-led acceptance** | Phase 17 closes only after corrected research/experiment tasks and protected meanings are demonstrated |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important remaining work now:

- M10-0 Research Cockpit + Experiment Contract design amendment is the current frontier.
- M10-A typed Research Recipe / capability preflight is blocked until review.
- M10-B Pair Research / Universal Scan / Experiment Lab Product work is blocked on M10-A.
- M10-C must prove truthful support/fidelity reporting using current methods, Student-t Copula as known-unimplemented, Palazzi exact/adapted cases, and an unknown method.
- M10-D representative-user acceptance remains final and blocked.
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
- `2026-08-20` — M9 lifecycle hardening completed centrally at `d9cb44e`. Market-data maintenance now persists PID/start-marker ownership and recovers orphaned `running` state as explicit failure; the launcher waits for exact API/workspace/web/collector readiness before declaring success; the shell refreshes collector status while open. A real Local Market launcher smoke reached `QAP workbench ready.` with the collector running and cleaned its ports on shutdown. Tauri remains deferred.
- `2026-08-20` — First real-user mobile research walkthrough reopened M10 in design review. Follow-up clarified the intended Product: not a Copula-specific UI, but machinery to declare/type-check research recipes, explain exact support/fidelity/readiness/constitution blockers, and run only faithfully supported methods through existing QAP experiment authority. Pair Research, Universal Scan, and an advanced Experiment Lab are now planned on top of that contract; M10-A/B/C/D remain blocked pending M10-0 review.
