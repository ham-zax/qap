# Broader Audit Continuation — Strategy Math, Economics, Boundaries, and Product

Date: 2026-11-16.
Status: completed initial broader-audit assessment (`AUDIT-WIDE` per Plan 25).
Authoritative plan: [Plan 25](../plans/25-audit-repairs-and-evidence-integrity.md).
Audit baseline: [2026-11-16 Audit](../research/2026-11-16-audit/README.md).
Research policy proposal: [RD-1 Proposal](../research/2026-11-16-rd1-research-policy-proposal.md).

Update context — 2026-11-17. Trigger: final review finds stale scanner status.
Purpose: record completed retirement and the current import-contract count.
Decision impact: none. Evidence: [repair completion](2026-11-16-audit-repair-completion.md), `.importlinter`, and retained product modules.

## Equal-Coverage Assessment Across All 7 Plan 25 Areas

| Area | Current status & inspected facts | Key remaining gaps / next evidence |
| --- | --- | --- |
| **1. All strategy mathematics** | `Z-Score` (`ratio`/`ols`/`tls`/`kalman`), `Spread Copula` (`direct`/`anchored`), `Ratio Trend`, and `Anchor Lead-Lag 1m` all share causal prefix indexing, `tests/invariants/test_quant_compiler_laws.py` scale invariance (`1e-6..1e6`), and registry dispatch (`lab_strategy_registry.py`). `AR-6` fixed misleading ratio-vs-residual labels, `conditional rank` wording, and walk-forward stitched signal provenance. | Stationarity admission, independence abstention, and 96-vs-100 bar sample sufficiency remain open under `RD-1`. Forward predictive usefulness is not yet established. |
| **2. Portfolio economics** | `PortfolioState` and `PortfolioLedger` enforce immutable `Decimal` holdings, spot-only nonnegative inventory, explicit fees, next-open historical fills, and matched passive HODL + simple-control benchmarks. `AR-2`/`AR-3`/`AR-4` repaired paper partial-rotation reconciliation, venue metadata enforcement, and nonnegative book-age timing. | Multi-asset simultaneous portfolio rebalancing (shared-coin conflicts across >1 pair), explicit concentration/drawdown risk budgets, and personal-constraint modeling are not yet in the pair-MVP engine. |
| **3. Relationship maps** | Current Lab supports 2-coin pair selection plus an optional 3rd defensive/explanatory anchor (`park_anchor`, `anchored` copula, `lead_lag`). | Multi-pair relationship maps (formation-only edge selection, shared-factor redundancy across overlapping pairs, multiple-testing ledger across waves, and conflicting target resolution) require `RD-1` and follow-on design. |
| **4. Repository boundaries** | `lint-imports` enforces 5 active architectural layer contracts; `check_source_size.py` keeps hand-written modules bounded; historical raw JSON/JSONL artifacts are preserved byte-for-byte. Shared catalog/protocol code now lives in `product_market_data_catalog.py` and `product_market_data_protocol.py`. The repair removes retired scanner code, worker branches, and dedicated tests. | Scanner retirement is complete. Keep retained product data preparation and historical artifact access covered by the full gate. |
| **5. Product usefulness** | Dual interfaces (`qap.lab_cli` + FastAPI/Watermelon UI `/lab`) share one backend core, expose Simple and Pro modes, render `Swap →` markers, and surface explicit legacy-session / missing-metadata recovery states (`AR-1`–`AR-8`). | Representative-user usability testing, novice comprehension studies, and sustained live-collector reliability remain unmeasured. |
| **6. Profitability** | **Unproven.** Neither `S4-A` (0/24 Holm survivors) nor `S4-B` (0/12 Holm survivors) establishes repeatable net edge over matched HODL and simple control after 2x tuning costs. | Next evidence must wait for explicit `RD-1` contract approval, then run a small predeclared comparison on fresh, uninspected data with both benchmarks and cost stress. |
| **7. Mainstream potential** | Plausible as local-first quantitative research software for disciplined pair/spread evaluation. | Customer demand, willingness to pay/return, distribution channels, and hosted multi-tenant authentication/security (explicitly absent today; `X-QAP-Actor-Id` is workspace isolation only) remain unvalidated. |

## Scope Boundaries

- No personal allocation recommendations are made without actual user holdings, tax basis, cash flows, and risk constraints.
- New copula families, multi-asset basket expansion, partial-sizing presets, and hosted deployment remain separate follow-on work outside Plan 25.
