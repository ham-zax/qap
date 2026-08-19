# QAP

QAP is a deterministic, spot-only crypto inventory-rebalancing research system built around explicit owned inventory, causal evidence, realistic costs, and matched passive counterfactuals.

The primary product objective is **portfolio wealth growth relative to the correct matched passive HODL/control after costs**. Coin-unit accumulation is a secondary attribution lens, not permission to destroy wealth. A numeraire is used to value heterogeneous holdings consistently; it is a measurement coordinate, not a directional market-prediction objective.

## Current repository state

QAP is an implemented local research product, not a documentation-only scaffold. The repository currently contains:

- a Python 3.14 experiment/replay engine with exact Decimal portfolio accounting, policy/control execution, HODL and matched-contribution comparisons, immutable run artifacts, integrity seals, and final-OOS commitment discipline;
- relationship evidence and simple-first predictive research components with explicit causal/provenance contracts;
- deterministic forward-paper execution over recorded public venue inputs, including precision/notional rules, routed fills, independent reconciliation, and self-auditing paper-operation artifacts;
- a loopback-only FastAPI command/query application boundary with a finite seven-command research mutation surface, durable single-active operation records, and validated immutable evidence reads;
- a React/Vite unified research workbench for Discovery, Prospective evidence, manual baskets, Operations, research runs, portfolio economics, pair evidence, and paper operations;
- a sequential local development harness under `tools/agent/` with recoverable state and bounded verification.

**Phase 12 remains `NO-GO` for live operation.** QAP has no private exchange credentials, authenticated trading API, browser order controls, live scheduler, or live-capital authority. The recorded decision is in [`docs/reviews/2026-08-17-live-readiness.md`](docs/reviews/2026-08-17-live-readiness.md).

Phase 14's analytical-workbench implementation has passed its rendered browser acceptance contract; see [`docs/reviews/2026-08-18-phase14-browser-acceptance.md`](docs/reviews/2026-08-18-phase14-browser-acceptance.md). Phase 15 Scanner V1 Slices 1–3 are complete and repository-verified; Slice-3 results are recorded in [`docs/research/2026-08-18-qap-scanner-slice3-results.md`](docs/research/2026-08-18-qap-scanner-slice3-results.md). Slice 1 establishes historical pair research economics only under QAP's declared deterministic replay/cost model; Slice 2 owns genuinely forward candidate evidence and current public capacity qualification; Slice 3 adds O(N) asset-native momentum and manual 3–6 asset one-inventory basket research through one policy target, the existing Phase-11 multi-asset executor, and ordinary QAP economics. Slice 4 is complete: the local unified workbench can initiate and inspect the admitted Slice-1/2/3 workflows through a finite command/query API while immutable scanner/QAP artifacts remain authoritative. Final rendered executable state is `6961937`; the current review-closure state is `62416cc`; verified results are in [`docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`](docs/research/2026-08-19-qap-slice4-unified-workbench-results.md). **Phase 16 — Human-Centered Workbench UX Re-architecture is complete through M8.** The primary IA is `Home / Discover / Validate / Portfolios / Results / Activity`; novice-first task flows, progressive disclosure, Results/Activity separation, forward/current-evidence guidance, portfolio authority boundaries, and the shared visual state grammar now sit over the same authoritative QAP/scanner evidence. Scientific/economic authority remains backend-owned, rejected research remains first-class evidence, and the UI still carries the explicit no-live-trading-authority boundary. The deterministic browser fixture live-exercises `research_only`; `small_capacity` and `tradable_now` presentation paths are implemented but are recorded as not yet live-exercised by that fixture.

**Phase 17 — Product Layer is now design-frozen at M0; implementation has not started.** The frozen design adds the missing clean-workspace operational layer: explicit operator-approved assets, current Binance/Gate Spot directory state, public historical market-data preparation/refresh, immutable dataset generations and provenance, a separately-versioned current-approved retrospective research claim, backend-owned research readiness/safe cutoffs, longitudinal Research Ideas, and persistent current public-evidence collection. The future primary IA is `Home / Research / Portfolios / History`; the current Phase-16 shell remains executable until those milestones land. CCXT is deliberately deferred for Product V1 because the existing Binance/Gate adapters are sufficient unless a concrete later exchange-boundary need earns it. QAP's scientific/economic authority and Phase-12 live-capital `NO-GO` remain unchanged. See [`docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`](docs/superpowers/specs/2026-08-19-qap-product-layer-design.md) and [`docs/plans/17-product-layer-market-data-and-research-lifecycle.md`](docs/plans/17-product-layer-market-data-and-research-lifecycle.md).

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

Then open `http://localhost:5173`. The launcher uses the repository `runs/` directory by default; set `QAP_RUN_ROOT=/path/to/runs` before invoking it if you want a different evidence root. Press `Ctrl+C` to stop both processes.

This launcher is the current pre-Phase-17 local workflow. Phase 17 M1 will make Sample versus Local Market workspace identity explicit and will stop treating port occupancy alone as proof that the intended workspace is already running.

For separate-process/manual startup, start the local single-operator API from the repository root. Mutation-capable serving is intentionally loopback-only and uses exactly one Uvicorn worker:

```bash
QAP_API_RUN_ROOT="$QAP_RUN_ROOT" \
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
- [`docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md`](docs/superpowers/plans/2026-08-19-qap-slice4-unified-workbench-implementation-plan.md) — completed implementation plan for the unified local application over Slices 1–3.
- [`docs/research/2026-08-19-qap-slice4-unified-workbench-results.md`](docs/research/2026-08-19-qap-slice4-unified-workbench-results.md) — verified Slice-4 command/query, browser workflow, repository-gate, and rendered-acceptance results.
- [`docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md`](docs/research/2026-08-19-qap-human-centered-workbench-ux-investigation.md) — current-route/task analysis, user journeys/flows, cognitive walkthrough, heuristic findings, terminology architecture, and IA hypothesis for non-expert users.
- [`docs/research/2026-08-19-qap-phase16-implementation-handoff.md`](docs/research/2026-08-19-qap-phase16-implementation-handoff.md) — Phase-16 implementation history, frozen contracts, boundary guidance, milestone commits, and closed handoff state.
- [`docs/plans/16-human-centered-workbench-ux-rearchitecture.md`](docs/plans/16-human-centered-workbench-ux-rearchitecture.md) — completed post-Slice-4 presentation/IA implementation plan and M8 human-centered closure evidence.
- [`docs/research/2026-08-19-qap-product-layer-investigation.md`](docs/research/2026-08-19-qap-product-layer-investigation.md) — repository/public-source evidence for the Phase-17 Product Layer: clean-workspace gaps, data/lifecycle ownership, CCXT boundary, current-evidence collection, and measured scanner scale.
- [`docs/superpowers/specs/2026-08-19-qap-product-layer-design.md`](docs/superpowers/specs/2026-08-19-qap-product-layer-design.md) — frozen Phase-17 Product Layer design: explicit asset admission, market-data generations/provenance, current-approved versus historical-PIT research claims, longitudinal Research Ideas, current-evidence collection, and protected authority boundaries.
- [`docs/plans/17-product-layer-market-data-and-research-lifecycle.md`](docs/plans/17-product-layer-market-data-and-research-lifecycle.md) — executable Phase-17 milestone plan; M0 design freeze is complete and M1 workspace identity/zero-state is next.
- [`tools/agent/README.md`](tools/agent/README.md) — sequential local development harness.
- [`docs/OSS_REUSE_BOUNDARY.md`](docs/OSS_REUSE_BOUNDARY.md) — open-source reuse boundary.
