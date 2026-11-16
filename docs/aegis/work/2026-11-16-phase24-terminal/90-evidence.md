# Integration evidence

- `uv run python scripts/qap_gate.py --full`: exit 0, 12 passes, 451.45 seconds.
  Covers lint, formatting, size, import layers, Python types, API schema, TypeScript,
  invariant laws, full Python tests, engine parity, full web tests, and production build.
- `pnpm --pm-on-fail=ignore --dir web test`: exit 0, 78 tests before the final cancellation test.
  The later full compiler gate includes that test and all subsequent source changes.
- `git diff --check`: exit 0.
- Impeccable detector: exit 0, no findings on Lab and shared components.
- Browser: real API, desktop and mobile, dark/light themes, local coin search,
  Pro controls, saved-run restoration, strategy execution, and wealth rendering.
- Directory: 619 Binance rows, 415 trading rows. The previous 600-row limit omitted 19 trading rows.
- Invariants: no edits to mathematical-law tests.

Confidence: B for the integration slice. Phase 24 acceptance remains partial.
No claim of profitable strategy performance, live-capital readiness, or multi-day paper stability.
The checkpoint records chart latency, header placement, and benchmark-option gaps.

Reflection: mock success concealed missing styles and incomplete state restoration.
The old running API also concealed the current contract. Provider quota and credit
failures interrupted the previous session. Proposed repository fixes appear in
[future improvements](../../../future-improvements.md).
