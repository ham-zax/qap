# QAP Plan Map

Update context — 2026-11-15
Trigger: Hamza defined the MVP constitution, math-repair gate, configurable crash-defense setting, 0%–100% starter rotation, and millisecond-aware Binance WebSocket L2 paper trading plan before further coding.
Purpose: Register Phase 20 and Phase 21 in the canonical plan map.
Impact: [Phase 21 — Pair Rotation MVP Constitution, Math Repair, and L2 Paper Trading Plan](21-pair-mvp-fundamentals-and-l2-paper-plan.md) governs upcoming work before Stage B/S5 trials. Economic, Decimal inventory, benchmark, and Shariah spot-only boundaries are unchanged.
Evidence: [Phase 21](21-pair-mvp-fundamentals-and-l2-paper-plan.md), [Phase 20 draft](20-earning-roadmap-proposal.md).

Update context — 2026-10-02
Trigger: continued approved Phase 19 through M0, M1 and the M2 backend.
Purpose: remove stale current-phase labels while preserving historical plans.
Impact: none; the September 30 decision remains authoritative.
Evidence: [Phase 19](19-pair-rotation-lab-mvp.md), [parity report](../research/2026-10-02-engine-parity.md).

Update context — 2026-09-30 (product direction)
Trigger: design interview with Hamza after the research console was rejected.
Purpose: introduce the product vision and the proposed next phase.
Impact: [Phase 19 — Pair Rotation Lab MVP](19-pair-rotation-lab-mvp.md) is the current
phase (approved 2026-09-30) and supersedes the Phase 18 M4–M7 experience direction. Product
intent now lives in [docs/product/vision.md](../product/vision.md). Economic and
research contracts are unchanged.
Evidence: [decision record](../product/decisions-2026-09-30.md).

Update context — 2026-09-30 (authorized cleanup)
Trigger: Hamza requested removal of legacy and stale code, data and documents,
then requested wrap-up before UI generation.
Purpose: point references to the current Phase 18 plan after retiring the two
explicitly superseded research proposals; preserve their decision context in Git.
Impact: no economic or research contract change here.
Evidence: [Phase 18 handoff](18-research-experience-and-asset-resolution.md).


**Status:** Phase 19 — Pair Rotation Lab MVP is current. M0 foundation and M1 engine
parity are complete; M2's coin/data backend is implemented. Rendered-answer
acceptance and M3 dashboard/analysis remain pending. This continuation stops before
UI generation. Phase 18 M1/M2 remain the asset-evidence foundation. Phase 17
representative-user acceptance remains open and is not satisfied by automated checks.

Update context — 2026-09-27 (Phase 18 approved)
Trigger: Hamza delegated investigation decisions D1–D7 and asked for implementation
plus a UI regeneration.
Purpose: make Phase 18 the current phase and the single tracker for decisions and
implementation.
Impact: [Phase 18](18-research-experience-and-asset-resolution.md) replaces the
overhaul proposal and the September 25 console contract. Its M7 acceptance also
closes the open Phase 17 M10-D representative-user gate.
Evidence: [investigation findings](../research/2026-09-27-research-product-investigation-findings.md).

Update context — 2026-09-27 (investigation findings)
Trigger: the research product investigation was executed.
Purpose: record where the results live and what blocks the master plan.
Impact: the [investigation findings](../research/2026-09-27-research-product-investigation-findings.md)
recommend evidence-backed asset resolution plus backend-owned research requests.
The replacement master plan waits on owner decisions D1–D7 in that report.
Evidence: live Binance/Gate/CoinGecko measurements, isolated-workspace
reproduction and source inspection at `ee9100d`.

Update context — 2026-09-27 (investigation before the master redesign plan)
Trigger: Hamza clarified that the app must handle asset discovery and its internal
setup without manual per-coin support or user-authored identity/provenance records.
Purpose: investigate the complete research journey and the causes of repeated UX
failures before selecting a replacement architecture.
Impact: the [Research Product Investigation Plan](../research/2026-09-27-research-product-investigation-plan.md)
is the current work sequence. The overhaul proposal below is provisional; its
catalog, navigation and orchestration choices await investigation. M10-D remains
unaccepted, and historical implementation completion does not close that gap.
Evidence: supplied walkthroughs, earlier product decisions and source at `ee9100d`.

Update context — 2026-09-27 (research experience overhaul proposal)
Trigger: Hamza's walkthrough rejected the current console, asset search, setup and
scanner experience and requested an overhaul plan before further implementation.
Purpose: make the current product-design frontier explicit.
Impact: the retired Research Experience Overhaul proposal
(replaced by [Phase 18](18-research-experience-and-asset-resolution.md)) recorded proposed journeys, asset-catalog/resolution changes and delivery gates.
Those choices are now provisional under the investigation-first correction above,
including the proposed identity-policy design amendment;
historical technical completion does not establish usability acceptance.
Evidence: supplied QAP and Uniswap screenshots and source inspection at `ee9100d`.

Update context — 2026-09-24 (resumable research correction)
Trigger: the user still cannot easily run and understand research and asked to infer
the interaction decisions and proceed, with CLI-only verification.
Purpose: make the research question, test, result and earlier attempts one workflow.
Impact: the [study-workspace correction](../superpowers/plans/2026-09-24-research-study-workspace.md)
records the first presentation/continuity iteration before M10-D. It does not reopen the
economic, identity, admission, holdout or live-authority contracts. Historical
milestone completion is not evidence of current human acceptance.
Evidence: [design](../superpowers/specs/2026-09-24-research-study-workspace.md),
[MFSM read-only experiment assessment](../research/2026-09-24-mfsm-experiment-patterns.md).

Update context — 2026-09-24 (plan-first revision)
Trigger: the user rejected that iteration's UX and requested an implementation plan
before further changes.
Purpose: make the proposed replacement and the implementation pause explicit.
Impact: the [intuitive research experience plan](../superpowers/plans/2026-09-24-intuitive-research-experience.md)
became the proposal for review. Its checklists were not implementation or acceptance
claims at that point. The first iteration's evidence remains in its original record.
Evidence: current screen source and the user's simple/minimum-clicks requirement.

Update context — 2026-09-25 (simple research experience implementation)
Trigger: the user approved the plan-first revision and asked to complete the remaining work.
Purpose: record the new Product interaction frontier without conflating implementation
checks with representative-user acceptance.
Impact: the pair path now uses one Run comparison action for preparation, backend
support checking and launch; Home prioritizes that task; results compare all declared
methods before one selected detail; History starts with recognizable recent work; and
scanner, custom-experiment and portfolio surfaces use the same progressive hierarchy.
The economic, identity, admission, holdout and live-authority contracts are unchanged.
Representative-user visual acceptance and automated interaction checks remain pending.
Evidence: [implementation plan and verification record](../superpowers/plans/2026-09-24-intuitive-research-experience.md).

Update context — 2026-09-25 (Research Console + human semantic layer)
Trigger: live browser walkthrough of the implemented simple-research revision showed that
ordinary Research still expands into backend-oriented relationship/evidence sections,
and the user asked to make real measurements understandable without losing expert detail.
Purpose: reshape ordinary Research around one persistent console and a deterministic
human semantic layer over authoritative backend values.
Impact: the retired Research Console + human semantic layer plan
(replaced by [Phase 18](18-research-experience-and-asset-resolution.md)) was the proposed interaction frontier. It introduces no new mathematical model,
economic rule, evidence authority, live-market streaming claim, or automated recommendation.
The 2026-09-24 implementation remains historical evidence until this successor plan is executed.
Evidence: 2026-09-25 live W/PIXEL browser walkthrough and current Pair Research source.

Implementation update — current branch, 2026-09-24
Trigger: approved correction pass and subsequent CLI-only console implementation.
Purpose: distinguish the implemented presentation from the still-pending human UX gate.
Impact: ordinary Research now has Relationship and Backtest comparison modes, a chart-first
semantic view, real progress stages, and an economic-first completed comparison. Browser-local
drafts and backend result authority remain distinct. The earlier proposal is retained as
the design record; representative-user visual acceptance is not claimed.
Evidence: focused web interaction tests, production frontend build, and the Research
Console implementation on `feat/research-study-workspace`.

Update context — 2026-08-20 (Research Cockpit correction)
Trigger: the first real-user iPhone walkthrough attempted the concrete job `W vs BTC/ETH` plus a universal scan and instead landed in unresolved identity/provenance administration. Exact-symbol search behaved as substring search, the selected identity task appeared below a long result list, and normal Product Research exposed neither a focused pair launcher nor a clear scanner cockpit.
Purpose: reopen M10 as a design review so QAP starts from the research question while preserving fail-closed identity, immutable data lineage, current-approved/PIT claim separation, and existing scientific/economic authority.
Impact: M0-M9 remain complete, M10-0 is approved, M10-A is integrated at `12ed08a`, M10-B at `f39b4b4`, and M10-C proof at `3e07878`. M10-C approved the current, known-unimplemented, constitution-blocked, adaptation, invalid final-OOS, family-continuity, and unknown-method cases without production remediation. M10-D first exposed a Product-operability defect, then follow-up review established a contract-composition defect: a researcher must be able to obtain exact Pair Study relationship evidence from same-venue `ASSET/USDT` inputs before QAP asks whether an economic recipe can run. Pair-scoped preparation and Pair Study are therefore the current design frontier; direct or admitted real two-leg economics remain downstream. Focus Scan stays deferred; Student-t Copula stays known-unimplemented; formal cointegration requires separate method admission.
Evidence: `docs/research/2026-08-20-qap-research-cockpit-investigation.md`; `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`.

Update context — 2026-08-19 (Phase-17 design freeze)
Trigger: post-Phase-16 investigation of clean-install operation showed that the remaining product problem is not another visual pass: QAP lacks an explicit operator-approved research universe, production market-data preparation/refresh, immutable source generations/provenance, honest current-approved versus historical-PIT claim separation, and persistent current-evidence collection.
Purpose: freeze the Product Layer architecture before implementation so market-data/onboarding work cannot silently weaken historical-universe, asset-admission, prospective, capacity, portfolio, or live-capital boundaries.
Impact: Phase 17 is explicitly authorized at M0. The frozen future primary IA is `Home / Research / Portfolios / History`; Phase-16 `Validate`, `Results`, and `Activity` become longitudinal/History/utility concepts rather than equal-weight primary destinations as later milestones land. Product V1 stays Binance/Gate public Spot, uses explicit operator asset admission, prefers existing adapters before CCXT, and introduces stdlib SQLite only for bounded Product operational state/current scheduled collection. QAP/scanner artifacts remain scientific/economic authority.
Evidence: `docs/research/2026-08-19-qap-product-layer-investigation.md`; `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`; `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`.

Update context — 2026-08-19 (legacy-QAP salvage amendment)
Trigger: read-only forensic review of `/home/hamza/repo/tradingview_ratio` identified reusable acquisition, readiness, comprehension, research-lifecycle, and state-ownership patterns plus runtime architecture that should explicitly not return.
Purpose: selectively carry forward hard-earned legacy knowledge without merging repositories or reopening current QAP scientific/economic authority.
Impact: M3 adds current-coverage-aware prepare/refresh and measured API-pressure/source-efficiency decisions; M4-M10 gain structured readiness reasons, truthful funnel/next-action UX, evidence-layer outcome semantics, focused state/process ownership audits, objective-aware Portfolio/History presentation, and stronger user-comprehension gates. Legacy monolithic fetch/cache ownership, global API guardian, CCXT-as-truth, synthetic execution, presentation-derived verdicts, and live runtime systems remain rejected.
Evidence: `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`; amended Product Layer design and Phase-17 plan.

Update context — 2026-08-19
Trigger: Slice 4 is complete, and rendered/current-state investigation shows the next problem is user comprehension and information architecture rather than missing research capability.
Purpose: Add the post-Slice-4 human-centered workbench re-architecture wave without reopening scientific/economic authority.
Impact: Phase 16 is complete through M8: goal-oriented navigation, novice-first task flows, progressive disclosure, Results/Activity separation, forward/current-evidence guidance, portfolio authority boundaries, and visual-state convergence were implemented without moving scientific/economic authority into React.
Evidence: `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`; `docs/research/2026-08-19-qap-phase16-implementation-handoff.md`; `docs/plans/16-human-centered-workbench-ux-rearchitecture.md`.

## Current wave

The current phase is [Phase 19 — Pair Rotation Lab MVP](19-pair-rotation-lab-mvp.md);
its tracker records decisions and implementation progress. The integrated milestone
record below describes historical implementation, not acceptance of the present experience.

Phases 00–13 produced the financial/research core, paper hardening, readiness decision, and autonomous-development harness. Phase 14 is implemented and its integrated rendered acceptance is green. **Phase 15 — Research Scanner and Basket Backend** is complete through Scanner V1 Slice 3, including the post-review remediation handoff at `142a18d`; Slice-3 results are in `docs/research/2026-08-18-qap-scanner-slice3-results.md`. The former Slice-3 Candidate Workbench milestone was explicitly superseded by the post-Phase-15 **Slice 4 Unified QAP Workbench**, which is complete and repository/browser-verified; its final rendered executable state is `6961937`, followed by the review-closure state on `main` at `62416cc`. Results are in `docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`. **Phase 16 — Human-Centered Workbench UX Re-architecture** is complete through M8 and remains the protected historical UX/evidence baseline. **Phase 17 — Product Layer** is technically complete through M10-C. The executable primary IA is `Home / Research / Portfolios / History`; strict PIT research remains under Advanced Research and specialist URLs remain stable. M10-0 is approved, M10-A is integrated at `12ed08a`, M10-B at `f39b4b4`, and M10-C proof at `3e07878`. Pair Study M11-A/B/C/D is integrated through `3528973`; **M10-D representative-user acceptance rerun is the current and final Phase-17 gate**. Do not replay earlier Product milestones or port legacy runtime architecture.

## Implementation waves

The current correction's verification record is in the linked study-workspace
plan above. Browser/representative-user acceptance remains pending; do not promote
CLI fixture checks into completion of that gate.

| Wave | Purpose | Phases | Exit condition |
|---|---|---|---|
| 1 | Prove financial truth | 00–03 | Inventory, public-data admission, point-in-time semantics, valuation, HODL comparison, and relative-wealth path are deterministic and reconciled |
| 2 | Prove accumulation mechanism | 04–07 | Relationship evidence can drive target allocation through paper replay with predeclared simple controls, family lineage, and final-holdout discipline |
| 3 | Make QAP inspectable | 08–09 | Typed API and web workbench expose the same authoritative results without duplicating financial logic |
| 4 | Test real relationship models | 10 | Pair, cross-sectional/common-mode, and any admitted historical model can be compared under one frozen benchmark/research-family contract |
| 5 | Harden paper operation | 11 | The Phase-02 public-data path scales to larger datasets; venue precision, explicit routing, reconciliation, and operator workflows are reliable |
| 6 | Decide live readiness | 12 | Separate go/no-go review; no live trading authority is implied by earlier phases |
| 7 | Automate development safely | 13 | Approved-plan execution can continue autonomously without becoming part of financial runtime |
| 8 | Make evidence understandable | 14 | Workbench is verdict/visual-first, preserves exact audit truth, and passes integrated desktop/mobile/browser acceptance |
| 9 | Make research generation explicit | 15 | A bounded scanner/candidate/basket backend can enumerate, evaluate, rank, combine, freeze, and replay research candidates without bypassing QAP economics or holdout discipline |
| 10 | Make QAP human-operable | Slice 4 | One local web application can initiate and inspect the admitted Slice-1/2/3 workflows while immutable QAP/scanner artifacts remain authoritative |
| 11 | Make QAP understandable without internal expertise | 16 | Goal-oriented navigation, plain-language task flows, progressive disclosure, and human-centered acceptance preserve the same authoritative evidence while reducing implementation vocabulary from the primary UX |
| 12 | Make a clean local workspace product-operational | 17 | Explicit asset admission, honest market-data/readiness ownership, immutable refreshable inputs, longitudinal research evidence, and persistent current-evidence collection make the existing research engine usable without expert fixture/catalog preparation |
| 13 | Establish automatic asset evidence | 18 | Venue metadata, registry/resolver and D1–D7 form the foundation; remaining experience work is superseded by Phase 19 |
| 14 | Prove and explain pair rotation | 19 | Independent engine parity, admission-free coin discovery and fresh data support the two-coin dashboard, honest proof and benchmarks; Hamza accepts the rendered experience |

## Phase plans

1. `00-constitution-and-repository-foundation.md`
2. `01-domain-kernel-and-inventory-semantics.md`
3. `02-market-data-admission-and-reproducibility.md`
4. `03-accounting-hodl-and-economic-evaluation.md`
5. `04-relationship-evidence-pairs-and-anchor-lens.md`
6. `05-policy-target-allocation-and-rebalancing.md`
7. `06-deterministic-paper-execution-and-replay.md`
8. `07-experiments-controls-and-research-protocol.md`
9. `08-fastapi-contract-and-web-boundary.md`
10. `09-react-analytical-workbench-and-charts.md`
11. `10-first-real-relationship-model-experiments.md`
12. `11-paper-operation-hardening.md`
13. `12-live-readiness-gate.md`
14. `13-autonomous-development-harness.md`
15. `14-analytical-workbench-ux-redesign.md` (overview; detailed route/design plans are under `docs/plans/14/`)
16. `15-research-scanner-and-candidate-workbench.md` (historical filename; Phase 15 now closes the scanner/basket backend and its former Candidate Workbench is superseded)
17. Slice 4: `docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md`
18. `16-human-centered-workbench-ux-rearchitecture.md` (post-Slice-4 presentation/IA phase; current-state evidence is in `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`; fresh-agent execution handoff is `docs/research/2026-08-19-qap-phase16-implementation-handoff.md`)
19. `17-product-layer-market-data-and-research-lifecycle.md` (Product Layer phase; M0-M9 and M10-A/B/C complete, M10-0 approved, M11 Pair Study redesign current before M10-D human closure; Pair Study design is `docs/superpowers/specs/2026-08-20-qap-pair-study-research-workflow-design.md`; implementation plan is `docs/superpowers/plans/2026-08-20-qap-pair-study-research-workflow-implementation-plan.md`; original Product investigation is `docs/research/2026-08-19-qap-product-layer-investigation.md`; cockpit investigation is `docs/research/2026-08-20-qap-research-cockpit-investigation.md`; M10-C proof is `docs/research/2026-08-20-qap-m10c-capability-fidelity-proof.md`)
20. `18-research-experience-and-asset-resolution.md` (foundation and historical D1–D7 decisions; remaining experience superseded by Phase 19)
21. `19-pair-rotation-lab-mvp.md` (Pair Rotation Lab MVP implementation record)
22. `20-earning-roadmap-proposal.md` and `20-earning-roadmap-tasks.md` (October 27 earning roadmap draft and Stage A/B1–B3 cards; superseded on sequencing and crash-defense/L2-paper details by Phase 21)
23. `21-pair-mvp-fundamentals-and-l2-paper-plan.md` (current master playbook: MVP constitution, dual AI-CLI + Subscriber-Web interface rule, signal-math repair, crash defense, and live WebSocket L2 taker paper trading)
24. `22-backend-and-agent-cli-tasks.md` (literal autonomous worker cards `S2-A`, `S2-B`, `S2-C`, and `S4-A` for AI agents)

The original cross-phase master implementation plan at `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md` closes the 00–15 research-engine mission. Phases 16, 17 and 18 are explicitly authorized post-master product phases and do not alter the original economic/research completion definition.

Decision records that affect multiple phases:

- `docs/research/2026-08-17-quant-oss-integration.md` — quant/backtesting/scanning OSS reuse and authority boundaries.
- `docs/research/2026-08-17-real-alpha-inventory-compounding.md` — admitted Deep Research refinements for accumulation/HODL/rebalancing controls, simple-first alpha search, falsification, and prospective evidence.
- `docs/research/document-update-method.md` — short context-retention method for material documentation changes.

## Global sequencing rule

A later phase may begin only when the prior phase's exit criteria are green or when the user explicitly approves a documented exception. A later plan may be refined as evidence appears, but it may not silently change:

- product economic objective;
- Shariah/action-space boundary;
- state ownership;
- benchmark semantics, including the primary incremental simple control;
- point-in-time timing and cost/fill/reference-price semantics;
- dataset role/final-OOS commitment or consumption status;
- fixed-basket versus point-in-time universe eligibility/claim semantics;
- v1/v2 historical-reference boundary;
- live-capital authority.

Any proposed change to those items returns to design review.

## Plan granularity

Each phase plan contains:

- goal and non-goals;
- exact file map;
- interfaces consumed and produced;
- numbered implementation sections;
- test/verification commands;
- acceptance criteria;
- explicit stop conditions;
- phase exit criteria.

This is deliberately less bureaucratic than QAP v2: the plans exist to make implementation executable and bounded, not to create a separate promotion system.
