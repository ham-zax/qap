# Agent 1 — M3 Historical Market-Data / Provenance / Generation Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Isolation reason:** no writable worktree needed; Agent 2 is the sole M2 writer in an isolated worktree
**Can start:** immediately
**Depends on:** integrated M1 at `461a33c`; use the M2 mission's frozen handoff contract as a planning boundary but do not assume its not-yet-landed implementation details
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** none unless a genuine external wait arises; do not manufacture waits/processes
**Developer visibility:** headless

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m2-market-directory-admission.md` — expected M2 -> M3 semantic handoff, not an implemented contract yet
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — especially M3
- `docs/research/2026-08-19-qap-product-layer-investigation.md`

## Objective

Prepare a bounded, repository-grounded M3 implementation reconnaissance so the planner can materialize M3 immediately after M2 integrates without repeating broad discovery.

Determine the smallest owners and stable seams for:

- historical Binance/Gate OHLCV acquisition for approved/resolved scope;
- immutable logical-dataset / physical-generation publication;
- upstream acquisition and derivation provenance;
- any required interval derivation owner;
- real same-venue direct-market data preparation;
- the scan-refresh-freeze ownership repair identified by the Product Layer investigation;
- whether M3 has a genuinely useful two-writer Binance/Gate fan-out after a shared foundation lands.

This mission is read-only. Do not implement M3.

## Ownership

You own read-only investigation of:

- current bar adapters/storage/catalog/preparation owners and callers;
- existing deterministic bar validation/fingerprinting/artifact publication primitives;
- scanner dataset ID/catalog semantics relevant to immutable generations;
- prospective freeze/replay lineage that currently interacts with whole-source fingerprints and current catalog generations;
- direct pair-market requirements for authoritative replay;
- exact Binance/Gate acquisition gaps and shared versus venue-specific responsibilities;
- the narrow M3 -> M4 output contract needed for readiness/safe-cutoff composition;
- a recommendation for sequential versus parallel M3 implementation based on real write ownership.

Agent 2 owns executable M2 in a separate worktree. Do not edit any repository file or absorb M2.

## Coordination contract

Preserve the frozen boundaries:

- M3 consumes only explicitly approved, canonically resolved current venue instruments from M2; unresolved identity is outside automatic acquisition scope;
- existing strict historical PIT lifecycle eligibility remains unchanged;
- no current-listing metadata is promoted into historical eligibility truth;
- stable logical dataset identity may point to newer immutable physical generations, but completed research must retain exact original physical/provenance identity;
- direct replay must use a real same-venue direct market where required; do not synthesize a cross from USDT legs;
- CCXT remains deferred unless existing adapters demonstrably cannot perform a required Product-V1 operation;
- Product acquisition/provenance must not become a second research/economic authority;
- no M4 current-approved policy/readiness calculation in this mission.

## Questions the report must answer

1. What existing code owns Binance and Gate historical bar retrieval today, including pagination/limits and missing venue capability?
2. What code owns canonical Parquet bar writing, semantic fingerprints, scanner catalog source specs, and data-root resolution?
3. What is the smallest immutable-generation publication model that fits existing dataset IDs/catalog consumers without overwriting research inputs?
4. What exact provenance information is currently missing for automatically acquired or derived bars, and where can it live without changing authoritative research artifacts unnecessarily?
5. Does any existing safe aggregation/resampling primitive cover required non-native intervals? If not, what is the smallest bounded owner M3 would need?
6. Where exactly is the scan-refresh-freeze coupling, and what owner should verify the original immutable historical replay sources rather than the current catalog generation?
7. How are direct same-venue pair instruments/data currently discovered/consumed, and what M3 must prepare when the direct market is unavailable?
8. What concrete shared foundation must land before Binance/Gate acquisition can safely split into two writers?
9. After that foundation, are the venue-specific diffs large and disjoint enough to justify two worktrees, or should M3 remain one writer?
10. What minimal M3 output/read contract does M4 need for per-timeframe readiness and latest safe cutoff?

## Success conditions

- The report identifies exact existing owners/callers and reusable primitives rather than proposing a parallel architecture.
- The scan-refresh-freeze mismatch is traced to a responsible owner with a falsifiable repair direction.
- The immutable generation/provenance seam is concrete enough to implement after M2 without guessing persistent/research ownership.
- Binance/Gate responsibilities and any missing acquisition paths are clearly separated from shared generation/provenance behavior.
- Direct-market handling remains consistent with existing authoritative replay semantics.
- The planner receives a clear recommendation on whether M3 should use one writer or a foundation-then-two-writer fan-out.
- No repository mutation occurs.

## Verification intent

Read-only repository evidence only:

- focused `rg` / symbol/caller inspection;
- bounded reads of existing adapters, storage/catalog/prospective code, specs/results;
- Git status before/after to prove no mutation.

Do not run tests, builds, formatters, generators, migrations, downloads, or market-data captures. Public-source lookup is optional only if a repository decision genuinely depends on a current official exchange capability; distinguish it clearly from repository evidence.

## Out of scope

- any source/docs/config mutation;
- M2 implementation/review;
- downloading market data;
- M4 policy/readiness implementation;
- performance optimization;
- CCXT adoption;
- new research model or scanner semantics;
- desktop packaging or collector implementation.

## Working style

Use Persistent Agent Loop for mission continuity and Causal Coding's read-only investigation rule. Use `mcp-harness-local` as the authoritative repository/filesystem source. Stop investigating when additional evidence would no longer change the proposed M3 owner, seam, dependency split, or next implementation decision.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. exact repository state proving read-only completion;
3. authoritative owner/caller map for acquisition, generations/provenance, direct markets, and freeze lineage;
4. proposed minimal M3 contract and M3 -> M4 handoff;
5. recommended one-writer versus fan-out implementation shape and why;
6. concrete risks/stop conditions for executable M3;
7. commands/evidence used and confirmation that no repository mutation/tests/builds occurred.
