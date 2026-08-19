# Agent 2 — M3 Combined Integration / Exit Cross-Check

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Isolation reason:** Agent 1 is the sole writer in the M3 orchestration worktree
**Can start:** after the legacy-salvage plan-upgrade coordination base lands on `main`
**Depends on:** integrated Binance and Gate venue branches on `main` plus the selective legacy-salvage amendment
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** none unless a genuine external wait arises

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m3-product-orchestration-exit.md`
- frozen/amended Product Layer design and upgraded Phase-17 plan
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md` — conceptual evidence only
- combined integrated M2/M3 owners on `main`

## Objective

Perform a bounded read-only cross-check of the now-integrated Binance + Gate + shared M3 foundation state so the planner and Agent 1 have an independent repository-grounded checklist for the final M3 orchestration/exit pass.

Do not implement anything.

## Questions to resolve

1. What exact combined Product callable/API behavior is still missing for a clean approved scope to drive both venue acquisition paths without manual catalog authoring?
2. Which Scanner-V1 horizon fields are the authoritative source for required intervals and trailing history, and which values must **not** be duplicated as Product constants?
3. What is the safest common completed-bar acquisition boundary relative to `ProductResearchScope.directory_observed_at` without prematurely implementing M4 safe-cutoff policy?
4. Do Binance and Gate logical dataset-ID policies conflict in a way the central pass must normalize, or can they remain venue-local?
5. What are the exact prepare-versus-refresh invariants needed to preserve old immutable generations while advancing the current pointer?
6. Which existing Product maintenance/app/API owners can be reused without adding an eighth research operation or a generic queue?
7. What combined end-to-end evidence is necessary and sufficient to declare the M3 exit criteria true?
8. Does the integrated state expose every field M4 reconnaissance requires through `ProductMarketData.projection()` and `ProductUniverse` after the central pass, or is one shared M3 read-field genuinely missing?
9. Can an already-satisfied/head/tail requested window be identified from current immutable generation coverage without a new mutable gap registry, and what is the smallest safe refresh behavior?
10. What request amplification does the current Binance daily-archive path imply for realistic timeframe windows, and is monthly support actually earned or merely speculative?
11. What bounded API-pressure behavior is necessary for M3 exit evidence, given current 429/transient handling, without creating a global legacy-style request guardian?
12. Where must the plan explicitly prevent acquisition availability/earliest history from becoming historical PIT eligibility evidence?

## Boundaries

- Read only `main`; do not inspect or mutate Agent 1's active worktree.
- No tests, builds, generators, downloads, captures, migrations, API mutations or Git mutations.
- Do not redesign M4, M5, venue acquisition, generation provenance or scanner science.
- Do not recommend CCXT/resampling unless a concrete combined-state insufficiency makes current M3 impossible.

## Success conditions

Return a concise repository-grounded M3 exit checklist that identifies:

- the exact remaining orchestration owner/call path;
- any real combined contract mismatch;
- minimum Product operation/API seam;
- data-window/timeframe ownership;
- prepare/refresh publication invariants;
- gap-aware/current-coverage reuse decision and measured request amplification;
- bounded API-pressure decision;
- explicit acquisition-availability versus historical-PIT boundary;
- exact M3 → M4 handoff completeness;
- any blocker Agent 1 must resolve before M3 can close.

If the venue and foundation contracts already compose cleanly, say so explicitly rather than inventing additional abstraction work.

## Verification intent

Focused repository reads/searches and fresh Git state only. No mutation and no testing.

## Working style

Use Persistent Agent Loop for continuity and Causal Coding's read-only rule. Use `mcp-harness-local` as authoritative for repository facts. Stop when more inspection would no longer change the final M3 exit checklist.

## Finish report

Return:

1. status;
2. exact clean repository state;
3. combined owner/caller map;
4. exact remaining M3 orchestration gap;
5. M3 exit checklist and M4 handoff assessment;
6. blockers/risks;
7. evidence inspected and confirmation of no mutation/tests/builds.