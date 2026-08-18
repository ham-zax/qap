# QAP Slice 4 Unified Workbench Implementation Plan

**Date:** 2026-08-19

**Status:** implementation plan created from the approved Slice-4 product-boundary decision. Do not execute until Slice-3 Milestone 7 and backend closure are complete and the user explicitly starts Slice 4.

**Goal:** make the completed Slice-1 discovery, Slice-2 prospective/actionability, and Slice-3 basket-research workflows operable and inspectable from one local web application without moving scientific or financial authority into FastAPI or React.

**Architecture:** extend the existing FastAPI + React analytical workbench into a local single-operator command/query application. FastAPI remains a thin boundary over existing Python application operations and immutable artifact readers. Long-running commands create a small durable local operation record and execute in a bounded local Python worker process; immutable QAP/scanner artifacts remain the scientific source of truth.

**Tech Stack:** existing FastAPI/Pydantic backend; Python standard-library process/filesystem primitives; existing QAP scanner/experiment/market application entry points; React 19, TypeScript, Vite, TanStack Router, TanStack Query, generated OpenAPI TypeScript contracts, existing chart/table/accessibility primitives, and native SVG for the bounded 3–6 node basket graph. No new runtime dependency is expected.

**Existing design authority:**

- `docs/superpowers/specs/2026-08-17-qap-web-operations-design.md`
- `docs/plans/08-fastapi-contract-and-web-boundary.md`
- `docs/plans/09-react-analytical-workbench-and-charts.md`
- `docs/plans/14/acceptance-and-regression.md`
- `docs/plans/15-research-scanner-and-candidate-workbench.md`
- the approved Slice-1/2/3 scanner designs and final backend result records

---

## Global Constraints

- Slice 4 is an application/product layer over Slices 1–3, not a fourth research or financial authority.
- Immutable scanner/QAP artifacts remain the source of scientific truth. Operation records answer only what the operator requested, whether it is running, and which authoritative result/evidence was produced.
- The browser submits domain intent only. It must not submit hidden scientific constants such as model windows, entry thresholds, maximum tilt, benchmark definitions, cost models, graph weights, or protocol versions when those are frozen by Scanner/QAP contracts.
- React never fits models, resolves graph targets, computes fills, accounting, costs, capacity, benchmark economics, or wealth.
- FastAPI routes call existing application/composition owners; they must not reproduce scanner, policy, execution, or experiment business logic.
- Do not route browser actions through shell commands or CLI subprocesses. A worker imports/calls Python application functions directly.
- Use a finite typed command vocabulary. Do not add a generic `execute`, arbitrary-command, strategy-DSL, or free-form config endpoint.
- No private exchange/account/order APIs, live-capital deployment, leverage, borrowing, derivatives, or final-OOS search/preview authority.
- Public capture remains the existing bounded one-shot public Binance/Gate capture. Slice 4 does not add a scheduler/daemon.
- Pair-level `tradable_now`/capacity remains pair/candidate evidence and must never be promoted to a basket-level capacity/actionability claim.
- Local/single-operator deployment remains the product boundary. Keep loopback binding as the default; do not add authentication, tenancy, cloud deployment, Redis, Celery, Kafka, a database, or a distributed queue without a separately demonstrated need.
- CORS remains explicit and narrow. Mutation routes add only the HTTP methods/headers they require.
- Preserve negative, invalid, failed, no-survivor, insufficient-evidence, and rejected outcomes in API/read models and UI. Do not filter them into a positive-only workflow.
- Keep OpenAPI the frontend contract source; do not hand-maintain parallel TypeScript DTOs.
- Reuse existing Portfolio, Experiment, Pair, Paper Operation, AppShell, table, chart, status, exact-number, and error presentation components where they already own the behavior.
- No new graph/visualization package solely for Slice 4. The basket graph is bounded to 3–6 assets and can be rendered with native SVG plus backend-provided edge/target values.
- Preserve the repository 500/700-line source-size policy and existing import-linter architecture.

---

## 1. Product boundary and dependency flow

Slice 4 turns the backend slices into one human-operated research application:

```text
Browser
  |
  v
FastAPI command/query boundary
  |
  +--> read models -------------------------> immutable scanner/QAP evidence
  |
  +--> typed command -> local operation ----> existing Python application owner
                                      |             |
                                      |             +--> Slice 1 discovery
                                      |             +--> Slice 2 forward/capture/qualification
                                      |             +--> Slice 3 basket -> ordinary QAP
                                      |
                                      +-----------> authoritative artifact/result reference
```

The operation resource is not part of research identity:

```text
operation_id
  = local operator/request lifecycle identity

scan_id / candidate_id / freeze_id / checkpoint_id /
qualification_id / basket_id / qap run_id
  = scientific/economic evidence identities owned by their existing modules
```

Do not derive scientific identities from the operation ID and do not rewrite completed evidence when an operation is retried.

---

## 2. Prerequisite application operations

Slice 4 begins only after Slice-3 backend closure has frozen the callable application surface.

Existing operations already present before Slice 4 include:

```text
qap.scanner_entry.run_scan_with_qap(...)
qap.scanner_entry.freeze_scan_with_qap(...)
qap.scanner_entry.advance_forward_with_qap(...)
qap.scanner_entry.qualify_forward_with_qap(...)
qap.market.public_capture.capture_public_spot(...)
```

Slice-3 Milestone 7 must add the basket application/composition operation that loads a persisted `BasketDefinition`, runs the ordinary-QAP basket experiment, and persists the basket attempt/result reference.

Slice 4 may add thin application glue only when a browser command cannot call these owners without reconstructing persisted intent. It must not add a second scanner, replay, qualification, capture, or basket engine.

---

## 3. File/module map

Create only files that have a concrete current responsibility.

### Backend

```text
src/qap/api/
  scanner_schemas.py        # Slice-1/2 read DTOs + admitted command request DTOs
  scanner_views.py          # scan/candidate/forward/qualification artifact projections
  basket_schemas.py         # Slice-3 basket read DTOs + basket command request DTOs
  basket_views.py           # basket/momentum/attempt/resolver projections
  operations.py             # local operation records, atomic lifecycle store, launcher
  operation_worker.py       # direct Python dispatch to existing application operations
  routes/
    scanner.py              # scanner/prospective/capture/qualification GET+POST resources
    baskets.py              # momentum/basket GET+POST resources
    operations.py           # operation list/detail
```

Expected focused changes:

```text
src/qap/api/app.py
src/qap/api/settings.py
src/qap/api/routes/__init__.py
src/qap/api/errors.py       # only if new stable operation error codes need the existing envelope
```

Do not create a generic repository/service/facade layer between routes and these readers/operation owners.

### Frontend

```text
web/src/api/client.ts
web/src/api/queries.ts
web/src/api/schema.d.ts      # generated
web/openapi.json             # generated

web/src/features/discovery/
web/src/features/prospective/
web/src/features/baskets/
web/src/features/operations/
web/src/features/lineage/

web/src/routes/scanner.index.tsx
web/src/routes/scanner.$scanId.tsx
web/src/routes/candidate.$scanId.$candidateId.tsx
web/src/routes/prospective.$cohortId.tsx
web/src/routes/baskets.index.tsx
web/src/routes/baskets.$basketId.tsx
web/src/routes/operations.index.tsx
web/src/routes/operations.$operationId.tsx

web/src/components/AppShell.tsx
web/src/routeTree.gen.ts      # generated by existing router tooling
```

Do not pre-create route/component files before the milestone that needs them.

---

## 4. Slice-4 Milestone 0 — freeze backend handoff and application command contracts

**Purpose:** prevent the web layer from discovering or redefining backend semantics while it is being built.

### Files

- Modify planning/status documentation only if Slice-3 final result names differ from this plan.
- No production code is expected in this milestone.

### Interfaces

**Consumes:** final Slice-1/2 results; completed Slice-3 M7/M9 result; existing `scanner_entry`, public capture, and basket application entry points.

**Produces:** one frozen command/query inventory used by later Slice-4 milestones.

### Steps

- [ ] Confirm Slice 3 is backend-complete and its final results document names the authoritative basket application function and persisted basket result identity.
- [ ] Freeze the command vocabulary below; remove any command whose owner does not actually exist at the handoff.
- [ ] Freeze the read-model identity joins: scan -> candidate -> QAP run; candidate -> freeze/checkpoint/qualification; candidate -> basket edge; basket -> ordinary-QAP run.
- [ ] Confirm browser requests never need filesystem paths, repository paths, protocol internals, or financial constants.

### Command vocabulary

The initial browser mutation surface is finite:

```text
run_scan
freeze_forward_cohort
advance_forward_cohort
capture_public_evidence
qualify_candidate
create_basket
run_basket
```

A manual/pinned Slice-1 investigation is represented through the admitted scan/pin/manual-replay inputs already owned by Slice 1; do not create a separate arbitrary replay engine.

### Acceptance criteria

- Every command maps to one existing application owner.
- Every scientific result maps to an immutable existing artifact identity.
- No browser command requires a hidden model/cost/benchmark/protocol constant.
- No Slice-4 code begins until this inventory matches the actual Slice-3 backend handoff.

---

## 5. Slice-4 Milestone 1 — unified read models over Slices 1–3

**Purpose:** absorb the former Slice-3 M8 read-only workbench backend into one reusable query surface before mutation controls are added.

### Files

- Create: `src/qap/api/scanner_schemas.py`
- Create: `src/qap/api/scanner_views.py`
- Create: `src/qap/api/basket_schemas.py`
- Create: `src/qap/api/basket_views.py`
- Create: `src/qap/api/routes/scanner.py`
- Create: `src/qap/api/routes/baskets.py`
- Modify: `src/qap/api/app.py`
- Modify: `src/qap/api/routes/__init__.py`

### Interfaces

**Consumes:** completed scan artifacts, prospective cohort/checkpoint/outcome/qualification artifacts, asset-momentum artifacts, BasketDefinition/attempt artifacts, existing QAP experiment/portfolio readers.

**Produces:** typed OpenAPI read models and stable cross-links to existing Experiment/Portfolio/Pair resources.

### Steps

- [ ] Add backend-authoritative projections for Scanner-V1 protocol, scan summaries, PIT universe, candidates, promotions/manual lineage, replay status, asset momentum, forward cohorts/checkpoints, qualifications, baskets, basket attempts, selected edges, resolver audit inputs/target, and QAP run references.
- [ ] Reuse existing artifact validators/readers. A view must fail closed on invalid artifacts rather than parse filenames or partially trust unvalidated tables.
- [ ] Preserve negative/invalid/failed rows and explicit automatic/manual lineage.
- [ ] Return identifiers and routeable references, not arbitrary absolute filesystem paths.
- [ ] Keep pair qualification evidence candidate-local and label basket actionability/capacity as unavailable rather than synthesizing it.
- [ ] Add read resources around the existing hierarchy, such as:

```text
GET /api/scanner/protocol
GET /api/scans
GET /api/scans/{scan_id}
GET /api/scans/{scan_id}/candidates
GET /api/scans/{scan_id}/candidates/{candidate_id}
GET /api/forward/cohorts
GET /api/forward/cohorts/{cohort_id}
GET /api/baskets
GET /api/baskets/{basket_id}
```

The exact child endpoints may be collapsed into a sufficiently bounded detail DTO when that avoids redundant routes.

### Acceptance criteria

- A candidate detail can navigate to its historical QAP result, prospective evidence, qualifications, and basket memberships without browser-side joins over raw files.
- A basket detail exposes its selected candidates, resolver audit/target, attempt state, and authoritative QAP run reference without duplicating run economics.
- Invalid/negative evidence remains visible.
- Existing Experiment/Portfolio/Pair routes remain the authority for experiment economics and time-series detail.

### Required repository-contract checks

Because API DTOs change, regenerate/check the existing deterministic OpenAPI contract using the repository's existing export/codegen flow. Do not create a second TypeScript schema source.

---

## 6. Slice-4 Milestone 2 — local research-operation lifecycle and command API

**Purpose:** make long-running QAP operations safe for a browser without holding one HTTP request open for minutes or introducing a distributed job platform.

### Files

- Create: `src/qap/api/operations.py`
- Create: `src/qap/api/operation_worker.py`
- Create: `src/qap/api/routes/operations.py`
- Modify: `src/qap/api/scanner_schemas.py`
- Modify: `src/qap/api/basket_schemas.py`
- Modify: `src/qap/api/routes/scanner.py`
- Modify: `src/qap/api/routes/baskets.py`
- Modify: `src/qap/api/settings.py`
- Modify: `src/qap/api/app.py`
- Modify: `src/qap/api/routes/__init__.py`

### Interfaces

**Consumes:** the frozen Milestone-0 command vocabulary and existing Python application functions.

**Produces:** durable local operation IDs/status plus resource-specific `POST` endpoints returning `202 Accepted` and an operation reference.

### Operation contract

Use a minimal lifecycle:

```text
queued -> running -> completed
                  -> failed
```

V1 deliberately does not add cancel/retry/pause/scheduling semantics. A new user request creates a new operation; deterministic underlying QAP/scanner identities continue to own idempotence/recovery where already supported.

Persist operation state under the configured run root in a separate operational namespace, for example:

```text
<run_root>/web-operations/<operation_id>/request.json
<run_root>/web-operations/<operation_id>/status.json
```

- `request.json` is immutable after creation.
- `status.json` is operational mutable state written by atomic replace.
- Operation IDs may use a standard random UUID; they are not scientific hashes.
- Public DTOs expose domain request summaries, timestamps, status, safe failure details, and authoritative result IDs/references. They do not expose arbitrary local paths.

### Worker boundary

- [ ] Launch a local worker with `subprocess.Popen([...])` using `sys.executable` and an importable Python module; do not invoke a shell and do not call the existing CLI.
- [ ] Worker reads the internal operation request and calls the existing Python owner directly.
- [ ] API restart must not erase completed/failed operation history. A worker process may continue independently of the HTTP process.
- [ ] If a previously `running` operation is later observed with no live worker after a process/machine interruption, mark it failed with an explicit `interrupted_worker` operational reason rather than pretending completion.
- [ ] Scientific/application exceptions become operation failure state; they do not mutate completed evidence or convert fatal research-integrity failures into ordinary positive results.

### Operational settings

Extend `ApiSettings` only with operational roots genuinely required by the command owners, such as repository root and public capture root. Continue to derive business/scientific rules from existing protocols, not environment variables.

The browser never supplies `data_root`, `run_root`, `capture_root`, or `repository_root`.

### Resource-specific command endpoints

Prefer finite resource commands rather than `POST /api/operations/execute`:

```text
POST /api/scans
POST /api/forward/cohorts
POST /api/forward/cohorts/{cohort_id}/advances
POST /api/captures
POST /api/qualifications
POST /api/baskets
POST /api/baskets/{basket_id}/runs

GET  /api/operations
GET  /api/operations/{operation_id}
```

`POST /api/scans` may carry the existing bounded pin/manual-replay intent because `run_scan_with_qap` already owns those semantics. Do not expose generator/model/template/threshold controls.

### CORS/API boundary

- Add only `POST` to the existing local CORS method set when mutation routes land.
- Continue `allow_credentials=False` and the existing explicit origin list.
- Preserve the existing typed error envelope for synchronous request-validation errors; asynchronous operation failures are represented in the operation resource.

### Acceptance criteria

- A long scan returns an operation ID promptly rather than keeping the browser request open until the scan finishes.
- A completed operation points to an authoritative scan/cohort/qualification/basket/QAP identity.
- API restart does not destroy completed operation history.
- No CLI, shell command, Redis/Celery/database, or scheduler is introduced.

---

## 7. Slice-4 Milestone 3 — Discovery workbench

**Purpose:** make Slice-1 discovery and research lineage operable from the browser without exposing a generic scanner builder.

### Files

- Modify: `web/src/api/client.ts`
- Modify: `web/src/api/queries.ts`
- Create focused files under: `web/src/features/discovery/`
- Create: `web/src/routes/scanner.index.tsx`
- Create: `web/src/routes/scanner.$scanId.tsx`
- Create: `web/src/routes/candidate.$scanId.$candidateId.tsx`
- Modify: `web/src/components/AppShell.tsx`

### Interfaces

**Consumes:** Milestone-1 scan/candidate read DTOs and Milestone-2 `run_scan` operation endpoint.

**Produces:** browser workflow for admitted universe discovery, scan execution, candidate inspection, pin/manual intent, and historical-QAP navigation.

### Steps

- [ ] Add one Discovery entry route with venue/horizon/UTC `as_of` intent and bounded `ScannerPinSpec` inputs.
- [ ] Present the frozen Scanner-V1 protocol rather than editable generator/model/template/threshold fields.
- [ ] Launch the scan as an operation and navigate to/track that operation while it runs.
- [ ] Show completed scan context: PIT universe state, graph/candidate counts, selection lineage, failures/no-survivor outcomes, and asset-native momentum when available.
- [ ] Candidate detail must explain why the candidate exists: PIT admission -> graph/neighbor evidence -> fixed trial/template/orientation -> scout -> promotion/manual lineage -> authoritative QAP result.
- [ ] Manual/pinned research remains visibly labeled and separate from automatic-selection evidence.
- [ ] Reuse existing Experiment/Portfolio/Pair navigation for economic/relationship detail instead of duplicating those views.

### Acceptance criteria

- The browser can initiate the canonical bounded scan and inspect all outcomes, including zero-survivor and failed candidates.
- No arbitrary scanner strategy/config editor exists.
- Scientific/economic values shown by the workbench are backend values or links to existing authoritative workbenches.

---

## 8. Slice-4 Milestone 4 — Prospective and actionability workbench

**Purpose:** expose the complete Slice-2 operator flow with causal timing and evidence reasons visible.

### Files

- Create focused files under: `web/src/features/prospective/`
- Create: `web/src/routes/prospective.$cohortId.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/api/queries.ts`
- Modify Discovery/candidate components only where they need forward-evidence links/actions.

### Interfaces

**Consumes:** forward/cohort/checkpoint/qualification read DTOs and `freeze`, `advance`, `capture`, `qualify` operation endpoints.

**Produces:** browser workflow matching the existing Slice-2 operator contract.

### Steps

- [ ] From an eligible candidate/scan, allow the operator to freeze a cohort at an explicit UTC timestamp.
- [ ] Show each freeze's horizon/resolution-specific forward window and checkpoint maturity rather than implying all members share one bar boundary.
- [ ] Allow explicit `advance --through` intent through the operation API and show candidate-specific partial/final/invalid outcomes.
- [ ] Expose one-shot Binance/Gate L1/depth/metadata capture actions. Do not add automatic cadence scheduling.
- [ ] Show causal capture coverage and distinguish missing evidence from economic failure.
- [ ] Qualification input is only explicit current UTC `as_of` + positive hypothetical capital; the backend derives current QAP state, coverage window, directional capacity, costs, and frozen protocol details.
- [ ] Present `research_only`, `small_capacity`, or `tradable_now` with the exact reasons/evidence references that justify the state.
- [ ] Keep automatic cohort scoreboard economics separate from manual/pinned evidence.

### Acceptance criteria

- The complete `freeze -> advance -> capture -> qualify` workflow is operable without a CLI.
- Future capture rows do not appear in an earlier qualification claim.
- The UI never labels an unqualified or incompletely captured candidate as actionable.
- Pair actionability is never displayed as basket actionability.

---

## 9. Slice-4 Milestone 5 — Portfolio/basket workbench

**Purpose:** make Slice-3 manual basket research graph-native and economically inspectable while leaving all resolver/replay math in QAP.

### Files

- Create focused files under: `web/src/features/baskets/`
- Create: `web/src/routes/baskets.index.tsx`
- Create: `web/src/routes/baskets.$basketId.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/api/queries.ts`

### Interfaces

**Consumes:** basket/momentum read DTOs plus `create_basket` and `run_basket` operations from the Slice-3 M7 handoff.

**Produces:** manual 3–6 asset basket construction, selected candidate-edge review, graph/target inspection, and authoritative basket-QAP navigation.

### Steps

- [ ] Let the operator select one source scan, one venue, one horizon, one decision resolution, and 3–6 admitted economic assets.
- [ ] Show candidate rules available for each unordered relationship and allow at most one admitted candidate ID per unordered pair.
- [ ] Keep scout-only/indirect/manual evidence visibly attributed rather than hiding it behind a generic edge state.
- [ ] Show asset-native momentum as contextual pair-blind evidence, not an automatic basket optimizer.
- [ ] Render the bounded 3–6 node selected-edge graph with native SVG. The frontend receives and displays backend edge identity/opinion/resolver audit values; it does not recompute pressure or target weights.
- [ ] Show the backend final target and execution-only USDT bridge separately from the economic basket.
- [ ] Launch the authoritative basket QAP operation.
- [ ] Present the required benchmark ladder through existing QAP run data: strategy, HODL, band-5pct-half, pair-blind relative momentum, and the declared adverse roles.
- [ ] Link to existing Portfolio Economics, Experiment Detail, and Pair Workbench routes for fills, costs, holdings, relative wealth, and relationship series.
- [ ] Show negative baskets and comparator failures as first-class outcomes.

### Acceptance criteria

- A manual basket can be created and run entirely from the browser using backend-owned scientific rules.
- The graph shown in React matches backend-provided selected edges/opinions/target; no financial target is reconstructed client-side.
- Basket QAP economics remain owned by existing experiment/portfolio resources.
- No basket capacity or basket `tradable_now` state is invented.

---

## 10. Slice-4 Milestone 6 — operation center and unified research lineage

**Purpose:** make the application coherent across slices rather than three adjacent mini-tools.

### Files

- Create focused files under: `web/src/features/operations/`
- Create focused files under: `web/src/features/lineage/`
- Create: `web/src/routes/operations.index.tsx`
- Create: `web/src/routes/operations.$operationId.tsx`
- Modify: `web/src/components/AppShell.tsx`
- Modify existing Discovery/Prospective/Basket detail features where cross-links are required.

### Interfaces

**Consumes:** operation DTOs and cross-slice identity references from previous milestones.

**Produces:** persistent operator-history view and navigable scientific lineage.

### Steps

- [ ] Add an Operation Center showing queued/running/completed/failed work with type, requested time, duration, safe failure reason, and authoritative result links.
- [ ] Do not show operation state as research success/failure; distinguish operational completion from scientific/economic outcome.
- [ ] Add a compact lineage view that can traverse:

```text
scan
 -> candidate
 -> historical QAP run
 -> freeze / checkpoint
 -> qualification
 -> basket membership
 -> basket QAP run
```

- [ ] Keep existing Experiment/Portfolio/Pair/Paper Operation routes in the main AppShell; Slice 4 adds Discovery, Prospective, Baskets, and Operations rather than replacing the established evidence workbenches.
- [ ] Preserve typed failure/recovery presentation through existing `QapApiError`, error boundary, and status components.

### Acceptance criteria

- An operator can leave a long-running task, inspect other evidence, and return to its status/result later.
- Cross-slice lineage does not depend on browser memory or inferred filenames.
- Operational failure and negative research outcome are visually/semantically distinct.

---

## 11. Slice-4 Milestone 7 — product closure

**Purpose:** prove the unified application preserves QAP's scientific boundaries across real browser workflows.

### Results/status files

Create/update only after implementation evidence exists:

```text
docs/research/2026-08-19-qap-slice4-unified-workbench-results.md
docs/plans/15-research-scanner-and-candidate-workbench.md
docs/plans/README.md
README.md
implementation_prompt.md
```

### Critical integrated workflows

The required end-to-end browser/application evidence is intentionally small and high-value:

```text
Discovery:
run canonical bounded scan
 -> operation completes
 -> inspect candidate including negative/manual lineage
 -> navigate to authoritative experiment/portfolio/pair evidence

Prospective:
freeze
 -> advance
 -> inspect partial/final outcome
 -> capture public evidence
 -> qualify explicit current as_of + capital
 -> inspect reasoned actionability state

Portfolio:
select 3-6 admitted assets + candidate edges
 -> create basket
 -> inspect backend graph/target
 -> run ordinary QAP basket experiment
 -> inspect HODL/band/pair-blind/strategy economics
 -> navigate to Portfolio/Experiment evidence
```

At least one operation failure and one negative scientific/economic result must remain visible through the browser rather than collapsing into a generic success state.

### Required repository/API/frontend gates

These are inherited from the repository's existing Phase-14/Phase-15 completion contracts because Slice 4 changes executable API/frontend behavior:

```text
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
uv run lint-imports
git diff --check

uv run python scripts/export_openapi.py /tmp/qap-openapi.json
diff -u web/openapi.json /tmp/qap-openapi.json

cd web
pnpm typecheck
pnpm typecheck:e2e
pnpm test
pnpm build
```

Run the repository Playwright wrapper for the existing Phase-14 critical flows plus the few new Slice-4 critical workflows implemented above:

```text
uv run python scripts/run_playwright_e2e.py
```

Use the existing rendered-browser/accessibility acceptance process for new primary routes at desktop and mobile widths. Do not add screenshot-snapshot or CSS-trivia tests merely to increase coverage.

### Exit criteria

Slice 4 is complete only when:

- Slices 1–3 can be initiated/inspected through one local web application without using the CLI for the supported workflows;
- FastAPI exposes a finite typed mutation surface rather than a generic execution API;
- long-running work uses the minimal durable local operation lifecycle and does not require a distributed queue/database;
- operation state remains operational metadata rather than scientific truth;
- browser inputs are domain intent, not hidden research/financial constants;
- immutable scanner/QAP artifacts remain authoritative and negative evidence is preserved;
- Discovery, Prospective, Basket, Operations, existing Experiment, Portfolio, Pair, and Paper Operation views form one coherent navigation model;
- no browser-side resolver/accounting/cost/capacity/wealth reconstruction exists;
- no final-OOS search, live trading, private API, scheduler, or deployment authority is introduced;
- OpenAPI/client/frontend and repository completion gates are green.

---

## 12. Explicit deferrals after Slice 4

Do not treat these as prerequisites for a finished human-operated research product:

- authentication/multi-user accounts while the application remains local single-operator;
- Redis/Celery/Kafka/database-backed job infrastructure;
- distributed or cloud execution;
- automatic scan/capture/basket scheduling;
- private exchange credentials/order placement;
- live-capital deployment controls;
- basket-level joint capacity / basket `tradable_now`;
- automatic basket optimizer/discovery;
- cross-venue inventory/transfer modeling;
- configurable strategy/model/plugin builders;
- generalized dashboard builder;
- cancellation/resume semantics for arbitrary operations;
- new graph/chart libraries solely for the bounded Scanner-V1 basket graph.

Each requires a concrete product need and separate design authority.
