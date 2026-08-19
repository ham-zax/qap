# Agent 2 — M3 Gate Historical Acquisition

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m3-gate`
**Isolation reason:** concurrent writable venue mission; must not share a worktree with Binance writer
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

Implement the Gate-specific historical Spot OHLCV acquisition path that turns an M2-resolved Gate instrument and bounded requested interval/window into validated QAP bars and publishes them through the already-integrated M3 generation/provenance contract.

This mission owns Gate transport/archive/window semantics only. It does not own the shared generation schema, catalog publisher, Product maintenance schema, M4 readiness, or scanner policy.

## Current state

- M2 is integrated at `8e45c36`; `ProductUniverse.resolved_scope()` is the approved/current identity seam.
- M3 shared foundation is integrated at `1a476db`; `ProductMarketData.publish_generation()` is the only venue-neutral generation publisher.
- The Gate public adapter currently owns current market metadata and microstructure reads but no historical candlestick path.
- Gate required Product-V1 intervals are natively available through current official Spot REST: `15m`, `1h`, `4h`, `1d`.
- Gate REST candle semantics differ from Binance; bounded time-window paging must respect the venue's actual `from`/`to`/`limit` rules rather than copying Binance pagination.
- Official Gate historical quotation archives may be used where their interval/format/source semantics match the requested Product data, with REST used for missing/tail windows as justified.

## Ownership

You own:

- Gate Spot candlestick parsing/retrieval needed for Product historical bars;
- Gate-specific bounded time-window pagination;
- Gate bulk historical quotation/archive handling where it materially simplifies a supported native interval;
- exact source-family/request/archive provenance;
- normalization into existing `ValidatedBarSeries` / `MarketDataGenerationInput` contracts;
- publication through `ProductMarketData.publish_generation()`;
- support for both approved `ASSET/USDT` instruments and real M2-resolved same-venue direct markets passed to the acquisition path;
- focused verification of Gate acquisition + publication behavior.

Agent 1 concurrently owns the Binance path. Do not modify Binance acquisition code.

## Shared no-write contract

Do not independently redesign or semantically change:

- `src/qap/product_market_data.py` publication semantics;
- `src/qap/product_market_data_models.py` shared generation/provenance schema;
- `src/qap/product_maintenance.py` maintenance schema;
- the historical freeze repair in `src/qap/scanner/prospective_run.py` / `src/qap/scanner_entry.py`;
- M4 policy/readiness/safe-cutoff logic;
- the strict Scanner-V1 PIT protocol.

If Gate cannot be implemented without changing one of these shared contracts, stop expanding scope and report the exact conflict to the planner.

## Required behavior

- Consume an explicit `ResolvedProductInstrument` that belongs to the supplied `ProductResearchScope`; never infer identity from ticker text.
- Acquire only the requested bounded time window and native interval.
- Preserve QAP completed-bar semantics; do not admit an incomplete trailing candle.
- Produce a contiguous validated series or fail explicitly. Do not repair gaps by interpolation/fill-forward.
- Use the frozen M3 source preference: official bulk/archive source where its semantics fit; public REST for missing/tail/bounded windows. Do not mix source families silently.
- Respect Gate's actual time-window/request constraints; do not clone Binance page logic.
- Record exact upstream provenance through `MarketDataUpstreamSource`: source family/provider, exact archive/object or REST request windows/pages, retrieval timestamp, and source/raw fingerprints as applicable.
- Publish immutable generations only through `ProductMarketData.publish_generation()`.
- Do not synthesize direct markets from USDT legs.
- Do not add CCXT or a resampler.

## Success conditions

- A bounded Gate historical request for an M2-resolved instrument can produce a `ValidatedBarSeries` covering the requested completed-bar window and publish a current immutable generation through the M3 foundation.
- Requests longer than one Gate API window are handled by explicit bounded orchestration.
- Exact acquisition provenance is sealed for every published generation.
- Unsupported/missing/gapped source data fails explicitly without publishing a partial current generation.
- Existing shared M3 interfaces remain stable enough for the Binance branch to integrate independently.
- No M4 or UI implementation is absorbed.

## Verification intent

Testing is opt-in and not authorized by this mission. Use the narrowest direct non-test evidence that can disprove the contract, such as deterministic candlestick/window inputs, isolated temporary Product scopes/data roots, and a bounded public smoke only when needed. Near completion run only relevant static/source checks once and inspect the complete diff.

## Out of scope

- Binance historical acquisition;
- shared generation/provenance schema changes;
- Product-wide prepare/refresh orchestration across both venues;
- M4 readiness/safe cutoff;
- historical PIT lifecycle reconstruction;
- resampling;
- CCXT;
- historical order-book backfill into current qualification;
- private exchange/authenticated trading;
- old-scan basket catalog coupling.

## Working style

Before the first mutation apply `causal-coding → ponytail → mcp-harness-router → mcp-harness-local`. Use Persistent Agent Loop for execution lifetime. Explore the actual integrated foundation and current Gate adapter before choosing file placement. Reuse existing bar/domain validation rather than creating a second representation. Do not merge/rebase/reset `main`.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. exact Gate acquisition behavior, source-family policy and window/archive semantics;
4. public/shared interfaces changed, if any;
5. checks actually run and why;
6. anything the Binance/integration/M4 sessions must know;
7. unresolved source-data or coordination risks.
