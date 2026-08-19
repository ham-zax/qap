# Agent 1 — M3 Shared Market-Data Generation / Provenance Foundation

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** executable behavior / Product infrastructure
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m3-foundation`
**Branch:** `phase17-m3-foundation`
**Isolation reason:** sole writable M3-foundation owner while `main` remains the integration/read-only base for Agent 2
**Can start:** immediately
**Depends on:** integrated M2 `8e45c36`
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** bounded commands normally; Terminal + event wait only if a genuine persistent process is required
**Developer visibility:** headless by default

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m3-reconnaissance.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m2-market-directory-admission.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M3 is authoritative
- `docs/research/2026-08-19-qap-product-layer-investigation.md`

Inspect the integrated M2 implementation itself before deciding names/placement. In particular, the semantic M3 input seam is `ProductUniverse.resolved_scope()` / `ProductResearchScope`; do not rediscover admission or canonical identity from scanner state.

## Objective

Land the **shared M3 foundation** that both venue-specific acquisition implementations can safely target later, without implementing the Binance or Gate historical acquisition drivers themselves.

The foundation must establish the smallest shared ownership for:

1. stable logical dataset identity plus immutable physical generations;
2. exact acquisition/derivation provenance for Product-prepared market data;
3. create-only generation publication and atomic current-pointer/catalog publication;
4. a backend/Product generation read seam that later M4 can use for coverage/readiness composition;
5. Product-maintenance state needed only to represent preparation/refresh status for this bounded foundation;
6. the scan-refresh-freeze lineage repair so historical freeze resolves the exact immutable generation originally sealed by the historical replay rather than whichever generation the current catalog now points to.

This mission deliberately stops before venue-specific downloading/pagination/archive logic.

## Current verified facts from M2 + M3 reconnaissance

M2 is integrated and owns:

```text
ProductUniverse.resolved_scope()
  -> directory_id / observation time
  -> explicitly approved canonical assets
  -> resolved current trading VenueInstrument values
  -> identity versions
  -> current directory source IDs/fingerprints
```

Unresolved identity does not enter automatic M3 scope.

Existing reusable market-data owners already exist:

- `qap.market.bars` for canonical bar/interval semantics;
- `validate_bar_series()` for exact ordering/cadence/gap rejection;
- `fingerprint_bar_series()` for semantic dataset fingerprints;
- create-only Parquet bar storage/readback validation;
- `ScannerSourceSpec.dataset_id` as a stable logical dataset identity;
- `relative_path + expected_semantic_fingerprint` as the existing physical-generation commitment used by scanner consumers.

No Product-V1 resampling subsystem is currently justified: the required `15m`, `1h`, `4h`, and `1d` intervals are available natively on the supported venue REST surfaces.

The historical freeze defect is narrow: the historical deep-replay manifest already seals `dataset_id`, `relative_path`, and `expected_semantic_fingerprint`; `_historical_replay_template()` drops the physical `relative_path`, and freeze later resolves `catalog.source(dataset_id)` from the **current** catalog. After a legitimate refresh that can point at generation B instead of historical generation A. The repair should preserve/use the originally sealed physical path and still recompute/verify the original fingerprint and selection slice. Later forward advancement intentionally continues using the current catalog generation.

A separate old-scan/current-catalog basket coupling was discovered during reconnaissance. It is **not** part of this mission unless direct implementation evidence proves the M3 foundation cannot be correct without addressing it. Report it rather than silently broadening scope.

## Ownership

You own:

- the shared immutable generation/provenance model and persistence/publication owner;
- generation-specific create-only artifact placement using existing Parquet/fingerprint semantics;
- current logical-dataset -> current immutable-generation publication semantics;
- the shared normalized acquisition-result/input seam that later Binance/Gate writers will emit into;
- a bounded Product generation/coverage read projection suitable for M4 consumption later;
- bounded Product maintenance state only to the extent required to represent prepare/refresh activity/failure for this foundation;
- the historical scan-refresh-freeze ownership repair described above;
- relevant public/internal documentation synchronization when the new shared contract must be durable.

Agent 2 concurrently owns **read-only M4 reconnaissance** on `main`. Do not absorb M4 policy/readiness semantics.

Future venue writers own:

- Binance archive/checksum retrieval and REST pagination/tail/gap orchestration;
- Gate candlestick retrieval/windowing and any admitted Gate bulk path;
- venue-specific normalization into the shared M3 generation-input contract.

## Coordination contract

Preserve these boundaries:

- consume only M2's explicit approved/resolved current scope; do not infer admission/identity from ticker text or `ScannerCatalog`;
- current directory observations remain current Product facts, not strict historical-PIT lifecycle evidence;
- old immutable physical generations must remain addressable and must not be overwritten when the logical dataset advances;
- publish a new current generation only after validation, semantic fingerprinting, provenance completion, and readback/contract validation succeed;
- completed historical research must continue to resolve the exact physical source it originally sealed;
- later forward advancement continues to use the current catalog generation by design;
- no synthetic direct cross from USDT legs;
- no CCXT, generic queue/workflow engine, cloud service, or live/private exchange authority;
- do not add an OHLCV resampling subsystem while all required Product-V1 intervals have admitted native venue paths;
- the existing seven scientific research commands and `OperationKind` values remain unchanged;
- M4 owns the new current-approved research policy, actual readiness/exclusion composition, and latest safe cutoff.

## Expected shared M3 output contract

Do not freeze exact class names merely from this brief; preserve the semantics below using the smallest repository-native design.

For each current logical dataset, the Product/data layer must be able to expose at least:

```text
logical dataset ID
current immutable generation reference / relative path
venue + real venue symbol
canonical base/quote identities
interval
validated coverage start
validated coverage end / latest completed bar boundary
semantic fingerprint
immutable acquisition/derivation provenance reference/status
current preparation/refresh state or failure reason where applicable
```

A completed immutable provenance record must bind the material acquisition facts required by the frozen design, including the upstream source family/provider, exact archive/object/checksum or REST request windows/page identities as applicable, retrieval timestamp, acquisition implementation identity/version, raw/source/page fingerprints where applicable, derivation identity/parents when any, and the resulting QAP semantic fingerprint.

Do not invent a second generation hash/identifier if a generation-specific immutable path plus existing semantic fingerprint is sufficient.

## Success conditions

- A venue-neutral shared generation input/publication contract exists and can accept validated bar series without knowing Binance/Gate transport details.
- Stable logical dataset IDs can advance to newer immutable generation paths without overwriting old physical artifacts.
- Current pointer/catalog publication is atomic and occurs only after a generation and its provenance are complete/valid.
- Exact upstream acquisition/derivation provenance has one authoritative Product/data owner separate from completed QAP/scanner economic artifacts.
- M4 has a bounded read seam for current generation coverage/provenance/preparation state, but no M4 readiness/safe-cutoff policy has leaked into this milestone.
- Historical freeze can still validate/freeze an older completed scan after the current catalog advances to a newer generation, by locating the historical generation originally sealed in the replay manifest and preserving tamper detection.
- Later prospective advancement remains bound to the current generation as before.
- No venue-specific historical download implementation, CCXT, resampler, synthetic direct-market logic, M4 current-approved policy, or basket-coupling cleanup is absorbed.
- Worktree is committed and clean at completion.

## Verification intent

Testing remains opt-in and is **not** authorized by this mission.

Use direct, focused evidence capable of disproving the foundation claims, such as:

- isolated temporary Product/data roots demonstrating create-only generation publication and atomic logical-pointer advancement;
- readback/fingerprint/provenance checks using existing non-test runtime APIs;
- a bounded reproduction of the scan-refresh-freeze ownership path proving the repaired code reads/verifies the originally sealed immutable generation rather than current catalog substitution, without running a test suite;
- relevant Ruff/format/Pyright/import/static checks once near candidate completion when affected by the diff;
- `git diff --check` and complete diff inspection.

Do not create/modify/run tests unless the user separately authorizes them or an independently authoritative repository rule specifically mandates them.

## Out of scope

- Binance historical downloading/archive/checksum/pagination implementation;
- Gate candlestick/bulk historical acquisition implementation;
- broad performance optimization;
- M4 current-approved research policy/readiness/safe cutoff;
- M5 UI/IA work;
- M7 collector/SQLite observation store;
- CCXT adoption;
- direct-market synthesis;
- automatic identity/admission changes;
- unrelated basket refresh remediation.

## Working style

Before the first mutation apply:

`causal-coding -> ponytail -> mcp-harness-router -> mcp-harness-local`

Use Persistent Agent Loop for mission continuity. Prefer reuse of the existing market/bar/storage/catalog/prospective owners over new frameworks. Keep one leading implementation boundary and stop when the shared foundation is sufficient for independent venue workers.

Do not merge, rebase, reset, switch, or mutate `main`.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit(s) and final clean Git state;
3. exact shared generation/provenance/publication behavior and internal/public contracts landed;
4. exact historical-freeze ownership repair and evidence that later forward-generation behavior remains distinct;
5. M3 venue-writer handoff contract and files/interfaces that must remain stable during fan-out;
6. direct/static checks actually run and why; explicitly confirm tests were not run unless separately authorized;
7. unresolved risks, intentionally deferred adjacent issues, or any reason the Binance/Gate fan-out is not yet safe.
