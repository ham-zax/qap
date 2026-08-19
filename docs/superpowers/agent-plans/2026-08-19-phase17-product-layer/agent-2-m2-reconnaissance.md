# Agent 2 — M2 Market Directory and Asset Admission Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Isolation reason:** no writable worktree is needed because this mission must not mutate repository state
**Can start:** immediately
**Depends on:** Phase-17 M0 design freeze at `1bb6e78`; executable M2 remains blocked by integrated M1
**Execution lifetime:** `persistent-agent-loop` required for mission continuity/steering
**Wake strategy:** none by default; do not manufacture waits or persistent processes for a bounded read-only investigation
**Developer visibility:** headless

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — Wave-1 dependency/ownership map
- `docs/research/2026-08-19-qap-product-layer-investigation.md` — market/lifecycle/CCXT/product evidence already gathered
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md` — frozen Product Layer design authority
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M2 acceptance and downstream M3/M4 dependencies
- `implementation_prompt.md` — protected QAP mission/economic/action-space boundaries

Load `causal-coding` before investigation and follow its read-only rule: do not mutate code for a diagnosis/reconnaissance mission. Use `persistent-agent-loop` for continuity if the user steers or requests status.

## Objective

Produce a repository-grounded implementation reconnaissance for Phase 17 Milestone 2 so the planner can materialize the smallest executable M2 mission immediately after M1 is integrated.

Determine the true owners, reusable primitives, public-data capabilities, identity/lifecycle constraints, persistence seam, API/read-model needs, and collision risks for:

- current Binance/Gate public Spot market directory;
- canonical economic asset identity and fail-closed uncertainty;
- explicit operator-approved asset admission separate from exchange listing;
- user-understandable Research Universe readiness state;
- exact boundary between M2 and M3 market-data acquisition.

Do not implement M2 and do not design beyond what the frozen Phase-17 plan requires.

## Current state

Verified at the coordination base:

- QAP already has Binance/Gate public adapters and lifecycle/canonical-identity domain concepts.
- Scanner catalogs currently assume curated admitted identity/lifecycle state; Product M2 must replace the hidden/manual implication with explicit current directory + operator admission.
- `currently listed` must never imply `approved to own`.
- ticker equality must never be treated as canonical asset identity.
- unresolved identity must fail closed as an exclusion/readiness reason.
- CCXT is intentionally deferred for Product V1 unless current explicit adapters are demonstrably insufficient.
- Agent 1 is concurrently implementing M1 workspace identity/status; executable M2 must wait for that integrated seam.

## Ownership

You own read-only evidence for the future M2 implementation:

- locate current Binance/Gate metadata methods and their normalized domain outputs;
- locate lifecycle/canonical asset identity owners and determine what they already express versus what Product M2 minimally needs;
- identify existing persistence conventions that could store explicit operator asset admission without claiming research/economic authority;
- identify API/settings/application composition points M2 will need after M1, while treating Agent 1's eventual landed M1 interface as authoritative over guesses;
- identify the minimum UI/read-model information required by the M2 exit criterion;
- identify likely write-collision areas and whether any part of executable M2 can safely be parallelized after M1;
- identify exact M2 -> M3 contract facts that downstream acquisition/provenance will need.

You do not own any repository mutation, branch/worktree creation, code generation, test execution, network scraping beyond what is necessary to inspect repository-owned adapter contracts, or implementation of M2/M3.

## Coordination contract

Your report must distinguish:

1. existing authoritative owners that should be reused;
2. minimal missing Product-layer state/contracts M2 must add;
3. facts that cannot be finalized until Agent 1 M1 is integrated;
4. work that belongs to M3 or later and must not leak into M2.

Do not recommend CCXT, a generic exchange abstraction, database/queue architecture, or broad lifecycle redesign unless repository evidence proves the frozen Binance/Gate V1 cannot meet M2 without it.

Do not propose automatically admitting all current venue assets. Operator approval is a protected boundary.

If canonical identity across Binance/Gate cannot be resolved safely for some rows, the executable M2 recommendation must fail closed rather than guess.

## Success conditions

Return a compact but implementation-ready reconnaissance containing:

- current owner map: symbols/files/functions/classes for Binance/Gate current market metadata, venue/instrument identity, lifecycle/canonical identity, API composition, and relevant persistence patterns;
- exact reusable behavior versus minimal M2 gaps;
- proposed M2 data/read-model contract at the conceptual field/ownership level, without inventing speculative APIs if M1 could change the exact route/settings seam;
- fail-closed identity/admission rules tied to current domain contracts;
- clear M2/M3 boundary: what M2 stores/reads versus what M3 later downloads/generates;
- parallelization recommendation for executable M2 after M1: one writer, or a justified stable seam for two isolated writers;
- concrete risks/blockers and what evidence would resolve them.

The report should be sufficient for the planner to materialize executable M2 after reading Agent 1's landed M1 interface without repeating broad repository discovery.

## Verification intent

This mission is read-only. Verification is repository evidence, not tests.

Use focused `rg`, targeted file reads, symbol/caller inspection when useful, and bounded inspection of existing adapter/domain/API contracts. Do not run tests, builds, formatters, generators, migrations, network capture commands, or commands that create/change files.

Before reporting completion, confirm `git status --short` is unchanged from the stable coordination base and state explicitly that you made no repository mutations.

## Out of scope

- implementing M1/M2/M3;
- editing docs to record the reconnaissance;
- generating OpenAPI/client types;
- fetching/normalizing historical OHLCV;
- choosing SQLite schema for M7 collector state;
- current-approved scanner policy/readiness from M4;
- M5+ UI redesign;
- private exchange credentials/live trading.

## Working style

Stay read-only and evidence-driven. Do not duplicate Agent 1's M1 implementation investigation except where an existing M1-adjacent owner must be understood to identify the future M2 seam. Treat any status/progress request as steering, not a stop, until the reconnaissance success conditions are complete.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. confirmation that the main checkout remained read-only/unchanged;
3. owner/reuse map and minimal M2 gaps;
4. proposed M2 ownership/read-model/persistence seam and M2->M3 boundary;
5. parallelization recommendation after M1 integration;
6. commands/reads actually used as evidence (no tests), and any unresolved risks/decisions.
