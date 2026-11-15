# QAP analytical workbench

This package contains the Pair Rotation Lab and the existing evidence workbench.
The local workspace opens `/lab`. Coin selection starts data preparation through
the existing background operation. The backend computes descriptive measurements
from exact immutable datasets. Portfolio economics remain authoritative in Python.
The Lab currently says **Strategy not tested**. The study API exists, but the
dashboard does not yet display its wealth, proof or saved results.

Update context — 2026-10-24
Trigger: connect the backend study API before the dashboard continuation.
Purpose: document the local entry point and the API/UI boundary.
Impact: automatic research-data preparation, with no trading authority.
Evidence: [Phase 19 checkpoint](../docs/plans/19-pair-rotation-lab-mvp.md).

## Pair Rotation Lab

Start the API from the repository root, with an existing or new local workspace:

```bash
QAP_API_RUN_ROOT="$PWD/runs" \
QAP_API_WORKSPACE_MODE=local_market \
QAP_API_MARKET_DATA_ROOT="$PWD" \
QAP_API_REPOSITORY_ROOT="$PWD" \
uv run uvicorn qap.api.app:create_default_app \
  --factory --host 127.0.0.1 --port 8000 --workers 1
```

Start Vite with the command below. Open `/lab` on port 5173. Search accepts trading
Binance spot listings. Preparation retains at least a year; display windows range
from 30 to 365 days. Data preparation uses cached identity evidence. The explicit
directory refresh operation owns registry acquisition. Unresolved identities remain
viewable, with economic calls blocked. Saved browser settings are drafts, not frozen
research results. Sample data is never an automatic fallback.

The backend exposes `POST /api/pair-rotation/studies` for explicit computation.
`GET /api/pair-rotation/studies` lists saved results. `GET /studies/{study_id}`
and `POST /studies/{study_id}/pin` use the same `/api/pair-rotation` prefix.
Reopening a result preserves its original data and settings. Pinning changes only
separate metadata. Restart the API after backend edits. The launcher does not reload.

## Local development

From the repository root, create or identify a run root containing immutable experiment artifacts. For a deterministic development run:

```bash
uv run python -m qap.experiment.cli \
  tests/fixtures/experiments/two_asset_dummy.json \
  --data-root "$PWD" \
  --repository-root "$PWD" \
  --run-root /tmp/qap-ui-runs \
  --run-timestamp 2026-08-17T10:00:00Z
```

Start the local single-operator API. The mutation-capable launcher is loopback-only and explicitly single-worker:

```bash
QAP_API_RUN_ROOT=/tmp/qap-ui-runs \
QAP_API_WORKSPACE_MODE=sample \
QAP_API_MARKET_DATA_ROOT="$PWD" \
QAP_API_REPOSITORY_ROOT="$PWD" \
QAP_API_CAPTURE_ROOT=/tmp/qap-ui-runs/public-capture \
uv run uvicorn qap.api.app:create_default_app \
  --factory --host 127.0.0.1 --port 8000 --workers 1
```

In a second shell, generate the API types and start Vite:

```bash
uv run python scripts/export_openapi.py web/openapi.json
cd web
pnpm install --frozen-lockfile
pnpm generate:api
pnpm dev --host 127.0.0.1 --port 5173
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Set `VITE_QAP_API_BASE_URL` only when the API is served elsewhere. The shell reads `/api/workspace` from the backend: sample mode carries a persistent `Sample Workspace` marker, while a `local_market` workspace with no prepared scanner catalog shows the clean setup zero-state rather than presenting sample data as local market state.

## Contract generation

The checked-in schema and an explicitly exported schema use the same deterministic generator:

```bash
pnpm generate:api
pnpm generate:api -- /tmp/qap-openapi.json
```

Both commands replace `src/api/schema.d.ts`; callers should regenerate after any API DTO or route change.

## Verification

```bash
pnpm typecheck
pnpm test
pnpm build
```

Rendered verification should also exercise desktop and mobile experiment, portfolio, pair, reciprocal-orientation, anchor, typed-error, keyboard, overflow, console, and WCAG paths with `agent-browser`.

## Evidence boundaries

- HODL-relative wealth is primary; coin accumulation is secondary.
- External-flow claims require matched-contribution static HODL.
- Relationship-alpha claims require incremental value over the predeclared stronger admissible control.
- Final-OOS consumption and research-family context remain visible.
- Common-reference identity coordinates are labeled synthetic unit paths, not market observations.
- Charts use presentation-number copies only; exact decimal strings remain authoritative in API payloads, tables, and metric cards.
