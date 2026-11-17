# QAP

Update context — 2026-11-16
Trigger: Audit repair AR-7 ([Plan 25](docs/plans/25-audit-repairs-and-evidence-integrity.md)).
Purpose: Align README with the current Pair Rotation Lab entry points, mark older Phases 14–19 descriptions as historical, and document local-only authority/actor boundaries.
Impact: Documentation alignment only; economic, Shariah, holdout, and `NO-GO` live-capital boundaries remain unchanged.
Evidence: [TASKS.md](TASKS.md), [Phase 21](docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md), [Phase 24 checkpoint](docs/aegis/work/2026-11-16-phase24-terminal/20-checkpoint.md), and [Plan 25](docs/plans/25-audit-repairs-and-evidence-integrity.md).

QAP is a deterministic, long-only, spot-only crypto inventory-rebalancing research system built around explicit owned inventory (`PortfolioState`), causal evidence, realistic spot costs, and matched passive HODL/rebalancing controls.

The primary product objective is **portfolio wealth growth relative to matched passive HODL and a predeclared rebalancing control after costs**. No live-capital order placement is authorized; **Phase 12 remains `NO-GO` for live operation** ([live-readiness decision](docs/reviews/2026-08-17-live-readiness.md)).

## Current Lab entry points & security boundary

QAP currently operates as **local research software** exposing one shared Python backend core through two equal interfaces:

- **Web UI (`/lab` and `/operations`):** FastAPI loopback API + React/Vite terminal (`TimeSeriesChart` + Watermelon UI). Supports coin discovery, descriptive ratio/dependence analysis, Smart Strategy Advisor presets, chronological walk-forward validation, side-by-side preset comparison, immutable saved runs, and forward L2 paper simulation.
- **Agent CLI (`qap.lab_cli`):** Token-efficient JSON/Markdown CLI sharing the same study, advisor, comparison, and L2 paper session stores (`uv run python -m qap.lab_cli --help`).
- **Actor isolation is not hosted authentication:** `X-QAP-Actor-Id` (`--actor-id`) partitions saved study and paper directories per local caller ID (`local` by default, or `actors/<id>`) to keep concurrent agent/user trials separated on a single local machine. It provides no authentication, authorization, TLS, or multi-tenant security for network/hosted exposure.

## Historical milestones (archived context)

Phases 12–19 (analytical workbench, Scanner V1 Slices 1–3, unified workbench, Pair Study workflow, and pre-Phase-21 Lab MVP) are superseded in the active UI by the Pair Rotation Lab terminal and archived at Git tag `archive/pre-phase21-workbench`. Current task status, Plan 25 audit repairs, and open research-policy items live in [TASKS.md](TASKS.md).

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

For normal local use, start the API and web app together from the repository root:

```bash
./scripts/start_workbench.sh
```

Then open `http://localhost:5173` after the launcher prints `QAP workbench ready.`. The launcher starts a `local_market` workspace by default and uses the resolved run root as its local workspace identity. Local Market starts the API, web app, and one workspace current-evidence collector; an intentional Sample Workspace (`QAP_API_WORKSPACE_MODE=sample`) starts only the API and web app. Set `QAP_RUN_ROOT=/path/to/runs` before invoking the launcher to select a different workspace root. Press `Ctrl+C` to stop the launcher-owned API/web/collector processes. Already-started scientific operation workers have their own durable lifecycle and are not implicitly cancelled by closing the interactive workbench.

Before starting anything, the launcher verifies the backend workspace mode and root. On a new start it also waits for API health, exact workspace identity, the QAP web app, and—only in Local Market—a running collector lease before declaring the workbench ready. It reports an already-running intended workspace separately from another/sample QAP workspace, an unrelated port occupant, a partial API/web startup, or an unhealthy initial collector instead of treating port occupancy or process creation alone as proof that the intended workspace is ready.

For separate-process/manual startup, start the local single-operator API from the repository root. Mutation-capable serving is intentionally loopback-only and uses exactly one Uvicorn worker:

```bash
QAP_API_RUN_ROOT="$QAP_RUN_ROOT" \
QAP_API_WORKSPACE_MODE=local_market \
QAP_API_MARKET_DATA_ROOT="$PWD" \
QAP_API_REPOSITORY_ROOT="$PWD" \
QAP_API_CAPTURE_ROOT="$QAP_RUN_ROOT/public-capture" \
uv run uvicorn qap.api.app:create_default_app \
  --factory --host 127.0.0.1 --port 8000 --workers 1
```

Then start the frontend in another terminal:

```bash
cd web
pnpm dev --host 127.0.0.1 --port 5173
```

The Vite development server proxies `/api` to `http://127.0.0.1:8000`.

## Verification

Full compiler gate (serializes heavy checks across worktrees via `/tmp/qap-gate-heavy.lock`):

```bash
uv run python scripts/qap_gate.py --full
```

Individual repository checks:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run lint-imports
uv run python scripts/check_source_size.py
uv lock --check
```

Frontend checks:

```bash
pnpm --dir web typecheck
pnpm --dir web test
pnpm --dir web build
```

To verify that the checked-in API contract is current:

```bash
uv run python scripts/export_openapi.py /tmp/qap-openapi.json
diff -u web/openapi.json /tmp/qap-openapi.json
```

## Project map

- [`TASKS.md`](TASKS.md) — active task tracker (Phase 21–24 evidence, Plan 25 audit repairs, RD-1, and wider audit queue).
- [`docs/plans/README.md`](docs/plans/README.md) — phase map and current sequencing.
- [`docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md`](docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md) — active Pair Rotation Lab & L2 paper specification.
- [`docs/plans/24-binance-terminal-ui-redesign.md`](docs/plans/24-binance-terminal-ui-redesign.md) — Phase 24 terminal UI design.
- [`docs/plans/25-audit-repairs-and-evidence-integrity.md`](docs/plans/25-audit-repairs-and-evidence-integrity.md) — Plan 25 audit repair sequence & open research-policy decisions (`RD-1`).
- [`docs/reviews/2026-11-16-audit-repair-completion.md`](docs/reviews/2026-11-16-audit-repair-completion.md) — Plan 25 baseline, probe reconciliation, and verification record.
- [`docs/reviews/2026-08-17-live-readiness.md`](docs/reviews/2026-08-17-live-readiness.md) — Phase-12 `NO-GO` live-readiness decision.
- [`docs/OSS_REUSE_BOUNDARY.md`](docs/OSS_REUSE_BOUNDARY.md) — open-source reuse boundary.
- [`docs/REFERENCE_BOUNDARY.md`](docs/REFERENCE_BOUNDARY.md) — read-only reference corpus boundary.
