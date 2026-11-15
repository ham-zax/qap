# QAP agent instructions

QAP is a deterministic, long-only, spot-only crypto inventory rebalancing
system whose primary objective is portfolio wealth relative to matched passive
HODL after realistic costs.

`PortfolioState` is the authoritative owner of actual owned inventory. Policy
emits targets, execution emits fills, relationship models emit evidence,
evaluation derives read-only economics, experiments record provenance, and API
or web layers render authoritative outputs. Keep one mutable state and one
authoritative owner for each domain.

The admissible action space is owned spot inventory only: no leverage, margin,
borrowing, unowned shorts, derivatives, synthetic exposure, or interest/riba
financing. No live-capital order placement is authorized before the separate
live-readiness/design gate.

Evaluate relationship intelligence on the benchmark ladder:
matched HODL → predeclared simple rebalancing control → relationship policy.
Beating HODL alone is insufficient. Fixed-basket retrospective evidence must
not be described as point-in-time universe-discovery performance. `final_oos`
is consumed information once inspected and used to adapt research.

QAP v1/v2 at `/home/hamza/repo/tradingview_ratio` are read-only reference
corpora, never runtime dependencies or default architecture templates. Do not
copy their architecture by default; use [REFERENCE_BOUNDARY.md](docs/REFERENCE_BOUNDARY.md)
for admission rules and [OSS_REUSE_BOUNDARY.md](docs/OSS_REUSE_BOUNDARY.md)
for library ownership limits.

Keep hand-written source/test files below 500 lines where possible; review
decomposition from 500–700 lines and fail above 700 unless a narrow exception
was approved. Reject mixed-responsibility God objects at any size.

Follow the approved work in [docs/plans/](docs/plans/), specifically the active
self-contained playbook [21-pair-mvp-fundamentals-and-l2-paper-plan.md](docs/plans/21-pair-mvp-fundamentals-and-l2-paper-plan.md),
literal worker cards [22-backend-and-agent-cli-tasks.md](docs/plans/22-backend-and-agent-cli-tasks.md),
and [TASKS.md](TASKS.md), alongside the historical [master
plan](docs/superpowers/plans/2026-08-17-qap-master-implementation-plan.md).
QAP exposes one shared backend core through two equal interfaces: a token-efficient
CLI (`qap.lab_cli`) for AI agents and a typed FastAPI/OpenAPI surface for the
`/lab` Web UI (serving simple and advanced human users).
Pre-Phase-21 legacy workbench code is archived at Git tag
`archive/pre-phase21-workbench`.
Before materially revising a long-lived plan, design, research, or decision
document, follow [document-update-method.md](docs/research/document-update-method.md).
Escalate before changing economic objectives, benchmark definitions,
cost/fill/reference-price semantics, dataset or holdout roles, universe
eligibility, or the Shariah/action-space boundary. Never weaken or delete
mathematical laws in `tests/invariants/test_quant_compiler_laws.py`.

Self-verifying compiler gate (use on every slice; serialized via `/tmp/qap-gate-heavy.lock`):

```text
uv run python scripts/qap_gate.py --pytest <target_test_paths>
uv run python scripts/qap_gate.py --full
```

Phase 00 verification:

```text
uv sync
uv run python -V
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run pyright src tests scripts
uv run python scripts/check_source_size.py
uv run lint-imports
```
