# Phase 15 — Research Scanner and Candidate Workbench Plan

**Goal:** Add a bounded active-research workflow above the existing QAP economic kernel: point-in-time discovery, fixed-budget authoritative replay, prospective evidence, liquidity qualification, and later manual basket analysis.

**Architecture:** The scanner is a candidate-production/research-orchestration layer, never a second backtester. Existing QAP experiment, policy, execution, inventory, accounting, HODL/control, and cost semantics remain authoritative.

> **Update context — 2026-08-18**
> **Trigger:** The two scanner Deep Research passes and the user-approved Slice-1 review superseded Phase 15's earlier generic “choose generator/models/parameter grid” workflow.
> **Purpose:** Reconcile this umbrella plan with the bounded Scanner-V1 slice architecture and remove accidental authorization for a generic Cartesian scan builder.
> **Impact:** Phase 15 now delegates detailed semantics to the approved slice specs. Scanner V1 has one pair generator, fixed pair-native templates, a separate prospective/liquidity slice, and a later asset-native momentum/basket slice. A generic strategy DSL, selector chooser, optimizer, or “run everything” UI is not Phase-15 scope.
> **Evidence:** `docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md`; `docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md`; 2026-08-18 Deep Research reviews.

> **Implementation status — 2026-08-18**
> **Slice 1:** complete and remediation-verified; results in `docs/research/2026-08-18-qap-scanner-slice1-results.md`.
> **Slice 2:** complete and repository-verified at tested commit `dbc968a`; results in `docs/research/2026-08-18-qap-scanner-slice2-results.md`.
> **Slice 3:** not started. It remains a hard separate design/approval gate and is not authorized by Slice-1/Slice-2 completion.

## 1. Authoritative slice map

Phase 15 is an umbrella plan. Detailed Scanner-V1 contracts live in the slice specs and take precedence if this plan is less specific.

```text
Slice 1 — bounded pair discovery foundation
  docs/superpowers/specs/2026-08-18-qap-scanner-slice1-design.md

Slice 2 — prospective evidence + liquidity qualification
  docs/superpowers/specs/2026-08-18-qap-scanner-slice2-prospective-evidence-liquidity-design.md

Slice 3 — broad asset-native momentum + manual basket workbench
  future design spec after Slice 2 review/implementation evidence
```

Do not implement Slice 3 merely because this umbrella plan describes its intended boundary.

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

## 6. Slice 3 — future basket and broader discovery surface

Slice 3 requires a separate approved design after Slice-2 evidence. Its intended boundary is:

- broad **asset-native** relative momentum/trend discovery, computed per asset rather than converted into pairwise NxM work;
- manual 3–6 asset basket construction from scanner/pinned assets;
- one active opinion per unordered pair/horizon;
- ternary `{-1, 0, +1}` pair preferences initially;
- fixed/equal edge contribution rather than learned historical-quality weights;
- degree-normalized/component-neutral deterministic aggregation;
- one feasible long-only target vector;
- one authoritative QAP portfolio replay;
- scanner API and Candidate Workbench projections only after backend contracts are proven.

Do not implement automatic graph-to-basket discovery, a portfolio optimizer, learned reliability weights, or cross-horizon authority weighting in Scanner V1.

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

Slice 2 is the first scanner slice allowed to turn captured current public order constraints/spread/depth/reference evidence into `research_only`, `small_capacity`, or `tradable_now` statements. Its capacity math is conservative: required order fraction comes from the frozen policy's 40/60↔60/40 transition envelope plus any larger current drift correction, and the liquidity friction ceiling derives only from the frozen adverse QAP `CostModel`. Required book snapshots that cannot fill a tested size make that size infeasible rather than disappearing from the percentile denominator. A future approved Slice 3 must use the existing Phase-11 multi-asset/bridge executor for basket execution rather than creating scanner-owned routing.

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

No scanner web UI is required by Slices 1–2.

After the backend contracts are proven, Slice 3 may add a dedicated scanner route. The UI should present the frozen ScannerProtocol rather than expose a generic “choose any generator/model/grid” builder.

Expected user actions are bounded:

```text
inspect protocol / PIT universe
run or inspect canonical scan
pin a pair explicitly
inspect candidates and authoritative replay
inspect forward/liquidity evidence
select 3–6 assets for basket analysis
inspect one combined QAP replay
```

The browser does not:

- fit models;
- compute fills/accounting/wealth;
- mutate frozen scan definitions;
- reveal reserved final OOS;
- launch unbounded search;
- provide a live/deploy button.

Phase-14 Research Runs remains the completed-run evidence archive. Scanner views link to immutable run details rather than copying their financial truth.

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

Frontend/E2E coverage is deferred until a scanner workbench is actually admitted in Slice 3.

## 12. Exit criteria

Phase 15 is complete only when all approved scanner slices have reached their own exit criteria. At minimum the completed program must demonstrate:

- [ ] bounded deterministic pair discovery with exact provenance;
- [ ] fixed automatic deep-replay budget independent of universe size;
- [ ] existing QAP remains sole financial authority;
- [ ] historical search cannot be mislabeled prospective or final OOS;
- [ ] forward candidate evidence is frozen before outcomes arrive;
- [ ] liquidity/capacity claims are backed by captured market evidence or fail closed;
- [ ] historical missing depth is not retroactively fabricated;
- [ ] broad momentum, if admitted, is asset-native rather than pairwise NxM;
- [ ] user-selected basket research produces one long-only QAP target/inventory;
- [ ] negative/no-survivor research generations remain valid outcomes;
- [ ] no live/deployment authority is introduced.

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
