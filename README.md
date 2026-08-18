# QAP

QAP is a deterministic, spot-only crypto inventory-rebalancing research system built around explicit owned inventory, causal evidence, realistic costs, and matched passive counterfactuals.

The primary product objective is **portfolio wealth growth relative to the correct matched passive HODL/control after costs**. Coin-unit accumulation is a secondary attribution lens, not permission to destroy wealth. A numeraire is used to value heterogeneous holdings consistently; it is a measurement coordinate, not a directional market-prediction objective.

## Current repository state

QAP is an implemented local research product, not a documentation-only scaffold. The repository currently contains:

- a Python 3.14 experiment/replay engine with exact Decimal portfolio accounting, policy/control execution, HODL and matched-contribution comparisons, immutable run artifacts, integrity seals, and final-OOS commitment discipline;
- relationship evidence and simple-first predictive research components with explicit causal/provenance contracts;
- deterministic forward-paper execution over recorded public venue inputs, including precision/notional rules, routed fills, independent reconciliation, and self-auditing paper-operation artifacts;
- a read-only FastAPI evidence API;
- a React/Vite analytical workbench for research runs, experiment verdicts, portfolio economics, pair evidence, and paper operations;
- a sequential local development harness under `tools/agent/` with recoverable state and bounded verification.

**Phase 12 remains `NO-GO` for live operation.** QAP has no private exchange credentials, authenticated trading API, browser order controls, live scheduler, or live-capital authority. The recorded decision is in [`docs/reviews/2026-08-17-live-readiness.md`](docs/reviews/2026-08-17-live-readiness.md).

Phase 14's analytical-workbench implementation has passed its rendered browser acceptance contract; see [`docs/reviews/2026-08-18-phase14-browser-acceptance.md`](docs/reviews/2026-08-18-phase14-browser-acceptance.md). Phase 15 Scanner V1 Slices 1–3 are complete and repository-verified; Slice-3 results are recorded in [`docs/research/2026-08-18-qap-scanner-slice3-results.md`](docs/research/2026-08-18-qap-scanner-slice3-results.md). Slice 1 establishes historical pair research economics only under QAP's declared deterministic replay/cost model; Slice 2 owns genuinely forward candidate evidence and current public capacity qualification; Slice 3 adds O(N) asset-native momentum and manual 3–6 asset one-inventory basket research through one policy target, the existing Phase-11 multi-asset executor, and ordinary QAP economics. The frozen Slice-4 unified-workbench plan is the next product layer and has not been implemented.

## Requirements and setup

- Python `>=3.14,<3.15`
- [`uv`](https://docs.astral.sh/uv/)
- Node.js plus `pnpm 11.21.0`

Install the locked dependencies:

```bash
uv sync --frozen
cd web
pnpm install --frozen-lockfile
cd ..
```

## Run a deterministic local experiment

Use an empty run root because run directories are immutable and deterministic run IDs are never overwritten:

```bash
export QAP_RUN_ROOT=/tmp/qap-demo-runs
mkdir -p "$QAP_RUN_ROOT"

uv run python -m qap.experiment.cli \
  tests/fixtures/experiments/two_asset_dummy.json \
  --data-root "$PWD" \
  --repository-root "$PWD" \
  --run-root "$QAP_RUN_ROOT" \
  --run-timestamp 2026-08-17T10:00:00Z
```

To create the recorded forward-paper demo in the same evidence root:

```bash
uv run python scripts/run_paper_operation.py \
  tests/fixtures/paper/four_asset_forward_paper.json \
  --repository-root "$PWD" \
  --output-root "$QAP_RUN_ROOT/paper-operations"
```

## Start the local evidence workbench

Start the read-only API from the repository root:

```bash
QAP_API_RUN_ROOT="$QAP_RUN_ROOT" \
QAP_API_MARKET_DATA_ROOT="$PWD" \
uv run uvicorn qap.api.app:create_default_app \
  --factory --host 127.0.0.1 --port 8000
```

Then start the frontend in another terminal:

```bash
cd web
pnpm dev --host 127.0.0.1 --port 5173
```

The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

## Verification

Backend and repository checks:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts tools
uv run lint-imports
uv run python scripts/check_source_size.py
uv lock --check
```

Frontend and browser checks:

```bash
cd web
pnpm typecheck
pnpm typecheck:e2e
pnpm test
pnpm build
cd ..
uv run python scripts/run_playwright_e2e.py
```

To verify that the checked-in API contract is current:

```bash
uv run python scripts/export_openapi.py /tmp/qap-openapi.json
diff -u web/openapi.json /tmp/qap-openapi.json
```

## Project map

- [`implementation_prompt.md`](implementation_prompt.md) — governing mission/economic/action-space constraints.
- [`docs/plans/README.md`](docs/plans/README.md) — phase map and current sequencing.
- [`docs/superpowers/specs/2026-08-17-qap-system-design.md`](docs/superpowers/specs/2026-08-17-qap-system-design.md) — economic/domain/system design.
- [`docs/superpowers/specs/2026-08-17-qap-web-operations-design.md`](docs/superpowers/specs/2026-08-17-qap-web-operations-design.md) — API/web/operations boundaries.
- [`docs/reviews/2026-08-17-live-readiness.md`](docs/reviews/2026-08-17-live-readiness.md) — current Phase-12 `NO-GO` decision.
- [`docs/plans/14-analytical-workbench-ux-redesign.md`](docs/plans/14-analytical-workbench-ux-redesign.md) — analytical-workbench acceptance contract.
- [`docs/plans/15-research-scanner-and-candidate-workbench.md`](docs/plans/15-research-scanner-and-candidate-workbench.md) — completed Scanner V1 / Phase-15 research-kernel umbrella plan for Slices 1–3.
- [`docs/superpowers/specs/2026-08-18-qap-scanner-slice3-asset-momentum-basket-design.md`](docs/superpowers/specs/2026-08-18-qap-scanner-slice3-asset-momentum-basket-design.md) — exact Slice-3 momentum, manual-basket, graph-resolver, multi-asset replay, research, and workbench contracts.
- [`docs/superpowers/plans/2026-08-18-qap-scanner-slice3-implementation-plan.md`](docs/superpowers/plans/2026-08-18-qap-scanner-slice3-implementation-plan.md) — completed Slice-3 backend implementation sequence and closure contract.
- [`docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md`](docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md) — frozen next-stage plan for one human-operated application over Slices 1–3; not yet implemented.
- [`tools/agent/README.md`](tools/agent/README.md) — sequential local development harness.
- [`docs/OSS_REUSE_BOUNDARY.md`](docs/OSS_REUSE_BOUNDARY.md) — open-source reuse boundary.
