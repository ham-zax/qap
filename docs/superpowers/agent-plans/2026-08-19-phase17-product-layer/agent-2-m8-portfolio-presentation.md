# Agent 2 — Phase 17 M8-B Product Portfolio Presentation Convergence

**Repository:** `/home/hamza/repo/qap`

**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m8-portfolio`

**Branch:** `phase17-m8-portfolio`

**Coordination base:** assigned by Wave-10 coordination commit

## Mission

Complete the Product Portfolio presentation half of M8 over the already-integrated M8-0 basket provenance/source-binding foundation.

Do not change basket science. The mission is to make the existing authoritative manual portfolio research understandable and claim-aware for Product users while preserving strict PIT as an Advanced source.

## Own

### 1. Product-first basket source experience

Update the normal Portfolios workflow so current-approved Product research is the primary source experience when available.

Use existing `ScanSummaryDto.claim` / scan detail claim truth. Do not infer claim type from protocol strings in React.

Normal Product copy should make clear:

- source = Current Approved Market Research when applicable;
- `Data through ...` is a frozen Product research boundary, not a PIT universe claim;
- strict Historical Point-in-Time research remains an Advanced source option;
- source scan / venue / timeframe / resolution / protocol IDs may live under progressive disclosure.

Do not silently mix Product and PIT claims.

### 2. Preserve manual portfolio authority

Keep unchanged:

- exactly 3–6 manually selected economic assets;
- one venue;
- one horizon;
- one decision resolution;
- explicit exact candidate edge choice per unordered pair;
- valid scanner relationship evidence broader than only historical Research Ideas;
- isolated asset neutral behavior;
- no pre-run resolver target or target weights;
- no optimizer/auto-basket discovery.

Do not restrict candidate edges to `deep_replay_survivor` / M6 Research Ideas only.

M8-0 deliberately does not support Product asset-momentum lineage. The UI must not pretend that Product momentum is available or necessary. Do not add Product momentum support in this mission.

### 3. Claim-aware Portfolio result presentation

Consume the M8-0 basket read contract as authoritative for:

- `source_claim`;
- source scanner protocol identity;
- basket protocol identity;
- exact Product execution-generation audit bindings;
- source scan link;
- QAP run link.

On BasketDetail, do not label every source as "historical research". Use claim-aware Product vs PIT wording.

Keep protocol/fingerprint/physical generation details under progressive disclosure/audit surfaces, not primary novice copy.

### 4. Objective-aware explanation

Reuse the existing authoritative QAP experiment/portfolio projections to explain, when present:

- strategy vs matched HODL;
- strategy vs declared primary control;
- relative drawdown/time-below benchmarks;
- fees/slippage/turnover/fill count;
- starting/terminal allocation;
- terminal concentration / HHI;
- selected relationship edges and post-run rebalance evidence.

Do not replace the declared economic objective with a generic USD-return headline.

Do not claim numeric relationship-level or causal asset-level P&L contribution; current artifacts do not support that.

A terminal per-asset delta vs HODL may be described only as a holdings/value difference, not causal profit contribution.

### 5. Product language cleanup

Update stale pre-Phase-17 terminology in the owned Portfolio UI, such as references to "Discover" where the normal flow is now Research.

Primary Product language should use:

- Research;
- Research Ideas / relationship evidence;
- Portfolios;
- Current Approved Market Research;
- Historical Point-in-Time Research only when actually strict PIT.

## Do not own

Do not modify:

- `src/qap/scanner/basket_protocol.py`;
- `src/qap/scanner/basket_source.py`;
- `src/qap/scanner/basket.py`;
- `src/qap/experiment/basket_scanner_adapter.py`;
- M8-0 generation-binding code;
- scanner economics;
- graph resolver/policy targets;
- HODL/control/cost/economic-gate definitions;
- M8-A History backend/read composition or Home Activity affordance;
- M7 collector/qualification code;
- M9 packaging/process lifecycle;
- live/private exchange authority.

The M8-0 public basket read contract should be sufficient. If it is genuinely insufficient for truthful presentation, stop and report the missing read contract rather than independently redesigning basket provenance. Avoid generated API/OpenAPI changes unless that concrete insufficiency is proven.

## Verification

Testing remains opt-in. Do not create, modify, or run tests unless separately authorized or independently mandatory.

Use bounded rendered/manual evidence for the Product/PIT Portfolio source states and final TypeScript/build/static checks relevant to changed files.

At minimum verify:

- Product current-approved source can be selected and submitted through the unchanged basket mutation contract;
- Product source is not called PIT or historical-as-of;
- strict PIT remains clearly Advanced and correctly labeled;
- manual 3–6 and exact-edge selection remain intact;
- zero-promotion valid scout relationship remains representable/selectable;
- Product momentum absence does not block basket creation or create false UI claims;
- basket result uses backend `source_claim` and audit provenance;
- negative basket research remains valid evidence, not application failure;
- HODL/control/cost/concentration language is supported by persisted authority;
- no basket science files changed.

## Completion report

Return:

1. status;
2. branch/worktree/commit/final Git state;
3. resulting Product-vs-Advanced source flow;
4. manual construction/exact-edge behavior;
5. claim/provenance presentation;
6. HODL/control/cost/concentration presentation;
7. stale terminology corrected;
8. checks actually run;
9. M9/M10 handoff, risks, and deliberate non-scope.
