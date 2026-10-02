# Phase 19 — Independent engine parity

Update context — 2026-10-02
Trigger: Hamza asked to continue the approved backend work, stopping before dashboard generation.
Purpose: record the M1 accounting gate before pair-data integration.
Impact: no changes to economic objectives, costs, fills, benchmarks or holdout roles.
Evidence: [machine-readable report](2026-10-02-engine-parity.json), [recorded sources](../../tests/fixtures/engine_parity/README.md).

All twelve comparisons pass: terminal values agree within 0.01%, executed leg counts match, and each inventory coordinate agrees within 0.0001 USDT of value. The five explicit QAP hand-computed inventory cases match exactly. `bt` checks those arithmetic cases within 1e-10 floating precision.

| Pair | Strategy | QAP terminal (USDT) | bt terminal (USDT) | Legs (both) | Relative error |
| --- | --- | ---: | ---: | ---: | ---: |
| BTC/ETH | hodl | 12533.05462321 | 12533.05462321 | 0 | 2.22e-16 |
| BTC/ETH | periodic | 12566.68693122 | 12566.68693122 | 352 | 4.44e-16 |
| BTC/ETH | threshold | 12533.05462321 | 12533.05462321 | 0 | 2.22e-16 |
| BTC/ETH | signal | 12558.47247723 | 12558.47247723 | 352 | 1.78e-15 |
| BTC/SOL | hodl | 13252.59268041 | 13252.59268041 | 0 | 2.22e-16 |
| BTC/SOL | periodic | 13280.60834992 | 13280.60834992 | 352 | 2.22e-16 |
| BTC/SOL | threshold | 13252.59268041 | 13252.59268041 | 0 | 2.22e-16 |
| BTC/SOL | signal | 12321.57499444 | 12321.57499444 | 350 | 1.22e-15 |
| ETH/SOL | hodl | 13496.37240135 | 13496.37240135 | 0 | 2.22e-16 |
| ETH/SOL | periodic | 13541.49931645 | 13541.49931645 | 356 | 0 |
| ETH/SOL | threshold | 13629.51445274 | 13629.51445274 | 4 | 0 |
| ETH/SOL | signal | 12548.10064187 | 12548.10064187 | 356 | 2.89e-15 |

Inputs: 2026-04-01 through 2026-10-01 (exclusive), 17,568 completed 15-minute bars per coin. Starting inventory is an equal-value mix worth 10,000 USDT at the first completed close; its acquisition is not charged as a simulated trade.

Predeclared controls: daily equal-value rebalancing, 5 percentage-point drift rebalancing, and a daily ratio signal using the preceding 96 bars with a 1% deviation and 25%/75% targets. Every executed leg pays 10 basis points in fees and 5 basis points of adverse slippage; minimum rebalance notional is 1 USDT. There was no parameter selection against these recordings.

The reference imports no QAP accounting or execution code. It books transactions, fees, holdings and cash through `bt.Strategy`; only raw prices and declared policy rules are shared. QAP uses the ordinary deterministic replay with a continuous `PortfolioLedger` and bounded two-bar windows. This avoids retaining quadratic diagnostic history while preserving each completed-close decision and next-open fill. Synthetic regression cases pin next-open gaps, last-bar non-execution, both-leg costs and unowned-inventory refusal.

Scope: fixed-basket accounting parity, not policy correctness, trading edge, point-in-time discovery performance or holdout evidence. Real pair runs use explicit USDT settlement and historically unconstrained market metadata. Direct conversion and quantity rounding are covered by exact hand cases. Volume-dependent slippage, live precision and direct-pair route selection are outside this report.

Verification: seven parity test cases and five existing verification-runner tests passed. The full Python suite passed with **769 passed, 1 skipped** before M2 owner changes began; all 116 web tests and the production build passed. Ruff, Pyright, import-linter and source-size checks passed for M1. An independent read-only Muse review found no verified blockers; its inventory-coordinate suggestion was incorporated.

Reproduce offline:

```bash
uv run python -m scripts.engine_parity --output /tmp/qap-engine-parity.json
uv run pytest -q tests/engine_parity
```

The `--max-bars` option is for smoke checks and does not satisfy full-window acceptance.
