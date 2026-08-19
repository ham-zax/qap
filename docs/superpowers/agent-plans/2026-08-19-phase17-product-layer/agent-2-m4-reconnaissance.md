# Agent 2 — M4 Current-Approved Research Policy / Readiness Reconnaissance

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** read-only
**Workspace:** `/home/hamza/repo/qap` read-only
**Isolation reason:** no writable worktree needed; Agent 1 is the sole M3-foundation writer in an isolated worktree
**Can start:** immediately
**Depends on:** integrated M2 `8e45c36`; treat the M3 foundation mission as the expected downstream data-generation handoff, not as implemented reality yet
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** none unless a genuine external condition arises; do not manufacture waits/processes
**Developer visibility:** headless

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-1-m3-foundation.md` — expected M3 -> M4 data-generation handoff
- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/agent-2-m2-market-directory-admission.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M4 is authoritative
- `docs/research/2026-08-19-qap-product-layer-investigation.md`

Inspect integrated M2 at `8e45c36`, especially `ProductUniverse.resolved_scope()` / `ProductResearchScope`, rather than assuming scanner catalog state still owns the Product universe.

## Objective

Produce the bounded repository-grounded reconnaissance needed to implement M4 immediately after the full M3 acquisition/generation work is integrated.

Determine the smallest owner and contract for the **separately versioned current-approved/current-survivor research claim** and the backend-composed readiness/safe-cutoff read model.

This mission is read-only. Do not implement M4 and do not edit the repository.

## Ownership

You own read-only investigation of:

- the current strict Scanner-V1 protocol/policy identity and where universe semantics are bound;
- how M2's approved/current `ProductResearchScope` can feed a new Product-default scope without weakening strict historical PIT behavior;
- timeframe -> required scanner interval/history requirements already frozen by Scanner V1;
- existing scanner preparation/catalog/source-slice owners relevant to selecting trailing admitted data through a safe cutoff;
- what M3 generation/coverage state M4 must consume once it lands;
- the correct backend owner for ready/excluded assets, exclusion reasons, direct-market readiness, scope size, active acquisition state, and latest safe completed-data cutoff;
- how the normal Product scan command can use the backend-selected safe cutoff without requiring a primary `as_of` field while preserving existing advanced/strict paths;
- the minimal API/read-model contract M5 will consume, without redesigning M5 UI.

Agent 1 concurrently owns executable **M3 foundation** in an isolated worktree. Do not inspect or mutate its active worktree unless the planner later changes the coordination contract.

## Coordination contract

Preserve these frozen boundaries:

- M4 must introduce a new versioned current-approved/current-survivor policy identity rather than reusing or weakening `scanner-v1-s1` historical PIT semantics;
- the Product-default claim is retrospective research over the operator-approved assets currently resolved/available on supported Spot venues using trailing admitted historical data through a backend-owned safe cutoff;
- current venue metadata remains a current observation, not historical listing/lifecycle proof;
- approved assets come only from M2 Product admission; no scanner or frontend inference may approve assets;
- M3 owns physical data generations, coverage, provenance, and preparation state; M4 owns the research-readiness composition over that state;
- M4 may reuse existing scanner candidate/replay/economic rules only where their assumptions remain valid under the new explicitly named scope;
- direct-market unavailability remains explicit evidence/reason, not synthetic quote-leg execution;
- React must not compute readiness, safe cutoffs, exclusion semantics, or policy meaning;
- no live/private exchange authority or change to Phase-12 `NO-GO`;
- do not implement M5 primary IA or copy redesign.

## Questions the report must answer

1. What exact code currently owns `scanner-v1-s1` protocol identity, PIT universe construction, requested horizons, preparation, and `as_of` binding?
2. Which of those rules can be reused unchanged under a separately named current-approved policy, and which universe/claim semantics require a new protocol/policy object or version identity?
3. What is the smallest input from integrated M2 (`ProductResearchScope`) that the new policy must bind, including directory observation identity/provenance and approved assets?
4. What exact M3 generation/coverage facts must M4 consume to determine timeframe readiness without re-reading/parsing filenames or duplicating provenance logic?
5. For Short / Medium / Swing, what backend-owned history/interval requirements and bar completion boundaries already exist, and how should they compose into one latest safe completed-data cutoff across the selected ready scope?
6. What exclusions/reasons must be representable before launch: unresolved identity, not approved, unavailable venue instrument, missing/insufficient interval history, acquisition failed/in progress, direct-market not ready/unavailable, or any other existing scientific reason that is genuinely relevant?
7. Should readiness be computed per venue, per economic asset, per horizon, or some combination? Identify the minimum user-facing aggregate that remains scientifically truthful.
8. Where should active Product acquisition/preparation state be joined into readiness without extending the protected seven scientific research commands?
9. How should the default scan initiation API avoid requiring a primary user-supplied `as_of` while retaining advanced/manual historical paths and immutable scan-definition commitments?
10. What minimal M4 DTO/read contract does M5 need to show: approved scope, ready/excluded counts/reasons, venues, timeframe, data-through cutoff, direct-market summary, and active preparation state?
11. Are there any hidden couplings that would make M4 require M3 venue implementation changes rather than merely consuming the promised foundation/generation handoff?
12. Recommend the writer topology for executable M4: one writer or any justified split.

## Success conditions

- The report identifies exact existing owners/callers for protocol identity, universe semantics, horizon requirements, preparation, safe bar completion, and scan definition.
- It gives a falsifiable design for a **new current-approved policy identity** without modifying the strict historical PIT policy.
- It defines the minimal M2 + M3 input contract needed for backend readiness/safe cutoff, with no frontend-derived scientific state.
- It distinguishes Product preparation failure/incomplete data from valid negative/rejected research outcomes.
- It identifies the exact default-scan API/composition seam that can remove primary manual `as_of` selection while preserving advanced/strict historical functionality.
- It provides a bounded M4 -> M5 DTO/read-model recommendation and writer-topology recommendation.
- No repository mutation occurs.

## Verification intent

Read-only repository evidence only:

- focused `rg` / caller/symbol inspection;
- bounded reads of scanner protocol, universe, preparation, catalog, command/API composition, and integrated M2 Product state;
- Git status before/after proving the main checkout remains unchanged.

Do not run tests, builds, formatters, generators, migrations, market-data downloads, captures, or mutating API calls. Current official-source web lookup is unnecessary unless a repository decision genuinely depends on an unstable external capability; prefer repository/frozen-design authority.

## Out of scope

- source/docs/config mutation;
- M3 implementation or review of Agent 1's active worktree;
- Binance/Gate historical acquisition implementation;
- M5 React/IA implementation;
- M6 longitudinal idea composition;
- M7 collector/SQLite work;
- scanner performance optimization;
- CCXT adoption;
- changing strict historical PIT semantics.

## Working style

Use Persistent Agent Loop for continuity and Causal Coding's read-only investigation rule. Use `mcp-harness-local` as authoritative for repository/Git evidence. Stop when additional exploration would no longer change the M4 owner, new-policy boundary, readiness/safe-cutoff composition, API seam, or writer topology.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. exact read-only repository state before/after;
3. owner/caller map for protocol identity, PIT/current scope, horizon/data requirements, preparation and scan initiation;
4. proposed separately-versioned current-approved policy contract;
5. proposed readiness/safe-cutoff composition including exclusion taxonomy and M2/M3 dependencies;
6. minimal M4 -> M5 API/read-model contract and normal scan initiation seam;
7. recommended M4 writer topology;
8. concrete risks/stop conditions and confirmation that no files/tests/builds/downloads were changed/run.
