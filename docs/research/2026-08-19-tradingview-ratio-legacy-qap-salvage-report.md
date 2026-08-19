# TradingView Ratio / Legacy QAP Salvage Report

**Date:** 2026-08-19
**Source repository:** `/home/hamza/repo/tradingview_ratio`
**Source branch / inspected HEAD:** `main` / `8d65bf28`
**Target context:** current QAP Phase 17 Product Layer work
**Status:** read-only forensic synthesis; this report does not authorize implementation, policy changes, research promotion, replay, runtime behavior, or live trading.

## Executive conclusion

The original `tradingview_ratio` repository contains substantial reusable knowledge, but the strongest salvage target is **not the old application architecture**.

The legacy repository has two distinct kinds of value:

1. **High-value accumulated contracts, algorithms, and product/research patterns** that can inform current QAP.
2. **High-coupling legacy runtime code** that should generally not be ported wholesale.

The correct strategy is therefore:

```text
legacy repository
  -> extract proven ideas and failure lessons
  -> map each idea to a current QAP owner
  -> reimplement only where current QAP lacks the capability
  -> preserve current scientific / Product Layer authority boundaries
```

The most immediately valuable findings are:

- historical acquisition gap planning from `AdaptiveFetcher`;
- API-pressure/rate-limit handling from `APIGuardian`;
- truthful discovery-funnel and progress-state modeling;
- first-class data freshness/readiness reporting;
- explicit evidence/authority boundaries and non-authority declarations;
- beginner-facing phase explanations and next-action UX;
- investigation and research-lifecycle discipline;
- basket/universe maintenance semantics;
- the original inventory-relative/HODL product thesis;
- ownership and hidden-state ledgers as architecture-planning tools.

The most important negative finding is equally clear: **do not merge or transplant the old runtime architecture into current QAP.** Several legacy modules combine exchange access, caching, symbol resolution, presentation, persistence, policy, and trading semantics in ways that current QAP has intentionally separated.

---

## 1. Scope and method

This investigation inspected the legacy repository read-only and compared its major concepts against the current `/home/hamza/repo/qap` architecture.

Primary legacy evidence reviewed included:

- `README.md`
- `docs/INVARIANTS.md`
- `docs/UX_MASTER_PLAN.md`
- `docs_v2/research-operating-system.md`
- `docs_v2/2026-06-17-original-intent-reconstruction-results.md`
- `docs_v2/2026-06-17-canonical-inventory-object-results.md`
- `docs_v2/2026-06-17-inventory-discovery-topology-results.md`
- `docs_v2/2026-06-17-research-object-and-promotion-object-results.md`
- `docs_v2/2026-06-17-basket-admission-and-maintenance-results.md`
- `docs_v2/qap-v1-runtime-map.md`
- `docs_v2/qap-v1-runtime-ownership-boundary-matrix.md`
- `docs_v2/qap-v1-hidden-state-and-assumptions-ledger.md`
- `src/python/core/data/adaptive_fetcher.py`
- `src/python/core/data/fetcher.py`
- `src/python/core/data/freshness_report.py`
- `src/python/core/data/market_snapshot.py`
- `src/python/core/api_guardian.py`
- `src/python/core/pair_discovery.py`
- `src/python/core/accumulation_scanner.py`
- `src/python/core/opportunity_ranker.py`
- `src/python/core/mesh_validator.py`
- `src/python/core/portfolio_heat.py`
- `src/python/core/decision_logger.py`
- `src/python/core/research/economic_screening.py`
- `src/python/core/research/validation_evidence.py`
- `src/cli/utils/phase_banner.py`
- `src/cli/translators/insights.py`
- `src/cli/presenters/decision_verdict.py`
- `docs/user-guides/BEGINNER_WORKFLOW.md`
- `scripts/ops/asset_research_eligibility_framework.py`

The current QAP comparison focused on the Phase 17 Product Layer design/plan and relevant present-day owners under:

- `src/qap/market/*`
- `src/qap/scanner/*`
- `src/qap/experiment/*`
- `src/qap/evaluation/*`
- `src/qap/api/*`
- `src/qap/portfolio/*`
- `web/src/*`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`

This is not a line-by-line migration plan. It identifies reusable knowledge and the safest present-day destination for that knowledge.

---

## 2. Salvage classification

### A. Reuse conceptually now

These findings should directly inform active or near-term Phase 17 work:

- acquisition gap planning;
- request throttling / retry policy;
- data freshness/readiness read models;
- discovery funnel/progress state;
- authority-boundary declarations;
- plain-language phase explanations;
- backend-owned next-action presentation;
- explicit negative/neutral result semantics.

### B. Reuse as research/product design evidence

These are valuable but should not automatically become code:

- inventory-first/HODL product framing;
- economic truth vs mechanism truth vs portfolio-expression truth vs strategy truth;
- investigation template;
- research debt tracking;
- basket admission and maintenance semantics;
- ownership/hidden-state audit methodology.

### C. Already superseded by current QAP

These should not be reimplemented because current QAP has stronger owners already:

- HODL / benchmark evaluation primitives;
- concentration diagnostics;
- anchor analysis;
- deterministic experiment provenance;
- scanner/experiment artifact ownership.

### D. Reject as legacy architecture

Do not port wholesale:

- `DataFetcher` as a monolithic owner;
- CCXT-driven multi-market fallback as Product truth;
- presentation-layer verdict authority;
- `OpportunityRanker` live-action semantics;
- synthetic Tethered Mesh tradeability rules;
- portfolio heat / bounded grid / live trading runtime systems;
- the old oversized CLI/module organization.

---

## 3. Highest-value engineering salvage: historical acquisition gap planning

### Legacy owner

`src/python/core/data/adaptive_fetcher.py`

### What it does well

The legacy `AdaptiveFetcher` does not treat historical acquisition as a simple pagination loop. It models the requested interval against what is already known and classifies missing regions.

The effective algorithm is:

```text
requested historical window
        ↓
read cached observations
        ↓
classify missing regions
  - head gap
  - internal gap
  - tail gap
        ↓
remove known-unfillable ranges
        ↓
coalesce nearby missing ranges
        ↓
fetch only required ranges
        ↓
merge observations
        ↓
verify interval consistency
        ↓
recompute coverage
        ↓
fail closed when stale data remains stale
```

Particularly useful methods include:

- `_identify_all_gaps()`
- `_coalesce_gaps()`
- `_get_exchange_earliest_timestamp()`
- `_classify_head_gap_reason()`
- `_filter_known_gaps()`
- `_record_unfilled_gaps()`

The old implementation distinguishes between:

- genuine pre-listing absence;
- an unverified head shortfall;
- an internal missing-data interval;
- a stale/missing tail;
- a previously attempted but unavailable range.

It also includes retry-TTL semantics for uncertain historical head gaps, preventing repeated expensive exchange queries for the same unresolved range.

### Why this matters to current QAP

Phase 17 M3 is creating honest historical acquisition and immutable generations. The old acquisition algorithm contains operational lessons that should not be rediscovered from scratch.

The reusable concept is **acquisition planning**, not the old mutable cache.

A current-QAP form could conceptually be:

```text
RequestedWindow
CurrentCoverage
MissingWindow[]

MissingWindow.kind:
  head
  internal
  tail

MissingWindow.disposition:
  fetch
  known_unavailable
  not_yet_available
  unresolved
```

Current QAP should continue to publish validated immutable generations with provenance. The old SQLite/cache ownership should not return.

### Recommendation

**Adapt conceptually into M3 acquisition. Do not port the legacy class.**

---

## 4. High-value engineering salvage: API pressure and rate-limit handling

### Legacy owner

`src/python/core/api_guardian.py`

### Useful behavior

`APIGuardian` contains several operational protections:

- proactive request-weight budgeting;
- capacity reservation before concurrent calls;
- release of reserved capacity on failed requests;
- Binance response-header weight tracking;
- sleeping outside the synchronization lock;
- exponential retry/backoff;
- observable current capacity/status.

The important design idea is that rate limiting is not merely an exception handler. It is an acquisition policy.

Conceptually:

```text
before request
  -> reserve expected capacity
  -> wait when required

response
  -> reconcile against exchange headers

failure
  -> release reservation if request did not consume expected capacity
  -> apply bounded backoff for rate-limit responses
```

### Current-QAP fit

Current public adapters should remain explicit venue adapters. The legacy code's CCXT coupling and historical numerical limits should not be copied.

A cleaner modern owner would be a small acquisition-level throttle/backoff policy used by the explicit Binance/Gate adapters.

Potential conceptual interface:

```text
AcquisitionThrottle

before_request(cost)
observe_response(headers)
observe_rate_limit(response)
release(cost)
```

The exact policy must be based on current supported-venue contracts, not legacy constants.

### Recommendation

**Reimplement the behavior narrowly if M3 needs sustained historical acquisition. Do not reuse the CCXT-bound implementation or stale constants.**

---

## 5. Discovery funnel and progress state

### Legacy owner

`src/python/core/pair_discovery.py`

### Valuable structures

The legacy discovery pipeline kept explicit counts through each stage using `DiscoveryStats`:

```text
total symbols fetched
symbols after volume filter
symbols after history filter

total possible pairs
pairs after correlation filter
pairs sent to deeper validation
pairs tested
pairs surviving
```

It also defined a structured `ProgressUpdate`:

```text
stage
current
total
message
```

### Product value

This directly addresses a current Product-layer comprehension problem: a nontechnical user should be able to answer **what QAP is scanning** and **how far it has progressed**.

A modern Product presentation should not expose old scanner internals. Instead, current QAP can map its real scanner stages into plain-language funnel states, for example:

```text
Researching 24 approved assets
276 possible relationships
83 passed the first relationship check
12 received deeper historical evaluation
3 produced Research Ideas
```

These numbers must come from authoritative backend scanner state, not be recomputed in React.

### Recommendation

**Adopt the funnel/progress pattern for M5. Map it to current scanner truth rather than old cointegration terminology.**

---

## 6. Data freshness/readiness as a first-class Product contract

### Legacy owners

- `src/python/core/data/freshness_report.py`
- `src/cli/use_cases/data_freshness_use_case.py`
- `src/python/core/data/market_snapshot.py`

### Useful pattern

The legacy system separated machine-readable freshness state from command rendering.

`SymbolFreshness` exposed concepts such as:

```text
symbol
bars_loaded
last_update
staleness
age_minutes
```

The pair-level report included:

```text
base bars
quote bars
paired bars
paired-bar ratio
market snapshot
fallback mode
worst staleness
```

`MarketSnapshot` also made metadata freshness explicit.

### Current-QAP fit

Phase 17 M4 is intentionally building a stronger version of this concept with:

- explicit Research Universe scope;
- immutable historical generations;
- backend-owned safe cutoffs;
- timeframe readiness;
- direct-market readiness where required;
- no frontend scientific calculation.

The old code therefore should not be ported, but it provides historical evidence that **freshness/readiness deserves a first-class Product read model**, not incidental filesystem or scanner metadata.

### Recommendation

**Use as design evidence for M4/M5. Current QAP's new readiness owner remains authoritative.**

---

## 7. Human-comprehension pattern: always explain what a phase can and cannot conclude

### Legacy owners

- `src/cli/utils/phase_banner.py`
- `docs/user-guides/BEGINNER_WORKFLOW.md`
- `README.md`

### Useful Product principle

The old CLI repeatedly told users:

```text
what phase am I in?
what is this phase for?
what authority does it have?
why can it not do more?
```

For example, Discovery was explicitly framed as observational and non-decisional.

The old beginner workflow also attached a learning goal to each stage and emphasized rules such as:

> No data = no opinion.

It also treated zero-action/neutral outcomes as valid evidence instead of software failure.

### Current-QAP translation

The terminology must change, but the interaction rule should survive.

Examples:

```text
Historical research
QAP is comparing relationships among the assets you approved.
These results describe historical evidence. They are not live-trading instructions.
```

```text
Later evidence
This checks what happened after the original Research Idea was frozen.
It does not rewrite the original historical evidence.
```

```text
Current public-market evidence
This estimates whether current public liquidity evidence supports evaluating the amount entered.
QAP does not place or authorize live trades.
```

### Recommendation

**Adopt the phase-explanation pattern in M5/M6 using current evidence classes and Product terminology.**

---

## 8. Backend-owned next actions

### Legacy owners

- `src/cli/ui_components.py`
- `src/cli/presenters/decision_verdict.py`
- README `Next Action` UX

### What was good

The old product understood that a result should not merely dump metrics. It should explain what the user can do next.

The useful shape is:

```text
What happened?
Why?
What should I do next?
```

### What was unsafe

Legacy presenter code sometimes derived strong operational recommendations directly from raw statistical metrics or presentation-layer classifications.

That must not return.

### Current-QAP rule

Use:

```text
backend authoritative state
        ↓
backend authoritative valid next actions
        ↓
React renders the explanation/action
```

Do not use:

```text
raw metric
  ↓
frontend invents a conclusion
```

### Recommendation

**Adopt the interaction model, reject the legacy authority implementation.**

---

## 9. Translation/presentation architecture

### Legacy owner

`src/cli/translators/insights.py`

### Useful pattern

The old code centralized technical-to-human translation into structured outputs rather than scattering prose throughout presenters.

The shape was roughly:

```text
raw value
category
human label
technical evidence label
confidence wording
explanation
```

### Unsafe legacy content

Some old translations turned p-values or z-scores into phrases such as strong trading recommendations or directional certainty. Those semantics do not satisfy current QAP's research-integrity standard.

### Current-QAP opportunity

A backend presentation-state owner can translate authoritative research state into plain language while preserving raw evidence under progressive disclosure.

The reusable lesson is centralization, not the old thresholds or wording.

### Recommendation

**Reuse the translator architecture concept. Rewrite all semantics around current authoritative state.**

---

## 10. Research Operating System: one of the strongest legacy assets

### Legacy owner

`docs_v2/research-operating-system.md`

### Key conceptual separation

The document separates:

```text
Economic Truth
  -> Mechanism Truth
  -> Portfolio Expression Truth
  -> Strategy Truth
```

Its most important implication is:

> Failure of one implementation or strategy expression does not automatically falsify the broader economic thesis.

This is highly relevant to how current QAP should describe Research Ideas and History.

A poor Product sentence is:

```text
BTC/ETH failed.
```

A more scientifically meaningful sentence identifies the failed object:

```text
Historical relationship evidence was present, but this economic implementation did not survive the declared cost checks.
```

or:

```text
The original historical idea survived, but later evidence weakened it.
```

### Legacy research lifecycle

The old operating system also defined a staged lifecycle:

```text
Observation
-> Hypothesis
-> Investigation
-> Attribution
-> Mechanism discovery
-> Validation
-> OOS
-> Portfolio expression
-> Replay
-> Promotion
```

Current QAP should not expose all of these stages to normal users, but the conceptual separation is valuable internally and for History semantics.

### Recommendation

**Preserve as research-methodology guidance. Do not automatically convert the full lifecycle into Product navigation.**

---

## 11. Investigation template and research debt

### Legacy owner

`docs_v2/research-operating-system.md`

Every investigation was expected to answer:

1. What was tested?
2. Why was it tested?
3. What was learned?
4. What was falsified?
5. What remains uncertain?
6. What is the next highest-information experiment?

The same document also formalized research debt: unresolved assumptions should not quietly become architecture or authority.

### Current-QAP value

This is useful for:

- internal Research Idea metadata;
- History summaries;
- experiment handoffs;
- deciding whether a negative result retires an implementation or a broader claim;
- preventing undocumented uncertainty from turning into Product truth.

### Recommendation

**Keep this as an internal research discipline; expose only the pieces that help users understand completed work.**

---

## 12. Explicit authority and non-authority declarations

### Legacy owner

`src/python/core/research/economic_screening.py`

A strong legacy pattern is the explicit authority boundary. The economic screen includes a declaration equivalent to:

```text
MULTI-PAIR SCREENING AND MEASURED RANKING ONLY
NO VALIDATION
NO ALPHA CLAIM
NO CANDIDATE PROMOTION
NO RUNTIME AUTHORITY
```

The result also carries:

- determinism information;
- ranking policy;
- counts;
- ranked results;
- exclusions/failure ledger;
- authority boundary.

The ranking policy is transparent and explicitly has no magical aggregate score.

### Current-QAP value

This pattern can defensively strengthen Product/read-model contracts.

For example, a readiness response can internally declare:

```text
Authority: DATA_READINESS_ONLY

Does not authorize:
- candidate promotion
- capital allocation
- live trading
```

A Research Universe recommendation layer can similarly declare that it does not override explicit operator approval.

These declarations need not be primary UI copy, but they are valuable backend contract metadata and review evidence.

### Recommendation

**Adopt the contract pattern where new derived Product state could otherwise be mistaken for stronger authority.**

---

## 13. Asset eligibility: use the gate representation, not the old policy

### Legacy owners

- `scripts/ops/asset_research_eligibility_framework.py`
- `docs_v2/registries/asset-universe/asset-promotion-framework.md`

### Useful structure

The old framework represented each eligibility condition as structured evidence:

```text
gate
passed
evidence
```

and carried:

```text
failed_gates
rationale
authority
non_authority
```

That is much better than a single opaque eligible/ineligible boolean.

### Unsafe part

The old concrete thresholds and classifications are historical research policy. They must not silently become Phase 17 Product policy.

### Current-QAP translation

Current Product state could render backend-owned reasons such as:

```text
BTC

Approved by you                     yes
Current Binance spot identity       resolved
Short timeframe history             ready
Medium timeframe history            ready
Longer timeframe history            not ready
```

The Product Layer should explain **why** an asset or timeframe is unavailable without creating a new hidden research ranking system.

### Recommendation

**Reuse structured gate/reason outputs; do not port legacy eligibility thresholds or promotion labels.**

---

## 14. Basket and Research-Universe maintenance semantics

### Legacy owner

`docs_v2/2026-06-17-basket-admission-and-maintenance-results.md`

Four particularly strong principles emerged:

1. Temporary exclusion is not the same as constitutional removal.
2. Candidate failure is not the same as asset invalidity.
3. Do not mutate a frozen candidate mid-cycle to rescue it.
4. Material changes to the governing basket/universe should create a new candidate cycle rather than rewriting the old one.

### Current-QAP value

These map directly onto Phase 17 Research Universe and Research Idea behavior.

Examples:

```text
SOL is approved by the operator
+
Gate lacks enough admitted historical data
```

should not imply:

```text
remove SOL from the approved Research Universe
```

Similarly:

```text
BTC/ETH research rejected
```

must not imply:

```text
BTC invalid
ETH invalid
```

The layers are distinct:

```text
operator approval
market/data readiness
relationship evidence
candidate evidence
portfolio evidence
```

### Recommendation

**Carry these distinctions into Phase 17 lifecycle and maintenance rules.**

---

## 15. Original product thesis: inventory-aware research rather than generic PnL chasing

### Legacy evidence

The strongest historical reconstruction appears in:

- `docs_v2/2026-06-17-original-intent-reconstruction-results.md`
- `docs_v2/2026-06-17-canonical-inventory-object-results.md`
- `README.md`
- legacy user guides.

The reconstructed original objective was approximately:

```text
Increase ownership of acceptable long-term assets by using relative-value
relationships and rebalancing opportunities, then compare the result against
passive holding in the same economic frame.
```

The old forensic work concluded that the broad economic object was closer to an anchor-aware ecosystem/basket of assets than to one isolated pair.

### Why this matters now

Phase 17's Product Layer is independently moving toward:

```text
operator-approved assets
  -> Research Universe
  -> relationships
  -> Research Ideas
  -> Portfolios
```

That direction is not a rejection of all legacy intent. In an important sense, it recovers part of the original user mental model while replacing the old implementation architecture.

### Current-QAP implications

Current QAP already contains stronger benchmark and evaluation primitives. No legacy engine port is required.

However, M8 Portfolio presentation should preserve meaningful questions such as:

- Did the research improve the declared owned-asset outcome relative to passive holding?
- Which assets contributed?
- Was the result concentrated in one asset or relationship?
- How much cost/turnover was required?

A generic headline USD return should not erase the declared economic objective.

### Recommendation

**Use the legacy thesis as product-intent evidence when refining Portfolio/History language, while keeping current QAP's declared experiment objective authoritative.**

---

## 16. Architecture-planning patterns worth retaining

### Legacy owners

- `docs_v2/qap-v1-runtime-ownership-boundary-matrix.md`
- `docs_v2/qap-v1-hidden-state-and-assumptions-ledger.md`

### Ownership matrix pattern

The legacy matrix explicitly recorded:

```text
current owner
candidate future owner
source of truth
allowed mutators
consumers
state lifetime
authority impact
characterization evidence
first safe move
blocked-by condition
```

### Hidden-state ledger pattern

The hidden-state ledger recorded:

```text
assumption
current owner
mutation surface
consumers
failure mode
required proof before movement
status
```

with statuses including:

```text
identified
characterized
partially_proven
proven
blocked
unknown
```

### Current-QAP value

These are useful architecture-review tools when Phase 17 reaches stateful operational areas such as:

- market-data publication/current-generation ownership;
- current-public-evidence collector persistence;
- process lifecycle / packaging;
- any future migration of research or operational state.

They are especially useful for preventing hidden mutable state from moving during refactors without proving consumers and failure modes.

### Recommendation

**Reuse the planning discipline when a Phase 17 change crosses state ownership boundaries. Do not create ledgers for ordinary small changes.**

---

## 17. What current QAP already supersedes

### Concentration diagnostics

Legacy areas such as `portfolio_heat.py` and later research concentration work should not be ported merely because they exist.

Current QAP already has dedicated evaluation ownership, including concentration diagnostics under:

```text
src/qap/evaluation/attribution.py
```

### HODL / benchmark logic

Legacy QAP invested heavily in passive-hold comparison. Current QAP already owns benchmark evaluation through its modern evaluation/experiment architecture, including:

```text
src/qap/evaluation/hodl.py
```

Use the old material for intent/history, not duplicate runtime logic.

### Anchor analysis

Legacy Tethered Mesh and `AnchorRegistry` should not be reintroduced wholesale. Current QAP already has explicit anchor analysis/read models under current relationship/API owners.

### Provenance and deterministic evidence

Later legacy v2 work moved toward manifests, hashes, exact sources, failure ledgers, and authority boundaries. Current QAP's scanner/experiment artifacts are already more explicit and better separated.

### Recommendation

**Before implementing any legacy concept, search current QAP for an existing owner. Prefer extension of the current owner over parallel legacy-style machinery.**

---

## 18. Explicit rejection list

### 18.1 Do not port `DataFetcher`

Legacy path:

```text
src/python/core/data/fetcher.py
```

The module is approximately 1,800 lines and owns too many concerns:

- CCXT construction;
- exchange state;
- symbol normalization;
- market loading;
- shared market caching;
- persisted market snapshots;
- OHLCV fetches;
- adaptive fetch fallback;
- futures/swap fallback;
- pagination;
- resampling;
- SQLite/cache behavior;
- output/printing;
- freshness metadata.

The legacy repository's own runtime ownership documentation identified this as hidden-state and ownership debt.

Current Phase 17 explicit adapters plus Product/market-data owners are a materially better architecture.

**Verdict: reject wholesale port.**

### 18.2 Do not adopt CCXT as current Product truth merely because legacy QAP used it

The old fetcher demonstrates how an exchange abstraction can gradually absorb business logic:

```text
spot missing
-> try swap
-> try future
-> reload markets
-> try perpetual notation
-> fall back
-> cache
-> normalize/resample
```

Current explicit Binance/Gate adapters are cleaner for the supported-venue boundary.

CCXT can be reconsidered only if future venue breadth justifies the abstraction and the Product Layer preserves explicit venue identity/provenance.

**Verdict: defer.**

### 18.3 Do not port `OpportunityRanker`

Legacy path:

```text
src/python/core/opportunity_ranker.py
```

This module carries live-entry/recommendation semantics and shows signs of authority drift after later hardening. One path constructs diagnostic/neutral metrics and then excludes them because they are not canonical copula authority.

Current scanner -> evidence -> promotion/economic evaluation is cleaner.

**Verdict: reject.**

### 18.4 Do not restore synthetic Tethered Mesh tradeability

Legacy `mesh_validator.py` could treat a missing main market as synthetically tradeable when anchors existed.

Current QAP's stronger requirement for real direct same-venue economic execution/replay evidence should remain.

**Verdict: reject as authoritative execution logic.**

### 18.5 Do not derive research authority in presenters/React

Legacy files such as:

- `src/cli/presenters/decision_verdict.py`
- `src/cli/translators/insights.py`
- `src/cli/ui_components.py`

sometimes convert raw metrics into recommendations such as trading readiness/actionability.

Current rule should remain:

```text
backend owns scientific/economic/readiness state
frontend owns presentation only
```

**Verdict: reuse UX structure only.**

### 18.6 Do not port live-trading/runtime systems into Phase 17

Examples:

- `portfolio_heat.py`
- `rotation_manager.py`
- `bounded_grid.py`
- risk/live trading runtime machinery;
- funding-driven execution logic;
- in-repo live order/action assumptions.

These are outside the current Product authority and would reopen frozen scientific/runtime boundaries.

**Verdict: leave archived unless a future explicitly approved phase reopens them.**

### 18.7 Do not copy the old module organization

The legacy repo contains multiple very large files, including roughly:

```text
discover.py                    > 3,000 lines
backtest_report_compact.py     > 3,000 lines
research_use_case.py           ~ 2,900 lines
pair_discovery.py              > 2,200 lines
cache_repo.py                  > 1,800 lines
fetcher.py                     > 1,800 lines
```

Many concepts are useful, but the file/ownership structure is itself evidence of why current QAP should keep bounded owners and source-size discipline.

**Verdict: mine concepts, not organization.**

---

## 19. Phase 17 mapping

| Legacy finding | Current value | Likely Phase 17 destination | Disposition |
|---|---|---|---|
| Adaptive historical gap planning | Very high | M3 acquisition | Adapt algorithm |
| API Guardian throttle/backoff | High | M3 acquisition | Reimplement small/native |
| DiscoveryStats / ProgressUpdate | Very high | M5 Research | Adapt to current scanner funnel |
| Freshness report | High | M4/M5 readiness UX | Design evidence |
| Phase banners / beginner workflow | Very high | M5/M6 comprehension | Adapt language/structure |
| Next-action UX | Very high | M5/M6 | Backend-owned next actions |
| Translation layer | High | M5 | Reuse architecture, rewrite semantics |
| Research Operating System | Very high | M6/History/research governance | Conceptual reuse |
| Investigation template | High | Research metadata | Internal discipline |
| Explicit authority/non-authority | Very high | Backend read models/artifacts | Adopt pattern |
| Asset gate evidence structure | Medium/high | M2/M4 readiness explanation | Reuse structure only |
| Basket maintenance semantics | High | M2/M6/M8 | Adapt lifecycle rules |
| Inventory/HODL product thesis | Very high | M8 Portfolio/History | Product intent evidence |
| Ownership/hidden-state ledgers | High | M7/M9/stateful refactors | Planning pattern |
| Legacy DataFetcher | Low as code | None | Reject |
| CCXT orchestration | Low now | Future venue expansion only | Defer |
| OpportunityRanker | Low/unsafe | None | Reject |
| Synthetic mesh execution | Conflicts | None | Reject |
| UI-derived verdict authority | Conflicts | None | Reject |
| Live/grid/rotation runtime | Out of scope | Future explicit phase only | Leave archived |

---

## 20. Immediate notes for active M3 work

The following legacy findings are the only ones that should directly influence the current Binance/Gate acquisition agents without reopening broader design:

### Acquisition planning

Study:

```text
tradingview_ratio/src/python/core/data/adaptive_fetcher.py
```

for:

- head/internal/tail gap classification;
- missing-window coalescing;
- earliest-history evidence;
- known-gap suppression;
- retry TTL for uncertain head gaps;
- fail-closed stale-refresh behavior.

Reimplement only through current QAP's:

```text
validated market observations
immutable generations
explicit provenance
current-generation publication rules
```

### API pressure

Study:

```text
tradingview_ratio/src/python/core/api_guardian.py
```

for:

- proactive throttling;
- reservation/release semantics;
- response-header usage accounting;
- bounded retry/backoff;
- observable capacity.

Do not copy:

- CCXT ownership;
- stale hard-coded exchange limits;
- global mutable singleton assumptions.

---

## 21. Later notes for M4-M8

### M4 readiness

Legacy freshness reporting reinforces that readiness should be a backend-composed Product contract, not a UI inference.

### M5 Research experience

Use the old discovery funnel, phase explanation, beginner workflow, translator architecture, and next-action concepts to ensure the normal page answers:

```text
What is QAP researching?
What data is actually ready?
What happened?
What does this result mean?
What can I do next?
```

Keep protocol IDs, candidate IDs, capture internals, and equivalent backend vocabulary under progressive disclosure.

### M6 Research Idea lifecycle

Use the old separation between original evidence, later evidence, and stronger promotion/runtime claims. A negative later-stage result should identify which layer failed rather than rewriting every earlier claim.

### M8 Portfolio + History

Use the original inventory-aware objective and HODL-relative framing as product-intent evidence, while allowing the current experiment manifest/evaluation owner to define the actual objective function for each run.

History should distinguish:

- research object;
- evidence stage;
- what was learned;
- what was falsified;
- what remains uncertain;
- valid next action.

---

## 22. Final verdict

The months invested in `tradingview_ratio` were not wasted, but the reusable asset is primarily **knowledge captured in the repository**, not the repository's final runtime shape.

The strongest legacy contributions are:

```text
data acquisition discipline
+ explicit readiness/freshness
+ research-stage semantics
+ authority boundaries
+ negative/neutral result handling
+ beginner comprehension patterns
+ inventory-relative product intent
+ state-ownership audit discipline
```

The strongest lesson from the legacy architecture is what **not** to repeat:

```text
large multi-owner modules
+ presentation-derived authority
+ exchange abstraction leaking into business truth
+ synthetic execution assumptions
+ trading/runtime concepts mixed into research UX
```

The recommended strategy is therefore:

> **Preserve current QAP architecture. Selectively re-derive the valuable legacy patterns inside current owners. Never treat legacy code existence as approval to port it.**

This report is a reference artifact only. Any implementation that uses a finding from this document must still be justified against the current Phase 17 design, current authoritative owner, and current scientific/product constraints.
