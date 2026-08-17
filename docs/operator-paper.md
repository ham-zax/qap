# QAP Paper Operator Workflow

QAP paper operation is command-driven and read-only from the browser. The browser never launches experiments or paper rebalances, and no private/live exchange API is part of this workflow.

## 1. Run a frozen experiment manifest

From the repository root:

```bash
uv run python -m qap.experiment.cli \
  path/to/manifest.json \
  --data-root . \
  --repository-root . \
  --run-root runs
```

The command writes one immutable run under `runs/<run_id>/`. A `final_oos` manifest is reserved/consumed through the artifact runner before result computation; do not bypass the command/artifact boundary for final OOS.

Inspect the emitted JSON for `run_id`, result `status`, the predeclared primary metric, and the run directory. Keep negative, neutral, failed, and invalid attempts in the family denominator.

## 2. Run a deterministic operational paper-rebalance dry run

The current paper-operation command consumes recorded public market metadata/reference prices and writes one immutable paper artifact:

```bash
uv run python scripts/run_paper_operation.py \
  tests/fixtures/paper/four_asset_forward_paper.json \
  --repository-root . \
  --output-root runs/paper-operations
```

A successful operation is written under:

```text
runs/paper-operations/<operation_id>/paper_operation.json
```

The command refuses to overwrite an existing operation ID. The artifact preserves normalized venue precision, real route legs, fills/no-fill reasons, exact ending holdings, target-weight tracking error, independent fee/turnover/slippage reconciliation, and terminal revaluation.

### Evidence boundary

The current paper-operation command is an **operational dry-run workflow only**. Its artifacts are derived as:

```text
evidence_class = operational_dry_run
prospective_candidate_evidence = false
```

A paper-operation input is not allowed to self-declare `prospective_candidate_evidence`, `evidence_class`, or candidate-freeze lineage. Those fields require a future verified lineage workflow that proves the candidate rule/manifest, cost model, decision semantics, and prospective observation period were frozen before the observed period began.

As of the Phase-10 daily momentum family result in `docs/research/2026-08-17-phase10-momentum-family-results.md`, the predeclared 2023 development family produced **zero surviving candidates**. Therefore the reserved 2024 final-OOS dataset remains unconsumed and there is currently no candidate eligible to start a prospective `forward_paper` evidence period. Do not relabel the recorded dry-run fixtures as prospective evidence to satisfy a readiness checklist.

If a future independently motivated research generation produces a frozen survivor, add/verify the candidate-lineage workflow **before** the prospective observation period starts. Forward-paper observations may identify defects, but once they are used to retune the candidate they become development evidence and a new prospective period is required.

## 3. Inspect immutable evidence through the local API and workbench

Launch the read-only API from the repository root:

```bash
QAP_API_RUN_ROOT=runs \
QAP_API_MARKET_DATA_ROOT=. \
uv run uvicorn qap.api.app:create_default_app \
  --factory \
  --host 127.0.0.1 \
  --port 8000
```

In a second shell:

```bash
cd web
VITE_QAP_API_BASE_URL=http://127.0.0.1:8000 \
  pnpm dev -- --host 127.0.0.1
```

Use the workbench only to inspect persisted evidence:

1. open the experiment result;
2. inspect Portfolio economics, including HODL-relative wealth and the predeclared primary control;
3. inspect Pair Workbench orientation/anchor evidence where available;
4. inspect Paper operations for reconciliation, per-leg costs, precision/no-fill reasons, bridge residual, and terminal target tracking;
5. record the research conclusion and whether any final-OOS holdout was consumed.

There is intentionally no browser-side experiment/paper execution endpoint.

## 4. Run the two critical browser acceptance flows

The deterministic E2E runner starts an isolated fixture API and Vite instance, runs exactly the two critical browser flows, and tears both servers down:

```bash
cd web
pnpm e2e
```

The flows verify:

- known run -> Portfolio economics -> HODL-relative metric + relative-wealth chart -> Pair Workbench;
- Pair Workbench -> reciprocal orientation -> anchor selection -> URL-owned state + synchronized anchor-lens labels.

The fixture E2E path uses local recorded data and does not depend on the public network.

## Stop conditions

Stop rather than improvising if any of these occur:

- required venue metadata/reference price is missing;
- a route or precision constraint is unsupported;
- reconciliation fails;
- an operation ID already exists;
- a prospective-evidence claim lacks a candidate freeze that predates the observation period;
- a forward-paper observation has already been used to retune the candidate;
- the requested action would require private exchange credentials, live order submission, asynchronous job infrastructure, or automatic model promotion.
