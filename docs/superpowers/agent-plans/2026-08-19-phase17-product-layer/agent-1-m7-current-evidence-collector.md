# Agent 1 — M7 Persistent Current Public-Evidence Collector

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m7-current-evidence`
**Branch:** `phase17-m7-current-evidence`
**Can start:** after the Wave-8 coordination base is committed and the worktree is created
**Depends on:** M6 integrated at `c1db648`
**Execution lifetime:** persistent-agent-loop required

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M7 is authoritative
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m7-reconnaissance.md`
- integrated M6 longitudinal read/follow-up contract at `c1db648`

Before the first mutation apply:

`causal-coding → ponytail → mcp-harness-router → mcp-harness-local`

Testing remains opt-in. Do not create, modify, or run tests unless explicitly authorized or independently mandatory.

## Objective

Make current-capital qualification honestly usable over real elapsed time by adding one workspace-local persistent collector that accumulates the existing public-evidence contract without changing its scientific authority.

M7 must preserve this ownership split:

```text
M6 frozen Research Idea lineage
        ↓ exact execution instrument
Product collection plan / slots / observations   <- operational owner only
        ↓ normalized public observations
existing capture-readiness authority
        ↓
existing qualification authority
```

The collector is not a scientific verdict engine.

## Frozen scientific contract

Reuse the existing `PROSPECTIVE_V1` capture requirements exactly:

- L1 every 60 seconds;
- top-20 depth every 5 minutes;
- minimum 14 calendar days;
- >=95% overall slot coverage;
- >=90% for every UTC day;
- market metadata required by the existing contract.

Do not change these thresholds, qualification/capacity math, or `research_only | small_capacity | tradable_now` semantics.

## Required Product operational state

Use stdlib SQLite only, preferably the existing workspace Product database:

`<workspace_root>/product/product-state.sqlite3`

Add a bounded M7 owner rather than turning `MarketDataMaintenanceStore` into a generic database framework.

Own only operational state equivalent to:

1. collector runtime lease/status;
2. explicit collection plans;
3. exact plan memberships/frozen references;
4. exact cached resolved instruments, revalidated against immutable lineage;
5. scheduled L1/depth slots;
6. accepted normalized public observations.

Do not copy scanner/prospective/QAP/qualification scientific artifacts into SQLite.

## Frozen-lineage instrument resolution

Never infer a market from ticker or pair text.

Resolve each active membership through immutable evidence equivalent to:

```text
active_freeze_id
  -> CandidateFreeze
  -> candidate_deep_replay_run_id
  -> historical ExperimentManifest
  -> execution.execution_instrument_id
  -> exact InstrumentSpec
  -> VenueInstrument
```

M6 reselections must continue using the already-active freeze/instrument stream rather than creating a duplicate stream for the new candidate ID.

If cached SQLite instrument identity disagrees with immutable lineage, fail closed.

## Collection-plan lifecycle

Collection is Product operational intent, separate from scientific freeze/forward outcome.

Provide the smallest explicit Product start/stop collection boundary needed for the normal Research Idea flow. Do not infer stop intent from forward maturity, a negative later result, qualification state, or later asset-admission changes.

An instrument is scheduled while at least one active plan references it.

Deduplicate at instrument level across multiple Research Ideas/frozen rules.

## Scheduled-slot semantics

Use exact UTC cadence slots derived from existing protocol constants.

Primary uniqueness:

`(instrument_id, kind, scheduled_slot)`

where `kind` is `l1` or `depth`.

Rules:

- `scheduled_slot` is nominal UTC slot start;
- `observed_at` is the real observation timestamp;
- one admitted observation maximum per slot;
- admitted observation must fall inside its half-open slot;
- future slots remain implicit;
- materialize only due/current slots;
- previously due unseen slots become `missed`;
- missed slots stay missed;
- later observations never fill old slots;
- no historical archive backfill.

Do not pre-materialize 14 days of future slots.

## Restart / idempotency / process ownership

Use a separate long-lived collector process for Local Market. Do not make it a FastAPI background task, scientific OperationStore worker, or in-memory singleton.

Use a SQLite singleton lease with robust process identity equivalent to PID + Linux process-start marker, plus bounded heartbeat/status.

On restart:

- stale closed `in_progress` slot with no accepted observation -> `missed`;
- still-open stale slot may be reclaimed;
- accepted observation means captured;
- downtime slots become explicit misses;
- never issue catch-up requests pretending to reconstruct missed historical observations.

One sequential Product-V1 collector process is sufficient initially. If measured load misses cadence, preserve the misses and report the bottleneck rather than adding speculative worker infrastructure.

## Public observation path

Reuse existing Binance/Gate public adapter methods and normalized `PublicBookSnapshot` / `PublicMarketMetadataSnapshot` identities.

Do not persist every collector tick through the current append-and-rewrite Parquet path. Add/reuse the smallest non-Parquet observation seam necessary for the persistent collector while leaving advanced/manual one-shot capture stable.

Metadata cadence is not newly specified by the scientific protocol. Do not invent a metadata-age threshold. Collect required metadata through explicit operational events sufficient for the existing contract.

## Evidence-reader bridge

Add the smallest backend-owned collector evidence reader/projection that can reconstruct existing normalized public evidence and feed the current authorities.

The Product path must present at most one admitted scheduled observation per slot; do not blindly concatenate repeated manual captures with collector data and overweight capacity evidence.

Preserve the advanced/manual Parquet path separately where required.

Existing authorities remain:

- `evaluate_capture_contract()` / forward capture readiness for coverage readiness;
- qualification machinery for capacity classification.

The collector itself never declares `contract_ready` from its process tables.

## Normal Product qualification

Normal Product UX must not require capture kind, venue symbol, checkpoint ID, or raw `as_of`.

Add only the smallest Product wrapper needed to qualify one longitudinal Research Idea with a user-supplied hypothetical amount while reusing `OperationKind.QUALIFY_CANDIDATE`.

Backend resolves the active freeze, appropriate completed checkpoint, exact frozen instrument, collector evidence, and a qualification-safe current market-data boundary.

Do not make the collector an OHLCV owner. If current bar data is stale, report that Product market data needs refresh.

## Product read/UI state

Keep process health and scientific evidence readiness separate.

Expose backend-composed states equivalent to:

Collector/process:

`not_running | running | failed`

Research Idea current evidence:

`not_collecting | collecting | coverage_incomplete | contract_ready | evidence_unavailable`

plus measured facts such as collection start, latest observation, scheduled/captured/missed slot counts, metadata availability, and existing coverage values.

No frontend slot math, fake percentage, or ETA.

Safe primary semantics include:

- collecting public market evidence in the background;
- coverage incomplete;
- current public evidence available for the declared boundary;
- one slot missed;
- collector stopped unexpectedly;
- current evidence does not support the requested amount.

None may rewrite historical or later evidence.

## Launcher / workspace lifecycle

Extend `scripts/start_workbench.sh` only as required to own the third Local Market process and clean it up on normal workbench shutdown.

Sample Workspace must not silently start real collection.

API/web may remain available if collector fails; Product status must surface the failure truthfully.

Do not solve desktop packaging/system-service restart here. M9 owns that decision.

## Acceptance

M7 is complete when direct evidence establishes at least:

1. exact UTC 60s/5m slot derivation including midnight boundaries;
2. uniqueness/idempotency per instrument/kind/slot;
3. restart downtime becomes explicit missed slots without historical network calls;
4. stale `in_progress` reconciliation is correct;
5. a duplicate collector cannot own the same workspace lease;
6. frozen instrument resolution matches a real completed M6 follow-up/deep-replay lineage;
7. M6 reselection reuses the existing active freeze/instrument schedule;
8. collector-backed observations can feed the actual existing capture-readiness authority;
9. missing slots remain missing and keep readiness incomplete;
10. one bounded real public L1/depth capture preserves real observed/source identities;
11. collector process restart recovers the same plan without fabricating coverage;
12. normal Product amount assessment reuses `QUALIFY_CANDIDATE` and existing qualification authority;
13. Sample/Local Market and launcher lifecycle remain explicit;
14. no scientific protocol, basket compatibility, or live-capital authority change is absorbed.

Use direct deterministic/non-test evidence, focused static checks, public-contract synchronization if changed, frontend type/build checks if changed, and `git diff --check`. Do not run tests unless separately authorized.

## Hard stop conditions

Stop and report rather than expand scope if correctness appears to require:

- changing Scanner-V1 or `PROSPECTIVE_V1`;
- changing capture thresholds/capacity math/classification semantics;
- historical order-book archive backfill;
- private credentials/live orders;
- guessing instruments from ticker/pair text;
- moving scientific artifacts/verdicts into SQLite;
- a generic workflow/job framework;
- PostgreSQL/Redis/Celery/Kafka/cloud queues;
- Product basket compatibility;
- M9 packaging/service decisions.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and clean Git state;
3. exact SQLite ownership/schema and lease/process model;
4. slot scheduling/idempotency/restart behavior;
5. frozen-lineage/reselection instrument resolution;
6. normalized observation/evidence-reader bridge;
7. Product collection/read/qualification API + UI behavior;
8. launcher/process lifecycle behavior;
9. checks/direct evidence actually run;
10. M8/M9 handoff risks, limitations, and deliberate deviations.
