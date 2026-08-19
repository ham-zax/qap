# Agent 1 — M3 Combined Product Market-Data Orchestration / Exit

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable/API coordination
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m3-orchestration`
**Isolation reason:** sole writer for the final shared M3 pass while Agent 2 performs read-only combined-state cross-checking on `main`
**Can start:** after the legacy-salvage plan-upgrade coordination base is committed and the existing `phase17-m3-orchestration` worktree is safely refreshed/recreated from that base
**Depends on:** integrated M3 foundation `1a476db`, Binance venue acquisition `f1fab24`, Gate venue acquisition integrated on `main`, the selective legacy-salvage amendment, and the refreshed Wave-4b coordination base
**Execution lifetime:** persistent-agent-loop required
**Developer visibility:** headless by default

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — upgraded M3/M4 boundary
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md` — conceptual salvage only; do not port legacy runtime owners
- `src/qap/product_universe.py`
- `src/qap/product_market_data.py`
- `src/qap/product_market_data_binance.py`
- `src/qap/product_gate_market_data.py`
- `src/qap/product_maintenance.py`
- `src/qap/scanner/protocol.py`

## Objective

Close Phase-17 M3 by adding the smallest Product-level orchestration that can take the explicit current approved M2 scope and actually prepare/refresh the historical market-data generations required by the selected Scanner-V1 timeframe(s) through the already-integrated Binance and Gate venue drivers.

The final result must make the canonical M3 exit true:

> a clean approved universe can become research-ready through Product operations, without manual catalog authoring.

This mission owns Product orchestration and M3 exit only. It must not implement M4 current-approved research policy/readiness/safe-cutoff semantics or M5 UI redesign.

## Current verified state

- M2 `ProductUniverse.resolved_scope()` is the only approved/current identity input.
- Shared M3 `ProductMarketData.publish_generation()` is the only immutable generation/current-pointer publisher.
- Binance acquisition is available through `BinanceHistoricalAcquirer`.
- Gate acquisition is available through `GateHistoricalAdapter` + `publish_gate_historical_generation()`.
- `ProductMarketData` already owns bounded `prepare_market_data | refresh_market_data` maintenance state.
- No Product-wide orchestration currently drives those venue paths.
- No M3 HTTP operation currently lets the local Product initiate the preparation/refresh lifecycle.
- Current published generations expose contiguous coverage; the combined Product owner still needs to decide whether an already-satisfied/head/tail window can avoid unnecessary reacquisition without weakening provenance.
- Current venue paths can fail on public API pressure; the combined M3 exit must measure realistic request amplification and add only the smallest bounded response/backoff behavior that evidence earns.

## Ownership

You may change the smallest shared Product/API owners necessary to:

- derive the required native intervals/history envelope for requested Scanner-V1 timeframe(s) from existing protocol definitions rather than duplicating scientific constants;
- consume one exact `ProductResearchScope` snapshot without mutating operator admission;
- invoke the correct venue acquirer for each resolved Binance/Gate instrument in that scope, including real resolved direct markets;
- use stable logical dataset identities for Binance and preserve the already-landed Gate dataset identity semantics;
- drive bounded Product maintenance state around prepare/refresh execution;
- expose the smallest Product operation boundary required for a local application to initiate preparation/refresh and inspect its maintenance/result state;
- prove the combined Binance+Gate path satisfies M3 exit criteria;
- compare requested preparation windows with current immutable generation coverage before network acquisition;
- measure realistic request amplification and establish bounded public-API pressure behavior without introducing a global request framework.

Agent 2 is read-only and may cross-check combined ownership. It must not write into this worktree.

## Coordination boundaries

Preserve these existing authorities:

- `ProductUniverse` owns approval, canonical identity and current listing scope.
- venue acquisition modules own source/archive/REST semantics.
- `ProductMarketData` owns immutable generation/provenance/current logical pointer publication.
- Scanner-V1 remains scientific/economic authority for timeframe/model protocol.
- M4 owns the separately-versioned current-approved claim, ready/excluded composition, direct-market readiness interpretation, and final safe analysis cutoff.
- the seven scientific `OperationKind` values remain unchanged.

Do not introduce a generic job/queue framework, CCXT, resampling, live/private exchange authority, or a second catalog/persistence system.

## Required behavior

### Scope

Preparation/refresh must start from a captured `ProductUniverse.resolved_scope()` and may acquire only instruments already present in that scope.

Directory refresh or asset approval changes must not be performed implicitly by market-data preparation.

### Timeframe/data requirements

The operation accepts the Product research timeframe(s) needed for preparation and derives required native intervals/history from `SCANNER_V1_SLICE1`/its horizon definitions. Do not hard-code a second scientific table when the protocol already owns the values.

Acquisition windows must:

- use completed-bar boundaries;
- not consume data beyond the current-directory observation that established the captured scope;
- obtain enough trailing history for the selected timeframe(s) so later M4 can truthfully evaluate readiness;
- remain bounded and deterministic.

This is acquisition-window composition, **not** M4 safe-cutoff/readiness policy.

### Gap-aware prepare / refresh

Apply the useful legacy `AdaptiveFetcher` lesson at the current QAP generation boundary, not by porting its mutable cache architecture.

For each logical dataset:

```text
requested window
+ current ProductMarketData projection/immutable generation
    -> already satisfied / missing head / missing tail / unavailable
```

- If the current immutable generation already satisfies the requested window, skip exchange acquisition.
- If only a head/tail extension is missing, prefer acquiring only the missing range when the existing generation/derivation contract can compose a complete new immutable generation with exact parent/source lineage.
- Do not invent an internal-gap database: published generations are already contiguous; source internal gaps remain explicit acquisition failure.
- Do not use missing/earliest retrievable bars as historical listing/PIT eligibility evidence.
- If safe incremental composition would require disproportionate new machinery, bounded full-window reacquisition remains acceptable for V1, but quantify the request cost and record the concrete upgrade trigger in the finish report.

### API pressure / source efficiency

Do not port legacy `APIGuardian` or hard-coded legacy quotas.

The combined operation must measure realistic request counts for at least the selected timeframe paths used in M3 exit evidence. If current public endpoints expose meaningful 429/transient pressure during that bounded evidence, add the smallest per-operation/per-venue retry/backoff behavior justified by current response status/headers and a finite retry budget. Otherwise record stronger proactive throttling as deferred.

Explicitly evaluate Binance daily-archive request amplification. Monthly archive support is optional and should be added only if measured complete-month preparation materially benefits from it without weakening checksum/reconciliation/provenance semantics.

### Venue dispatch

- Binance instruments use the integrated Binance historical acquirer.
- Gate instruments use the integrated Gate historical path.
- real direct markets in M2 scope use the same venue path;
- missing direct markets are never synthesized.

### Stable logical IDs

Freeze a deterministic Binance logical dataset-ID policy compatible with immutable generations and identity versions. Preserve the existing Gate logical-ID semantics unless a direct inconsistency requires a narrowly coordinated adjustment.

Do not derive identity from ticker strings.

### Prepare / refresh semantics

Use the existing bounded Product maintenance owner.

A later refresh must publish newer immutable generations rather than overwrite prior physical artifacts. Already-published valid generations must remain intact if a later instrument/source fails.

Do not disguise partial/incomplete preparation as scientific readiness; M4 will interpret the resulting projection.

### Product operation boundary

Expose the smallest bounded local Product operation needed to initiate prepare/refresh without adding an eighth research command or a generic arbitrary-job surface.

The operation may be asynchronous if the existing API/process pattern makes that the smallest honest way to avoid tying a long historical acquisition to one request. Keep any worker/manager specific to these two Product maintenance kinds.

Do not add the M5 primary UI in this mission.

## M3 exit acceptance

Completion evidence must establish all of the following:

1. Starting from a clean Local Market workspace with explicit M2 mappings/admission and current directory state, Product preparation can drive at least one approved Binance path and one approved Gate path through the real venue drivers and shared immutable publisher without manual catalog editing.
2. Requested Scanner-V1 timeframe requirements determine the native data intervals/history being prepared.
3. Published datasets carry the exact venue provenance already defined by the venue writers and appear through `ProductMarketData.projection()` with complete provenance/coverage.
4. Refreshing the same logical dataset creates/advances to a new immutable generation while the old generation remains present.
5. The historical scan-refresh-freeze repair from the shared foundation remains intact.
6. Product maintenance reports idle/running/failed truthfully and is separate from scientific `OperationKind`.
7. Already-satisfied generation windows do not trigger unnecessary network acquisition, or the bounded full-reacquisition limitation is explicitly measured and justified for V1.
8. Realistic combined preparation either stays within bounded public API pressure or demonstrates finite retry/failure behavior without a global request guardian.
9. Acquisition availability remains explicitly separate from strict historical PIT eligibility.
10. No current-approved research policy, readiness/safe-cutoff claim, React IA redesign, CCXT, resampler, synthetic direct market, or private exchange authority is absorbed.

## Verification intent

Testing remains opt-in and is not authorized by this mission.

Use focused direct non-test evidence only: isolated Local Market state, small approved Binance+Gate scope, bounded historical windows, current-generation coverage comparison, immutable generation/provenance projection, prepare/refresh state transitions, measured request counts/source families, bounded API-pressure behavior where encountered, API/runtime smoke if a Product endpoint is introduced, applicable static/OpenAPI/client checks only if those artifacts change, and a final complete diff inspection.

Do not run a broad test suite merely for confidence.

## Out of scope

- M4 current-approved policy/readiness/safe cutoff;
- M5 UI/primary IA;
- automatic asset admission or identity resolution;
- historical PIT lifecycle reconstruction;
- current-evidence collector;
- portfolio/basket refresh coupling;
- CCXT/resampling;
- private/authenticated exchange trading;
- generic background job infrastructure.

## Working style

Before the first mutation apply `causal-coding → ponytail → mcp-harness-router → mcp-harness-local`.

Use Persistent Agent Loop for the mission lifetime. Reuse the integrated venue/foundation contracts and prefer one small Product orchestration owner over modifying either venue implementation. Stop and report if full M3 cannot be completed without changing the M4 scientific/product-policy boundary.

Do not merge/rebase/reset `main`.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. exact prepare/refresh orchestration behavior and timeframe/window semantics;
4. Product operation/API/interface changes;
5. combined Binance/Gate and immutable-refresh evidence;
6. checks actually run and why;
7. exact M3 exit determination and M3 → M4 handoff;
8. remaining risks/deferred issues.