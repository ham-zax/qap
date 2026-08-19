# Agent 2 — M2 Current Market Directory and Explicit Asset Admission

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m2-universe` on branch `phase17-m2-universe`
**Isolation reason:** sole writable M2 worktree while `main` remains the coordination/read-only base for Agent 1 reconnaissance
**Can start:** immediately after this mission file exists in the assigned worktree
**Depends on:** integrated M1 at `461a33c`
**Execution lifetime:** persistent-agent-loop required
**Wake strategy:** normal bounded commands; Terminal + event waits only if a persistent local server is genuinely needed for runtime verification
**Developer visibility:** headless by default; status/progress steering does not terminate the mission

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md` — current dependency/ownership map
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md` — frozen Product Layer authority
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md` — M2 exit contract
- `docs/research/2026-08-19-qap-product-layer-investigation.md` — product/data evidence
- integrated M1 workspace implementation around `GET /api/workspace`, `ApiSettings.workspace_mode`, and the Home/sample zero-state

## Objective

Implement the smallest Product-owned **current Binance/Gate Spot market directory + fail-closed canonical identity + explicit operator asset admission + asset-oriented Research Universe read model** needed to satisfy Phase-17 M2.

At completion, a nontechnical user must be able to tell which canonical economic assets they have explicitly allowed QAP to research and which currently observed supported Spot venues/instruments are available for those assets, without QAP silently treating exchange listings or ticker equality as approval/identity truth.

Stop at M2. Do not download historical OHLCV or make research-readiness/safe-cutoff claims; those belong to M3/M4.

## Current state and reconnaissance conclusions

M1 is integrated on `main` at `461a33c`:

- backend-owned `workspace_mode: sample | local_market`;
- resolved `run_root` is the stable workspace identity exposed through `GET /api/workspace`;
- `market_data_status: not_prepared | catalog_detected` is intentionally coarse and is **not** admission/readiness truth;
- Sample/Local Market shell identity and Local Market zero-state exist;
- Product maintenance state is not yet persisted.

The completed M2 reconnaissance established:

- reuse `AssetId`, `VenueInstrument`, `MarketMetadata`, lifecycle/continuity primitives, public payload fingerprinting, and existing Binance/Gate public adapters;
- neither venue adapter currently owns broad current-Spot directory enumeration;
- current venue ticker text is not canonical economic identity;
- unresolved identity must fail closed and remain visible as `identity review required`/equivalent exclusion evidence;
- operator admission is canonical-asset state, separate from venue listing availability;
- admission must not live in `ScannerCatalog`, lifecycle research artifacts, scientific `OperationStore`, or completed run artifacts;
- SQLite is not the default owner for admission under the frozen design. Prefer the smallest versioned atomically replaced Product-state document rooted by the landed M1 workspace identity unless repository evidence proves an even smaller existing owner fits;
- executable M2 is one coherent writer mission; do not split backend/frontend or Binance/Gate merely for parallelism.

## Ownership

You own:

- bounded current Binance/Gate Spot directory reads using the existing venue adapters;
- a current venue-market observation model that can exist **before** canonical identity is resolved;
- current observation/source provenance sufficient for the Product directory claim;
- the minimum explicit current canonical-identity mapping state needed for Product V1;
- fail-closed resolution from venue-local asset codes/instruments to QAP canonical asset identities;
- persistent explicit operator admission of canonical assets under the M1 workspace identity;
- backend composition/read/write boundary for the Research Universe;
- thin OpenAPI/client/query synchronization required by that Product API;
- the minimal asset-oriented Local Market UI needed for users to approve/unapprove assets and understand current venue availability/identity state;
- artifact-appropriate verification of this M2 behavior.

Agent 1 concurrently owns **read-only M3 reconnaissance**. Do not absorb M3 implementation.

## Coordination contract

Preserve these boundaries exactly:

- `currently listed` never implies `approved to own`;
- admission is keyed to canonical economic assets, not exchange symbols or raw ticker strings;
- raw ticker equality is never sufficient identity evidence;
- unresolved/ambiguous identity remains excluded from automatic Product research rather than guessed;
- current metadata is not historical point-in-time lifecycle truth and must not satisfy Scanner-V1 PIT eligibility;
- existing `AssetIdentityContinuity`/lifecycle semantics remain authoritative for rename/migration continuity;
- M2 may say `needs market data` where appropriate, but actual OHLCV acquisition/generations are M3 and exact research readiness/safe cutoff is M4;
- the protected seven scientific command kinds remain unchanged;
- CCXT is not needed unless existing Binance/Gate adapters prove concretely insufficient for the required current directory operation;
- no private exchange credentials, order placement, live-capital action, generic job system, or browser-side research authority.

M3 must be able to consume an explicit resolved scope equivalent in meaning to:

```text
current directory observation identity + observed_at + source provenance
operator-approved canonical assets
resolved current venue instruments:
  venue
  venue_symbol
  canonical base asset
  canonical quote asset
  applicable identity version/current resolution
```

Do not freeze exact class names merely to match this brief. Follow repository conventions and keep the interface as small as possible.

## Success conditions

- Binance and Gate current public Spot markets can be represented without first pretending venue-local codes are canonical QAP assets.
- A trustworthy known mapping can resolve to existing canonical identity/lifecycle types; unknown/ambiguous mappings fail closed and remain visible.
- A Local Market user can explicitly approve and unapprove canonical assets independent of current listing refreshes.
- Directory refreshes do not automatically modify the approved asset set.
- Admission persists under the M1 workspace identity before any scanner catalog/history exists.
- A backend-owned Research Universe projection shows canonical asset, approval state, identity state, current supported venue/instrument availability, observation provenance/time, and only coarse `needs data`-style state that M2 can honestly know.
- The normal UI is asset-oriented and understandable; exact venue symbols/raw metadata are secondary/disclosed rather than the primary mental model.
- Existing M1 Sample/Local Market behavior remains intact.
- No strict historical-PIT scanner semantics, research economics, current-capacity policy, or seven-command scientific mutation contract changes.
- M3 receives a clear stable scope/provenance seam rather than having to infer approval/identity from the scanner catalog.

## Verification intent

Testing is opt-in and is not authorized by this mission. Do not create, modify, or run tests.

Use the smallest direct/non-test evidence that can disprove the M2 claims, such as:

- bounded adapter/parser/runtime checks for current directory normalization and unresolved identity behavior;
- direct API reads/writes against isolated Sample/Local Market workspace roots;
- restart/persistence evidence for admission state;
- proof that directory refresh does not mutate approval state;
- OpenAPI/type synchronization checks for changed public contracts;
- focused Ruff/Pyright and frontend type/build checks for changed executable boundaries;
- rendered/browser inspection only for the M2 Research Universe/zero-state interaction actually changed;
- `git diff --check` and full mission diff inspection near completion.

Do not run broad test suites merely because executable code changed.

## Out of scope

- historical OHLCV acquisition or pagination;
- bulk archive ingestion;
- data generation/provenance manifests beyond current directory observation provenance;
- scan-refresh-freeze repair;
- direct-pair historical dataset preparation;
- current-approved scanner policy identity;
- safe research cutoff/readiness computation;
- M5 primary IA migration;
- SQLite collector/task infrastructure;
- CCXT adoption;
- external broad identity service;
- automated religious/asset suitability classification;
- live/private exchange access.

## Working style

Before the first mutation apply:

`causal-coding -> ponytail -> mcp-harness-router -> mcp-harness-local`

Use Persistent Agent Loop for execution lifetime. Inspect the landed M1 owner before deciding Product-state paths/API composition. Prefer existing types/adapters and a small workspace-rooted state document over new frameworks. If repository reality proves a protected boundary needs changing, stop expansion and report the design conflict rather than silently redefining it.

Do not merge, rebase, reset, or mutate `main`. Commit coherent M2 work only on the assigned branch/worktree.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. workspace/branch and commits created;
3. resulting current-directory, identity-resolution, admission, API/read-model, and UI behavior;
4. exact public/interface changes and the M2 -> M3 handoff contract;
5. checks actually run, results, and why they were relevant;
6. anything Agent 1/planner needs for M3;
7. unresolved identity/data risks, deviations, or decisions needed.
