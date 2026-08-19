# QAP Slice-4 Unified Workbench Results

Date: 2026-08-19
Status: complete. Slice 4 now provides one local human-operated application over the completed Slice-1 discovery, Slice-2 prospective/actionability, and Slice-3 basket-research workflows while immutable scanner/QAP artifacts remain authoritative. This is a local research application, not live-trading or deployment authority.

## Verified executable state

- Branch: `qap-implementation-20260818`
- M0/M1 read-model handoff: `2111d46` (`feat: add slice4 scanner read models`)
- M2 finite command/operation boundary: `afa6318` (`feat: add slice4 operation boundary`)
- M3 Discovery workbench: `d50669c` (`feat: add slice4 discovery workbench`)
- M4 Prospective workbench: `cf4d29a` (`feat: add slice4 prospective workbench`)
- M5 Basket workbench: `6ab6f72` (`feat: add slice4 basket workbench`)
- M6 Operation Center / lineage: `54f07a3` (`feat: add slice4 operation center and lineage`)
- Slice-3 remediation inherited before closure: `142a18d` source + `b8a6e7b` handoff documentation
- M7 bridge/control integration fix: `04a5e89` (`fix: preserve basket bridge control boundary`)
- M7 contract/browser evidence: `4bc214c` (`test: close slice4 application workflows`)
- Final rendered/accessibility closure: `6961937` (`fix: close slice4 rendered acceptance seams`)

The Python source/test content used by the final full repository pytest gate is unchanged between `4bc214c` and `6961937`; `6961937` changes only React layout/accessibility files and was separately verified by the final frontend, Playwright, and rendered-browser acceptance gates.

## Product boundary now implemented

The application follows one command/query boundary:

```text
Browser
  |-- local draft / domain intent
  |-- GET -> validated immutable evidence
  `-- POST -> one bounded application operation
                 |
                 v
         existing Slice-1/2/3 owner
                 |
                 v
         authoritative artifacts
```

The browser never becomes a scanner, graph resolver, execution engine, accounting engine, capacity engine, or economics engine.

## Finite mutation vocabulary

Slice 4 exposes exactly the approved V1 research mutations:

```text
run_scan
generate_asset_momentum
freeze_forward_cohort
advance_forward_cohort
capture_public_evidence
qualify_candidate
run_basket
```

The HTTP surface is finite and typed. It does not expose a generic shell/CLI/command executor or a generic strategy/configuration builder.

Long-running work is represented by a small durable local operation resource with only:

```text
running
completed
failed
interrupted
```

V1 admits at most one active mutation globally. A second mutation receives typed `409 operation_busy`, while read-only evidence queries remain available. The supported mutation-capable launcher is loopback-only and explicitly `--workers 1`. Worker identity uses PID plus Linux process-start evidence so PID reuse cannot falsely preserve a stale `running` state.

No Redis, Celery, Kafka, database-backed queue, scheduler, retry orchestration, cancellation framework, worker pool, or per-resource lock framework was added.

## Read models and workbenches

### Discovery

The Discovery workbench can:

- initiate the bounded Scanner-V1 scan with venue/horizon/UTC `as_of` intent and explicit manual pins;
- display the frozen Scanner-V1 protocol rather than editable scientific constants;
- inspect PIT universe and graph-scope evidence;
- inspect every valid/invalid candidate trial, automatic/manual selection lineage, replay state, and economic-gate status;
- generate first-class asset momentum using scan + venue + horizon intent only;
- navigate historical QAP candidates into the existing Experiment, Portfolio, and Pair evidence workbenches.

### Prospective / actionability

The Prospective workbench exposes the existing Slice-2 sequence without duplicating its rules:

```text
freeze -> advance -> capture -> qualify
```

It preserves candidate-specific forward windows, partial/final outcome state, automatic/manual selection separation, causal capture evidence, explicit current `as_of`, hypothetical capital, directional capacity fields, and reasoned `research_only` / `small_capacity` / `tradable_now` qualification evidence.

One-shot Binance/Gate public L1/depth/metadata capture remains the existing production owner. Slice 4 adds no capture scheduler or daemon.

### Basket / portfolio research

Basket drafting remains browser-local until submission. The operator selects one completed source scan, venue, horizon, decision resolution, 3-6 economic assets, and at most one admitted candidate per unordered relationship.

Before replay, the UI shows topology and selected evidence only. It deliberately does not synthesize edge opinions, graph pressures, or final target weights.

One `run_basket` intent delegates to the Slice-3 application owner, which creates the immutable `BasketDefinition`, enumerates the attempt, runs ordinary QAP, and publishes terminal basket/QAP evidence. After replay, React displays backend-recorded decision evidence and target weights from QAP's existing portfolio audit. It does not recompute the resolver.

The completed basket view exposes the required benchmark ladder and links to authoritative Experiment/Portfolio/Pair evidence. Negative baskets remain visible as first-class scientific outcomes.

### Operations and lineage

The Operation Center retains durable local history for running/completed/failed/interrupted work and makes operational failure visibly distinct from a negative scientific/economic result.

Cross-slice lineage uses persisted identities rather than filename inference or browser memory:

```text
scan
 -> candidate
 -> historical QAP
 -> freeze/checkpoint
 -> qualification
 -> basket membership
 -> basket QAP
```

Existing Research Runs, Portfolio Economics, Pair Workbench, and Paper Operations remain first-class routes rather than being replaced.

## Integration defect found during M7

The deterministic browser basket flow exposed a real multi-asset control seam. After ordinary multi-asset execution, non-zero execution-only USDT residue can remain in portfolio state. `BandPartialPolicy` previously rejected any holding outside its economic target basket, so a valid basket replay could fail when the declared execution bridge remained non-zero.

`04a5e89` fixes the boundary narrowly:

- `BandPartialPolicy` receives the manifest-declared execution-only bridge for multi-asset runs;
- that bridge is excluded from the control's economic-weight drift calculation;
- any other unexpected outside asset still fails closed;
- ordinary replay continues to value and route the bridge through the existing multi-asset execution owner.

The identical deterministic basket that failed before this fix now completes through ordinary QAP and persists a legitimate `basket_development_rejected` result instead of crashing.

## Deterministic no-network browser evidence

The Slice-4 Playwright fixture uses local checked-in market data plus deterministic generated continuation bars. It seeds only prerequisite immutable evidence and public-capture files; browser workflows call the real FastAPI operation boundary and existing application owners.

The critical browser evidence proves:

### Discovery -> momentum -> basket

1. launch a real swing scan through `POST /api/scans` and track its durable operation;
2. inspect the resulting PIT universe and candidate trials;
3. generate first-class swing momentum through the operation boundary;
4. inspect persisted momentum and candidate lineage;
5. construct a browser-local three-asset basket draft;
6. verify the pre-run view does not expose an authoritative target;
7. submit one real basket-QAP operation;
8. persist and inspect a completed `basket_development_rejected` result;
9. inspect backend-provided graph decision evidence/target and the HODL/band/pair-blind benchmark ladder;
10. navigate to authoritative Portfolio economics.

### Prospective -> qualification -> operation failure

1. open a manually selected historical deep-replay survivor;
2. freeze a real forward cohort through the operation API;
3. advance it to a real partial checkpoint;
4. expose the one-shot public-capture controls without invoking exchange network traffic in repository E2E;
5. qualify against deterministic preseeded 14-day local public microstructure evidence;
6. persist/display `research_only` with `capture complete` and `economic_gates_failed` rather than confusing missing evidence with economics;
7. deliberately submit a nonexistent-scan momentum request and preserve the resulting operational `failed` state without inferring scientific evidence from it.

Public exchange capture itself is intentionally not called by the repository browser gate. Production `capture_public_evidence` still delegates to the existing one-shot Binance/Gate public capture owner; the E2E gate remains deterministic and no-network.

The inherited Phase-14 critical routes also remain green. The final Playwright wrapper result is:

```text
4 passed in 59.9s
```

covering Pair anchor/orientation, Experiment -> Portfolio -> Pair navigation, Slice-4 Discovery/Basket, and Slice-4 Prospective/Operations.

## Rendered browser acceptance

The final agent-browser acceptance used the same isolated local fixture and checked the new primary/read-detail surfaces at desktop `1440x1000` and mobile `390x844`:

| Surface | Desktop | Mobile | Axe | Page errors | Document overflow |
|---|---|---|---|---|---|
| Discovery | pass | pass | 0 violations / 0 incomplete | 0 | none |
| Scan detail | pass | pass | 0 / 0 | 0 | none |
| Candidate detail | pass | pass | 0 / 0 | 0 | none |
| Prospective | pass | pass | 0 / 0 | 0 | none |
| Baskets | pass | pass | 0 / 0 | 0 | none |
| Operations | pass | pass | 0 / 0 | 0 | none |

Rendered acceptance found and closed three presentation seams before finalization:

- the expanded six-link primary navigation now wraps at mobile width instead of forcing a 689px document;
- persisted momentum cards use `min-w-0`, preventing their tables from leaking grid min-content width into the document;
- horizontal momentum/universe data regions are keyboard-focusable labeled regions, and the decorative lineage arrow that caused an axe incomplete was removed.

Every final checked route has exactly one main landmark and one primary navigation.

## Repository/API/frontend completion gate

Final full Python repository suite on the final Python source/test content:

```text
uv run pytest -q
672 passed, 1 skipped in 281.77s
```

Final independent repository/API gates:

```text
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

uv run python scripts/export_openapi.py /tmp/qap-slice4-final-openapi.json
diff -u web/openapi.json /tmp/qap-slice4-final-openapi.json
no diff
```

Final frontend gate after rendered fixes:

```text
pnpm typecheck
PASS

pnpm typecheck:e2e
PASS

pnpm test
22 files / 49 tests passed

pnpm build
PASS

uv run python scripts/run_playwright_e2e.py
4 / 4 passed
```

The source-size warning list remains a review tripwire only; no hand-written source file violates the repository hard limit.

## Explicit non-goals retained

Slice 4 does not introduce:

- authentication or multi-user accounts while the application remains local single-operator;
- distributed/cloud execution or a general task queue;
- automatic scan/capture/basket scheduling;
- private exchange credentials or order placement;
- live-capital deployment authority;
- basket-level joint capacity or basket `tradable_now`;
- automatic basket optimization/discovery;
- cross-venue inventory transfer modeling;
- browser-side financial/resolver logic;
- configurable strategy/plugin/dashboard builders;
- generalized cancellation/resume orchestration;
- concurrent mutating worker pools.

Those require independent product/design authority if they are ever needed.

## Completion conclusion

Slices 1-3 remain the research/economic engines. Slice 4 is now the finite human-operability layer over them. The admitted workflows can be initiated, inspected, and traversed through one local web application without bypassing the scientific contracts or moving financial authority into React/FastAPI.
