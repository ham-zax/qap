# Phase 17 Product Layer — Agent Coordination

**Repository:** `/home/hamza/repo/qap`
**Source design:** `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
**Source plan:** `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
**Investigation evidence:** `docs/research/2026-08-19-qap-product-layer-investigation.md`
**Legacy salvage evidence:** `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
**Research cockpit evidence:** `docs/research/2026-08-20-qap-research-cockpit-investigation.md`
**Pair Study design:** `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md`
**Pair Study implementation plan:** `docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md`
**Frozen design base:** `1bb6e78`
**Execution shape:** M0-M9 and M10-A/B/C are integrated, M10-0 is approved, and the Pair Study redesign is frozen. M11-A is integrated through `2f055d1` and M11-B study-first Product flow at `9890431`. Wave 18 is one serial M11-C contract/economics writer: add explicit relationship-input roles and transient USDT research authority, then reuse the existing `multi_asset_bridge` executor for honest two-leg Pair Research economics.
**Current wave:** 18 — M11-C honest two-leg Pair Research economics

## Current frontier

| Mission | Type | Status | Can start | Workspace | Isolation reason | Blocked by |
|---|---|---|---|---|---|---|
| M10-0 Research Cockpit + Experiment Contract amendment | design contract | complete / approved | complete | `main` | frozen contract | none |
| Agent B — M10-A Typed Research Recipe + capability preflight | executable backend | complete / integrated at `12ed08a` | complete | historical clean worktree | no active ownership | M10-0 approved |
| Agent A — M10-B Research Cockpit + Experiment Lab | mixed Product/API read composition | complete / integrated at `f39b4b4` | complete | historical clean worktree | no active ownership | M10-A integrated |
| Agent B — M10-C capability/fidelity proof | research/acceptance evidence | complete / integrated at `3e07878` | complete | historical clean worktree | no active ownership | M10-A and M10-B integrated |
| Agent A — M10-D Pair Research UX remediation | mixed Product UX / minimal application orchestration | completed candidate `6609a1c`; superseded as closure path | historical evidence only | `/home/hamza/repo/qap/.worktrees/phase17-m10d-pair-research-ux` | preserved bounded remediation evidence | deeper Pair Study contract finding |
| M11-0 Pair Study design freeze | design contract | complete / approved at `df41d0c` | complete | historical clean worktree | frozen contract | none |
| M11-A Pair Study backend/API | executable Product/backend | complete / integrated through `2f055d1` | complete | historical clean worktree | no active ownership | M11-0 |
| Agent A — M11-B Pair Research Product flow | mixed Product/browser/API consumption | complete / integrated at `9890431` | complete | historical clean worktree | no active ownership | M11-A integrated |
| Agent A — M11-C honest two-leg Pair Research economics | mixed experiment contract / Product authority / minimal Product UI | ready / current writer | now | `/home/hamza/repo/qap/.worktrees/phase17-m11c-pair-bridge-economics` | isolates a serial manifest/compiler/state/runtime change from protected live-session state on `main` | M11-A/B integrated |
| M11-D integrated research-completion evidence | mixed Product/read composition | blocked | after M11-C | future implementation workspace | depends on final economic contract | M11-C |
| M10-D representative-user closure | human-led acceptance | blocked / rerun after M11 | after M11 integration | stable integrated `main` | must use real participants | M11-A/B/C/D |

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
M10-0 Research Cockpit + Experiment Contract design         APPROVED
        |
        v
M10-A typed Research Recipe + capability preflight          COMPLETE / INTEGRATED 12ed08a
        |
        v
M10-B Research Cockpit + Experiment Lab                     COMPLETE / INTEGRATED f39b4b4
        |
        v
M10-C capability/fidelity proof with real methods           COMPLETE / APPROVED 3e07878
        |
        v
M10-D first representative-user Pair Research               UX REMEDIATION REQUIRED
        |
        v
bounded remediation candidate 6609a1c                       EVIDENCE / NOT FINAL ARCHITECTURE
        |
        v
M11-0 Pair Study design freeze                              COMPLETE / APPROVED df41d0c
        |
        v
M11-A Pair Study backend/API                                COMPLETE / INTEGRATED 2f055d1
        |
        v
M11-B Pair Research Product flow                            COMPLETE / INTEGRATED 9890431
        |
        v
M11-C real two-leg pair economics                           CURRENT
        |
        v
M11-D integrated research-completion evidence               BLOCKED
        |
        v
M10-D representative-user comprehension / authority closure RERUN / FINAL HUMAN GATE
```

Full M8 is integrated through `3b7c32d` and M9 at `d9cb44e`. M10-0/A/B/C are also complete. M11-0 froze the corrected Pair Study boundary, M11-A provides scoped backend Pair Study evidence, and M11-B now exposes that study-first flow on Research. The current frontier is M11-C: make the same exact pair evidence economically replayable through two real same-venue USDT legs only when explicit transient bridge authority exists.

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
| M10-0 Research Cockpit + Experiment Contract design | complete / approved at Wave-12 base | — |
| M10-A typed Research Recipe + capability preflight | complete / integrated at `12ed08a` | Agent B finished |
| M10-B Research Cockpit + Experiment Lab | complete / integrated at `f39b4b4` | Agent A finished |
| M10-C capability/fidelity proof with real methods | complete / integrated at `3e07878` | Agent B finished |
| M10-D Pair Research UX remediation | candidate complete at `6609a1c`; no longer sufficient for closure | historical Agent A branch |
| M11-0 Pair Study research workflow design | complete / approved at `df41d0c` | — |
| M11-A pair-scoped preparation + Pair Study backend/API | complete / integrated through `2f055d1` | — |
| M11-B Pair Research Product flow + current values | complete / integrated at `9890431` | — |
| M11-C real two-leg Pair Research economics | current | Agent A serial contract/economics writer |
| M11-D integrated research-completion evidence | blocked | after M11-C |
| M10-D representative-user comprehension/authority closure | blocked / rerun after M11 | human moderator + representative users |

## Shared contracts

- Phase 17 changes Product operation, not QAP scientific/economic authority.
- Phase-12 live-capital authority remains `NO-GO`.
- The strict historical point-in-time scanner policy remains intact. The separately-versioned current-approved retrospective claim belongs to M4, not M1/M2.
- Asset-level admission remains explicit operator authority; exchange listing must never imply approval to own.
- Negative, invalid, incomplete, unavailable, and rejected research evidence remains first-class.
- Manual Pair Study relationship evidence may exist without a runnable economic recipe; direct-market absence is an execution limitation, not pair invalidity.
- Pair-scoped Product preparation is separate from universe-scoped Universal Scan preparation; neither may silently mutate the other's research scope.
- Real two-leg Pair Research economics, if admitted by M11-C, must reuse existing `multi_asset_bridge` execution with explicit transient bridge authority and must never synthesize a direct pair market.
- Existing `evidence_instrument_ids` remain evidence-only. Any market series used both as relationship input and execution reference must have an explicit additive role rather than weakening that contract globally.
- The existing seven-command research mutation vocabulary remains protected; Product maintenance is a separate bounded owner.
- CCXT is not required for Product V1. Existing Binance/Gate public adapters are preferred until a concrete insufficiency is demonstrated.
- Legacy `tradingview_ratio` is conceptual evidence only: no monolithic fetcher/cache owner, global mutable API guardian, synthetic execution, presenter-derived verdict authority, or legacy eligibility thresholds may be ported into Phase 17.
- Acquisition availability/earliest history is not strict historical PIT eligibility evidence.
- Tests are opt-in. This coordination wave does not authorize creating, modifying, or running tests. Use direct evidence and the smallest relevant non-test/static/build checks instead.

## Workspace policy

M10-0 is approved; M10-A is integrated at `12ed08a`; M10-B at `f39b4b4`; M10-C at `3e07878`; M11-A is integrated through `2f055d1`; M11-B at `9890431`. M11-C is the only current writer. Its isolated worktree exists because `main` contains protected live-session `catalog.json` and `product-market-data/` state and this mission changes manifest/compiler/Product authority plus runtime economics; no concurrent production writer is authorized.

## Integration policy

M1 is integrated at `461a33c`, M2 at `8e45c36`, the M3 shared foundation at `1a476db`, Binance at `f1fab24`, Gate is integrated from original venue commit `30297cd`, final adaptive M3 orchestration at `c1d97eb`, M4 at `d49e597` plus planner closure `c3c81ca`, M5 at `6b40028`, M6 at `c1db648`, M7 at `d5fbddc`, M8-0 at `01e8d3e`, M8-A at `2aa60ea`, M8-B centrally at `0efd728` plus claim-wording closure `3b7c32d`, M9 at `d9cb44e`, M10-A at `12ed08a`, M10-B at `f39b4b4`, M10-C at `3e07878`, M11-A through `2f055d1`, and M11-B at `9890431`.

Full M8 and M9 are closed. M10-0 is approved and frozen. M10-A, M10-B, and M10-C are integrated on `main` at `12ed08a`, `f39b4b4`, and `3e07878`; M11-A is integrated through `2f055d1` and M11-B at `9890431`. M11-C is now ready as the sole serial writer. Representative-user M10-D remains blocked until M11 completes.

## Execution lifetime policy

M11-C uses Persistent Agent Loop because it owns one end-to-end contract/runtime/economic proof and may need a durable API/Product runtime plus repeated steering. M11-D remains blocked. Human M10-D remains the final authority after M11 integration; never fabricate participant reactions or usability metrics.

## Verification policy

### M10-C — capability/fidelity proof

Use the eight frozen cases rather than new method implementations: current rolling-residual pair, current slow-momentum semantics, known-unimplemented Student-t Copula, Palazzi exact replication with simultaneous reasons, separately declared adaptation lineage, invalid multi-variant final-OOS, development-to-final-OOS family continuity, and an unknown method ID. Verify integrated M10-B presentation preserves backend support truth and exact run/lineage references. A blocking mismatch is `REQUEST CHANGES`, not permission to patch production code inside the proof mission.

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
| **11 — complete** | **M10-0 Research Cockpit + Experiment Contract amendment/reviews** | contract reconnaissance/review | approved; family continuity and final-OOS selection lineage frozen |
| **12 — complete** | **Agent B writes M10-A typed Research Recipe + capability preflight** | **Agent A read-only M10-B reconnaissance** | M10-A integrated at `12ed08a`; Agent A reconnaissance reconciled against the actual public contract |
| **13 — complete** | **Agent A writes M10-B Research Cockpit + Experiment Lab** | no second writer | M10-B integrated at `f39b4b4`; exact-first Pair Research / scanner-owned Universal Scan / Experiment Lab are available |
| **14 — complete** | **Agent B runs M10-C capability/fidelity proof** | no second writer | approved and integrated at `3e07878`; no production remediation required |
| **15 — human evidence** | first representative-user Pair Research walkthrough | **M10-D human-led acceptance** | returned `UX REMEDIATION REQUIRED`; research task continuity/setup was too complicated |
| **15a — evidence complete** | **Agent A bounded Pair Research UX remediation** | no second writer | candidate `6609a1c` proved continuity plus acquisition/cutoff fixes, but exposed the deeper direct-recipe-before-study mismatch |
| **16 — complete** | **M11-0 Pair Study design freeze** | no production writer | approved at `df41d0c`; relationship study is separated from economic replay |
| **17a — complete** | **M11-A Pair Study backend/API** | no second writer | integrated through `2f055d1`; pair-scoped preparation and immediate current relationship evidence are available |
| **17b — complete** | **Agent A M11-B Pair Research Product flow** | no second writer | integrated at `9890431`; study-first W/PIXEL Product flow is proven without direct-market gating |
| **18 — current contract implementation** | **Agent A M11-C real two-leg Pair Research economics** | serial writer only | additive relationship-input role + explicit transient USDT authority + existing `multi_asset_bridge` executor |
| **19 — blocked integration/acceptance** | **M11-D research-completion evidence then M10-D human rerun** | human final gate after integration | user completes the research question without developer coaching |

This map is a dependency plan, not permission to start future writers early. The planner must re-evaluate each wave from returned commits/reports and may collapse or reshape later waves when repository reality makes the original split unnecessary.

Important remaining work now:

- M10-0 Research Cockpit + Experiment Contract is approved and frozen.
- M10-A typed Research Recipe / capability preflight is complete and integrated at `12ed08a`; executable objects remain only `pair | fixed_basket`.
- M10-B Pair Research / Universal Scan reshaping / Experiment Lab is complete and integrated at `f39b4b4`; Universal Scan remains existing scanner authority and Focus Scan remains deferred unless mechanically reusable.
- M10-C is complete and integrated at `3e07878`; all eight frozen cases passed without production remediation.
- M10-D first representative-user evidence returned `UX REMEDIATION REQUIRED`. Candidate remediation `6609a1c` is useful evidence but no longer the final architecture path.
- M11-0 Pair Study design is approved at `df41d0c`; M11-A is complete and integrated through `2f055d1` after central review closure.
- M11-B Pair Research Product flow is complete and integrated at `9890431`; M11-C is the current frontier. M11-D remains blocked and final human M10-D reruns only after M11 integration.
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
- `2026-08-20` — M10-0 contract review requested four major corrections and all four are now incorporated for re-review: recipe compilation is constrained to `pair | fixed_basket` while Universal/Focus discovery stays scanner-owned; `SupportReportV1` is compositional instead of precedence-based; `ResearchRecipeV1` plus immutable compilation lineage binds methodology to family/manifests; and `final_oos` rejects multi-variant/search recipes before compilation. The capability catalog remains explanatory and delegates validation/composition to existing canonical owners.
- `2026-08-20` — Final M10-0 re-review found one remaining lineage defect: deriving `research_family_id` from exact `recipe_sha256` would sever development-to-final-OOS family continuity and weaken the existing family+holdout guard. The contract now keeps exact recipe identity separate from stable family identity, adds immutable prior-compilation selection lineage for final OOS, and requires the same family ID to survive `[A,B]/development -> [A]/final_oos`. Agent B's M10-A reconnaissance is complete; implementation remains blocked pending Agent A's final approval.
- `2026-08-20` — M10-A `12ed08a` returned complete and was fast-forward integrated. Integration review confirmed the stable public handoff: support-check, asynchronous recipe launch, completed operation result containing `compilation_sha256` + exact `run_ids[]`, and generated TypeScript recipe/support types. Agent A's reconnaissance also exposed one Product read gap: capability/default descriptors and immutable compilation-lineage are internal-only. Wave 13 therefore materializes one Agent-A M10-B writer that may add only the smallest read-only projections needed to present existing M10-A truth.
- `2026-08-20` — M10-B `f39b4b4` returned complete, its previously missing post-commit status was freshly verified clean, and it was fast-forward integrated into `main`. Pair Research, scanner-owned Universal Scan reshaping, Experiment Lab, exact-first shared asset selection, just-in-time setup, exact recipe-operation result links, and advanced recipe/compilation lineage are now integrated. Wave 14 materializes one Agent-B M10-C proof writer; Agent A is idle/reviewer, and M10-D remains human-led.
- `2026-08-20` — Agent A APPROVED M10-0 at `052aaaf` with no remaining blockers. Wave 12 materializes one M10-A writer (Agent B) plus concurrent read-only M10-B reconnaissance (Agent A). M10-B implementation and M10-C remain blocked until M10-A integrates.
- `2026-08-20` — M10-C `3e07878` returned `APPROVE M10-C` with all eight frozen capability/fidelity/final-OOS cases passing and no production remediation required. The docs-only proof commit was fast-forward integrated into `main`. Wave 15 is now human-led M10-D acceptance only; no autonomous coding writer is authorized unless representative-user evidence requests bounded remediation.
- `2026-08-20` — The first live M10-D Pair Research walkthrough attempted `W / PIXEL` and returned `UX REMEDIATION REQUIRED`: exact-first selection worked, but quote-identity administration and fragmented market-data preparation made ordinary research too difficult before experiments/results. Wave 15a materialized one bounded Agent-A Product remediation.
- `2026-08-20` — Candidate remediation `6609a1c` proved two useful acquisition corrections (invalid Gate archive -> existing REST path, one shared preparation cutoff) and a one-action draft-preserving flow. Follow-up review found a deeper design defect: `_pair_draft()` requires a real direct pair market before collecting the existing `ASSET/USDT` relationship inputs, so a Slice-1 replay restriction became a manual research-entry restriction. The user explicitly authorized the M11 Pair Study redesign. Wave 16 is design-only; production implementation and M10-D rerun remain blocked pending approval.
- `2026-08-20` — Pair Study design `df41d0c` was approved as the M11-0 contract. M11-A returned at `2505528` with real Gate `W_USDT + PIXEL_USDT` evidence and no direct `W/PIXEL` market. Central review found three bounded integration seams: ambiguous current path/direct-market selection needed to fail closed, universe-wide preparation had unintentionally inherited selected-pair shared-cutoff semantics, and checked-in OpenAPI/generated TypeScript had drifted. Review closure `2f055d1` fixed those seams, preserved optional unscoped request compatibility, passed focused Ruff/format/Pyright/OpenAPI/typecheck/diff-hygiene checks, and was fast-forward integrated into `main`. No tests were run; protected live-session `catalog.json` and `product-market-data/` were untouched.
- `2026-08-20` — Wave 17b materializes one M11-B Product/browser writer against the integrated Pair Study API. The mission must make Pair Study readiness primary on Research, preserve Universal Scan and Experiment Lab authority, and leave real two-leg economics/transient bridge authority to blocked M11-C.
- `2026-08-20` — M11-B `9890431` returned complete and was centrally reviewed with no blocking finding. Its headed W/PIXEL evidence is against the exact unchanged commit: Pair Study relationship data is ready on Gate while direct-market replay remains unavailable, scoped preparation excludes unrelated BTC, and no M11-C concepts leaked into the Product slice. The commit was fast-forward integrated into `main`. Wave 18 materializes one serial M11-C writer to add explicit relationship-input roles and transient USDT research authority, then prove W/PIXEL economics through the existing `multi_asset_bridge` executor. No tests were run.
