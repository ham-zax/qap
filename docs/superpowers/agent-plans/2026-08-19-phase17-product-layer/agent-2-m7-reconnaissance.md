# Agent 2 — M7 Persistent Current-Evidence Collector / State-Ownership Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Can start:** immediately after the Wave-7 coordination base is committed
**Depends on:** M5 integrated at `6b40028`; M6 executable work runs concurrently in an isolated worktree
**Execution lifetime:** persistent-agent-loop for continuity only

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M7 is authoritative
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m6-reconnaissance.md`
- integrated current capture/readiness/qualification code on `main`

Do not inspect Agent 1's active M6 worktree.

## Objective

Produce a precise read-only M7 implementation brief for persistent current public-evidence collection.

M7 must make the existing 14-day current-evidence contract operational over real elapsed time while preserving all current QAP/qualification authority.

The collector is a Product operational owner that feeds existing evidence consumers. It is **not** a second scientific qualification system and is not part of the seven scientific mutation commands.

## Frozen contract to investigate

Current public-evidence target:

```text
L1 / book ticker cadence   60 seconds
top-20 depth cadence       5 minutes
minimum window             14 calendar days
overall coverage           >=95%
per UTC day coverage       >=90%
```

At 14 days per instrument this implies approximately:

```text
20,160 expected L1 slots
4,032 expected depth slots
```

M7 must preserve actual observation timestamps and explicit missing scheduled slots. It must not fabricate historical backfill.

## Highest-priority ownership questions

Map the exact current owners/callers for:

1. one-shot public evidence capture;
2. public L1/depth storage format;
3. market metadata snapshots;
4. `forward_capture_readiness()`;
5. capture-contract evaluation;
6. qualification initiation and persisted qualification evidence;
7. Product/API process lifetime and launcher behavior;
8. existing Product maintenance state;
9. any current SQLite usage and repository rules around it.

Then determine the smallest new M7 ownership boundary for:

```text
tracked frozen instruments
scheduled capture slots
actual observations
missed slots
collector/process status
recovery after restart
```

## Mandatory state-ownership audit

Apply the legacy ownership/hidden-state lesson here because M7 introduces long-lived mutable operational state.

For every proposed mutable state collection, record:

```text
owner
allowed mutator
readers/consumers
lifetime
recovery behavior
failure mode
authority impact
```

The frozen design allows stdlib SQLite only for bounded Product operational/collector state. Determine exactly which records belong there and which must stay in existing immutable evidence files/artifacts.

Do not recommend PostgreSQL, Redis, Celery, Kafka, cloud queues, or another database/service unless current repository evidence makes the stdlib-SQLite boundary impossible.

## Scheduling semantics

Investigate the smallest correct scheduler/coordinator model.

The expected uniqueness concept is:

```text
(instrument, kind, scheduled_slot)
```

Actual `observed_at` remains the real observation time.

A missed scheduled slot remains missing; it is not silently filled by a later observation.

Determine:

- who creates future slots;
- whether slots are materialized ahead of time or deterministically derived;
- how restart/recovery avoids duplicate capture;
- how the collector decides which active Research Ideas/instruments require collection;
- how an instrument leaves the tracked set;
- how collector state remains separate from scientific OperationStore state;
- whether one process can serve all tracked instruments safely for Product V1.

Do not invent a generic workflow/job engine.

## Instrument authority

Current readiness resolves required current public instruments from frozen historical QAP lineage.

M7 must continue to derive tracked instruments from authoritative Research Idea/freeze lineage, e.g.:

```text
CandidateFreeze
  -> historical deep_replay_run_id
  -> historical execution instrument
```

Never infer instruments from pair text, ticker equality, or string concatenation.

Evaluate what M6 needs to expose to make this handoff clean, but do not inspect/mutate its worktree.

## Existing capture adapter boundary

Determine whether the current one-shot `qap.market` capture primitives can remain bounded and be called by an external Product coordinator/scheduler.

Prefer that shape unless concrete code evidence requires changing the capture primitive itself.

Historical Gate order-book archives and other backfill sources must not satisfy the prospective/current capture contract retroactively.

## Persistence and evidence separation

Clarify the split between:

### Operational SQLite

May own bounded concepts such as:

```text
collector/tracked-instrument registration
scheduled slot identity/state
capture attempt/process status
normalized public observations if frozen design/current code supports it
```

### Existing scientific/read evidence

Must continue to own:

```text
capture-contract truth
forward checkpoint truth
qualification verdicts
QAP current-state/capital replay artifacts
historical scan/prospective lineage
```

Do not move capacity/readiness/economic verdict authority into SQLite merely because the collector writes there.

## Process lifecycle

Inspect current API/launcher/process conventions and determine the smallest operational lifetime model for a collector that must run for days.

Questions:

- separate long-lived Product collector process vs API child/background process;
- startup/shutdown ownership;
- single-instance/duplicate prevention;
- crash/restart recovery;
- workspace identity/mode binding;
- sample-workspace behavior;
- how API/UI read collector status;
- what M9 packaging/process work should remain deferred.

Do not prematurely solve M9 packaging.

## Product read handoff

Define the minimal read state M7 should expose to M6/M8 UI, such as:

```text
not collecting
collecting
coverage incomplete
contract ready
collector failed
```

with actual elapsed/coverage facts rather than fake progress estimates.

Current readiness/qualification should still be evaluated by existing owners. Collector state should not proclaim a scientific/capacity verdict.

## Verification / implementation evidence to recommend

Because M7 is time- and recovery-sensitive, specify direct non-test evidence that can establish correctness without pretending to wait 14 real days during one development session.

Examples may include:

- deterministic slot planning around UTC-day boundaries;
- restart/idempotency with existing scheduled-slot identities;
- actual missing-slot retention;
- one bounded real capture through the existing public adapter;
- synthetic elapsed-time fixture/data only when it exercises the actual collector contract without falsifying production evidence;
- coverage/readiness evaluation against persisted observations;
- process ownership/recovery smoke;
- focused static/type/import checks.

Do not create/run tests during reconnaissance.

## Stop conditions

Stop and report rather than broadening M7 if the design starts to require:

- changing qualification/capacity scientific rules;
- historical order-book backfill for prospective evidence;
- private exchange authentication;
- order placement/live capital authority;
- generic queue/workflow infrastructure;
- cloud services;
- moving immutable QAP research authority into SQLite;
- Product basket compatibility work;
- M9 packaging decisions that are not required for collector correctness.

## Success criteria

Reconnaissance is complete when the report identifies:

1. exact existing capture/readiness/qualification owners;
2. exact new mutable state collections and one authoritative owner for each;
3. proposed bounded SQLite schema responsibilities, without overreaching into scientific authority;
4. exact scheduled-slot/idempotency/restart semantics;
5. exact frozen-lineage instrument resolution path;
6. smallest process-lifecycle arrangement that can run persistently for Product V1;
7. API/read-state handoff to the longitudinal Research Idea UI;
8. failure/recovery semantics;
9. executable M7 writer topology and likely files/owners;
10. M8/M9 handoff risks and hard stop conditions.

## Finish report

Return:

1. status and exact read-only Git state before/after;
2. existing owner/caller map for capture -> readiness -> qualification;
3. mutable state ownership ledger;
4. recommended SQLite responsibility/schema boundaries;
5. scheduler/slot/idempotency/restart semantics;
6. instrument-lineage resolution and active Research Idea tracking model;
7. process-lifecycle recommendation for Product V1;
8. Product read/API handoff and failure states;
9. executable M7 writer topology and verification strategy;
10. M8/M9 risks, stop conditions, and explicit no-mutation confirmation.
