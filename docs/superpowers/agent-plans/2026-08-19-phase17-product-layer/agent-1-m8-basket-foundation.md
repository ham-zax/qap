# Agent 1 — M8-0 Product Basket Compatibility Foundation

**Repository:** `/home/hamza/repo/qap`
**Artifact type:** mixed executable
**Workspace:** `/home/hamza/repo/qap/.worktrees/phase17-m8-basket-foundation`
**Branch:** `phase17-m8-basket-foundation`
**Can start:** after the Wave-9 coordination base is committed and the worktree is created
**Depends on:** M7 integrated at `d5fbddc`
**Execution lifetime:** persistent-agent-loop required

## Read first

- `docs/superpowers/agent-plans/2026-08-19-phase17-product-layer/README.md`
- `docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`
- `docs/plans/17-product-layer-market-data-and-research-lifecycle.md`
- `docs/research/2026-08-19-tradingview-ratio-legacy-qap-salvage-report.md`
- the integrated M3 Product market-data generation/provenance owners
- the integrated M4 current-approved Product scanner policy
- `src/qap/scanner/basket_protocol.py`
- `src/qap/scanner/basket.py`
- `src/qap/experiment/basket_scanner_adapter.py`
- `src/qap/scanner/basket_artifacts.py`

## Objective

Implement only the shared M8 foundation required for a current-approved Product scan to be a truthful source of the existing manual Scanner-V1 basket research.

The problem is provenance/source binding, not portfolio economics.

Product-v1 preserves the existing basket-relevant scientific/economic primitives. The current implementation rejects Product scans because:

1. the basket protocol identity explicitly names strict `scanner-v1-s1` as its source pair protocol;
2. basket definition/replay resolve historical execution sources through the current scanner catalog;
3. an M3 refresh can advance the current catalog away from the exact immutable generation used by the source Product scan.

M8-0 must make Product basket provenance honest and replay source binding immutable while leaving current strict PIT basket behavior intact.

## Required outcomes

### 1. Separately version Product basket source provenance

Do not silently reuse `scanner-v1-basket-v1` while feeding it a Product source scan.

Add the smallest separate Product-compatible basket protocol/source-policy identity that truthfully means:

> Existing Scanner-V1 basket economics derived from a Current Approved Market Research source scan.

Product source admission must fail closed and validate the actual immutable source scan as current-approved Product-v1. At minimum verify the real Product scanner protocol identity, current-approved universe policy, claim identity/scope binding, selected venue/horizon, and the existing basket-relevant scientific primitives.

Do not generalize this into “any scanner protocol is basket-compatible”.

### 2. Preserve all existing basket economics and manual authority

Do not change:

- exactly 3–6 manually selected economic assets;
- one venue;
- one horizon;
- one decision resolution;
- explicit candidate/rule selection per unordered pair;
- the current graph/relationship evidence semantics;
- equal-weight neutral start;
- maximum asset tilt;
- USDT bridge;
- hysteresis/resolver behavior;
- pair-blind control;
- matched HODL/control comparisons;
- fees/slippage/cost assumptions;
- ordinary QAP accounting/economic gates.

Do not require basket edges to be M6 historical survivors. Existing valid relationship-edge eligibility is broader than `deep_replay_survivor` and must remain so.

### 3. Seal exact Product execution-generation bindings

For Product source scans, resolve each selected economic asset/decision-resolution execution source from immutable M3 generation provenance using the exact source scan input commitment.

The binding must be equivalent to:

```text
asset
logical dataset_id
exact immutable relative_path
source semantic fingerprint
```

Resolve it from authoritative Product generation provenance and the source scan's immutable input slices. Require a unique exact match. No current-catalog substitution. No ticker inference. No heuristic filesystem search.

The resulting BasketDefinition/basket artifact must seal enough exact physical lineage that replay/recovery can read the same immutable generation even after Product market-data refresh advances the logical dataset pointer.

### 4. Replay from frozen Product binding

For Product-compatible baskets, the basket replay adapter must use the physical generation committed by the basket definition/artifact and revalidate its semantic fingerprint.

It must not ask the current catalog which physical generation now owns the logical dataset ID.

This should mirror the already-established principle used by the historical prospective-freeze repair: old evidence reads the exact original physical generation/fingerprint; later Product work may use newer current generations separately.

### 5. Keep existing strict PIT basket behavior unchanged

Do not claim a universal repair for arbitrary pre-M3 strict scans whose old physical paths are not reconstructible.

Strict `scanner-v1-s1` baskets keep their existing admission/replay semantics unless an exact already-authoritative physical lineage is already available without guessing.

Do not weaken strict PIT checks globally merely so Product baskets pass.

### 6. Claim-aware basket reads

Expose the smallest read/public-contract addition needed so Product Portfolio/History presentation can distinguish its source research claim:

```text
Historical Point-in-Time Research
Current Approved Market Research
```

The immutable `source_scan_id` remains the claim authority; do not duplicate scientific claim truth into a mutable second store.

Keep exact protocol/generation identities available as audit detail.

### 7. Public contract synchronization

If DTO/API contracts change, synchronize OpenAPI and the generated TypeScript schema/client surface required by later M8 presentation work.

Do not perform the full M8 Portfolio or History UI convergence in this foundation mission.

## Out of scope

- M8-A History composition/UI;
- M8-B Portfolio presentation convergence beyond the smallest claim/read seam needed by the foundation;
- Product basket auto-discovery or optimization;
- changing manual 3–6 asset selection;
- restricting edges to Research Ideas only;
- pre-run target/resolver opinions;
- new portfolio strategy/economic policy;
- Product asset-momentum support unless actual basket correctness proves it independently required;
- generic repair of every old strict scan/current-catalog case;
- heuristic recovery of missing historical files;
- M7 collector/qualification work;
- History database;
- generic workflow/job framework;
- M9 packaging;
- private exchange/live-capital authority.

## Stop conditions

Stop and report rather than broadening scope if correctness appears to require:

- changing Scanner-V1/Product-v1 relationship economics;
- changing basket HODL/control/cost/economic-gate semantics;
- weakening strict PIT source validation globally;
- guessing a physical generation that is not proven by immutable M3 provenance;
- changing Product market-data generation identity semantics;
- changing Product basket construction from manual-only;
- inventing relationship-level profit attribution;
- a new mutable portfolio-state database;
- Product basket compatibility requiring M7 or M9 authority.

## Acceptance

M8-0 is complete when all are established:

1. a current-approved Product-v1 source scan can be admitted under a separately versioned truthful basket source/protocol identity;
2. strict PIT source admission remains unchanged;
3. Product basket economics and manual selection semantics are unchanged;
4. Product execution assets are bound to exact immutable M3 generation paths + fingerprints from the source scan's committed input lineage;
5. Product basket replay/recovery reads that frozen generation after the current Product catalog has advanced to a newer generation;
6. missing/tampered/ambiguous historical Product generations fail closed;
7. no current-catalog substitution can silently change an already-defined Product basket;
8. basket reads expose enough source-claim identity for later Product Portfolio/History presentation;
9. no M8-A/M8-B presentation work or unrelated old strict-scan repair is absorbed.

## Verification intent

Testing remains opt-in. Do not create, modify, or run tests unless separately authorized or independently mandatory.

Use the smallest direct non-test evidence that proves the contract, including a deterministic Product-v1 basket built from M3 immutable generation provenance, a later simulated/current-pointer refresh, and replay/recovery proving the basket still reads the original physical generation.

Also use focused final static/contract checks appropriate to changed files, OpenAPI/client synchronization if public contracts change, `git diff --check`, and complete diff inspection.

## Finish report

Return:

1. status: complete / blocked / needs decision;
2. branch/worktree/commit and final Git state;
3. exact Product basket protocol/source-policy identity added;
4. exact Product source-scan compatibility validation;
5. exact immutable execution-generation binding persisted in the basket definition/artifacts;
6. replay/recovery behavior after current-catalog refresh;
7. strict PIT behavior and files proven unchanged;
8. public/read contract changes;
9. direct evidence/static checks actually run;
10. M8-A/M8-B handoff, remaining strict old-scan caveats, and any deliberate deviations.
