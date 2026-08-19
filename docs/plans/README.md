# QAP Plan Map

**Status:** Implementation authorized for completed/approved phases; Phase 16 M1 terminology/IA is frozen as a `single-stakeholder provisional` baseline and M2 presentation-code execution is authorized.

Update context — 2026-08-19
Trigger: Slice 4 is complete, and rendered/current-state investigation shows the next problem is user comprehension and information architecture rather than missing research capability.
Purpose: Add the post-Slice-4 human-centered workbench re-architecture wave without reopening scientific/economic authority.
Impact: Phase 16 current-state investigation and terminology/IA checkpoint are complete; goal-oriented Home/shell implementation may proceed without changing scientific/backend authority.
Evidence: `docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`; `docs/plans/16-human-centered-workbench-ux-rearchitecture.md`; Phase-16 definition commit `fc14d29`.

## Current wave

Phases 00–13 produced the financial/research core, paper hardening, readiness decision, and autonomous-development harness. Phase 14 is implemented and its integrated rendered acceptance is green. **Phase 15 — Research Scanner and Basket Backend** is complete through Scanner V1 Slice 3, including the post-review remediation handoff at `142a18d`; Slice-3 results are in `docs/research/2026-08-18-qap-scanner-slice3-results.md`. The former Slice-3 Candidate Workbench milestone was explicitly superseded by the post-Phase-15 **Slice 4 Unified QAP Workbench**, which is complete and repository/browser-verified; its final rendered executable state is `6961937`, followed by the review-closure state on `main` at `62416cc`. Results are in `docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`. **Phase 16 — Human-Centered Workbench UX Re-architecture** is now the active product-design wave: M0 current-state investigation is complete and M1 freezes `Home / Discover / Validate / Portfolios / Results / Activity` plus the plain-language presentation vocabulary as a `single-stakeholder provisional` baseline. M2 goal-oriented Home/shell implementation is authorized. Later dependent work still begins only after predecessor exit criteria are green or the user explicitly approves a documented exception.

## Implementation waves

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

The original cross-phase master implementation plan at `docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md` closes the 00–15 mission. Phase 16 is a post-master product refinement and does not alter the original economic/research completion definition.

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
