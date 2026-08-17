# Quant OSS Integration Decision

Date: 2026-08-17
Status: Accepted planning decision
Scope: backtesting, scanning, screening, quantitative research, portfolio tooling, performance diagnostics, and differential oracles

## Update context

- Date: 2026-08-17
- Trigger: accepted OSS/tooling research decisions for QAP.
- Purpose: replace planned custom commodity quant work with vetted dependencies while preserving QAP economic authority.
- Impact: implementation phases and dependency boundaries updated; core ownership architecture unchanged.
- Evidence: primary-source OSS review and the existing QAP design/phase plan.

## Executive decision

QAP will use a two-speed quant architecture:

1. Fast research and screening may use mature third-party numerical/query engines.
2. QAP's deterministic replay, inventory state, fees/slippage application, matched-HODL semantics, Shariah-constrained action space, and experiment/OOS identity remain authoritative QAP code.

The goal is aggressive reuse without surrendering economic truth. A package may produce measurements, candidate weights, diagnostics, or an independent comparison result. It may not silently become the owner of QAP inventory, wealth, fills, benchmark semantics, or admissible actions.

## Golden quant OSS stack

| Tool | Decision | QAP use | Boundary |
| --- | --- | --- | --- |
| PyArrow + Parquet | ADOPT NOW | canonical immutable research datasets/interchange | storage only |
| DuckDB | ADOPT WHEN SCANNING STARTS | Parquet scans, joins, universe queries | research query only |
| Polars | ADOPT WHEN SCANNING STARTS | fast pair/universe feature computation | research compute only |
| statsmodels | ADOPT WHEN RELATIONSHIP RESEARCH STARTS | econometrics and time-series primitives | measurements only |
| arch | ADOPT WHEN EVALUATION STARTS | unit-root/cointegration helpers, bootstrap, multiple-comparison tooling, volatility models | research/evaluation only |
| pyvinecopulib | ADOPT WHEN COPULA FAMILY IS TESTED | copula fitting/selection, h-functions, simulation | model evidence only |
| skfolio | EVALUATE WITH SPIKE | long-only candidate allocation, walk-forward/CV, turnover/cost experiments | target-weight candidate only |
| QuantStats | ADOPT WHEN ANALYTICS STARTS | standard return/drawdown diagnostics and tear sheets | diagnostics only |
| CCXT | ADOPT AT EXCHANGE BOUNDARY | current spot metadata and later exchange adapter primitives | no accounting ownership |
| Binance Public Data | ADOPT FOR BINANCE HISTORICAL INGEST | official spot archives/checksums | raw source only |
| NautilusTrader | DIFFERENTIAL ORACLE ONLY | event/fill model study and selected replay parity tests | never QAP authority |
| vectorbt Community | EVALUATE WITH SPIKE, RESEARCH ONLY | broad parameter/signal screening | never final economic verdict |

## Authoritative backtester decision

QAP keeps its own small deterministic replay kernel. It owns only the semantics that make the research claim meaningful:

- actual owned quantities;
- target allocation to executable spot deltas;
- no selling more than inventory;
- no negative inventory, leverage, borrowing, shorting, derivatives, or synthetic exposure;
- deterministic event ordering;
- costs applied exactly once;
- point-in-time market/universe constraints;
- matched-HODL construction;
- net portfolio wealth and relative wealth;
- experiment-family and OOS identity.

This is not a general-purpose backtester. Keeping it narrow is the anti-bloat constraint.

NautilusTrader is the preferred external differential oracle, not the QAP engine. First parity cases should be deliberately simple: buy-and-hold, periodic rebalance with zero costs, the same rebalance with explicit costs, and a fixed externally supplied target-weight path. Compare holdings, fills, costs, and terminal wealth before using it on any relationship-conditioned policy.

## Fast exploratory scanning

Research speed and economic authority are separate:

```text
immutable Parquet
      |
      +--> DuckDB: universe/time-range/query pruning
      +--> Polars: vectorized pair/universe features
      +--> statsmodels / arch / pyvinecopulib: measurements
      +--> optional vectorbt research spike
                    |
                    v
          ranked research candidates
                    |
                    v
       QAP deterministic replay + OOS evaluation
```

A fast screen may be approximate and float-based and may cheaply reject weak candidates. It may not promote a strategy or claim economic success. Every material candidate must be replayed through QAP with the declared data fingerprint, costs, universe, policy, and OOS split.

### vectorbt policy

vectorbt Community is valuable for broadcasting many parameter combinations and fast exploratory portfolio/signal calculations. It is not QAP's authoritative backtester because its portfolio abstraction is cash/position oriented rather than QAP's inventory-relative economic contract.

Its current license is Apache 2.0 with Commons Clause rather than a plain permissive OSS license. Keep it isolated as an optional research tool. The application, core package, and reproducibility contract must not depend on it. If the spike fails license/dependency/semantic review, use Polars + NumPy/SciPy and add focused compiled/vectorized kernels only after profiling.

## Pair and relationship screening

Do not implement generic statistical estimators from scratch.

Use mature primitives for:

- Pearson/Spearman/Kendall and basic distribution tests: SciPy;
- regression, Engle-Granger/Johansen and time-series econometrics: statsmodels;
- unit-root/cointegration support, bootstrap, and multiple-model comparison/evaluation: arch where its APIs match the required test;
- Gaussian, Student-t, Archimedean and vine/pair-copula fitting and conditional calculations: pyvinecopulib;
- broad data reshaping and rolling pair computation: Polars;
- Parquet candidate/universe query pruning: DuckDB.

QAP code adds only domain semantics these packages do not know: canonical unordered relation identity `{A,B}`, explicit A/B versus B/A economic orientation, point-in-time availability, feature timestamp/causality contracts, uncertainty/admission metadata, and mapping evidence to a portfolio target policy.

Do not add DCC, change-point detection, graph topology, ML, or feature-extraction frameworks merely because libraries exist. They enter only after a falsifiable experiment requires them. `ruptures` remains deferred while Python 3.14 support is unresolved and until a concrete regime-change experiment earns the dependency.

## Crypto universe and market-data screening

Use `binance/binance-public-data` as a primary raw source for Binance spot historical files where appropriate and preserve/verify published checksums.

Do not infer a point-in-time historical universe from today's `exchangeInfo` or CCXT market list. The official public-data repository does not by itself establish a complete historical listing/delisting manifest, and 2026 issue reports show archive discrepancies that justify source reconciliation rather than blind trust.

QAP therefore still owns source manifests, file checksums/fingerprints, symbol lifecycle evidence, listing/delisting/rename provenance where known, daily/monthly/API reconciliation policy for suspect data, and point-in-time universe admission.

CCXT is useful for current market metadata and later live spot exchange adaptation. It is not historical-universe authority. CoinGecko or other aggregators may provide supplementary metadata only.

Do not introduce `cryptofeed` as a new dependency: its upstream repository was archived in July 2026. Study patterns only if useful.

## Portfolio and rebalancing stack

QAP will not recreate generic portfolio optimization algorithms.

`skfolio` is the preferred evaluation spike when the project reaches model-driven target-weight research. It can produce candidate weights and provide walk-forward/CV, turnover/cost, and long-only portfolio machinery. The boundary is strict:

```text
skfolio candidate model
       |
       v
candidate target weights
       |
       v
QAP policy contract
       |
       v
QAP rebalance decision -> QAP execution -> QAP accounting
```

skfolio never mutates QAP inventory or defines QAP success. A simple transparent baseline remains mandatory so an optimizer must demonstrate incremental value rather than complexity.

Riskfolio-Lib, PyPortfolioOpt, cvxportfolio, and similar optimizers remain references unless a specific experiment exposes a capability the chosen stack cannot provide.

## Performance and diagnostics

QAP owns the wealth/equity series and benchmark-relative series. Third-party analytics may consume those outputs.

Adopt QuantStats when the analytics/reporting phase begins for standard diagnostics and tear sheets, after validating metric conventions against a small golden dataset. It may not redefine terminal wealth, matched-HODL relative wealth, fees/slippage, turnover, inventory attribution, or benchmark construction.

## Implementation work removed or reduced

Delete or sharply reduce these custom tasks:

1. Generic dataframe/query acceleration layer: use DuckDB/Polars over Parquet.
2. Generic cointegration/unit-root/econometric estimators: use statsmodels/arch adapters.
3. Generic bootstrap and multiple-comparison machinery: use arch where semantics match; QAP keeps experiment-family bookkeeping.
4. Copula distribution fitting/selection/h-functions: wrap pyvinecopulib rather than implement families.
5. Generic portfolio optimizer/cross-validation framework: spike skfolio instead of building one.
6. Generic tear-sheet/performance-statistics package: use QuantStats for standard diagnostics.
7. General event-driven trading framework: do not build one; QAP replay remains deliberately narrow.
8. High-throughput parameter-sweep framework: spike vectorbt and otherwise use Polars/vectorized kernels; do not invent a plugin framework.

What cannot be deleted: deterministic inventory replay; QAP accounting truth; matched-HODL semantics; point-in-time universe/provenance; Shariah action admissibility; canonical pair/orientation semantics; cost/no-trade/partial-rebalance semantics; experiment lineage/OOS/search-denominator bookkeeping; and narrow adapters translating third-party outputs into QAP-owned contracts.

## Phase-plan deltas

Apply these deltas to the existing phase plan; phase objectives otherwise remain unchanged.

| Existing phase concern | Plan change |
| --- | --- |
| Repository/foundation | Classify dependencies as runtime, research-only, or oracle-only. No framework registry. |
| Historical market data and universe | Keep PyArrow/Parquet canonical; add Binance Public Data checksum ingestion; add DuckDB when scan queries justify it; preserve QAP historical-universe provenance. |
| Portfolio/accounting | No optimizer dependency. Keep Decimal/inventory/accounting authority QAP-owned. |
| Deterministic execution/replay | Keep narrow QAP kernel. Add NautilusTrader differential-oracle spike only after baseline replay is green. |
| Baseline rebalancing | No framework needed. Transparent QAP policies and benchmark ladder stay authoritative. |
| Relationship evidence | Use SciPy/statsmodels/arch; wrap pyvinecopulib only when copula experiments begin. |
| High-throughput screening | Add DuckDB + Polars. Evaluate vectorbt only as optional research acceleration; final candidates go through QAP replay. |
| Allocation research | Spike skfolio for candidate target weights/CV only after simple cost-aware rebalancing is established. |
| Economic evaluation/OOS | Use arch bootstrap/multiple-comparison primitives where appropriate; keep QAP experiment-family and OOS identity. |
| Analytics/workbench | Add QuantStats diagnostics only from QAP-produced wealth/return series. |
| Live-readiness | CCXT remains the candidate spot exchange boundary; do not adopt archived cryptofeed. |
| Operations/autonomy | No quant framework may move from research-only to runtime without explicit dependency and semantic review. |

## Dependency admission rules

Before adding any quant package to the main environment, answer all of:

1. Which current QAP task disappears because of this dependency?
2. Is the package runtime, research-only, or oracle-only?
3. Does it try to own cash, positions, fills, P&L, clocks, or portfolio state?
4. Can QAP consume its result through a narrow value-object/dataframe boundary?
5. Does it support the project's Python version on the target platform?
6. Is its license acceptable for the intended use?
7. Can the same experiment be reproduced without hidden service state?
8. What is the removal/fallback path if it becomes abandoned or incompatible?

If there is no current task deletion or experimentally required capability, do not add it.

## Research-to-authority promotion rule

```text
fast scan
  -> reproducible candidate
  -> QAP deterministic replay
  -> matched benchmarks
  -> realistic costs
  -> OOS / multiple-testing evaluation
  -> only then eligible for policy consideration
```

No result produced solely by vectorbt, skfolio, a copula library, a notebook, or an external backtester may skip this chain.

## Repositories worth studying without adopting as architecture

- `nautechsystems/nautilus_trader`: deterministic clocks, event/fill architecture, testing patterns.
- `polakowo/vectorbt`: high-throughput broadcasting and vectorized screening patterns; license-isolated research only.
- `skfolio/skfolio`: walk-forward/CV and portfolio-model evaluation patterns.
- `cvxgrp/cvxportfolio`: transaction-cost-aware allocation ideas and test patterns; reference only unless later required.
- `stefan-jansen/zipline-reloaded` and `pyfolio-reloaded`: reference patterns only; do not inherit cash/equity assumptions.
- `freqtrade/freqtrade` and `hummingbot/hummingbot`: exchange/runtime operational patterns only; not QAP economic kernels.

Clone for study only when a concrete implementation task needs the pattern; do not vendor these projects.

## Explicit rejected or deferred choices

- General trading/backtesting framework as QAP accounting authority: rejected.
- vectorbt as final backtest authority: rejected.
- NautilusTrader as QAP portfolio/accounting owner: rejected.
- Backtrader/Zipline/LEAN/bt/backtesting.py as core engine: rejected; reference only where useful.
- Freqtrade/Hummingbot/Jesse as strategy runtime: rejected for core architecture.
- cryptofeed as a new dependency: rejected because upstream is archived.
- `ruptures` now: deferred pending a concrete experiment and stable Python 3.14 support.
- Risk/optimizer megastack now: deferred; transparent rebalancing baselines come first.

## Architecture impact verdict

GO on integrating the OSS stack into the plan.

NO-GO on changing QAP's core ownership architecture.

QAP should stay small where semantics are unique and aggressively reuse OSS where mathematics, storage/query, optimization, or diagnostics are commodity capabilities.

## Primary-source references checked on 2026-08-17

- https://github.com/polakowo/vectorbt
- https://github.com/nautechsystems/nautilus_trader
- https://github.com/skfolio/skfolio
- https://github.com/ranaroussi/quantstats
- https://github.com/pola-rs/polars
- https://github.com/duckdb/duckdb-python
- https://github.com/statsmodels/statsmodels
- https://github.com/bashtage/arch
- https://pypi.org/project/pyvinecopulib/
- https://github.com/ccxt/ccxt
- https://github.com/binance/binance-public-data
- https://github.com/bmoscon/cryptofeed
