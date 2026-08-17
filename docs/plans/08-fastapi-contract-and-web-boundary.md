# Phase 08 — FastAPI Contract and Web Boundary Implementation Plan

**Goal:** Expose authoritative QAP run, portfolio, pair, and experiment data through a thin typed local HTTP/OpenAPI boundary without moving business logic into the API layer.

**Architecture:** `qap.api` is a presentation adapter over run artifacts and existing domain/query functions. FastAPI/Pydantic own HTTP parsing/serialization only. The first API is intentionally read-oriented; experiment execution remains the Phase-07 command path until a real web-run workflow is justified.

**Tech Stack:** Python 3.14, FastAPI, Pydantic, Uvicorn, HTTPX/TestClient, OpenAPI.

## Global Constraints

- API never owns wallet/accounting/model truth.
- No duplicated HODL/ratio/calculation logic in route handlers.
- Local/single-operator boundary; bind to loopback by default.
- No auth system, database, background job queue, websocket, or live exchange credential.
- Business policy is not read from environment variables.
- API errors are typed and explicit; no silent fallbacks.
- API exposes persisted experiment/run artifacts, not an arbitrary raw-market explorer; this prevents the web layer from bypassing final-holdout discipline.

## File Map

**Modify:**
- `pyproject.toml` — add FastAPI, Uvicorn, HTTPX test dependency.

**Create:**
- `src/qap/api/__init__.py`
- `src/qap/api/app.py` — app factory and local middleware setup.
- `src/qap/api/settings.py` — operational-only roots/origins/bind settings.
- `src/qap/api/errors.py` — stable error envelope and handlers.
- `src/qap/api/schemas.py` — HTTP DTOs only.
- `src/qap/api/readers.py` — run/artifact read adapter.
- `src/qap/api/routes/health.py`
- `src/qap/api/routes/portfolios.py`
- `src/qap/api/routes/pairs.py`
- `src/qap/api/routes/experiments.py`
- `scripts/export_openapi.py` — deterministic OpenAPI JSON export for web type generation.
- `tests/contract/api/test_health.py`
- `tests/contract/api/test_portfolios.py`
- `tests/contract/api/test_pairs.py`
- `tests/contract/api/test_experiments.py`
- `tests/contract/api/test_errors.py`
- `tests/contract/api/test_openapi.py`

## Section 08.1 — Operational Settings and App Factory

**Interfaces:**
- Consumes: explicit run/data roots, allowed local origins.
- Produces: FastAPI application.

**Behavior:**
- `ApiSettings` contains operational values only: run root, optional market-data root, allowed origins, host/port.
- Default host is `127.0.0.1`.
- Environment may override operational paths/ports for launch convenience; no model, fee, basket, policy, or benchmark setting appears here.
- CORS allows only configured local development origin(s).

**Steps:**
- [ ] Add settings tests distinguishing operational settings from business configuration.
- [ ] Implement `create_app(settings)` rather than module-level hidden configuration.

## Section 08.2 — Stable Error Envelope

**Interfaces:**
- Produces: JSON error shape used by every endpoint.

**Shape:**

```json
{
  "error": {
    "code": "run_not_found",
    "message": "...",
    "context": {"run_id": "..."}
  }
}
```

**Behavior:**
- Known QAP/domain validation failures map to stable codes and appropriate 4xx status.
- Unexpected server failures return generic 500 message without leaking secrets/path internals in normal response.
- Missing run/data, invalid pair orientation, unavailable anchor series, and corrupt artifact each have distinct codes.

**Steps:**
- [ ] Write handler contract tests first.
- [ ] Implement minimal exception mapping local to API boundary.

## Section 08.3 — HTTP Schemas

**Interfaces:**
- Consumes: domain/evaluation/experiment result objects.
- Produces: JSON-safe DTOs.

**DTO families:**
- `RunSummaryDto`
- `PortfolioSnapshotDto`
- `PortfolioPerformanceDto`
- `PairSeriesDto`
- `AnchorLensDto`
- `ExperimentDetailDto`
- `RebalanceDecisionAuditDto`
- shared timestamp/value point DTOs.

**Behavior:**
- Decimal values serialize as strings when exact financial precision matters; chart-only float series serialize as JSON numbers.
- UTC timestamps serialize in RFC3339 `Z` form.
- Run/experiment DTOs include research family/parent, universe mode, data role, final-OOS consumption state, primary incremental benchmark, and sibling-trial count where available.
- Pair/model DTO metadata exposes `orientation_behavior` when fitted evidence exists.
- DTO conversion functions live beside schemas/readers, not in domain objects.
- No API schema is imported into core financial packages.

## Section 08.4 — Experiment Artifact Read API

**Endpoints:**

```text
GET /api/health
GET /api/experiments
GET /api/experiments/{run_id}
```

**Behavior:**
- List scans/reads Phase-07 run artifacts under configured root; no database index.
- Summary returns run ID, experiment name, research family/parent, universe mode, data-role/final-OOS-consumed state, status, primary metric, incremental-vs-primary-control metric, created timestamp, dirty-code flag.
- Detail returns manifest summary, sibling-trial count, declared benchmark ladder/primary control, final-OOS commitment/consumption state, provenance, economic result, and available series metadata.
- Corrupt artifacts are surfaced, not silently skipped: the list includes an explicit item with `artifact_status=invalid` and error context, so one corrupt old run does not hide all valid runs.

**Steps:**
- [ ] Create temporary run-root fixtures in contract tests.
- [ ] Implement artifact reader using Phase-07 parser/schema versioning.

## Section 08.5 — Portfolio API

**Endpoints:**

```text
GET /api/portfolios/{run_id}
GET /api/portfolios/{run_id}/performance
```

**Behavior:**
- Portfolio endpoint returns starting and terminal holdings, benchmark holdings, allocation snapshots available in run trace, and cost/concentration summaries.
- Performance returns time-aligned QAP vs HODL vs all declared simple-control values, QAP/HODL relative-wealth path, QAP/primary-control incremental path/metric, and relative drawdown where present.
- The run trace can produce `RebalanceDecisionAuditDto` records containing current weights, baseline target, strategy target, evidence IDs, modeled costs, fills, and post-fill holdings.
- Backend computes/loads authoritative series; frontend does not recalculate benchmark wealth.

**Steps:**
- [ ] Add contract fixtures with exact Decimals and chart series.
- [ ] Verify no route imports execution internals merely to recompute history.

## Section 08.6 — Pair and Anchor Lens API

**Endpoints:**

```text
GET /api/pairs/{asset_x}/{asset_y}/series?run_id=...&orientation=X/Y
GET /api/pairs/{asset_x}/{asset_y}/anchor?run_id=...&anchor=BTC
```

**Behavior:**
- Pair series response includes canonical pair, requested orientation, ratio/log ratio, normalized path values or references, source fingerprints, and rebalance markers from the run trace. Model-evidence responses, when present, also state the model's reciprocal `orientation_behavior`.
- Anchor endpoint returns synchronized X/Y, X/A, Y/A series when source data exists.
- Inverse orientation is explicit in response metadata.
- Missing required source series returns explicit error; API never substitutes another quote/anchor.

**Steps:**
- [ ] Contract-test orientation reversal and missing anchor data.
- [ ] Reuse Phase-04 relationship functions/read artifacts; no route-level ratio math.

## Section 08.7 — OpenAPI Export Contract

**Interfaces:**
- Produces: deterministic OpenAPI JSON used by Phase 09.

**Steps:**
- [ ] Implement `scripts/export_openapi.py` importing `create_app` with deterministic test settings and writing JSON to a caller-supplied path.
- [ ] Add contract test asserting expected endpoint operation IDs and schema names exist.
- [ ] Avoid snapshotting the entire OpenAPI document if a focused assertion catches relevant contract drift more economically.

**Verification:**

```bash
uv run python scripts/export_openapi.py /tmp/qap-openapi.json
python -m json.tool /tmp/qap-openapi.json >/dev/null
```

## Section 08.8 — Local Launch Smoke

**Steps:**
- [ ] Document/run `uv run uvicorn qap.api.app:create_default_app --factory --host 127.0.0.1 --port 8000` or the exact equivalent app factory entry selected during implementation.
- [ ] Test `/api/health` through TestClient; a manual network server is not required in automated suite.

## Phase Verification

```bash
uv run pytest -q tests/contract/api
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/export_openapi.py /tmp/qap-openapi.json
```

## Phase Exit Criteria

- [ ] API is thin and read-oriented.
- [ ] API DTOs preserve research family/universe/data-role/final-OOS/benchmark context needed by the web product.
- [ ] No endpoint exposes arbitrary uncommitted/raw holdout browsing outside persisted run-artifact semantics.
- [ ] Business calculations remain owned by existing QAP packages.
- [ ] Error semantics are typed.
- [ ] OpenAPI exports deterministically for TypeScript generation.
- [ ] Local bind/CORS defaults are conservative.
- [ ] No auth/database/job queue/websocket/live integration was introduced.

## Stop Conditions

Do not add a second backend, GraphQL, websocket streaming, async job infrastructure, public deployment, user accounts, or experiment-mutation endpoints merely for UI convenience. Add a run-trigger endpoint only when an operator workflow and long-run execution semantics are explicitly designed.
