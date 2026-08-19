# Phase 15 — Research Scanner and Basket Backend Plan

**Goal:** Add a bounded active-research workflow above the existing QAP economic kernel: point-in-time discovery, fixed-budget authoritative replay, prospective evidence, liquidity qualification, and later manual basket analysis.

**Architecture:** The scanner is a candidate-production/research-orchestration layer, never a second backtester. Existing QAP experiment, policy, execution, inventory, accounting, HODL/control, and cost semantics remain authoritative.

> **Update context — 2026-08-18**
> **Trigger:** The two scanner Deep Research passes and the user-approved Slice-1 review superseded Phase 15's earlier generic “choose generator/models/parameter grid” workflow.
> **Purpose:** Reconcile this umbrella plan with the bounded Scanner-V1 slice architecture and remove accidental authorization for a generic Cartesian scan builder.
> **Impact:** Phase 15 now delegates detailed semantics to the approved slice specs. Scanner V1 has one pair generator, fixed pair-native templates, a separate prospective/liquidity slice, and a later asset-native momentum/basket slice. A generic strategy DSL, selector chooser, optimizer, or “run everything” UI is not Phase-15 scope.
> **Evidence:** `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`; `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`; 2026-08-18 Deep Research reviews.

> **Implementation status — 2026-08-18**
> **Slice 1:** complete and remediation-verified; results in `docs/research/2026-08-18-qap-scanner-slice1-results.md`.
> **Slice 2:** complete and repository-verified at tested commit `809431c`; results in `docs/research/2026-08-18-qap-scanner-slice2-results.md`.
> **Slice 3:** complete. Milestone-6 integrity closure is `dd9df14`, the Milestone-7 application vertical is `0a15506`, the original M9 full repository gate was green at `a79bd4d`, and the post-review remediation handoff is `142a18d`. Slice-4 closure subsequently updated the stale OpenAPI assertions that had temporarily blocked the whole-repository suite; the current final repository gate is green at 672 passed / 1 skipped. The former Milestone-8 Candidate Workbench is superseded by the now-complete Slice 4; Milestone-9 backend/Phase-15 research-kernel closure remains complete. Results: `docs/research/2026-08-18-qap-scanner-slice3-results.md`.

> **Product-boundary amendment — 2026-08-19**
> The standalone Slice-3 read-only Candidate Workbench is intentionally not implemented. The unified Slice-4 QAP application/workbench now exposes the completed Slice-1 discovery, Slice-2 prospective/actionability, and Slice-3 basket-research operations instead of duplicating API DTOs, route hierarchies, navigation, and frontend evidence views across two consecutive workbenches.
> **Slice-4 plan:** `docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md`. **Verified results:** `docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`; final rendered executable state `6961937`.

## 1. Authoritative slice map

Phase 15 is an umbrella plan. Detailed Scanner-V1 contracts live in the slice specs and take precedence if this plan is less specific.

```text
Slice 1 — bounded pair discovery foundation
  docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md

Slice 2 — prospective evidence + liquidity qualification
  docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md

Slice 3 — broad asset-native momentum + manual basket workbench
  docs/superpowers/specs/2026-08-18-qap-scanner-slice3-asset-momentum-basket-design.md
  docs/superpowers/plans/2026-08-18-qap-scanner-slice3-implementation-plan.md

Slice 4 — unified human-operated QAP application
  docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md
```

Slice 4 is not part of the Phase-15 research-kernel completion gate. Phase 15 closes after the Slice-3 backend vertical and repository evidence are complete; Slice 4 then productizes the completed Slices 1–3 through one application boundary.

## 2. Global constraints

- Primary objective remains net portfolio wealth relative to matched passive HODL.
- Relationship intelligence earns incremental credit only over the strongest applicable predeclared simple admissible control.
- Scanner results are hypotheses; only authoritative QAP replay produces official historical economics.
- Slice-1 authoritative replay establishes historical research economics under the frozen QAP replay/cost model; it does not retroactively certify venue precision, historical MARKET-filter reference prices, spread/depth, or executable capacity when those observations were not captured contemporaneously.
- Same-sample screening/ranking/replay remains development/search evidence.
- Prospective evidence requires a frozen rule/candidate before outcome data exists.
- Reserved final OOS cannot be searched, previewed, or consumed by ordinary scanner work.
- Every search-bearing decision and manual override remains attributable.
- No opaque composite score may replace HODL/control economics, costs, drawdown, or search provenance.
- One portfolio/inventory authority remains constitutional.
- Browser/API layers may configure/inspect admitted operations but never recompute financial truth.
- No live credentials, order placement, leverage, borrowing, derivatives, unowned shorts, or deployment authority.
- No database, distributed queue, scheduler platform, plugin registry, generic strategy DSL, or optimizer without separately earned need and design approval.

## 3. Product/research flow

Scanner V1 is intentionally narrower than the original generic Phase-15 workflow:

```text
admitted point-in-time Binance/Gate evidence
        ↓
fixed ScannerProtocol version
        ↓
Slice 1: one SSD pair graph
        ↓
fixed residual-MR + ratio-MR trials
        ↓
approximate ranking
        ↓
hard top-K authoritative QAP replay
        ↓
deep-replay survivors
        ↓
Slice 2: immutable forward enrollment
        ↓
prospective candidate evidence + liquidity qualification
        ↓
Slice 3: asset-native momentum + user-selected 3–6 asset baskets
        ↓
one combined long-only target through QAP
```

The operator may pin pairs/baskets. Manual input is explicit lineage, not a hidden replacement for automatic discovery.

## 4. Slice 1 — bounded pair discovery

The Slice-1 spec owns these contracts:

- three-valued point-in-time eligibility;
- separate Binance-USDT and Gate-USDT graphs;
- one normalized-log-price SSD generator;
- `k=8` nearest-neighbor budget per asset/horizon;
- fixed horizon/resolution mapping;
- residual-MR and log-ratio-MR only;
- residual orientations refit separately; log-ratio reciprocity is exact;
- three frozen coarse templates per family/horizon;
- a non-authoritative scout proxy with exact neutral/no-action/entry state semantics;
- complete search ledger;
- at most ten automatic authoritative replays per horizon, with frozen asset-diversity and pair/family caps;
- candidate-specific HODL/control economic gates;
- no positive-proxy admission gate;
- no adaptive diagnostic router.

Phase 15 must not reintroduce a UI or backend path for selecting among arbitrary pair generators, thresholds, parameter grids, or alpha families during Scanner-V1 execution.

## 5. Slice 2 — prospective evidence and liquidity

The Slice-2 spec owns:

- immutable forward cohort enrollment after Slice-1 development selection;
- prospective evidence checkpoints using only later-completed observations;
- strict separation from `forward_paper` operational dry-run evidence;
- candidate-level forward economics through existing QAP replay;
- cohort/policy-selection evidence that does not algebraically sum overlapping pair books;
- append-only L1/book-ticker and shallow-depth capture for promoted/pinned instruments;
- coverage requirements and direct book-sweep capacity estimates;
- `research_only`, `small_capacity`, and `tradable_now` classification as `instrument/candidate × timestamp × hypothetical capital`, not a permanent coin label;
- no retroactive certification of historical capacity where historical spread/depth evidence does not exist.

Prospective evidence does not grant live authority.

## 6. Slice 3 — designed basket and broader discovery surface

The detailed Slice-3 design is `docs/superpowers/specs/2026-08-18-qap-scanner-slice3-asset-momentum-basket-design.md`, with its completed file/task plan at `docs/superpowers/plans/2026-08-18-qap-scanner-slice3-implementation-plan.md`. Those documents remain the detailed authority if this umbrella summary is less specific. Verified results are recorded in `docs/research/2026-08-18-qap-scanner-slice3-results.md`.

The frozen Scanner-V1 boundary is now:

- broad **asset-native** relative momentum using one O(N) formation rule per horizon, never pairwise NxM momentum search;
- manual same-venue 3–6 asset baskets only;
- one source scan, one horizon, and one decision resolution per basket;
- at most one explicitly selected `candidate_id` per unordered pair;
- stateful ternary `{-1, 0, +1}` pair preferences that preserve the existing Slice-1 neutral/hold/entry hysteresis;
- equal edge contribution with exact incidence-pressure -> declared-degree normalization -> component centering -> fixed ±10pp asset-tilt resolution;
- equal-weight neutral economic allocation and USDT as execution-only bridge;
- one feasible long-only target vector owned by `qap.policy`;
- one authoritative QAP portfolio replay through the existing Phase-11 multi-asset executor;
- matched HODL, the frozen mechanical band control, and a pair-blind relative-momentum control under the same timing/cost path;
- pair-level Slice-2 evidence visible beside basket edges but never algebraically converted into basket capacity or prospective status;
- no standalone Slice-3 scanner API/Candidate Workbench; those read models and human workflows move to the unified Slice-4 application after backend contracts are proven.

Do not implement automatic graph-to-basket discovery, a portfolio optimizer, learned reliability weights, momentum/reversal routing, cross-horizon authority weighting, cross-venue shared inventory, or basket-level `tradable_now` in Scanner V1.

## 7. Core artifact families

Use focused current-schema artifacts rather than deriving research state from filenames or browser memory.

### Scan generation

Slice 1 persists immutable scan intent, PIT universe evidence, candidate graph, all fixed scout trials, promotion decisions, a pre-enumerated replay-attempt ledger, and references to authoritative QAP run artifacts.

A scan is incomplete until its final manifest publishes atomically. Interrupted staging state may support deterministic resume but is not completed evidence.

Every promoted candidate gets a deterministic replay-attempt record before `qap.experiment` preparation/data admission begins. Preparation/setup failures remain explicit failed attempts and therefore remain in the search denominator even when no experiment run manifest could be produced.

### Candidate lineage

A candidate binds:

- exact protocol/version;
- `as_of` and information cutoff;
- venue/pair/orientation/horizon/resolution/model/template;
- source artifact and exact evaluated-slice fingerprints;
- automatic/manual selection lineage;
- scout proxy values;
- authoritative replay run identity/status.

No scanner table becomes an alternative owner of run economics.

### Historical execution claim boundary

Slice 1 is pair-native and may use the existing deterministic historical direct replay to compare QAP, matched HODL, and the strongest declared simple control under identical costs/timing **only when a real direct venue instrument and admitted historical bars exist for that candidate pair**. Discovered indirect crosses may remain scout/research evidence but are ineligible for authoritative deep replay; Slice 1 must not synthesize a cross, route through a bridge, or pretend the single-instrument replay engine executed Phase-11 bridge semantics. It must not synthesize historical venue metadata or Binance/Gate MARKET notional-reference truth from current exchange state or OHLCV. Missing contemporaneous execution/capacity observations remain unknown.

Slice 2 is the first scanner slice allowed to turn captured current public order constraints/spread/depth/reference evidence into `research_only`, `small_capacity`, or `tradable_now` statements. Its capacity math is conservative: required order fraction comes from the frozen policy's 40/60↔60/40 transition envelope plus any larger current drift correction, and the liquidity friction ceiling derives only from the frozen adverse QAP `CostModel`. Required book snapshots that cannot fill a tested size make that size infeasible rather than disappearing from the percentile denominator. Slice 3 uses the existing Phase-11 multi-asset/bridge executor for basket execution and does not create scanner-owned routing.

### Forward evidence

Slice 2 adds immutable freeze/cohort identities and append-only prospective evaluation checkpoints. Prospective status comes from the freeze/outcome time ordering, not from relabeling old development data after the fact.

### Basket analysis

Slice 3 may reference persisted candidates/evidence but must generate one combined target and send it through normal QAP replay. It must never add terminal pair P&Ls in the browser.

## 8. Ranking and falsification

Scanner ranking is a bounded research funnel, not proof of alpha.

Historical promotion uses a clearly non-authoritative scout proxy only to allocate the fixed deep-replay budget. Authoritative replay then exposes, separately:

- vs matched HODL;
- vs strongest applicable simple control;
- explicit costs/turnover/fills;
- drawdown/concentration diagnostics;
- model/template/orientation identity;
- search denominator and selection source.

A candidate failing either mandatory economic gate is not a historical survivor.

Formal SPA/Reality Check/Romano-Wolf/DSR/PBO methods may be used later at research-review boundaries over suitable frozen comparable series. They are not per-row Scanner-V1 promotion gates.

## 9. API and workbench boundary

Phase 15 no longer implements a scanner-specific browser/API surface. Its job is to leave Slices 1–3 with stable Python application operations, immutable evidence, and authoritative QAP result references.

Slice 4 now owns the implemented unified human-operated application. Its bounded command vocabulary initiates admitted discovery, prospective, capture/qualification, and basket-research operations, while its query/read models expose the resulting immutable evidence.

The Slice-4 browser still does not:

- fit models or supply hidden model/protocol constants;
- compute resolver targets, fills, accounting, costs, capacity, or wealth;
- mutate completed scan/freeze/checkpoint/basket/run evidence;
- reveal or consume reserved final OOS;
- launch an unbounded search or generic strategy DSL;
- provide private-exchange/live-capital/deployment authority.

Phase-14 Research Runs remains the completed-run evidence archive. Slice-4 scanner/prospective/basket views link to immutable experiment/portfolio/pair evidence rather than copying their financial truth.

## 10. Reproducibility and recovery

- Identical frozen scan protocol + PIT universe + exact data slices + manual inputs produce the same candidate identities/rankings.
- Search-bearing failures/losers remain attributable.
- Completed QAP run artifacts are immutable.
- Interrupted scan/forward processing resumes from persisted identities, never UI display state.
- Future rows appended to a source artifact cannot alter an older candidate's evaluated-slice identity.
- Changing protocol/model/template/promotion/liquidity rules creates a new version; previous forward evidence is not silently pooled into the new policy's record.

## 11. Testing strategy

Prioritize contracts and end-to-end semantics over combinatorial UI tests.

Backend coverage across the slices must prove:

- PIT admission fails closed;
- fixed candidate generation/trial enumeration is deterministic;
- oriented residual trials and exact log-ratio reciprocity are correct;
- future-row append does not alter frozen slice identity;
- manual/automatic overlap preserves one candidate plus both lineage facts;
- deep replay budgets cannot be exceeded;
- scanner never replaces QAP financial authority;
- prospective observations cannot precede freeze;
- forward operational dry-run evidence cannot masquerade as prospective alpha evidence;
- incomplete microstructure cannot graduate a candidate from `research_only`;
- basket combination eventually goes through one QAP target/inventory.

Frontend/E2E coverage is implemented and verified in Slice 4. Its unified workbench exercises the completed Slice-1/2/3 backend operations through deterministic no-network browser workflows while preserving the existing Phase-14 analytical routes.

## 12. Exit criteria

Phase 15 is complete only when all approved scanner slices have reached their own exit criteria. At minimum the completed program must demonstrate:

- [x] bounded deterministic pair discovery with exact provenance;
- [x] fixed automatic deep-replay budget independent of universe size;
- [x] existing QAP remains sole financial authority through Slices 1–2;
- [x] historical search cannot be mislabeled prospective or final OOS;
- [x] forward candidate evidence is frozen before outcomes arrive;
- [x] liquidity/capacity claims are backed by captured market evidence or fail closed;
- [x] historical missing depth is not retroactively fabricated;
- [x] broad momentum is implemented asset-native rather than pairwise NxM;
- [x] user-selected basket research produces one long-only QAP target/inventory through the approved Slice-3 resolver;
- [x] negative/no-survivor research generations remain valid outcomes;
- [x] no live/deployment authority has been introduced through Slices 1–3.

## 13. Stop conditions

Return to design review before introducing:

- a second accounting/backtest authority;
- adaptive/unbounded search without a new frozen protocol;
- multiple competing pair generators selected from downstream P&L;
- automatic final-OOS consumption;
- Bayesian/AutoML/LLM strategy search;
- generic strategy/plugin DSLs;
- automatic portfolio discovery or optimizer-driven baskets;
- databases/distributed queues/cloud schedulers merely for convenience;
- live/private exchange API or capital deployment;
- any change to QAP's protected objective, action space, benchmark, timing/fill/cost, universe, or OOS semantics.
