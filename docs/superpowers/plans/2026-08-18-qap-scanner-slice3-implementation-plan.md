# QAP Scanner V1 Slice 3 Implementation Plan

**Date:** 2026-08-18

**Status:** amended 2026-08-19 after Milestone 6 implementation at `46ef407` and integrity closure at `dd9df14`. `dd9df14` is the authoritative Milestone-6 handoff baseline. Milestone 7 remains the final Slice-3 backend vertical. Milestone 8 is explicitly superseded by Slice 4's unified QAP Workbench. Milestone 9 closes the Slice-3 backend only.

**Goal:** implement the approved Slice-3 asset-native momentum surface and manual 3–6 asset one-inventory basket workflow without creating a second backtester, optimizer, cross-venue wallet, or live-capital path.

**Authoritative design:** `docs/superpowers/specs/2026-08-18-qap-scanner-slice3-asset-momentum-basket-design.md`.

**Upstream implementation baseline:** Scanner V1 Slices 1–2 complete and repository-verified at the Slice-2 handoff documented by `docs/research/2026-08-18-qap-scanner-slice2-results.md`.

---

## 1. Non-negotiable implementation rules

- Keep runtime names domain-based; do not create `slice3_*` Python modules.
- `qap.scanner` remains outside financial authority and may not import `qap.policy`, `qap.execution`, `qap.evaluation`, or `qap.experiment` except existing thin CLI-to-outer-composition exceptions.
- The graph-to-target resolver is policy-owned.
- The existing Phase-11 `execute_multi_asset_rebalance()` path is the only basket execution authority.
- Ordinary QAP replay/economics/artifacts remain the only owner of basket P&L, wealth, fills, HODL, and controls.
- One basket is one venue, one horizon, one decision resolution, one USDT bridge, and 3–6 economic assets.
- Basket construction is manual only.
- Historical basket replay is development evidence only.
- Pair prospective evidence may be shown but cannot relabel the basket as prospective.
- No basket capacity/`tradable_now` derivation in Scanner V1 Slice 3.
- No current venue metadata may be backfilled into old bars and represented as historical execution truth.
- No new dependency is expected. Reuse current Python/NumPy/QAP primitives.
- Preserve the repository 500/700-line source-size policy. The existing large `model_policies.py` is not a dumping ground for Slice-3 behavior.

---

## 2. Implementation/module map

New modules should be limited to responsibilities that have a real current owner/use.

```text
src/qap/scanner/
  basket_protocol.py
  asset_momentum.py
  asset_momentum_artifacts.py
  basket.py
  basket_artifacts.py
  basket_cli.py

src/qap/policy/
  graph_basket.py

src/qap/experiment/
  basket_policy.py
  basket_manifest.py
  control_specs.py
  cross_sectional_policy.py
  basket_scanner_adapter.py
```

Expected existing-module changes:

```text
src/qap/experiment/manifest.py
src/qap/execution/replay.py
src/qap/execution/routing.py
src/qap/execution/multi_asset.py
src/qap/experiment/runner.py
src/qap/experiment/economics.py
src/qap/experiment/events.py
src/qap/experiment/model_policies.py  # dispatcher/decomposition only
src/qap/scanner_entry.py
.importlinter
```

The scanner/basket web workbench is no longer a Slice-3 deliverable. The unified application/API/workbench is owned by Slice 4. Do not pre-create Slice-4 routes, DTOs, operation resources, or frontend feature trees while finishing the Slice-3 backend.

---

## 3. Milestone 0 — freeze baseline and authority

**Purpose:** ensure Slice 3 begins from the completed Slice-2 handoff without reopening Slice-1/2 contracts.

### Work

- Confirm the implementation branch contains the committed Slice-2 result/status handoff.
- Confirm no uncommitted Slice-1/2 implementation work is mixed into the Slice-3 start.
- Treat the Slice-3 design contract IDs (`MOM-*`, `BASK-*`, `EDGE-*`, `RES-*`, `CTRL-*`, `EXEC-*`, `EVAL-*`, `RSCH-*`, `CAP-*`, `ART-*`, `UI-*`, `ARCH-*`) as normative.
- Do not modify reserved final-OOS fixtures/registry semantics.

### Exit

One documented baseline commit/state is selected for Slice-3 implementation and no upstream protected contract is silently reopened.

---

## 4. Milestone 1 — typed basket protocol and O(N) asset-native momentum

**Design contracts:** `MOM-*`, protocol §5.

### Files

- `src/qap/scanner/basket_protocol.py`
- `src/qap/scanner/asset_momentum.py`
- focused scanner tests

### Work

1. Add one typed/versioned domain protocol such as `SCANNER_V1_BASKET` with:
   - `protocol_id = scanner-v1-basket-v1`;
   - source Scanner-V1 pair-protocol identity/reference;
   - Binance/Gate + USDT bridge;
   - 3–6 asset bounds;
   - equal-weight neutral rule;
   - fixed `0.10` maximum asset tilt;
   - one-venue/horizon/resolution flags;
   - broad momentum horizon mapping:
     - short `1h`, `2d`;
     - medium `4h`, `10d`;
     - swing `1d`, `28d`.
2. Reuse existing Slice-1 universe/slice machinery rather than defining a second listing/coverage policy.
3. Implement asset-native observations over `EvaluatedSeries`:
   - own trailing log return;
   - equal-weight valid-universe common mode;
   - relative momentum;
   - status/reason;
   - exact slice/source identities.
4. Persist deterministic rank fields only after all scope observations are known.
5. Keep invalid/insufficient eligible assets in the result denominator.
6. Do not enumerate pairs or call the SSD graph.
7. Do not add automatic promotion/replay from momentum ranks.

### Required evidence

- hand-calculated own/common-mode/relative score;
- deterministic rank tie-break;
- invalid asset remains visible;
- fewer than two valid assets fails/invalidates the relative scope explicitly;
- future append changes whole-source provenance but not an older exact-slice semantic identity;
- a code-level guard/test demonstrates the momentum implementation does not enumerate NxM pair combinations.

### Exit

One completed in-memory momentum generation is deterministic from PIT universe + exact slices and performs O(N) asset work.

---

## 5. Milestone 2 — immutable asset-momentum artifacts

**Design contracts:** `MOM-06`, `ART-*`.

### Files

- `src/qap/scanner/asset_momentum_artifacts.py`
- artifact schema helpers only if the existing scanner artifact pattern needs them
- focused artifact tests

### Work

1. Implement the layout:

```text
runs/asset-momentum/<momentum_scan_id>.partial/
  definition.json
  eligible_assets.parquet
  observations.parquet
  manifest.json
  integrity.json
```

2. Reuse the neutral `qap.artifact_integrity` exact-file/digest primitive.
3. Publish atomically from `.partial` to completed generation.
4. Fail closed on undeclared files, digest mismatch, schema mismatch, or semantic manifest/table disagreement.
5. Preserve whole-source physical fingerprints separately from semantic exact-slice identity.
6. Expose a focused read function for completed generations; do not build a database/index service.

### Required evidence

- write/read round trip;
- tamper and undeclared-file rejection;
- later source append does not change semantic generation identity when slices are unchanged;
- invalid observation rows survive persistence/readback.

### Exit

Asset-native momentum is a first-class immutable scanner evidence product, not browser memory.

---

## 6. Milestone 3 — BasketDefinition identity and attempt ledger

**Design contracts:** `BASK-*`, `RSCH-*`, `ART-*`, `CAP-*`.

### Files

- `src/qap/scanner/basket.py`
- `src/qap/scanner/basket_artifacts.py`
- focused scanner tests

### Work

1. Implement frozen `BasketEdge`/`BasketDefinition` domain records.
2. Bind exactly one completed Slice-1 source scan.
3. Validate:
   - 3–6 unique economic assets;
   - one venue;
   - one horizon;
   - one allowed decision resolution;
   - assets belong to source scan's PIT admitted universe;
   - selected candidates belong to the same source scan/venue/horizon/resolution;
   - selected scout trial is valid;
   - both edge assets are in the basket;
   - maximum one candidate per unordered pair;
   - at least one selected edge;
   - execution bridge is USDT;
   - every economic asset has one required same-venue asset/USDT execution series at the basket resolution.
4. Permit `unsupported_direct_market`/scout-only alt/alt relationship research when the constituent USDT execution legs exist; do not treat integrity/data-admission failures as this exception.
5. Preserve deep-replay/prospective/manual evidence classes as references/projections, never as one weighted score.
6. Propagate forensic historical-eligibility lineage to the whole basket.
7. Derive deterministic `basket_id` from semantic inputs, excluding creation timestamp.
8. Derive deterministic basket research-family identity from basket protocol + source scan + venue + horizon + resolution so sibling manual attempts remain grouped.
9. Implement durable basket generation staging:

```text
runs/baskets/<basket_id>.partial/
  definition.json
  replay_attempt.json
  manifest.json
  integrity.json
```

10. Enumerate `replay_attempt.json` before QAP experiment preparation with finite status:

```text
enumerated -> setup_failed | replay_failed | completed
```

11. Completed basket artifacts reference a QAP `run_id`; they do not copy economics.
12. Do not add `BasketFreeze`, basket capacity, or automatic basket promotion.

### Required evidence

- reject mixed scan/venue/horizon/resolution;
- reject duplicate unordered-pair candidate selection;
- reject edge outside basket;
- accept valid scout-only indirect edge with valid constituent USDT legs;
- reject provenance/integrity failure disguised as indirect research;
- forensic input makes basket forensic;
- identical semantic definition gets identical basket ID despite different creation timestamp;
- two different manually tried baskets share the expected research-family ID but have distinct basket IDs;
- pre-QAP setup failure remains durably attributable.

### Exit

A manual basket is an immutable, auditable research hypothesis before any combined economics are computed.

---

## 7. Milestone 4 — policy-owned deterministic graph resolver

**Design contracts:** `EDGE-*`, `RES-*`, `ARCH-*`.

### Files

- `src/qap/policy/graph_basket.py`
- policy unit tests

### Work

1. Implement a pure resolver accepting:
   - neutral `AllocationTarget`;
   - frozen economic asset set;
   - frozen selected graph topology represented with generic `PairOrientation`/pair keys;
   - current integer opinions in `{-1,0,+1}`;
   - `Decimal("0.10")` maximum tilt.
2. Implement design math literally:
   - signed incidence pressure `v = B^T p`;
   - declared-degree normalization using all selected edges, including neutral edges;
   - connected-component mean centering;
   - global max-absolute normalization;
   - equal-weight neutral + fixed ±10pp maximum tilt.
3. Use exact Decimal arithmetic crossing into `AllocationTarget`.
4. Do not accept edge-quality/reliability/P&L/capacity inputs.
5. Do not add a generic graph library or optimizer. Basket size is at most six; simple deterministic traversal is sufficient.
6. Keep the resolver scanner-independent so Import Linter's financial-core rule remains intact.

### Required evidence

- exact two-asset limiting result `60/40` and `40/60`;
- exact/hand-calculated three-asset chain;
- pure cycle returns neutral;
- disconnected components preserve component-neutral capital;
- declared-degree behavior differs correctly from active-degree behavior;
- all supported 3–6 asset topologies return long-only weights summing to one;
- invalid opinions/duplicate edges fail at the owner boundary.

### Exit

The vague prior “degree-normalized/component-neutral” phrase is executable as one small deterministic policy primitive.

---

## 8. Milestone 5 — generalize ordinary replay to multi-fill/multi-asset execution

**Design contracts:** `EXEC-*`, `ARCH-03`.

This is the main financial-kernel extension. Do not implement basket economics before it is correct.

### Files

- `src/qap/experiment/manifest.py`
- `src/qap/execution/replay.py`
- `src/qap/execution/routing.py`
- `src/qap/execution/multi_asset.py`
- `src/qap/experiment/runner.py`
- `src/qap/experiment/economics.py`
- `src/qap/experiment/events.py`
- focused execution/experiment scenario tests

### 8.1 Execution manifest

Extend the existing execution contract minimally so a manifest can explicitly distinguish:

```text
direct execution
multi_asset_bridge execution
```

The direct mode remains backward-compatible with current manifests.

Multi-asset bridge mode must bind:

- execution-only bridge asset;
- exact execution instrument IDs;
- valuation numeraire;
- ordinary/adverse cost policy;
- minimum rebalance notional;
- no requirement that the execution bridge be an economic target basket member.

Do not use an arbitrary singular `execution_instrument_id` as a fake representative for a basket.

### 8.2 Historical research metadata boundary

Generalize routing/multi-asset execution only as much as needed to allow historical research callers to omit contemporaneous `MarketMetadata`.

Required behavior:

- reference prices remain mandatory;
- when metadata is supplied, existing Phase-11 precision/notional checks remain strict and unchanged;
- when metadata is intentionally absent for declared historical research mode, direct legs use the existing unconstrained research fill/cost semantics rather than today's metadata;
- no silent fallback from “expected metadata” to “ignore metadata.” The execution mode/caller intent must be explicit.

### 8.3 Replay step

Generalize `ReplayStep` so the authoritative execution payload may contain 0..N fills.

A recommended minimal compatibility shape is:

- preserve current direct execution details for direct runs;
- add the multi-asset execution result/detail when that mode is used;
- expose an authoritative `fills: tuple[Fill, ...]` property for all modes;
- keep any singular `fill` property only as a direct/one-fill convenience and remove all financial dependencies on it.

Do not create a second replay loop if the existing causal loop can branch only at the execution step.

### 8.4 Multi-asset next-open references

At one basket decision boundary, derive next contiguous open references for every declared asset/USDT execution instrument from the same aligned decision-resolution data.

Then:

```text
PolicyDecision
  -> RebalancePlan
  -> execute_multi_asset_rebalance()
  -> fills
  -> apply fills to the one PortfolioLedger exactly once
```

Verify the ledger ending state equals the multi-asset result ending state.

### 8.5 Economics/events

Change role economics and event serialization to iterate `step.fills`.

All of these must include every fill exactly once:

- fees;
- slippage;
- turnover;
- fill count;
- event records;
- reconciliation/audit projections.

Expose multi-asset order outcomes/tracking errors in an audit-safe form without making them a second economic state.

### Required evidence

- all pre-existing direct replay scenarios preserve their behavior;
- one four-asset replay decision produces multiple Phase-11 fills inside ordinary QAP replay;
- fills are applied once and terminal state reconciles;
- fees/slippage/turnover equal the sum over all fills;
- execution-only USDT residue remains owned and valued;
- historical research mode does not require current metadata;
- Phase-11 operational mode with metadata still produces its existing precision/minimum no-fills;
- unsupported/missing route data fails before partial accepted execution according to existing multi-asset preflight semantics.

### Exit

Ordinary QAP replay—not scanner code—can authoritatively execute and evaluate one multi-asset target.

---

## 9. Milestone 6 — causal basket strategy policy and pair-blind momentum control

**Design contracts:** `EDGE-*`, `CTRL-*`, `EVAL-*`.

### Files

- `src/qap/experiment/basket_policy.py`
- `src/qap/experiment/relative_momentum_control.py` if needed
- `src/qap/experiment/model_policies.py` dispatcher/decomposition only
- `src/qap/experiment/manifest.py` for the narrow control spec
- `src/qap/experiment/runner.py` for role composition
- focused experiment/policy tests

### 9.1 Basket strategy composition

Implement one replay policy that:

1. reads the exact selected edge rule/config from the frozen manifest generated from `BasketDefinition`;
2. computes every selected edge's existing rolling log-ratio or residual observation from completed bars only;
3. maps the candidate orientation into the canonical BasketEdge sign;
4. maintains the deterministic ternary opinion state:
   - `|z| >= 1.5` -> update sign;
   - `0.5 < |z| < 1.5` -> retain prior sign;
   - `|z| <= 0.5` -> reset to zero;
5. if any required edge is insufficient/invalid, emits basket-level no-action and leaves all edge states unchanged;
6. otherwise delegates target math to `qap.policy.graph_basket`;
7. records edge observation IDs and resolver audit inputs in the decision/evidence trail.

Do not duplicate the rolling relationship models.

### 9.2 Pair-blind control

Make the existing cross-sectional relative-return + `CrossSectionalTiltPolicy` composition reusable as a real benchmark role.

Because `model_policies.py` is already near the repository hard size threshold and this becomes a second real use, prefer extracting the existing cross-sectional composition into a focused reusable module rather than adding another large branch to `model_policies.py`.

Add one narrow benchmark control spec, for example:

```text
kind: pair_blind_relative_momentum
control_id: relative-momentum-<horizon>
window_returns: exact horizon formation converted to decision bars
maximum_tilt: 0.10
```

It must use the same neutral target, current inventory, timing, execution mode, and cost model as the basket strategy.

### 9.3 Required benchmark roles

For basket experiments, produce at least:

```text
hodl
control:band-5pct-half
control:pair_blind_relative_momentum
strategy
strategy:adverse_cost
primary pair-blind control:adverse_cost
```

The pair-blind relative-momentum control is the predeclared primary incremental benchmark for pair-specific intelligence.

The basket-development gate separately requires strategy > HODL, > band, and > pair-blind momentum under ordinary costs.

### Required evidence

- middle-band state retention;
- neutral reset;
- orientation mapping for residual reverse orientation;
- one invalid edge produces whole-basket no-action without partial state update;
- pure cycle produces neutral target through the real replay policy;
- momentum control does not inspect pair edges;
- all roles receive identical starting inventory/timestamps/costs;
- strategy can beat one comparator and lose another without result presentation hiding the loss.

### Exit

Relationship intelligence and its pair-blind predictive control run under the same QAP economic contract.

---

## 10. Milestone 7 — application operations and BasketDefinition -> ordinary QAP vertical

**Design contracts:** `BASK-*`, `EXEC-*`, `EVAL-*`, `RSCH-*`, `ART-*`.

### Files

- `src/qap/experiment/basket_scanner_adapter.py`
- `src/qap/scanner_entry.py`
- `src/qap/scanner/basket_cli.py`
- basket artifact/orchestration tests
- no-network vertical scenario

### Work

1. Implement the only intentional scanner->experiment basket adapter.
2. Add one thin `qap.scanner_entry` application operation for first-class asset-momentum generation from a completed source scan + venue + horizon. The operation must derive the frozen momentum resolution/formation from `SCANNER_V1_BASKET`, select the matching immutable PIT universe snapshot, build/publish the momentum generation through the existing scanner owners, and accept no override for those protocol constants.
3. Add one thin `qap.scanner_entry` basket-run operation that accepts manual basket intent (source scan, venue, horizon, decision resolution, 3–6 assets, selected candidate IDs, optional persisted momentum reference when available), then internally builds the immutable `BasketDefinition`, enumerates the attempt, runs ordinary QAP, transitions the attempt, and publishes the terminal basket generation. Do not expose a separate durable `create_basket` draft operation.
4. The experiment adapter receives the validated `BasketDefinition`/enumerated attempt from that application operation and resolves exact source scan catalog/data identities.
5. Build one self-contained development `ExperimentManifest` that freezes:
   - economic basket assets;
   - equal-value starting quantities;
   - all selected edge model rules;
   - basket graph policy/config;
   - exact same-venue asset/USDT execution instruments;
   - multi-asset bridge execution mode with USDT;
   - ordinary/adverse cost policy;
   - band control;
   - pair-blind relative-momentum control as primary incremental benchmark;
   - common evaluation/warm-up window;
   - `DataRole.DEVELOPMENT`.
6. Prepare/run through normal `qap.experiment` artifacts.
7. Derive `basket_development_survivor` only from the authoritative run result/roles and the three required gates; store only the status/reference in the basket attempt record.
8. Transition the basket attempt to completed/replay-failed/setup-failed and publish the basket generation atomically.
9. Make retry/recovery deterministic around `.partial` staging and existing deterministic QAP run identity; do not overwrite completed artifacts.
10. Update `.importlinter` with one narrow intentional exception:

```text
qap.experiment.basket_scanner_adapter -> qap.scanner.**
```

and no broader scanner dependency.
11. Add the thin operator surface under `basket_cli.py`; it may route through `qap.scanner_entry` in the same pattern as existing scanner/forward CLIs. If momentum generation is exposed in the CLI, it must call the same application operation rather than rebuilding momentum rules locally.

### Required no-network vertical scenario

Using deterministic local data:

```text
completed Slice-1 scan
  -> optional first-class asset-native momentum generation
  -> manual 3–6 asset BasketDefinition
  -> selected direct + indirect/scout pair rules
  -> enumerated basket replay attempt
  -> ordinary QAP multi-asset replay
  -> HODL/band/momentum/strategy economics
  -> completed basket artifact referencing QAP run
```

Include at least one negative basket that fails an economic comparator and remains persisted.

### Exit

One completed scan can produce first-class immutable asset-momentum evidence, and one manual basket intent reaches one authoritative QAP portfolio result end-to-end without a separate durable draft state or scanner-owned economics.

---

## 11. Milestone 8 — superseded by Slice 4 unified QAP Workbench

**Status:** superseded by explicit product-boundary decision on 2026-08-19.

Do not implement the former standalone read-only Scanner API/Candidate Workbench in Slice 3.

The original M8 responsibilities now belong to:

`docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md`

That plan owns one unified application surface over Slices 1–3 rather than duplicating scanner DTOs, routes, navigation, evidence components, and frontend state immediately before a broader workbench would replace them.

Slice 3 may expose only the Python application/adapter operations needed by Milestone 7. It must not add FastAPI scanner routes, browser mutation endpoints, or React scanner/basket features.

### Exit

No Slice-3 web/API work is implemented; the completed Slice-3 backend presents stable application operations and immutable evidence for Slice 4 to consume.

---

## 12. Milestone 9 — Slice-3 backend / Phase-15 research-kernel closure

### Results/status files

Create/update only after implementation evidence exists:

```text
docs/research/2026-08-18-qap-scanner-slice3-results.md
docs/plans/15-research-scanner-and-candidate-workbench.md
docs/plans/README.md
README.md
implementation_prompt.md
```

### Required integrated scenarios

- asset-native momentum with mixed valid/invalid PIT assets;
- valid sparse 3-asset basket;
- pure-cycle neutral basket;
- disconnected 4+ asset components;
- scout-only indirect pair whose asset/USDT legs execute inside one basket;
- mixed edge evidence causing basket no-action;
- multiple fills per decision with exact reconciliation;
- negative basket vs one or more controls;
- no basket capacity/actionability claim;
- completed `BasketDefinition -> ordinary QAP` adapter result references authoritative experiment/portfolio artifacts without duplicating economics in scanner artifacts.

### Repository completion gate

The implementation plan makes the existing repository completion checks mandatory before declaring the Slice-3 backend complete:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
uv run lint-imports
git diff --check
```

No frontend/OpenAPI gate is added solely for Slice 3 because the former M8 web/API milestone is moved to Slice 4.

Do not add a new framework or generic benchmark service merely to run these checks.

### Exit criteria

Slice 3 is complete only when:

- asset-native momentum is O(N), deterministic, PIT-bound, and persisted;
- manual 3–6 asset baskets are immutable/search-attributable;
- one selected candidate per unordered pair is explicit;
- exact ternary hysteresis + graph resolver produces one long-only target;
- ordinary QAP replay owns multi-asset fills/economics;
- HODL + band + pair-blind momentum comparisons are present;
- negative/failed basket siblings remain visible;
- the former Candidate Workbench milestone is explicitly superseded by the Slice-4 unified workbench plan;
- pair qualifications are not misrepresented as basket capacity;
- reserved final OOS/live authority remain untouched;
- all mandatory backend completion gates are green.

---

## 13. Explicit deferrals after Slice 3

Do not pull these into the implementation merely because the new modules make them conceivable:

- automatic basket discovery/optimizer;
- learned pair reliability weights;
- graph cycle/Hodge diagnostics that alter allocation;
- basket-level prospective freeze/outcome machinery;
- joint multi-leg basket capacity / basket `tradable_now`;
- cross-venue inventory/transfer modeling;
- cross-horizon signal blending;
- momentum/reversal router;
- private exchange credentials/order placement;
- live scheduler/deployment control.

Each requires its own concrete need and design authority.
