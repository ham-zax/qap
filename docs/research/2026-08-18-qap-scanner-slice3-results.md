# QAP Scanner V1 Slice-3 Results

Date: 2026-08-19
Status: asset-native momentum and manual one-inventory basket research are complete. The original M9 full repository gate was green at `a79bd4d`; post-review remediation is complete at `142a18d` with the Slice-3 scenario and static repository gates green. The current whole-repository pytest gate is blocked only by two later Slice-4 OpenAPI contract-test mismatches. This is development evidence only, not final-OOS evidence, basket capacity evidence, or a trading recommendation.

## Verified source state

- Branch: `qap-implementation-20260818`
- Milestone-6 implementation commit: `46ef407` (`feat: complete slice3 basket strategy milestone`)
- Milestone-6 research-integrity closure: `dd9df14` (`fix: close slice3 milestone6 integrity seams`)
- Milestone-7 application vertical: `0a15506` (`feat: complete slice3 basket application vertical`)
- Final architecture-gate alignment: `a79bd4d` (`test: align slice3 architecture gate`)
- Original M9 repository-verified Slice-3 source/test state: `a79bd4d`
- Post-review Slice-3 remediation handoff: `142a18d` (`fix: close slice3 basket review findings`)
- Slice-1 historical discovery and Slice-2 prospective/current qualification contracts remain prerequisites and were not reopened.
- The former Slice-3 Milestone-8 Candidate Workbench is intentionally superseded by the separately frozen Slice-4 unified-workbench plan; Slice 4 was not implemented during this closure.

## Scope closed by Slice 3

Slice 3 now provides the approved asset-to-portfolio research path:

```text
completed Slice-1 scan / PIT universe
  -> O(N) asset-native relative momentum
  -> immutable momentum generation
  -> manual same-venue 3-6 asset basket intent
  -> immutable BasketDefinition + enumerated attempt
  -> causal selected-edge opinions
  -> deterministic graph resolver
  -> one long-only economic target
  -> ordinary QAP multi-asset/USDT-bridge execution
  -> strategy / HODL / band / pair-blind momentum / adverse economics
  -> basket_development_survivor or basket_development_rejected
  -> terminal immutable basket artifact referencing the QAP run
```

Slice 3 does not add an optimizer, automatic basket discovery, cross-venue shared inventory, basket prospective status, basket capacity, private exchange authority, or live trading.

## Asset-native momentum

The first-class momentum product is O(N) over the admitted point-in-time asset universe rather than pairwise NxM search. The frozen Scanner-V1 rules remain:

- short: `1h` resolution over `2d`;
- medium: `4h` resolution over `10d`;
- swing: `1d` resolution over `28d`.

`generate_asset_momentum(...)` is now an outer application operation. It accepts completed scan + venue + horizon intent, reuses the frozen Slice-1 PIT admission decision, derives the momentum rule in the backend, creates exact causal `EvaluatedSeries` slices, and publishes the existing immutable momentum artifact. It does not restore the incorrect graph-slice/momentum-slice fingerprint equality and it verifies each evaluated series against the universe row's economic asset, venue symbol, quote bridge, venue, cutoff, resolution, and formation window.

## Manual basket authority

A `BasketDefinition` binds one completed Slice-1 source scan, one venue, one horizon, one decision resolution, 3-6 economic assets, and at most one explicitly selected candidate per unordered pair. Manual selection remains lineage, not a hidden optimizer.

`run_basket_with_qap(...)` is the single application operation for basket intent. There is no durable pre-run web/application draft object. The operation:

1. validates the completed source scan and frozen catalog;
2. optionally validates a persisted matching momentum generation;
3. builds the immutable `BasketDefinition`;
4. enumerates the basket replay attempt before QAP setup;
5. prepares one development-only ordinary-QAP manifest;
6. runs/reuses the deterministic authoritative QAP run;
7. derives the basket development gate only from authoritative QAP role economics;
8. transitions the attempt to a terminal state and atomically publishes the basket generation.

A repeated identical basket intent returns the already validated terminal basket artifact rather than overwriting it.

## Graph policy and benchmark contract

The committed graph resolver remains policy-owned and deterministic. Selected pair rules produce canonical ternary opinions only when all required edge evidence is valid; invalid mixed evidence fails the basket decision closed without partially advancing edge state.

The resolver uses the frozen equal-weight neutral target and exact declared-degree/component-centering/global-tilt semantics. Resolver evidence contains the selected edge observations, canonical opinions, and fixed `0.10` tilt audit input.

Every authoritative `basket_graph` experiment is development-only and requires:

- ordinary strategy;
- matched HODL;
- frozen `band-5pct-half` control;
- pair-blind relative momentum as the primary incremental benchmark;
- declared adverse-cost roles;
- `multi_asset_bridge` execution through the existing Phase-11 executor;
- no reserved final-OOS consumption.

The pair-blind comparator derives its formation window from the frozen horizon and fixes maximum tilt at `0.10`; those are not caller-configurable research knobs.

## Ordinary QAP multi-asset execution

Slice 3 did not add scanner-owned P&L, fills, routing, or accounting. Ordinary QAP owns all economics and uses the existing Phase-11 multi-asset executor.

The completed kernel supports 0..N fills per decision, run-scoped fill identities, authoritative single-ledger application, fee/slippage/turnover aggregation over all fills, execution-only USDT residue, and unchanged direct-replay behavior.

M7 exposed one artifact projection seam from the earlier multi-asset work: terminal QAP summaries correctly included non-zero execution-only USDT residue while `inventory.parquet` serialized economic basket assets only. The inventory table now includes the declared bridge asset for multi-asset runs, so terminal artifact semantics reconcile exactly while zero bridge rows remain harmless.

## Basket economic gate

A completed basket attempt records one explicit development classification:

```text
basket_development_survivor
basket_development_rejected
```

`basket_development_survivor` requires the authoritative ordinary-cost strategy to beat all three mandatory development comparators:

- matched HODL;
- `band-5pct-half`;
- pair-blind relative momentum.

A basket failing any mandatory comparator remains a completed, persisted `basket_development_rejected` result. No rule is loosened to manufacture a survivor.

## No-network vertical evidence

The deterministic Slice-3 scenario exercises the real owners without exchange network access:

1. writes local immutable Binance-style AAA/USDT, BBB/USDT, and CCC/USDT hourly evidence plus one real AAA/BBB direct market and lifecycle/catalog records;
2. runs the real Slice-1 short-horizon scan;
3. proves at least one selected candidate reaches completed direct pair replay and also retains a valid scout-only indirect candidate whose pair has no direct market;
4. generates and publishes the first-class short-horizon asset-momentum artifact;
5. submits a three-asset manual basket using the scout-only indirect rule and the real asset/USDT execution legs;
6. verifies the pair-blind control has all 48 required short-horizon returns at the first evaluation boundary and that both strategy and primary control are causally available there;
7. runs ordinary QAP through multi-asset bridge execution and publishes a completed basket survivor with authoritative QAP reference;
8. submits a second basket containing both the completed direct edge and the scout-only indirect edge and reaches one authoritative QAP result;
9. repeats the original intent and reuses the terminal immutable basket artifact;
10. submits a valid negative-scaffold sibling from the same scan and persists it as `basket_development_rejected` rather than filtering it out;
11. verifies the resulting QAP run is `DataRole.DEVELOPMENT`, does not consume final OOS, and contains strategy, HODL, band, and pair-blind roles.

This fixture is deterministic implementation evidence. Its positive/negative synthetic classifications are not claims about real-market profitability.

## Application/operator handoff

The Slice-3 backend now exposes the two application operations Slice 4 requires in addition to the pre-existing Slice-1/2 operations:

```text
generate_asset_momentum(...)
run_basket_with_qap(...)
```

A thin `python -m qap.scanner.basket_cli` operator surface delegates to those owners; it does not reimplement scientific rules.

The experiment-to-scanner dependency remains limited to three intentional adapters:

- `scanner_adapter.py`;
- `prospective_scanner_adapter.py`;
- `basket_scanner_adapter.py`.

Import-linter and the repository architecture test both enforce that narrow boundary.

## Repository completion gate

The original M9 `a79bd4d` source/test state was verified with the mandatory Slice-3/M9 repository gates:

```text
uv run pytest -q
667 passed, 1 skipped in 237.51s

uv run ruff check .
All checks passed!

uv run ruff format --check .
334 files already formatted

uv run pyright src tests scripts
0 errors, 0 warnings, 0 informations

uv run python scripts/check_source_size.py
source-size: ok (23 review warnings; no >700-line hard failure)

uv run lint-imports
8 contracts kept, 0 broken

git diff --check
passed
```

Post-review remediation at `142a18d` corrected the pair-blind warm-up to reserve one more price observation than the required return count and extended the no-network vertical to cover a completed direct edge together with a scout-only indirect edge. Verification after that remediation:

```text
uv run pytest -q tests/scenarios/test_scanner_slice3.py
1 passed in 96.17s

uv run ruff check .
All checks passed!

uv run ruff format --check .
345 files already formatted

uv run pyright src tests scripts
0 errors, 0 warnings, 0 informations

uv run python scripts/check_source_size.py
source-size: ok (24 review warnings; no >700-line hard failure)

uv run lint-imports
8 contracts kept, 0 broken

git diff --check
passed
```

The current whole-repository `uv run pytest -q` result after `142a18d` was `665 passed, 1 skipped, 2 failed`. Both failures are in `tests/contract/api/test_openapi.py` and are caused by later Slice-4 API work: the test still expects the former read-only operation-ID set and the former `QAP Research Evidence API` title while the current application exposes the new Slice-4 command/query surface and `QAP Research Application API` title. Neither failure touches the Slice-3 remediation files or invalidates the targeted Slice-3 scenario above.

The 500-700 line source-size warnings remain review tripwires only. No current hand-written source file exceeds the repository hard limit; the new basket scanner adapter is 495 lines.

## Research limitations and deferrals

Slice 3 establishes a trustworthy development-only combined-inventory research path; it does not establish basket prospective survival, basket execution capacity, or live readiness.

Pair-level Slice-2 `research_only` / `small_capacity` / `tradable_now` evidence may be displayed beside basket edges later, but it must not be algebraically converted into basket actionability or capacity.

Reserved final OOS remains sealed. `basket_graph` manifest admission requires `DataRole.DEVELOPMENT`, so the generic experiment surface cannot consume final OOS through the Slice-3 policy.

The following remain explicitly deferred: automatic basket discovery/optimization, learned reliability weights, basket-level prospective machinery, joint multi-leg capacity, cross-venue inventory/transfer modeling, cross-horizon signal blending, private exchange credentials, live scheduling, and deployment authority.

The next product layer is the frozen Slice-4 Unified QAP Workbench plan. It has not been implemented as part of Slice-3/Phase-15 closure.
