# Recorded engine parity inputs

Captured on 2026-10-02 from Binance public spot `/api/v3/klines` at
`https://data-api.binance.vision`. The frozen window is 2026-04-01 through
2026-10-01 exclusive, 17,568 completed 15m bars for BTCUSDT, ETHUSDT and SOLUSDT.

Each gzip JSONL file contains the exact source response text and request URL,
retrieval time and SHA-256. `manifest.json` records all requests, raw/artifact
hashes and semantic fingerprints. Parquet metadata retains the explicit venue,
symbol, assets, interval and bar-series fingerprint. No current workspace catalog
or economic result is modified by acquisition.

These are fixed-basket accounting verification inputs, not holdout or strategy
selection evidence. Tests verify raw byte hashes; the offline parity harness
verifies artifact and semantic fingerprints before replay.

Acquisition is explicit and refuses to replace existing inputs:

```bash
uv run python scripts/capture_engine_parity.py --output /tmp/qap-parity-inputs
```

The ordinary tests and parity report need no network access. The raw API
recordings are preserved directly; no Khiip documentation capture is claimed.
