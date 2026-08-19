# QAP Open-Source Reuse Boundary

**Status:** design policy, reviewed 2026-08-17.
**Purpose:** slash commodity implementation time without importing another trading framework's economic semantics.

## Principle

QAP reuses mature OSS for algorithms, serialization, HTTP, statistical inference, API code generation, chart rendering, and test generation. QAP continues to own the semantics that make results trustworthy.

**Never outsource:** authoritative `PortfolioState`, asset quantities, matched-HODL construction, target-allocation semantics, cost/no-trade decisions, deterministic spot-fill/accounting rules, bridge/fee-asset inventory, research-family/final-OOS information state, and the definition of economic success.

Third-party objects are adapter inputs/outputs. A library's `Portfolio`, `Order`, `Strategy`, or `Backtest` object never becomes QAP's domain model merely because it exists.

## Golden-path dependency set

| Phase | Candidate | Decision | Why |
|---|---|---|---|
| 00 | `import-linter` | ADOPT NOW after tiny config spike | Maintained import-boundary enforcement; replaces bespoke graph traversal. |
| 01+ | `hypothesis` | ADOPT WHEN PHASE REACHED | Property-based testing and shrinking for inventory/accounting invariants. |
| 02 | `httpx` | ADOPT WHEN PHASE REACHED | Small explicit public REST boundary. |
| 02 | `pyarrow` | ADOPT WHEN PHASE REACHED | Mature Parquet/Arrow implementation with Python 3.14 support. |
| 02 | official `binance-sdk-spot` | EVALUATE WITH SPIKE | May remove endpoint/filter glue, but its generated Spot surface is broader than QAP needs. |
| 02/11 | `ccxt` | BORROW PATTERN / REFERENCE ONLY initially | Mature MIT exchange normalization, but much too broad to define QAP's Spot/Shariah action boundary. Reconsider for genuine multi-venue need. |
| 07 | `arch` | ADOPT WHEN PHASE REACHED | Block bootstrap, SPA/Reality Check, StepM/MCS; do not reimplement. |
| 10 | `statsmodels` | ADOPT WHEN PHASE REACHED | Established econometrics/cointegration/regression diagnostics. |
| 10 | `pyvinecopulib` | EVALUATE WITH SPIKE, likely adopt | MIT, active, Python 3.14 support, broad bivariate/asymmetric/nonparametric Copulas. Keep behind a model adapter. |
| 08 | `openapi-typescript` + lightweight fetch client | ADOPT WHEN PHASE REACHED | Prevent handwritten Python/TypeScript contract drift with small MIT tooling. |
| 08 | Hey API | EVALUATE WITH SPIKE only if useful | Strong codegen/TanStack support, but larger plugin/codegen surface. |
| 09 | `lightweight-charts` | ADOPT WHEN PHASE REACHED | Mature financial charting; satisfy NOTICE/TradingView attribution. |
| 02+ tests | HTTPX `MockTransport`; RESPX if needed | ADOPT SIMPLEST OPTION | Start built-in; add RESPX only when request matching/fixtures justify it. |

## Trading/backtest frameworks

These can be references or differential-test oracles, but do not own clean-QAP replay/accounting:

- NautilusTrader: production-grade and active, but vastly larger/instrument-richer than the bounded QAP kernel.
- LEAN: mature general trading engine; its security/order/accounting abstractions would create architectural gravity.
- Freqtrade / Hummingbot: useful crypto references, but bot/exchange workflows are not QAP's research object.
- Backtrader / backtesting.py: trade/position-centric semantics do not match inventory-first QAP; review licensing before code reuse.
- vectorbt: possible independent numerical/research oracle only; review Commons-Clause/source-available restrictions before use.

Prefer a library through its public API. If code/patterns are borrowed, record source commit and license obligations.

## Data and experiment tooling

Do not initially add MLflow, DVC, Sacred, an experiment database, or an experiment server. QAP needs only immutable manifest + code/data fingerprints + lineage + outputs. Admit DVC-like data versioning only when local immutable Parquet artifacts/hashes stop being operationally adequate; admit a database only when filesystem lookup/query/concurrency is a measured bottleneck.

Do not add Polars alongside pandas/NumPy/PyArrow until a benchmark shows a real need. One dataframe paradigm is cheaper than two.

## Statistical reuse rule

```text
QAP declares family / holdout / benchmark / claim
    -> statsmodels / arch / pyvinecopulib compute admitted math
    -> QAP converts output to a QAP observation/inference artifact
    -> QAP policy + replay + accounting remain unchanged
```

Library defaults are hypotheses, not QAP constants. Record versions, seeds, important options, and fitted artifacts when results depend on them.

## Supply-chain and license guard

- Prefer official released packages/registries; avoid arbitrary Git dependencies.
- Keep a lockfile and review direct-dependency changes.
- Record numerical-library versions in experiment provenance where material.
- Prefer permissive licenses when capability is comparable; accurately review LGPL/GPL/AGPL/Commons-Clause obligations before distribution or copying.
- Lightweight Charts requires product attribution/NOTICE compliance.
- CCXT being MIT-licensed does not make its entire API surface admissible to QAP.
- Source-available is not automatically OSI open source; vectorbt's Commons Clause needs explicit review.

## Phase-spike rule

Every dependency spike asks one bounded question: **does this remove meaningful code while preserving QAP contracts?** Inspect API ergonomics, version compatibility, determinism, numeric types, dependency weight, and license. Do not create architecture around a candidate before its phase admits it.

## Quant research/scanning extension

QAP uses a two-speed quant workflow: mature OSS may accelerate exploratory screening and commodity mathematics, but every material candidate must pass through QAP's deterministic replay, accounting, benchmark, cost, and OOS contracts before it can support an economic claim.

- **DuckDB + Polars:** admit when broad pair/universe scanning creates a measured need for Parquet query pruning and vectorized feature computation. Keep them research-only; PyArrow/Parquet remains the canonical interchange layer.
- **statsmodels / arch / pyvinecopulib:** prefer these for established econometrics, bootstrap/multiple-comparison procedures, and Copula fitting/conditional calculations rather than reimplementing estimators.
- **vectorbt Community:** optional research-acceleration spike only. It may screen candidates but cannot become QAP's final backtest authority; review its current license before adoption.
- **skfolio:** optional target-weight/CV spike only after transparent rebalancing controls exist. QAP still owns target admission, execution, inventory, and accounting.
- **QuantStats:** diagnostic/tear-sheet consumer of QAP-produced wealth/return series only; it cannot redefine benchmark or accounting semantics.
- **NautilusTrader:** differential/reference oracle for deliberately simple replay parity cases, never QAP's portfolio/accounting owner.
- **Binance Public Data / CCXT:** Phase-17 Product V1 should prefer official Binance/Gate public sources plus QAP's existing explicit adapters. CCXT stays deferred until a third venue or demonstrated duplicated adapter work earns it; if later admitted it may normalize transport/metadata only, while QAP retains canonical identity, historical-universe, provenance, Spot-admission, and accounting semantics.

Detailed decision record: `docs/research/2026-08-17-quant-oss-integration.md`.
