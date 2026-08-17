# QAP analytical workbench

This package is the read-only React evidence workbench for QAP experiment artifacts. It does not run strategies, mutate portfolios, recompute financial results, or authorize live capital. Exact economics and research-state classifications come from the Python artifact/API layer.

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

Start the read-only API:

```bash
QAP_API_RUN_ROOT=/tmp/qap-ui-runs \
QAP_API_MARKET_DATA_ROOT="$PWD" \
uv run uvicorn qap.api.app:create_default_app \
  --factory --host 127.0.0.1 --port 8000
```

In a second shell, generate the API types and start Vite:

```bash
uv run python scripts/export_openapi.py web/openapi.json
cd web
pnpm install --frozen-lockfile
pnpm generate:api
pnpm dev --host 127.0.0.1 --port 5173
```

Vite proxies `/api` to `http://127.0.0.1:8000`. Set `VITE_QAP_API_BASE_URL` only when the API is served elsewhere.

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
