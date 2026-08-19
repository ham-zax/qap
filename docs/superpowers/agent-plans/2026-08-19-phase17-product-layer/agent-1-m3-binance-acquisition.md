# Agent 1 — M3 Binance Historical Acquisition

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m3-binance`
**Isolation reason:** concurrent writable venue mission; must not share a worktree with Gate writer
**Can start:** immediately after this coordination wave is materialized
**Depends on:** integrated M3 foundation `1a476db` and the Wave-4 coordination base
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** use bounded commands normally; Terminal + event wait only if a real long-running download/smoke process is required
**Developer visibility:** headless by default

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M3
- `docs/research/2026-08-19-qap-product-layer-investigation.md`
- integrated M2/M3 owners: `src/qap/product_universe.py`, `src/qap/product_market_data.py`, `src/qap/product_market_data_models.py`

## Objective

Implement the Binance-specific historical Spot OHLCV acquisition path that turns an M2-resolved Binance instrument and bounded requested interval/window into validated QAP bars and publishes them through the already-integrated M3 generation/provenance contract.

This mission owns Binance transport/archive/pagination semantics only. It does not own the shared generation schema, catalog publisher, Product maintenance schema, M4 readiness, or scanner policy.

## Current state

- M2 is integrated at `8e45c36`; `ProductUniverse.resolved_scope()` is the approved/current identity seam.
- M3 shared foundation is integrated at `1a476db`; `ProductMarketData.publish_generation()` is the only venue-neutral generation publisher.
- `BinancePublicAdapter.fetch_klines()` already validates one exact completed-bar page but is bounded to the exchange's 1000-row limit.
- Binance required Product-V1 intervals are natively available: `15m`, `1h`, `4h`, `1d`.
- `src/qap/market/adapters/binance_public.py` is already above the repository source-size hard threshold at the coordination base. Do not grow it with orchestration logic or perform unrelated refactoring merely to make a global size script green.

## Ownership

You own:

- Binance historical acquisition orchestration for resolved current Spot instruments;
- official-source selection and exact provenance for archive/checksum and/or REST requests as justified by the current code and frozen M3 preference order;
- bounded REST pagination/tail/gap handling around the existing validated single-page adapter primitive;
- normalization into existing `ValidatedBarSeries` / `MarketDataGenerationInput` contracts;
- publication through `ProductMarketData.publish_generation()`;
- support for both approved `ASSET/USDT` instruments and real M2-resolved same-venue direct markets passed to the acquisition path;
- focused verification of Binance acquisition + publication behavior.

Agent 2 concurrently owns the Gate path. Do not modify Gate acquisition code.

## Shared no-write contract

Do not independently redesign or semantically change:

- `src/qap/product_market_data.py` publication semantics;
- `src/qap/product_market_data_models.py` shared generation/provenance schema;
- `src/qap/product_maintenance.py` maintenance schema;
- the historical freeze repair in `src/qap/scanner/prospective_run.py` / `src/qap/scanner_entry.py`;
- M4 policy/readiness/safe-cutoff logic;
- the strict Scanner-V1 PIT protocol.

If Binance cannot be implemented without changing one of these shared contracts, stop expanding scope and report the exact conflict to the planner.

## Required behavior

- Consume an explicit `ResolvedProductInstrument` that belongs to the supplied `ProductResearchScope`; never infer identity from ticker text.
- Acquire only the requested bounded time window and native interval.
- Preserve QAP completed-bar semantics; do not admit an incomplete trailing candle.
- Produce a contiguous validated series or fail explicitly. Do not repair gaps by interpolation/fill-forward.
- Use the frozen M3 source preference: official bulk/checksum where its semantics fit; existing public REST for missing/tail/bounded gaps. Do not mix source families silently.
- Record exact upstream provenance through `MarketDataUpstreamSource`: source family/provider, exact archive/object/checksum or REST request windows/pages, retrieval timestamp, and source/raw fingerprints as applicable.
- Publish immutable generations only through `ProductMarketData.publish_generation()`.
- Do not synthesize direct markets from USDT legs.
- Do not add CCXT or a resampler.

## Success conditions

- A bounded Binance historical request for an M2-resolved instrument can produce a `ValidatedBarSeries` covering the requested completed-bar window and publish a current immutable generation through the M3 foundation.
- Requests exceeding one Binance REST page are handled by bounded orchestration rather than the existing single-page limitation leaking to Product behavior.
- Exact acquisition provenance is sealed for every published generation.
- Unsupported/missing/gapped source data fails explicitly without publishing a partial current generation.
- Existing shared M3 interfaces remain stable enough for the Gate branch to integrate independently.
- No M4 or UI implementation is absorbed.

## Verification intent

Testing is opt-in and not authorized by this mission. Use the narrowest direct non-test evidence that can disprove the contract, such as deterministic parser/pagination inputs, isolated temporary Product scopes/data roots, and a bounded public smoke only when needed. Near completion run only relevant static/source checks once and inspect the complete diff.

The pre-existing `binance_public.py` size violation is not a reason to refactor unrelated adapter behavior or to claim this mission failed when your new/changed ownership remains bounded.

## Out of scope

- Gate historical acquisition;
- shared generation/provenance schema changes;
- Product-wide prepare/refresh orchestration across both venues;
- M4 readiness/safe cutoff;
- historical PIT lifecycle reconstruction;
- resampling;
- CCXT;
- private exchange/authenticated trading;
- old-scan basket catalog coupling.

## Working style

Before the first mutation apply `causal-coding → ponytail → mcp-harness-router → mcp-harness-local`. Use Persistent Agent Loop for execution lifetime. Explore the actual integrated foundation before choosing file placement. Prefer a bounded Binance Product-acquisition owner over growing the already oversized adapter. Do not merge/rebase/reset `main`.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. exact Binance acquisition behavior, source-family policy and pagination/archive semantics;
4. public/shared interfaces changed, if any;
5. checks actually run and why;
6. anything the Gate/integration/M4 sessions must know;
7. unresolved source-data or coordination risks.
